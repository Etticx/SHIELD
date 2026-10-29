import unittest
from experimental_accounting import calculate_features, run_prediction

class AccountingTests(unittest.TestCase):
    def test_ratios_and_order(self):
        values = calculate_features(10, 100, 60, 40, 15)
        self.assertEqual(list(values.values()), [0.25, 0.1, 0.15, 0.6, 0.4, 40/60, 1.5])
    def test_losses_are_not_clamped(self):
        self.assertEqual(list(calculate_features(-10, 100, 120, -20, -30).values())[0], 0.5)
    def test_invalid_denominators(self):
        for args in [(10, 0, 60, 40, 15), (10, 100, 0, 100, 15), (10, 100, 100, 0, 15)]:
            with self.assertRaises(ValueError): calculate_features(*args)
    def test_non_finite(self):
        with self.assertRaises(ValueError): calculate_features(float('nan'),100,60,40,15)
    def test_model_order_and_positive_class(self):
        class Model:
            feature_names_in_ = [' Net Income to Total Assets', ' Net Income to Stockholder\'s Equity', ' Retained Earnings to Total Assets', ' Debt ratio %', ' Net worth/Assets', ' Equity to Liability', ' Liability to Equity']
            classes_ = [1, 0]
            def predict_proba(self, frame):
                self.frame = frame
                return [[0.7, 0.3]]
        model = Model()
        result = run_prediction(model, calculate_features(10,100,60,40,15))
        self.assertEqual(result['bankruptcy_score'],0.7)
        self.assertEqual(model.frame.iloc[0,0],0.1)

if __name__ == '__main__': unittest.main()
