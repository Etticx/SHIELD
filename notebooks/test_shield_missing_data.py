"""Verify masking and interpretation boundaries, rather than model accuracy claims."""
import unittest
import numpy as np
import pandas as pd
from shield_missing_data import random_mask, apply_mask, metrics


class MissingDataTests(unittest.TestCase):
    def test_mask_counts_and_reproducibility(self):
        for count in (1, 2, 5, 10, 20):
            a = random_mask(80, 20, count, 42)
            np.testing.assert_array_equal(a.sum(axis=1), np.full(80, count))
            np.testing.assert_array_equal(a, random_mask(80, 20, count, 42))
        self.assertFalse(np.array_equal(random_mask(80, 20, 5, 42), random_mask(80, 20, 5, 43)))
        with self.assertRaises(ValueError):
            random_mask(80, 20, 21, 42)

    def test_native_and_median_share_mask_and_preserve_observed_zero(self):
        X = pd.DataFrame({'a': [0., .6], 'b': [.7, .8]}, index=[8, 9])
        before = X.copy()
        mask = np.array([[False, True], [True, False]])
        medians = pd.Series({'a': .3, 'b': .4})
        native = apply_mask(X, mask, 'native_nan', medians)
        median = apply_mask(X, mask, 'training_median', medians)
        np.testing.assert_array_equal(native.isna().to_numpy(), mask)
        self.assertEqual(native.loc[8, 'a'], 0.)
        self.assertEqual(median.loc[8, 'a'], 0.)
        self.assertEqual(median.loc[8, 'b'], .4)
        self.assertEqual(median.loc[9, 'a'], .3)
        pd.testing.assert_frame_equal(X, before)
        self.assertEqual(list(native.columns), ['a', 'b'])
        self.assertEqual(list(native.index), [8, 9])

    def test_new_misses_are_not_cancelled_by_new_detections(self):
        y = np.array([1, 1, 0, 0])
        reference = np.array([.8, .2, .1, .4])
        changed = np.array([.2, .8, .1, .7])
        output = metrics(y, changed, reference, .6)
        self.assertEqual(output['recall'], .5)
        self.assertEqual(output['newly_missed_bankrupt'], 1)
        self.assertEqual(output['newly_detected_bankrupt'], 1)
        self.assertEqual(output['fp'], 1)
        self.assertEqual(output['false_positive_rate'], .5)
        self.assertEqual(output['decision_change_pct'], 75.)

    def test_threshold_and_tier_boundaries_match_app(self):
        p = np.array([.299, .3, .599, .6, .799, .8])
        y = np.array([0, 0, 0, 1, 1, 1])
        reference = np.zeros(6)
        result = metrics(y, p, reference, .6)
        self.assertEqual(result['tp'], 3)
        self.assertEqual(result['fn'], 0)
        self.assertAlmostEqual(result['tier_change_pct'], 100 * 5 / 6)


if __name__ == '__main__':
    unittest.main()
