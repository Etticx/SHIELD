"""Frozen-model stress test for SHIELD's saved 20-feature Random Forest.

This runner is embedded in the Colab notebook; no helper upload is required.
It never trains a model, tunes a threshold, or writes production artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split

MODEL_FILE = "SHIELD_BestModel_RF_8020_CV10.joblib"
DATA_FILES = ["preprocessed_dataset.csv", "X_train_processed_8020.csv",
              "y_train_processed_8020.csv", "X_test_processed_8020.csv",
              "y_test_processed_8020.csv"]
METHODS = ("native_nan", "training_median")
THRESHOLDS = (0.60, 0.50)  # App high-risk cutoff; historical classification reference.
TIER_EDGES = np.array([0.30, 0.60, 0.80])
GROUPS = {
    "earnings_history_missing": ["Persistent EPS in the Last Four Seasons"],
    "share_based_unavailable": ["Persistent EPS in the Last Four Seasons",
                               "Per Share Net profit before tax",
                               "Net Value Per Share (A)", "Net Value Per Share (B)"],
    "leverage_records_missing": ["Debt ratio %", "Net worth/Assets",
                                 "Borrowing dependency", "Degree of Financial Leverage (DFL)",
                                 "Retained Earnings to Total Assets"],
}


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_inputs(project):
    """Recover original train rows and verify their match to the saved split."""
    project = Path(project)
    model_path = project / "model" / MODEL_FILE
    paths = {name: project / "data" / name for name in DATA_FILES}
    for path in [model_path, *paths.values()]:
        if not path.is_file():
            raise FileNotFoundError(f"Required file missing: {path}")
    if importlib.metadata.version("scikit-learn") != "1.6.1":
        raise RuntimeError("Use scikit-learn==1.6.1, matching the saved model. Run the notebook installation cell and restart the runtime if necessary.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        model = joblib.load(model_path)
    steps = [(name, type(step).__name__) for name, step in model.steps]
    if steps != [("smote", "SMOTE"), ("model", "RandomForestClassifier")]:
        raise ValueError(f"Unexpected saved pipeline: {steps}. This experiment targets the current prototype RF.")
    features = list(model.feature_names_in_)
    if len(features) != 20 or list(model.classes_) != [0, 1]:
        raise ValueError("Expected 20 features and class order [0, 1].")

    train = pd.read_csv(paths["X_train_processed_8020.csv"])
    y_train = pd.read_csv(paths["y_train_processed_8020.csv"]).iloc[:, 0]
    test = pd.read_csv(paths["X_test_processed_8020.csv"])
    y_test = pd.read_csv(paths["y_test_processed_8020.csv"]).iloc[:, 0]
    raw = pd.read_csv(paths["preprocessed_dataset.csv"])
    for name, X, y in [("saved train", train, y_train), ("saved test", test, y_test)]:
        if list(X.columns) != features or len(X) != len(y):
            raise ValueError(f"{name}: feature order or feature/label alignment differs.")
        if not np.isfinite(X.to_numpy(dtype=float)).all() or set(y.unique()) != {0, 1}:
            raise ValueError(f"{name}: expected complete numeric inputs and both binary classes.")
        if ((X < 0) | (X > 1)).any().any():
            raise ValueError(f"{name}: expected normalised values in [0, 1].")
    if raw.columns.duplicated().any() or "Bankrupt" not in raw or not set(features).issubset(raw.columns):
        raise ValueError("Original source CSV must contain Bankrupt and all 20 feature names.")
    if set(raw.Bankrupt.unique()) != {0, 1}:
        raise ValueError("Original target must be numeric 0/1.")

    # The numeric stratified seed-42 split reproduces the saved files. Fail rather
    # than silently fitting medians on synthetic records or mismatched companies.
    original_train, original_test, original_y_train, original_y_test = train_test_split(
        raw[features], raw.Bankrupt, test_size=0.20, random_state=42, stratify=raw.Bankrupt,
    )
    n_original = len(original_train)
    if len(train) < n_original or len(test) != len(original_test):
        raise ValueError("Saved files do not match the original 80:20 partition sizes.")
    np.testing.assert_allclose(original_train.to_numpy(), train.iloc[:n_original].to_numpy(), rtol=0, atol=1e-8)
    np.testing.assert_allclose(original_test.to_numpy(), test.to_numpy(), rtol=0, atol=1e-8)
    np.testing.assert_array_equal(original_y_train.to_numpy(), y_train.iloc[:n_original].to_numpy())
    np.testing.assert_array_equal(original_y_test.to_numpy(), y_test.to_numpy())
    if set(original_train.index) & set(original_test.index):
        raise AssertionError("Train/test source rows overlap.")
    # Use the full-precision ORIGINAL prefix verified against source, not SMOTE rows.
    medians = train.iloc[:n_original].median()
    if not np.isfinite(medians).all():
        raise ValueError("Training medians are not finite.")
    info = {
        "model_sha256": file_hash(model_path),
        "data_sha256": {name: file_hash(path) for name, path in paths.items()},
        "pipeline_steps": steps, "feature_order": features,
        "original_training_rows": n_original, "synthetic_training_rows": len(train) - n_original,
        "test_rows": len(test), "test_bankrupt": int(y_test.sum()),
        "median_source": "verified original training prefix; synthetic SMOTE rows excluded",
        "partition_verification": "source seed-42 stratified 80:20 split matches saved features within 1e-8 and labels exactly",
    }
    return model, test, y_test.to_numpy(dtype=int), medians, original_test.index.to_numpy(), info


def random_mask(n_rows, n_features, count, seed):
    if not 0 <= count <= n_features:
        raise ValueError("Missing-feature count must be between 0 and feature count.")
    rng = np.random.default_rng(seed)
    positions = np.argsort(rng.random((n_rows, n_features)), axis=1)[:, :count]
    mask = np.zeros((n_rows, n_features), dtype=bool)
    mask[np.arange(n_rows)[:, None], positions] = True
    return mask


def apply_mask(X, mask, method, medians):
    if mask.shape != X.shape or mask.dtype != bool:
        raise ValueError("Mask shape/type differs from the financial matrix.")
    missing = X.mask(mask)
    if method == "native_nan":
        return missing
    if method == "training_median":
        return missing.fillna(medians)
    raise ValueError(f"Unknown missing-data method: {method}")


def score(model, X):
    p = np.asarray(model.predict_proba(X)[:, 1], dtype=float)
    if p.shape != (len(X),) or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Model returned invalid probabilities.")
    return p


def metrics(y, p, reference, threshold):
    prediction, baseline_prediction = p >= threshold, reference >= threshold
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0, 1]).ravel()
    movement = np.abs(p - reference)
    return {
        "threshold": threshold, "accuracy": accuracy_score(y, prediction),
        "precision": precision_score(y, prediction, zero_division=0),
        "recall": recall_score(y, prediction, zero_division=0),
        "f1": f1_score(y, prediction, zero_division=0),
        "average_precision": average_precision_score(y, p), "roc_auc": roc_auc_score(y, p),
        "brier": brier_score_loss(y, p), "false_positive_rate": fp / (tn + fp),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "mean_probability_change_pp": float(movement.mean() * 100),
        "p95_probability_change_pp": float(np.quantile(movement, 0.95) * 100),
        "max_probability_change_pp": float(movement.max() * 100),
        "bankrupt_probability_change_pp": float(movement[y == 1].mean() * 100),
        "tier_change_pct": float(np.mean(np.digitize(p, TIER_EDGES) != np.digitize(reference, TIER_EDGES)) * 100),
        "decision_change_pct": float(np.mean(prediction != baseline_prediction) * 100),
        "newly_missed_bankrupt": int(np.sum((y == 1) & baseline_prediction & ~prediction)),
        "newly_detected_bankrupt": int(np.sum((y == 1) & ~baseline_prediction & prediction)),
        "unique_probabilities": int(len(np.unique(p))),
    }


def baseline_bootstrap(y, p, repeats=500, seed=7241):
    """Stratified company resampling; conditional on this reused test set."""
    if repeats < 2:
        raise ValueError("Use at least two bootstrap draws.")
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(y == label) for label in [0, 1]]
    values = {name: [] for name in ["recall", "precision", "average_precision", "roc_auc", "brier"]}
    for _ in range(repeats):
        rows = np.concatenate([rng.choice(indices, len(indices), replace=True) for indices in groups])
        resampled_y, resampled_p = y[rows], p[rows]
        values["recall"].append(recall_score(resampled_y, resampled_p >= 0.60, zero_division=0))
        values["precision"].append(precision_score(resampled_y, resampled_p >= 0.60, zero_division=0))
        values["average_precision"].append(average_precision_score(resampled_y, resampled_p))
        values["roc_auc"].append(roc_auc_score(resampled_y, resampled_p))
        values["brier"].append(brier_score_loss(resampled_y, resampled_p))
    return pd.DataFrame([{"metric": name, "lower_95": np.quantile(v, .025),
                          "upper_95": np.quantile(v, .975), "bootstrap_draws": repeats}
                         for name, v in values.items()])


def run_experiment(project, output_base=None, repeats=20, seed=42,
                   missing_counts=(1, 2, 5, 10, 20), bootstrap_draws=500):
    if repeats < 2 or not missing_counts or len(set(missing_counts)) != len(missing_counts):
        raise ValueError("Use >=2 repeats and distinct missing-feature counts.")
    if any(not 1 <= count <= 20 for count in missing_counts):
        raise ValueError("Counts must be between 1 and 20.")
    model, X, y, medians, source_rows, info = load_inputs(project)
    packages = {name: importlib.metadata.version(name) for name in
                ["scikit-learn", "imbalanced-learn", "numpy", "pandas", "joblib", "scipy"]}
    config = {"experiment_version": "shield-missing-data-v1", "seed": seed,
              "random_repeats": repeats, "missing_counts": list(missing_counts),
              "methods": METHODS, "thresholds": THRESHOLDS, "tier_edges": TIER_EDGES.tolist(),
              "bootstrap_draws": bootstrap_draws, "groups": GROUPS, "packages": packages,
              "test_usage": "historical test set reused in development; exploratory stress test",
              "scope": "frozen RF predictions only; no SHAP/Groq/API validation; no Malaysian startup validation",
              **info}
    run_id = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
    out = Path(output_base or Path(project) / "reports" / "missing_data") / run_id
    out.mkdir(parents=True, exist_ok=True)
    baseline = score(model, X)
    rows, prediction_records, mask_records = [], [], []
    baseline_metrics = {threshold: metrics(y, baseline, baseline, threshold) for threshold in THRESHOLDS}
    for threshold in THRESHOLDS:
        rows.append({"family": "baseline", "scenario": "complete_20", "method": "complete",
                     "repeat": 0, "missing_count": 0, **baseline_metrics[threshold]})
    print(f"Verified original train={info['original_training_rows']}, synthetic={info['synthetic_training_rows']}; test={len(X)}, bankrupt={int(y.sum())}", flush=True)
    print("Model stays frozen. Primary threshold=0.60; secondary reference=0.50.", flush=True)

    def evaluate(family, scenario, mask, repeat=0):
        count = int(mask.sum(axis=1)[0])
        assert np.all(mask.sum(axis=1) == count)
        mask_records.append({"family": family, "scenario": scenario, "repeat": repeat,
                             "missing_count": count, "mask_sha256": hashlib.sha256(mask.tobytes()).hexdigest()})
        for method in METHODS:
            modified = apply_mask(X, mask, method, medians)
            p = score(model, modified)
            for threshold in THRESHOLDS:
                result = metrics(y, p, baseline, threshold)
                for name in ["recall", "precision", "average_precision", "roc_auc", "accuracy", "false_positive_rate"]:
                    result[name + "_change_pp"] = (result[name] - baseline_metrics[threshold][name]) * 100
                result["brier_change"] = result["brier"] - baseline_metrics[threshold]["brier"]
                rows.append({"family": family, "scenario": scenario, "method": method,
                             "repeat": repeat, "missing_count": count, **result})
            prediction_records.append(pd.DataFrame({
                "test_row": np.arange(len(X)), "source_row": source_rows, "true_label": y,
                "family": family, "scenario": scenario, "method": method, "repeat": repeat,
                "missing_count": count, "complete_probability": baseline, "probability": p,
                "missing_features": [" | ".join(np.asarray(X.columns)[row]) for row in mask],
            }))

    for i, feature in enumerate(X.columns):
        mask = np.zeros(X.shape, dtype=bool)
        mask[:, i] = True
        evaluate("single", feature.strip(), mask)
    lookup = {name.strip(): i for i, name in enumerate(X.columns)}
    for scenario, features in GROUPS.items():
        mask = np.zeros(X.shape, dtype=bool)
        mask[:, [lookup[feature] for feature in features]] = True
        evaluate("group", scenario, mask)
    for count in missing_counts:
        for repeat in range(repeats):
            # A repeat supplies one mask shared by both methods, independent of y.
            mask_seed = int(np.random.SeedSequence([seed, count, repeat]).generate_state(1)[0])
            evaluate("random", f"random_{count}_missing", random_mask(len(X), X.shape[1], count, mask_seed), repeat)
        print(f"Finished {count} missing metrics/company, {repeats} paired repetitions.", flush=True)

    results = pd.DataFrame(rows)
    results.to_csv(out / "scenario_metrics.csv", index=False)
    pd.concat(prediction_records, ignore_index=True).to_csv(out / "company_predictions.csv.gz", index=False, compression="gzip")
    pd.DataFrame(mask_records).to_csv(out / "mask_manifest.csv", index=False)
    pd.DataFrame({"feature": medians.index, "original_training_median": medians.values}).to_csv(out / "training_medians.csv", index=False)
    pd.DataFrame({"test_row": np.arange(len(X)), "source_row": source_rows, "true_label": y,
                  "complete_probability": baseline}).to_csv(out / "complete_predictions.csv", index=False)
    baseline_bootstrap(y, baseline, bootstrap_draws).to_csv(out / "baseline_bootstrap.csv", index=False)
    summary_metrics = ["recall", "precision", "average_precision", "roc_auc", "brier", "false_positive_rate",
                       "tier_change_pct", "decision_change_pct", "mean_probability_change_pp", "newly_missed_bankrupt"]
    random = results[results.family == "random"]
    summary = random.groupby(["missing_count", "method", "threshold"])[summary_metrics].agg(["mean", "std", "min", "max"])
    summary.columns = ["_".join(column) for column in summary.columns]
    summary.reset_index().to_csv(out / "random_summary.csv", index=False)
    config["run_id"] = run_id
    (out / "run_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_readout(results, config, out)
    print(f"Saved {len(results)} metric rows to {out}", flush=True)
    return {"output_dir": out, "results": results, "config": config}


def write_readout(results, config, out):
    primary = results[results.threshold == .60]
    baseline = primary[primary.family == "baseline"].iloc[0]
    lines = ["SHIELD MISSING-DATA STRESS TEST", "",
             "Exploratory evaluation on the historical test partition; no retraining or production policy changes.",
             f"Test companies: {config['test_rows']}; bankrupt: {config['test_bankrupt']}.",
             "Primary high-risk threshold is 0.60. Average precision summarises the precision-recall curve.",
             f"Complete-input recall: {baseline.recall:.3f}; precision: {baseline.precision:.3f}; AP: {baseline.average_precision:.3f}; missed bankrupt: {int(baseline.fn)}.", ""]
    for method in METHODS:
        worst = primary[(primary.family == "single") & (primary.method == method)].sort_values(["recall", "average_precision"]).iloc[0]
        lines.append(f"{method}: lowest single-missing recall is {worst.recall:.3f} when '{worst.scenario}' is missing; AP={worst.average_precision:.3f}; newly missed bankrupt={int(worst.newly_missed_bankrupt)}.")
    lines.extend(["", "Read scenario_metrics.csv for every metric and paired change from baseline.",
                  "Random repetition spread measures variation in simulated masks, not a confidence interval across independent companies.",
                  "baseline_bootstrap.csv gives conditional stratified company-bootstrap intervals; it does not correct historical test reuse.",
                  f"With {config['test_bankrupt']} bankrupt companies, one changed detection alters recall by about {100 / config['test_bankrupt']:.2f} percentage points.",
                  "The 20-missing scenario is a no-information control; a returned number is not a useful individual assessment.",
                  "Share-based/historical group masks are proxies. Structurally undefined metrics must not be treated as observed financial values.",
                  "Brier score is descriptive; probabilities from SMOTE training are not automatically calibrated real-world default probabilities.",
                  "No result automatically approves a 19/20 gate. Define acceptable absolute detection/false-alarm performance and degradation before independent validation.",
                  "Malaysia/new-business suitability, missingness related to distress, and SHAP/advisory behaviour need separate validation."])
    (out / "READOUT.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_results(output_dir, show=True):
    import matplotlib.pyplot as plt
    out = Path(output_dir)
    results = pd.read_csv(out / "scenario_metrics.csv")
    primary = results[results.threshold == .60]
    baseline = primary[primary.family == "baseline"].iloc[0]
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))
    for method in METHODS:
        grouped = primary[(primary.family == "random") & (primary.method == method)].groupby("missing_count")
        for axis, metric, label in zip(axes, ["recall", "average_precision", "false_positive_rate", "tier_change_pct"],
                                       ["Bankruptcy recall", "Average precision", "False-positive rate", "Companies changing risk tier (%)"]):
            mean, low, high = grouped[metric].mean(), grouped[metric].min(), grouped[metric].max()
            axis.plot(mean.index, mean.values, marker="o", label=method)
            axis.fill_between(mean.index, low.values, high.values, alpha=.15)
            axis.axhline(baseline[metric], color="black", linestyle="--", linewidth=1)
            axis.set(xlabel="Missing metrics per company", ylabel=label, xticks=mean.index)
            axis.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle("Frozen RF: random missing metrics (bands = min/max across masks, not confidence intervals)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "random_degradation.png", dpi=160, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)

    single = primary[primary.family == "single"].pivot(index="scenario", columns="method", values="recall_change_pp")
    single = single.loc[single.min(axis=1).sort_values().index]
    fig, axis = plt.subplots(figsize=(11, 9))
    single.plot.barh(ax=axis)
    axis.axvline(0, color="black", linewidth=1)
    axis.set(xlabel="Bankruptcy recall change from complete inputs (percentage points)", ylabel="Missing metric",
             title="19/20 inputs: the identity of the missing metric matters")
    axis.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(out / "single_feature_effects.png", dpi=160, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--bootstrap-draws", type=int, default=500)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    run = run_experiment(args.project, repeats=args.repeats, bootstrap_draws=args.bootstrap_draws)
    if not args.no_plots:
        import matplotlib
        matplotlib.use("Agg")
        plot_results(run["output_dir"], show=False)
