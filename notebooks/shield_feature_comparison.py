"""Matched comparison of IG top 20 and all original financial predictors."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from shield_focused_improvement import (
    Config, candidate_specs, clean_data, data_fingerprint, run_focus,
)


def load_prior_ig(folder, raw, config, specs):
    """Only reuse the completed top-20 run if its data/settings/packages are identical."""
    folder = Path(folder)
    metadata = json.loads((folder / "run_config.json").read_text(encoding="utf-8"))
    X, y = clean_data(raw, config.top_k)
    if metadata["data_fingerprint"] != data_fingerprint(X, y):
        raise ValueError("Prior IG data differs. Omit prior_ig_dir to run a fresh matched comparison.")
    fields = ["seed", "folds", "test_size", "top_k", "smote_neighbors", "target_precision",
              "target_recall", "model_jobs", "include_leaf_variants", "evaluate_holdout"]
    for key in fields:
        if metadata["config"][key] != asdict(config)[key]:
            raise ValueError(f"Prior IG setting differs: {key}.")
    if metadata["config"].get("feature_mode", "ig20") != "ig20":
        raise ValueError("Prior folder must be the IG top-k run.")
    if metadata["candidates"] != specs:
        raise ValueError("Prior IG candidate parameters differ.")
    for name, version in metadata["packages"].items():
        if importlib.metadata.version(name) != version:
            raise ValueError(f"Prior IG package version differs: {name}.")
    results = pd.DataFrame(json.loads((folder / "training_oof_results.json").read_text(encoding="utf-8")))
    results["Feature_Mode"], results["Feature_Count"] = "ig20", config.top_k
    if len(results) != 2*len(specs) or results.Candidate.nunique() != len(specs):
        raise ValueError("Prior IG result set is incomplete.")
    thresholds = {s["id"]: pd.read_csv(folder / f"{s['id']}_thresholds.csv", float_precision="round_trip") for s in specs}
    for spec in specs:
        p = pd.read_csv(folder / f"{spec['id']}_oof_predictions.csv", float_precision="round_trip")
        if p.Source_Row.duplicated().any() or not np.isfinite(p.OOF_Score).all():
            raise ValueError("Prior IG OOF predictions are invalid.")
    holdout_path = folder / "holdout_results.json"
    holdout = pd.DataFrame(json.loads(holdout_path.read_text(encoding="utf-8"))) if holdout_path.exists() else pd.DataFrame()
    if len(holdout):
        holdout["Feature_Mode"], holdout["Feature_Count"] = "ig20", config.top_k
    return dict(output_dir=folder, training_results=results, thresholds=thresholds,
                choice=json.loads((folder / "frozen_choice.json").read_text(encoding="utf-8")),
                holdout_results=holdout)


def run_feature_comparison(raw, output_base, config=Config(), prior_ig_dir=None, source_note=""):
    specs = candidate_specs(config.include_leaf_variants)
    X_all, _ = clean_data(raw, config.top_k, retain_constants=True)
    constants = [c for c in X_all if X_all[c].nunique(dropna=False) <= 1]
    print(f"Raw columns: {len(raw.columns)}. Excluded Company and Bankrupt; "
          f"all-feature arm retains {len(X_all.columns)} numeric financial predictors.", flush=True)
    print(f"Retained constant predictors: {constants}", flush=True)
    ig_config = replace(config, feature_mode="ig20")
    if prior_ig_dir is not None:
        ig = load_prior_ig(prior_ig_dir, raw, ig_config, specs)
        print(f"Reusing verified matching IG run: {prior_ig_dir}", flush=True)
    else:
        ig = run_focus(raw, output_base, ig_config, source_note, specs)
    full = run_focus(raw, output_base, replace(config, feature_mode="all"), source_note, specs)
    old_members = pd.read_csv(ig["output_dir"] / "partition_membership.csv")
    new_members = pd.read_csv(full["output_dir"] / "partition_membership.csv")
    pd.testing.assert_frame_equal(old_members, new_members)
    for spec in specs:
        old = pd.read_csv(ig["output_dir"] / f"{spec['id']}_oof_predictions.csv", float_precision="round_trip")
        new = pd.read_csv(full["output_dir"] / f"{spec['id']}_oof_predictions.csv", float_precision="round_trip")
        pd.testing.assert_frame_equal(old[["Source_Row", "True_Label", "Fold"]],
                                      new[["Source_Row", "True_Label", "Fold"]])
    signature = {"ig_run": str(ig["output_dir"]), "all_run": str(full["output_dir"]),
                 "config": asdict(config), "comparison_version": "shield-all-features-v1"}
    compare_id = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()[:16]
    out = Path(output_base) / f"comparison_{compare_id}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison_config.json").write_text(json.dumps({
        **signature, "raw_columns": len(raw.columns), "all_financial_predictors": len(X_all.columns),
        "constant_predictors_retained": constants,
        "membership_verified": "identical companies, labels, train/holdout split and training CV folds",
        "source": source_note,
    }, indent=2), encoding="utf-8")
    metrics = ["Accuracy (%)", "Precision (%)", "Recall (%)", "F1-Score (%)", "ROC-AUC (%)",
               "F2-Score (%)", "Average Precision (%)", "Max_Precision_At_Target_Recall (%)"]
    keys = ["Candidate", "Decision_Rule"]
    paired = ig["training_results"].merge(full["training_results"], on=keys,
                                          suffixes=("_IG20", "_All"), validate="one_to_one")
    for metric in metrics:
        paired[metric + "_Change_pp"] = paired[metric + "_All"] - paired[metric + "_IG20"]
    paired.to_csv(out / "paired_training_comparison.csv", index=False)
    all_results = pd.concat([ig["training_results"], full["training_results"]], ignore_index=True)
    all_results.to_csv(out / "all_training_results.csv", index=False)
    holdouts = pd.concat([ig["holdout_results"], full["holdout_results"]], ignore_index=True)
    if len(holdouts):
        holdouts.to_csv(out / "exploratory_holdout_comparison.csv", index=False)
    selected = all_results[all_results.Decision_Rule == "OOF selected"]
    winner = selected.sort_values(["Both_Targets_Feasible_OOF", "F2-Score (%)", "Precision (%)", "Candidate"],
                                  ascending=[False, False, False, True]).iloc[0]
    comparison_choice = dict(Feature_Mode=winner.Feature_Mode, Candidate=winner.Candidate,
                              Threshold=float(winner.Threshold),
                              Selection_Data="training OOF only; historical holdouts not used for selection")
    (out / "training_selected_comparison_choice.json").write_text(
        json.dumps(comparison_choice, indent=2), encoding="utf-8")
    plot_comparison(paired, ig, full, out, config)
    write_comparison_report(out, ig, full, paired, config, source_note, len(X_all.columns), constants)
    print(f"Comparison saved: {out}", flush=True)
    return dict(output_dir=out, ig=ig, full=full, paired=paired,
                training_results=all_results, holdout_results=holdouts, choice=comparison_choice)


def plot_comparison(paired, ig, full, out, config):
    import matplotlib.pyplot as plt
    rows = paired[paired.Decision_Rule == "OOF selected"].reset_index(drop=True)
    metric = "Max_Precision_At_Target_Recall (%)"
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(rows))
    ax.barh(x-.18, rows[metric+"_IG20"], height=.36, label=f"IG top {config.top_k}", color="#4878a8")
    ax.barh(x+.18, rows[metric+"_All"], height=.36, label="All financial predictors", color="#777777")
    ax.axvline(config.target_precision*100, color="black", linestyle="--", label="70% precision target")
    ax.set(yticks=x, yticklabels=rows.Candidate, xlim=(0,100),
           xlabel=f"Maximum bankruptcy precision while recall >= {config.target_recall*100:.0f}% (%)",
           ylabel="Fixed model/SMOTE candidate",
           title=f"All financial predictors versus IG top {config.top_k}: training OOF threshold potential")
    ax.invert_yaxis()
    ax.legend(fontsize=8)
    fig.text(.01,.01,"Source: matched 5-fold training OOF curves. Tuning results; not independent final evaluation.",fontsize=8)
    fig.tight_layout(rect=(0,.04,1,1))
    fig.savefig(out/"precision_at_70_recall_comparison.png",dpi=180)
    plt.close(fig)
    winner_ids = list(dict.fromkeys(["RF_SMOTE025", ig["choice"]["Candidate"], full["choice"]["Candidate"]]))
    fig, axes = plt.subplots(1,len(winner_ids),figsize=(6*len(winner_ids),5.5),squeeze=False)
    for ax, candidate in zip(axes.flat,winner_ids):
        for run,label,color in [(ig,f"IG top {config.top_k}","#4878a8"),
                                 (full,"All financial predictors","#777777")]:
            table=run["thresholds"][candidate]
            ax.plot(table.Recall*100,table.Precision*100,label=label,color=color)
        ax.axvline(config.target_recall*100,color="black",linestyle="--",linewidth=1)
        ax.axhline(config.target_precision*100,color="black",linestyle="--",linewidth=1)
        ax.set(xlim=(0,100),ylim=(0,100),xlabel="Bankruptcy recall (%)",ylabel="Bankruptcy precision (%)",title=candidate)
        ax.legend(fontsize=8)
    fig.suptitle("Matched training OOF precision–recall curves",fontsize=14)
    fig.text(.01,.01,"Source: same companies, folds and declared model settings; thresholds selected on training OOF predictions.",fontsize=8)
    fig.tight_layout(rect=(0,.04,1,.95))
    fig.savefig(out/"matched_precision_recall_curves.png",dpi=180)
    plt.close(fig)


def write_comparison_report(out, ig, full, paired, config, source_note, full_count, constants):
    ig_rows=ig["training_results"].query("Decision_Rule == 'OOF selected'")
    full_rows=full["training_results"].query("Decision_Rule == 'OOF selected'")
    metric="Max_Precision_At_Target_Recall (%)"
    lines=["SHIELD - ALL FINANCIAL PREDICTORS VERSUS IG TOP 20", "",
           f"Top-{config.top_k} IG: any candidate reaches both targets: {bool(ig_rows.Both_Targets_Feasible_OOF.any())}.",
           f"All {full_count} financial predictors: any candidate reaches both targets: {bool(full_rows.Both_Targets_Feasible_OOF.any())}.",
           f"Maximum OOF precision at recall >=70%: IG={ig_rows[metric].max():.2f}%; All={full_rows[metric].max():.2f}%.", "",
           f"Source: {source_note}", "Raw file has 97 columns, not 97 financial predictors.",
           "Company is an identifier; Bankrupt is the target. Both are excluded from predictors.",
           f"All-feature arm: {full_count} financial predictors, no IG. Constants retained: {constants}.",
           "IG arm: previous cleaning removes constants, then training-fold IG selects top 20.",
           "Same seed=42, 80:20 split, five training CV folds, nine fixed candidates and threshold-selection rule.",
           "SMOTE remains training-fold only. No new models, parameter grids, or nested CV.",
           "Changing the feature count also changes the meaning of fractional/sqrt max_features in RF.",
           "OOF threshold/model-selection metrics are tuning scores. Reused historical holdout scores are exploratory.",
           f"IG report: {ig['output_dir']}", f"All-feature report: {full['output_dir']}", "",
           "MATCHED TRAINING OOF RESULTS - SELECTED CUTOFFS", ""]
    reference_lines = ["MATCHED RF SMOTE 0.25 AT CUTOFF 0.5 - EXPLORATORY HOLDOUT", ""]
    for label, run in [("IG top 20", ig), ("All financial predictors", full)]:
        reference = run["holdout_results"]
        if len(reference):
            reference = reference[reference.Decision_Rule == "Reference default 0.5"]
            for _, r in reference.iterrows():
                reference_lines += [f"{label}: Precision {r['Precision (%)']:.2f}% | Recall {r['Recall (%)']:.2f}% | F1 {r['F1-Score (%)']:.2f}% | TP={r.TP}; FP={r.FP}"]
    if len(reference_lines) > 2:
        lines[6:6] = reference_lines + [""]
    for _,r in paired[paired.Decision_Rule=="OOF selected"].iterrows():
        lines += [r.Candidate,
                  f"  IG20: P={r['Precision (%)_IG20']:.2f}% | R={r['Recall (%)_IG20']:.2f}% | F1={r['F1-Score (%)_IG20']:.2f}% | F2={r['F2-Score (%)_IG20']:.2f}% | cutoff={r.Threshold_IG20:.8f}",
                  f"  All:  P={r['Precision (%)_All']:.2f}% | R={r['Recall (%)_All']:.2f}% | F1={r['F1-Score (%)_All']:.2f}% | F2={r['F2-Score (%)_All']:.2f}% | cutoff={r.Threshold_All:.8f}",
                  f"  Max precision at recall >=70%: IG={r[metric+'_IG20']:.2f}%; All={r[metric+'_All']:.2f}%.",""]
    lines += ["EXPLORATORY HOLDOUT RESULTS - PER-ARM TRAINING-SELECTED CHOICES", ""]
    for label,run in [("IG top 20",ig),("All financial predictors",full)]:
        for _,r in run["holdout_results"].iterrows():
            lines += [f"{label} | {r.Candidate} | {r.Decision_Rule} | cutoff {r.Threshold:.8f}",
                      f"  Accuracy: {r['Accuracy (%)']:.2f}% | Precision: {r['Precision (%)']:.2f}% | Recall: {r['Recall (%)']:.2f}% | F1: {r['F1-Score (%)']:.2f}% | ROC-AUC: {r['ROC-AUC (%)']:.2f}%",
                      f"  TP={r.TP}; FP={r.FP}; FN={r.FN}; TN={r.TN}",""]
    lines += ["No production model, frontend fields or risk bands were changed.",
              "All comparison metrics and parameter settings are retained at full precision in the CSV files.",
              "Reload score/threshold CSVs using pandas.read_csv(..., float_precision='round_trip') to preserve equal-cutoff decisions.",""]
    (out/"FEATURE_COMPARISON_RESULTS.txt").write_text("\n".join(lines),encoding="utf-8")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",required=True)
    parser.add_argument("--output",default="reports/feature_comparison")
    parser.add_argument("--prior-ig-dir")
    parser.add_argument("--source-note",default="")
    args=parser.parse_args()
    path=Path(args.data)
    raw=pd.read_excel(path) if path.suffix.lower() in [".xlsx",".xls"] else pd.read_csv(path)
    run_feature_comparison(raw,args.output,prior_ig_dir=args.prior_ig_dir,
                           source_note=args.source_note or str(path.resolve()))
