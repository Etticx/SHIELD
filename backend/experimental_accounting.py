"""Raw accounting-ratio experiment; deliberately does not guess dataset encoding."""
import math
import pandas as pd

FEATURES = [
    "Net Income to Stockholder's Equity", "Net Income to Total Assets",
    "Retained Earnings to Total Assets", "Debt ratio %", "Net worth/Assets",
    "Equity to Liability", "Liability to Equity",
]

def calculate_features(net_income, total_assets, total_liabilities, equity, retained_earnings):
    numbers = [net_income, total_assets, total_liabilities, equity, retained_earnings]
    if not all(math.isfinite(n) for n in numbers):
        raise ValueError('All five accounting figures must be finite numbers.')
    if total_assets <= 0 or total_liabilities <= 0 or equity == 0:
        raise ValueError('Assets and liabilities must be positive; equity cannot be zero because the ratios divide by these values.')
    ratios = [net_income/equity, net_income/total_assets, retained_earnings/total_assets,
              total_liabilities/total_assets, equity/total_assets, equity/total_liabilities,
              total_liabilities/equity]
    if not all(math.isfinite(n) for n in ratios):
        raise ValueError('The calculated ratios exceed the supported numeric range.')
    return dict(zip(FEATURES, ratios))

def run_prediction(model, features):
    names = list(model.feature_names_in_)
    if len(names) != 7 or {str(n).strip() for n in names} != set(FEATURES):
        raise ValueError('The experimental model must expect exactly the seven accounting features.')
    frame = pd.DataFrame([[features[str(n).strip()] for n in names]], columns=names)
    probability = float(model.predict_proba(frame)[0][list(model.classes_).index(1)])
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError('The model returned an invalid score.')
    return {'bankruptcy_score': probability, 'prediction': 'Bankrupt' if probability >= 0.5 else 'Not Bankrupt',
            'threshold': 0.5, 'features_sent': dict(zip(names, frame.iloc[0].tolist())),
            'experimental': True, 'representation': 'Raw fractions; no scaling or clipping',
            'notice': 'Experimental response to raw ratios. Dataset encoding is unverified; this score is not a validated bankruptcy probability.'}
