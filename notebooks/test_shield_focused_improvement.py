"""Checks for threshold counts/ties, leakage guards and the resumable experiment path."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification

from shield_focused_improvement import (
    Config, clean_data, fitted_features, make_pipeline, metrics, run_focus, select_threshold, threshold_table,
)


class ThresholdTests(unittest.TestCase):
    def test_threshold_counts_match_predictions_including_ties(self):
        y = np.array([0, 1, 0, 1, 1, 0, 0, 1])
        score = np.array([.1, .1, .4, .4, .4, .8, .8, .9])
        table = threshold_table(y, score)
        for _, row in table.iterrows():
            actual = metrics(y, score, row.Threshold)
            for key in ["TP", "FP", "TN", "FN"]:
                self.assertEqual(row[key], actual[key])
            self.assertAlmostEqual(row.F2 * 100, actual["F2-Score (%)"])

    def test_target_selection_and_unattainable_target_fallback(self):
        config = Config()
        both = pd.DataFrame({"Threshold": [.1, .5, .9], "Precision": [.4, .8, 1.],
                             "Recall": [1., .8, .2], "F2": [.7, .8, .24]})
        self.assertEqual(select_threshold(both, config), (.5, True))
        neither = both.copy()
        neither.loc[1, "Precision"] = .6
        self.assertEqual(select_threshold(neither, config), (.5, False))

    def test_guard_duplicate_company_and_predictor_rows(self):
        d = pd.DataFrame({"x": [1, 1, 2], "Bankrupt": [0, 1, 0]})
        with self.assertRaisesRegex(ValueError, "Repeated predictor"):
            clean_data(d, 1)
        d = pd.DataFrame({"Company": [1, 1, 2], "x": [1, 2, 3], "Bankrupt": [0, 1, 0]})
        with self.assertRaisesRegex(ValueError, "Repeated Company"):
            clean_data(d, 1)

    def test_all_feature_mode_excludes_identifier_target_and_retains_constants(self):
        raw = pd.DataFrame({"Company": range(12), "f1": np.arange(12)*.1,
                            "f2": np.arange(12)**2, "constant": 1,
                            "Bankrupt": [1,1]+[0]*10})
        X, y = clean_data(raw, 2, retain_constants=True)
        self.assertEqual(X.columns.tolist(), ["f1", "f2", "constant"])
        baseline_X, _ = clean_data(raw, 2)
        self.assertEqual(baseline_X.columns.tolist(), ["f1", "f2"])
        for smote in [None, .5]:
            spec = dict(model="RandomForest", smote=smote, params=dict(n_estimators=4, max_depth=2))
            pipe = make_pipeline(spec, Config(feature_mode="all", top_k=2, smote_neighbors=1, model_jobs=1))
            self.assertNotIn("ig", pipe.named_steps)
            pipe.fit(X,y)
            self.assertEqual(pipe.named_steps['model'].n_features_in_,3)
            self.assertEqual(fitted_features(pipe,X.columns),X.columns.tolist())
            self.assertEqual(pipe.predict_proba(X).shape,(12,2))

    def test_invalid_feature_mode_rejected(self):
        with self.assertRaisesRegex(ValueError,"feature_mode"):
            make_pipeline(dict(model="RandomForest",smote=None,params={}),Config(feature_mode="invalid"))

    def test_end_to_end_and_resume(self):
        X, y = make_classification(n_samples=500, n_features=10, n_informative=5,
                                   weights=[.94, .06], flip_y=0, random_state=7)
        raw = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
        raw["Bankrupt"] = y
        config = Config(folds=2, top_k=6, smote_neighbors=2, model_jobs=1)
        specs = [dict(id="RF_SMOTE025", model="RandomForest", smote=.25,
                      params=dict(n_estimators=8, max_depth=4)),
                 dict(id="XGB_TEST", model="XGBoost", smote=None,
                      params=dict(n_estimators=8, max_depth=2, learning_rate=.1))]
        test_dir = Path(__file__).resolve().parent.parent / "reports" / ".focused_verification"
        test_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=test_dir) as folder:
            first = run_focus(raw, folder, config, "synthetic verification only", specs)
            second = run_focus(raw, folder, config, "synthetic verification only", specs)
            pd.testing.assert_frame_equal(first["training_results"], second["training_results"])
            self.assertEqual(first["choice"], second["choice"])
            membership = pd.read_csv(first["output_dir"] / "partition_membership.csv")
            self.assertEqual(len(membership), len(raw))
            self.assertEqual(membership.Source_Row.nunique(), len(raw))
            training_rows = set(membership[membership.Partition == "training"].Source_Row)
            holdout_rows = set(membership[membership.Partition == "holdout"].Source_Row)
            self.assertFalse(training_rows & holdout_rows)
            for candidate in ["RF_SMOTE025", "XGB_TEST"]:
                oof = pd.read_csv(first["output_dir"] / f"{candidate}_oof_predictions.csv")
                self.assertEqual(set(oof.Source_Row), training_rows)
                self.assertFalse(set(oof.Source_Row) & holdout_rows)
            self.assertTrue((Path(first["output_dir"]) / "selected_feature_manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
