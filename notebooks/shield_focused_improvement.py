"""Training-fold threshold experiments for SHIELD; also embedded in the Colab notebook."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
from dataclasses import asdict, dataclass
from functools import partial
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.metrics import (
    accuracy_score, average_precision_score, classification_report, confusion_matrix,
    f1_score, fbeta_score, precision_recall_curve, precision_score, recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from xgboost import XGBClassifier


@dataclass(frozen=True)
class Config:
    seed: int = 42
    folds: int = 5
    test_size: float = 0.20
    top_k: int = 20
    smote_neighbors: int = 5
    target_precision: float = 0.70
    target_recall: float = 0.70
    model_jobs: int = 2
    include_leaf_variants: bool = True
    evaluate_holdout: bool = True
    feature_mode: str = "ig20"  # ig20: top-k IG; all: every financial predictor, no IG
    version: str = "shield-focused-threshold-v2"


def candidate_specs(include_leaf_variants=True):
    rf = dict(n_estimators=200, max_depth=10, min_samples_split=2,
              min_samples_leaf=1, max_features="sqrt", class_weight=None)
    xgb = dict(n_estimators=100, max_depth=6, learning_rate=0.1)
    specs = [
        dict(id="RF_SMOTE025", model="RandomForest", smote=0.25, params=rf.copy()),
        dict(id="RF_SMOTE050", model="RandomForest", smote=0.50,
             params={**rf, "min_samples_split": 5}),
        dict(id="XGB_SMOTE010", model="XGBoost", smote=0.10, params=xgb.copy()),
        dict(id="XGB_SMOTE050", model="XGBoost", smote=0.50, params=xgb.copy()),
        dict(id="RF_NO_SMOTE", model="RandomForest", smote=None, params=rf.copy()),
        dict(id="RF_NO_SMOTE_WEIGHTED", model="RandomForest", smote=None,
             params={**rf, "class_weight": "balanced_subsample"}),
        dict(id="XGB_NO_SMOTE", model="XGBoost", smote=None, params=xgb.copy()),
    ]
    if include_leaf_variants:
        specs += [
            dict(id="RF_SMOTE025_LEAF3", model="RandomForest", smote=0.25,
                 params={**rf, "min_samples_leaf": 3}),
            dict(id="RF_SMOTE025_LEAF3_FEATURES050", model="RandomForest", smote=0.25,
                 params={**rf, "min_samples_leaf": 3, "max_features": 0.5}),
        ]
    return specs


def clean_data(raw, top_k, retain_constants=False):
    df = raw.copy()
    if "Bankrupt" not in df:
        raise ValueError("Input must have Bankrupt: 0=Not Bankrupt, 1=Bankrupt.")
    if "Company" in df and df["Company"].duplicated().any():
        raise ValueError("Repeated Company IDs: resolve/group them before splitting.")
    df = df.drop(columns=["Company"], errors="ignore")
    if not retain_constants:
        df = df.drop(columns=[c for c in df if c != "Bankrupt" and
                              df[c].nunique(dropna=False) <= 1])
    if df.isna().any().any():
        raise ValueError("Missing data: investigate before running this comparison.")
    if set(df["Bankrupt"].unique()) != {0, 1}:
        raise ValueError("Bankrupt must contain exactly the labels 0 and 1.")
    X = df.drop(columns="Bankrupt")
    if len(X.columns) < top_k or not all(pd.api.types.is_numeric_dtype(X[c]) for c in X):
        raise ValueError("Supply at least top_k numeric financial predictors, before IG/SMOTE.")
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError("Infinite values in input.")
    if X.duplicated().any():
        raise ValueError("Repeated predictor rows: investigate/group these before CV.")
    y = df["Bankrupt"].astype(int)
    if y.value_counts()[1] >= y.value_counts()[0]:
        raise ValueError("This experiment expects Bankrupt=1 to be the minority class.")
    return X, y


def make_pipeline(spec, config, memory=None):
    if config.feature_mode not in {"ig20", "all"}:
        raise ValueError("feature_mode must be ig20 or all.")
    if spec["model"] == "RandomForest":
        model = RandomForestClassifier(**spec["params"], random_state=config.seed,
                                       n_jobs=config.model_jobs)
    else:
        model = XGBClassifier(**spec["params"], random_state=config.seed,
                              n_jobs=config.model_jobs, eval_metric="logloss")
    steps = []
    if config.feature_mode == "ig20":
        selector = SelectKBest(partial(mutual_info_classif, random_state=config.seed),
                               k=config.top_k).set_output(transform="pandas")
        steps.append(("ig", selector))
    if spec["smote"] is not None:
        steps.append(("smote", SMOTE(sampling_strategy=spec["smote"],
                                      random_state=config.seed,
                                      k_neighbors=config.smote_neighbors)))
    steps.append(("model", model))
    return Pipeline(steps, memory=memory)


def fitted_features(pipe, columns):
    if "ig" in pipe.named_steps:
        return columns[pipe.named_steps["ig"].get_support()].tolist()
    return list(columns)


def data_fingerprint(X, y):
    hasher = hashlib.sha256()
    hasher.update(pd.util.hash_pandas_object(X, index=True).values.tobytes())
    hasher.update(pd.util.hash_pandas_object(y, index=True).values.tobytes())
    hasher.update(json.dumps([(c, str(X[c].dtype)) for c in X]).encode())
    return hasher.hexdigest()


def metrics(y, scores, threshold):
    pred = (np.asarray(scores) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "Accuracy (%)": accuracy_score(y, pred) * 100,
        "Precision (%)": precision_score(y, pred, zero_division=0) * 100,
        "Recall (%)": recall_score(y, pred, zero_division=0) * 100,
        "F1-Score (%)": f1_score(y, pred, zero_division=0) * 100,
        "ROC-AUC (%)": roc_auc_score(y, scores) * 100,
        "F2-Score (%)": fbeta_score(y, pred, beta=2, zero_division=0) * 100,
        "Average Precision (%)": average_precision_score(y, scores) * 100,
        "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
    }


def threshold_table(y, scores):
    """Exact observed thresholds; equal scores are always kept in the same group."""
    y, scores = np.asarray(y), np.asarray(scores)
    p, r, thresholds = precision_recall_curve(y, scores)
    p, r = p[:-1], r[:-1]  # final (precision=1, recall=0) has no threshold
    tp = np.rint(r * np.sum(y == 1)).astype(int)
    positives = np.searchsorted(np.sort(scores), thresholds, side="left")
    fp = len(scores) - positives - tp
    fn = int(np.sum(y == 1)) - tp
    tn = int(np.sum(y == 0)) - fp
    f1 = np.divide(2*p*r, p+r, out=np.zeros_like(p), where=(p+r) > 0)
    f2 = np.divide(5*p*r, 4*p+r, out=np.zeros_like(p), where=(4*p+r) > 0)
    return pd.DataFrame({"Threshold": thresholds, "Precision": p, "Recall": r,
                         "F1": f1, "F2": f2, "TP": tp, "FP": fp, "FN": fn, "TN": tn})


def select_threshold(table, config):
    """First try both 70% targets, otherwise maximize F2 subject to the recall floor."""
    recall_ok = table[table.Recall >= config.target_recall - 1e-12]
    both_ok = recall_ok[recall_ok.Precision >= config.target_precision - 1e-12]
    pool = both_ok if len(both_ok) else recall_ok
    if pool.empty:
        raise ValueError("No threshold satisfies the configured recall floor.")
    selected = pool.sort_values(["F2", "Precision", "Recall", "Threshold"],
                                ascending=[False, False, False, False]).iloc[0]
    return float(selected.Threshold), bool(len(both_ok))


def wilson_interval(successes, total):
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denom = 1 + z*z/total
    center = (p + z*z/(2*total))/denom
    margin = z*np.sqrt(p*(1-p)/total + z*z/(4*total*total))/denom
    return [float(100*(center-margin)), float(100*(center+margin))]


def _write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def run_focus(raw, output_base, config=Config(), source_note="", specs=None):
    """Tune from OOF training predictions. Freeze choices before touching holdout labels."""
    specs = candidate_specs(config.include_leaf_variants) if specs is None else specs
    if not specs or len({s["id"] for s in specs}) != len(specs):
        raise ValueError("Supply distinct candidate IDs.")
    if "RF_SMOTE025" not in {s["id"] for s in specs}:
        raise ValueError("Include RF_SMOTE025 as the reference baseline.")
    if config.feature_mode not in {"ig20", "all"}:
        raise ValueError("feature_mode must be ig20 or all.")
    X, y = clean_data(raw, config.top_k, retain_constants=config.feature_mode == "all")
    train_idx, test_idx = train_test_split(np.arange(len(y)), test_size=config.test_size,
                                          random_state=config.seed, stratify=y)
    X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
    X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]
    cv = list(StratifiedKFold(config.folds, shuffle=True, random_state=config.seed)
              .split(X_train, y_train))
    for a, b in cv:
        if len(np.intersect1d(a, b)) or y_train.iloc[b].nunique() != 2:
            raise ValueError("Invalid validation fold.")
        counts = y_train.iloc[a].value_counts()
        for spec in specs:
            if spec["smote"] is not None and (
                counts[1] <= config.smote_neighbors or
                int(spec["smote"] * counts[0]) <= counts[1]
            ):
                raise ValueError("SMOTE is not feasible for this data/fold/configuration.")
    versions = {name: importlib.metadata.version(name) for name in
                ["numpy", "pandas", "scikit-learn", "imbalanced-learn", "xgboost", "joblib"]}
    run_spec = dict(config=asdict(config), candidates=specs, packages=versions,
                    python=platform.python_version(), data_fingerprint=data_fingerprint(X, y),
                    source_note=source_note, rows=len(y), predictors=len(X.columns),
                    labels=y.value_counts().sort_index().to_dict(),
                    selection_policy="both targets if feasible; otherwise max F2 with recall >= target",
                    interpretation="OOF threshold/candidate-selection scores are tuning scores; holdout was historically reused")
    run_id = hashlib.sha256(json.dumps(run_spec, sort_keys=True).encode()).hexdigest()[:16]
    out = Path(output_base) / run_id
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "run_config.json", run_spec)
    membership = pd.DataFrame({"Source_Row": train_idx, "Partition": "training",
                               "Fold": np.zeros(len(train_idx), dtype=int)})
    for fold, (_, b) in enumerate(cv, 1):
        membership.loc[b, "Fold"] = fold
    membership = pd.concat([membership, pd.DataFrame({"Source_Row": test_idx,
                            "Partition": "holdout", "Fold": -1})], ignore_index=True)
    membership.to_csv(out / "partition_membership.csv", index=False)
    memory = joblib.Memory(out / "pipeline_cache", verbose=0)
    summary_rows, threshold_frames, fold_rows = [], {}, []
    print(f"Run {run_id}: {len(specs)} candidates x {config.folds} training folds", flush=True)
    print(f"Feature mode: {config.feature_mode}; input predictors: {len(X.columns)}. "
          "SMOTE fit on training folds only; thresholds use OOF training predictions.", flush=True)
    print("OOF selection metrics are exploratory tuning results, not an unbiased final estimate.", flush=True)
    for spec in specs:
        scores = np.full(len(y_train), np.nan)
        assigned = np.zeros(len(y_train), dtype=int)
        for fold, (a, b) in enumerate(cv, 1):
            cp = out / f"{spec['id']}_fold{fold}.npz"
            detail_path = out / f"{spec['id']}_fold{fold}.json"
            if cp.exists() and detail_path.exists():
                saved = np.load(cp, allow_pickle=False)
                np.testing.assert_array_equal(saved["validation_positions"], b)
                fold_scores = saved["scores"]
                detail = json.loads(detail_path.read_text(encoding="utf-8"))
            else:
                start = time.perf_counter()
                pipe = make_pipeline(spec, config, memory)
                pipe.fit(X_train.iloc[a], y_train.iloc[a])
                positive_column = list(pipe.classes_).index(1)
                fold_scores = pipe.predict_proba(X_train.iloc[b])[:, positive_column]
                chosen = fitted_features(pipe, X.columns)
                detail = dict(Candidate=spec["id"], Fold=fold, Training_Count=len(a),
                              Validation_Count=len(b), Selected_Features=chosen,
                              Elapsed_Seconds=time.perf_counter()-start,
                              **metrics(y_train.iloc[b], fold_scores, 0.5))
                np.savez_compressed(cp, validation_positions=b, scores=fold_scores)
                _write_json(detail_path, detail)
            scores[b] = fold_scores
            assigned[b] += 1
            fold_rows.append(detail)
            print(f"  {spec['id']} fold {fold}/{config.folds} complete", flush=True)
        assert np.all(assigned == 1) and np.isfinite(scores).all()
        pd.DataFrame({"Source_Row": train_idx, "True_Label": y_train.to_numpy(),
                      "OOF_Score": scores, "Fold": membership.iloc[:len(train_idx)].Fold.to_numpy()
                      }).to_csv(out / f"{spec['id']}_oof_predictions.csv", index=False)
        table = threshold_table(y_train, scores)
        table.to_csv(out / f"{spec['id']}_thresholds.csv", index=False)
        threshold_frames[spec["id"]] = table
        threshold, feasible = select_threshold(table, config)
        chosen_metrics = metrics(y_train, scores, threshold)
        for rule, t in [("Default 0.5", 0.5), ("OOF selected", threshold)]:
            row = dict(Model=spec["model"], Experiment="80-20 + training CV threshold study",
                       Split=config.test_size, CV=config.folds, Candidate=spec["id"],
                       SMOTE_Ratio=spec["smote"], Decision_Rule=rule, Threshold=t,
                       Feature_Mode=config.feature_mode,
                       Feature_Count=config.top_k if config.feature_mode == "ig20" else len(X.columns),
                       Best_Params=spec["params"], Parameter_Source="predeclared fixed candidate",
                       Evaluation="training OOF tuning; not independent test",
                       **metrics(y_train, scores, t))
            row["CV_F1_Mean (%)"] = float(np.mean([
                f1_score(y_train.iloc[b], scores[b] >= t, zero_division=0)*100 for _, b in cv]))
            row["Both_Targets_Feasible_OOF"] = feasible
            recall_pool = table[table.Recall >= config.target_recall - 1e-12]
            row["Max_Precision_At_Target_Recall (%)"] = float(recall_pool.Precision.max()*100)
            summary_rows.append(row)
        print(f"  OOF cutoff {threshold:.6f}: P={chosen_metrics['Precision (%)']:.2f}% "
              f"R={chosen_metrics['Recall (%)']:.2f}% F2={chosen_metrics['F2-Score (%)']:.2f}% "
              f"both targets={feasible}", flush=True)
        pd.DataFrame(summary_rows).to_csv(out / "training_oof_results.csv", index=False)
    results = pd.DataFrame(summary_rows)
    selected = results[results.Decision_Rule == "OOF selected"]
    winner = selected.sort_values(["Both_Targets_Feasible_OOF", "F2-Score (%)", "Precision (%)", "Candidate"],
                                  ascending=[False, False, False, True]).iloc[0]
    choice = dict(Candidate=winner.Candidate, Threshold=float(winner.Threshold),
                  Selection_Data="training OOF only", Both_Targets_Feasible_OOF=bool(winner.Both_Targets_Feasible_OOF),
                  Holdout_Status="not evaluated yet", Run_ID=run_id)
    _write_json(out / "frozen_choice.json", choice)  # freeze before predicting holdout
    pd.DataFrame(fold_rows).to_json(out / "fold_details.json", orient="records", indent=2)
    plot_training_curves(results, threshold_frames, out, config)
    test_rows = []
    if config.evaluate_holdout:
        ids = list(dict.fromkeys(["RF_SMOTE025", winner.Candidate]))
        specs_by_id = {s["id"]: s for s in specs}
        for candidate in ids:
            spec = specs_by_id[candidate]
            pipe = make_pipeline(spec, config, memory)
            pipe.fit(X_train, y_train)
            score = pipe.predict_proba(X_test)[:, list(pipe.classes_).index(1)]
            rules = [("Reference default 0.5", 0.5)] if candidate == "RF_SMOTE025" else []
            if candidate == winner.Candidate:
                if candidate != "RF_SMOTE025":
                    rules.append(("Selected candidate default 0.5", 0.5))
                rules.append(("Frozen OOF threshold", float(winner.Threshold)))
                joblib.dump(pipe, out / "selected_training_pipeline.joblib")
                _write_json(out / "selected_feature_manifest.json", {
                    "Candidate": candidate, "Threshold": float(winner.Threshold),
                    "Features": fitted_features(pipe, X.columns),
                    "Feature_Mode": config.feature_mode,
                    "All_Input_Columns": X.columns.tolist(),
                    "Score_Meaning": "uncalibrated bankruptcy model score; not validated risk-band probability",
                    "Production_Status": "research candidate; prototype unchanged"})
            prediction_data = pd.DataFrame({"Source_Row": test_idx, "True_Label": y_test.to_numpy(),
                                            "Score": score})
            for rule, threshold in rules:
                m = metrics(y_test, score, threshold)
                row = dict(Model=spec["model"], Experiment="80-20 + CV=5 threshold study",
                           Split=config.test_size, CV=config.folds, Candidate=candidate,
                           Decision_Rule=rule, Threshold=threshold, Best_Params=spec["params"],
                           Feature_Mode=config.feature_mode,
                           Feature_Count=config.top_k if config.feature_mode == "ig20" else len(X.columns),
                           **m, **{"CV_F1_Mean (%)": None},
                           Evaluation="historically reused 80:20 holdout; exploratory",
                           Precision_95CI=wilson_interval(m["TP"], m["TP"]+m["FP"]),
                           Recall_95CI=wilson_interval(m["TP"], m["TP"]+m["FN"]))
                test_rows.append(row)
                prediction_data[rule] = (score >= threshold).astype(int)
                print(f"\n=== Classification Report: {spec['model']} | {rule} ===")
                print(classification_report(y_test, score >= threshold, labels=[0, 1],
                      target_names=["Not Bankrupt", "Bankrupt"], zero_division=0))
                print(f"Accuracy: {m['Accuracy (%)']:.2f}% | Precision: {m['Precision (%)']:.2f}% | "
                      f"Recall: {m['Recall (%)']:.2f}% | F1: {m['F1-Score (%)']:.2f}% | "
                      f"ROC-AUC: {m['ROC-AUC (%)']:.2f}%", flush=True)
            prediction_data.to_csv(out / f"{candidate}_holdout_predictions.csv", index=False)
        choice["Holdout_Status"] = "evaluated after freeze; historically reused and exploratory"
        _write_json(out / "frozen_choice.json", choice)
        pd.DataFrame(test_rows).to_csv(out / "holdout_results.csv", index=False)
        _write_json(out / "holdout_results.json", test_rows)
    _write_json(out / "training_oof_results.json", summary_rows)
    write_report(out, config, choice, selected, test_rows, source_note)
    print(f"\nSaved reports: {out}", flush=True)
    return dict(output_dir=out, training_results=results, thresholds=threshold_frames,
                choice=choice, holdout_results=pd.DataFrame(test_rows))


def plot_training_curves(results, tables, out, config):
    import matplotlib.pyplot as plt
    selected = results[results.Decision_Rule == "OOF selected"]
    fig, ax = plt.subplots(figsize=(10, 7))
    for _, row in selected.iterrows():
        table = tables[row.Candidate]
        ax.plot(table.Recall*100, table.Precision*100, label=row.Candidate, linewidth=1.3)
    ax.axvline(config.target_recall*100, color="black", linestyle="--", linewidth=1)
    ax.axhline(config.target_precision*100, color="black", linestyle="--", linewidth=1)
    ax.set(xlabel="Bankrupt-class recall (%)", ylabel="Bankrupt-class precision (%)",
           xlim=(0, 100), ylim=(0, 100),
           title=f"Training out-of-fold precision–recall curves ({config.feature_mode}, {config.folds}-fold CV)")
    ax.legend(fontsize=8, loc="upper right")
    fig.text(.01, .01, "Source: training OOF predictions; candidate/threshold tuning, not independent evaluation.", fontsize=8)
    fig.tight_layout(rect=(0, .035, 1, 1))
    fig.savefig(out / "training_precision_recall.png", dpi=180)
    plt.close(fig)
    for _, row in selected.iterrows():
        table = tables[row.Candidate]
        fig, ax = plt.subplots(figsize=(9, 5))
        for metric in ["Precision", "Recall", "F1", "F2"]:
            ax.plot(table.Threshold, table[metric]*100, label=metric)
        ax.axvline(row.Threshold, color="black", linestyle="--", label=f"Selected cutoff {row.Threshold:.3f}")
        ax.axhline(70, color="gray", linestyle=":", linewidth=1)
        ax.set(xlabel="Uncalibrated bankruptcy score cutoff (0–1)", ylabel="Bankrupt-class score (%)",
               ylim=(0, 100), title=f"{row.Candidate}: metrics across training OOF thresholds")
        ax.legend(fontsize=8)
        fig.text(.01, .01, "Source: training OOF predictions; scores shown are used for threshold selection.", fontsize=8)
        fig.tight_layout(rect=(0, .035, 1, 1))
        fig.savefig(out / f"{row.Candidate}_threshold_curve.png", dpi=160)
        plt.close(fig)


def write_report(out, config, choice, selected, test_rows, source_note):
    any_joint_target = bool(selected.Both_Targets_Feasible_OOF.any())
    best_precision = float(selected["Max_Precision_At_Target_Recall (%)"].max())
    lines = ["SHIELD - FOCUSED IMPROVEMENT ROUND", "",
             f"OUTCOME: Both precision/recall targets available on training OOF curves: {any_joint_target}.",
             f"Highest OOF precision with recall >= {config.target_recall*100:.0f}%: {best_precision:.2f}%.",
             "This round does not establish a permanent limit for the dataset.", "",
             f"Run ID: {choice['Run_ID']}",
             f"Source: {source_note}", f"Seed: {config.seed}; split: 80:20; training CV: {config.folds}",
             (f"IG: top {config.top_k}, fitted within every training fold." if config.feature_mode == "ig20"
              else "All financial predictors retained, including constants. No IG selection."),
             "Company identifier and Bankrupt target excluded from predictors. SMOTE: training folds only.",
             "Decision: score >= cutoff. Scores are not calibrated bankruptcy probabilities.",
             "All candidates use fixed, declared parameters; no grid search or nested CV.",
             "Threshold selection: both precision/recall targets if feasible; otherwise max F2 with recall floor.",
             "OOF results below are tuning scores after threshold/model selection, not independent performance.",
             "The old 80:20 holdout has already been used in historical experiments: further results are exploratory.",
             "A new split of these same companies cannot undo historical test reuse; external/new companies are preferable.",
             "", "TRAINING OOF THRESHOLD RESULTS", ""]
    for _, row in selected.iterrows():
        lines += [f"{row.Candidate} | cutoff {row.Threshold:.8f}",
                  f"  Precision: {row['Precision (%)']:.2f}% | Recall: {row['Recall (%)']:.2f}% | F1: {row['F1-Score (%)']:.2f}% | F2: {row['F2-Score (%)']:.2f}%",
                  f"  Both targets available: {row.Both_Targets_Feasible_OOF}; maximum precision at target recall: {row['Max_Precision_At_Target_Recall (%)']:.2f}%",
                  f"  Params: {json.dumps(row.Best_Params, sort_keys=True)}", ""]
    lines += [f"Frozen choice before holdout: {choice['Candidate']} | cutoff {choice['Threshold']:.8f}",
              "", "EXPLORATORY HOLDOUT RESULTS", ""]
    for row in test_rows:
        lines += [f"{row['Candidate']} | {row['Decision_Rule']} | cutoff {row['Threshold']:.8f}",
                  f"  Accuracy: {row['Accuracy (%)']:.2f}% | Precision: {row['Precision (%)']:.2f}% | Recall: {row['Recall (%)']:.2f}% | F1: {row['F1-Score (%)']:.2f}% | ROC-AUC: {row['ROC-AUC (%)']:.2f}%",
                  f"  TN={row['TN']}; FP={row['FP']}; FN={row['FN']}; TP={row['TP']}",
                  f"  Precision 95% Wilson interval: {row['Precision_95CI']}; Recall interval: {row['Recall_95CI']}", ""]
    lines += ["References:", "https://scikit-learn.org/stable/modules/classification_threshold.html",
              "https://imbalanced-learn.org/stable/common_pitfalls.html", ""]
    (out / "FOCUSED_RESULTS.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", default="reports/focused_improvement")
    parser.add_argument("--source-note", default="")
    parser.add_argument("--skip-holdout", action="store_true")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--feature-mode", choices=["ig20", "all"], default="ig20")
    args = parser.parse_args()
    path = Path(args.data)
    raw = pd.read_excel(path) if path.suffix.lower() in [".xlsx", ".xls"] else pd.read_csv(path)
    config = Config(evaluate_holdout=not args.skip_holdout, model_jobs=args.jobs,
                    feature_mode=args.feature_mode)
    run_focus(raw, args.output, config, args.source_note or str(path.resolve()))
