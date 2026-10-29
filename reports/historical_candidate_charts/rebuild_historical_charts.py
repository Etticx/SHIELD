"""Rebuild requested historical figures from the original pasted result tables.

No estimator is trained and no company-level predictions are invented.
Confusion counts are derived from the reported P/R/F1/accuracy and known supports.
"""
import ast
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
ATTACHMENTS = Path("C:/Users/User/.codex/attachments")
SUPPORT_NEGATIVE = 1320
SUPPORT_POSITIVE = 44
SPECS = [
    dict(model="RandomForest", label="Random Forest", ratio=0.25,
         attachment="b1001435-c810-4838-adea-d3334c789082", stem="rf_smote_025",
         color="#4C93E0", cmap="Blues"),
    dict(model="XGBoost", label="XGBoost", ratio=0.1,
         attachment="a9acd921-8a2e-40aa-98cc-a46863fdeb25", stem="xgb_smote_010",
         color="#9A63C7", cmap="Purples"),
]


def read_historical_row(spec):
    source = ATTACHMENTS / spec["attachment"] / "Pasted text.txt"
    raw = source.read_text(encoding="utf-8-sig")
    matches = []
    for line in raw.splitlines():
        parts = [p.strip() for p in line.replace("\\", "").strip().strip("|").split("|")]
        if len(parts) != 12 or not parts[0].isdigit():
            continue
        if parts[1] == spec["model"] and parts[2] == "80-20 + CV=10":
            matches.append(parts)
    if len(matches) != 1:
        raise ValueError(f"Expected one historical row for {spec['model']}; found {len(matches)}.")
    p = matches[0]
    row = {**spec, "Experiment": p[2], "Split": float(p[3]), "CV": int(float(p[4])),
           "Accuracy (%)": float(p[5]), "Precision (%)": float(p[6]),
           "Recall (%)": float(p[7]), "F1-Score (%)": float(p[8]),
           "ROC-AUC (%)": float(p[9]), "Best_Params": ast.literal_eval(p[10]),
           "CV_F1_Mean (%)": float(p[11]), "Original_Source_Index": int(p[0]),
           "Source": str(source), "Source_SHA256": hashlib.sha256(source.read_bytes()).hexdigest()}
    return row


def derive_and_check_counts(row):
    tp = round(row["Recall (%)"] / 100 * SUPPORT_POSITIVE)
    predicted_positive = round(tp / (row["Precision (%)"] / 100))
    fp = predicted_positive - tp
    fn = SUPPORT_POSITIVE - tp
    tn = SUPPORT_NEGATIVE - fp
    if min(tn, fp, fn, tp) < 0:
        raise ValueError("Invalid confusion counts.")
    cm = np.array([[tn, fp], [fn, tp]], dtype=int)
    actual = {
        "Accuracy (%)": (tn+tp)/cm.sum()*100,
        "Precision (%)": tp/(tp+fp)*100,
        "Recall (%)": tp/(tp+fn)*100,
        "F1-Score (%)": 2*tp/(2*tp+fp+fn)*100,
    }
    for name, value in actual.items():
        np.testing.assert_allclose(value, row[name], rtol=0, atol=1e-10)
    # Verify uniqueness across every possible integer confusion matrix at these supports.
    matches = []
    for candidate_tp in range(SUPPORT_POSITIVE+1):
        if abs(candidate_tp/SUPPORT_POSITIVE*100-row["Recall (%)"]) > 1e-9:
            continue
        for candidate_fp in range(SUPPORT_NEGATIVE+1):
            precision = candidate_tp/(candidate_tp+candidate_fp)*100 if candidate_tp+candidate_fp else 0
            accuracy = (SUPPORT_NEGATIVE-candidate_fp+candidate_tp)/cm.sum()*100
            if abs(precision-row["Precision (%)"]) < 1e-9 and abs(accuracy-row["Accuracy (%)"]) < 1e-9:
                matches.append((candidate_tp, candidate_fp))
    assert matches == [(tp, fp)]
    row["Confusion_Matrix"] = cm.tolist()
    row["Confusion_Matrix_Order"] = ["Not Bankrupt (0)", "Bankrupt (1)"]
    row["Support"] = {"Not Bankrupt": SUPPORT_NEGATIVE, "Bankrupt": SUPPORT_POSITIVE}
    row["Count_Provenance"] = "Uniquely reconstructed from original reported metrics and test supports; not newly fitted predictions."
    return cm


def save(fig, stem):
    fig.savefig(OUT / f"{stem}.png", dpi=300, facecolor="white")
    fig.savefig(OUT / f"{stem}.svg", facecolor="white")
    plt.close(fig)


def draw_matrix(ax, row, cm):
    ax.imshow(cm, cmap=row["cmap"], vmin=0, vmax=cm.max())
    ax.set_title(f"{row['label']} — SMOTE {row['ratio']:g}", fontsize=14, weight="bold", pad=14)
    ax.set_xticks([0,1], labels=["Not Bankrupt (0)", "Bankrupt (1)"])
    ax.set_yticks([0,1], labels=["Not Bankrupt (0)", "Bankrupt (1)"])
    ax.set_xlabel("Predicted label", fontsize=12, labelpad=10)
    ax.set_ylabel("True label", fontsize=12, labelpad=10)
    ax.tick_params(axis="both", length=0, labelsize=10)
    for i in range(2):
        for j in range(2):
            ax.text(j,i,str(cm[i,j]),ha="center",va="center",fontsize=19,
                    color="white" if cm[i,j] > cm.max()/2 else "black")
    for spine in ax.spines.values():
        spine.set_visible(False)


def metrics_chart(rows, stem):
    fields=["Accuracy (%)", "ROC-AUC (%)", "Precision (%)", "Recall (%)", "F1-Score (%)"]
    fig,ax=plt.subplots(figsize=(12,6.5))
    x=np.arange(len(fields))
    width=.36 if len(rows)==2 else .55
    for i,row in enumerate(rows):
        offset=(i-(len(rows)-1)/2)*width
        values=[row[m] for m in fields]
        bars=ax.bar(x+offset,values,width,color=row["color"],
                    label=f"{row['label']} (SMOTE {row['ratio']:g})")
        ax.bar_label(bars,labels=[f"{v:.2f}%" for v in values],padding=4,fontsize=10)
    ax.set_xticks(x, labels=["Accuracy", "ROC-AUC", "Precision", "Recall", "F1-score"])
    ax.set_ylabel("Score (%)",fontsize=12)
    ax.set_xlabel("Held-out test metric",fontsize=12,labelpad=10)
    ax.set_ylim(0,113)
    ax.set_title("Historical candidate performance — 80:20 split + 10-fold training CV",
                 fontsize=15,weight="bold",pad=16)
    ax.legend(loc="upper center",bbox_to_anchor=(.5,-.13),ncol=len(rows),frameon=False,fontsize=11)
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y",alpha=.15)
    ax.set_axisbelow(True)
    fig.text(.02,.015,"Source: original Phase 02 result tables. Redrawn from recorded metrics; no model rerun.\nPrecision, recall and F1 refer to Bankrupt (1). Different SMOTE ratios are shown explicitly.",fontsize=8.5)
    fig.tight_layout(rect=(0,.10,1,1))
    save(fig,stem)


def write_record(rows):
    lines=["SHIELD - REQUESTED HISTORICAL CANDIDATE CHARTS", "",
           "Figures recreated on 21 October 2026 (Asia/Kuala_Lumpur) from original pasted experiment tables.",
           "No training or new performance evaluation was performed to produce these figures.",
           "Confusion counts are uniquely reconstructed and checked against full-precision historical metrics.",
           "Supports: 1320 Not Bankrupt; 44 Bankrupt; 1364 test companies.",
           "Both configurations: 80:20 holdout split; 10-fold CV within training; top-20 IG; original default predict() rule.",
           "Rows of each confusion matrix are true labels; columns are predicted labels.",
           "Label order: [Not Bankrupt (0), Bankrupt (1)].", ""]
    for row in rows:
        cm=np.array(row["Confusion_Matrix"])
        lines += [f"{row['label']} | SMOTE {row['ratio']:g} | {row['Experiment']}",
                  " | ".join(f"{m}: {row[m]}" for m in ["Accuracy (%)","Precision (%)","Recall (%)","F1-Score (%)","ROC-AUC (%)"]),
                  f"Confusion matrix: {cm.tolist()}",
                  f"TN={cm[0,0]}; FP={cm[0,1]}; FN={cm[1,0]}; TP={cm[1,1]}",
                  "Best_Params: "+json.dumps(row["Best_Params"],sort_keys=True),
                  f"Training CV_F1_Mean: {row['CV_F1_Mean (%)']}%",
                  f"Original source: {row['Source']} | table row {row['Original_Source_Index']}", ""]
    lines += ["ROC CURVE STATUS",
              "The reported ROC-AUC values are available and included in the metric charts.",
              "The original per-company prediction scores for these two exact historical runs were not found locally.",
              "AUC and a single confusion matrix cannot uniquely reconstruct a ROC curve. No curve is invented.",
              "Existing PNGs/notebook figures and saved models were checked; they belong to other configurations.", "",
              "To recover exact ROC curves from the original Colab Google Drive reports, locate:",
              "SMOTE 0.25 / checkpoints_master/8020_cv10_RandomForest_preds.npz",
              "SMOTE 0.1 / checkpoints_master/8020_cv10_XGBoost_preds.npz",
              "Each original NPZ should contain y_true, y_pred and y_score; the adjacent _result.json identifies its run.",
              "Validate its metrics against historical_metrics.json before plotting y_true versus y_score.", "",
              "Historical results are exploratory: repeated comparison on the holdout is not an untouched final evaluation.", ""]
    (OUT/"HISTORICAL_CHARTS_README.txt").write_text("\n".join(lines),encoding="utf-8")


if __name__ == "__main__":
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11})
    rows=[read_historical_row(spec) for spec in SPECS]
    matrices=[derive_and_check_counts(row) for row in rows]
    assert matrices[0].tolist()==[[1275,45],[14,30]]
    assert matrices[1].tolist()==[[1305,15],[22,22]]
    (OUT/"historical_metrics.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    fig,axes=plt.subplots(1,2,figsize=(13,6.2))
    for ax,row,cm in zip(axes,rows,matrices):
        draw_matrix(ax,row,cm)
    fig.suptitle("Historical confusion matrices — 80:20 split + 10-fold training CV",fontsize=15,weight="bold",y=.98)
    fig.text(.02,.025,"Reconstructed from original reported metrics and test supports; no model rerun.\nTest support per configuration: 1320 Not Bankrupt and 44 Bankrupt companies.",fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.94),w_pad=4)
    save(fig,"historical_candidates_confusion_matrices")
    metrics_chart(rows,"historical_candidates_metric_comparison")
    for row,cm in zip(rows,matrices):
        fig,ax=plt.subplots(figsize=(7,6.6))
        draw_matrix(ax,row,cm)
        ax.set_title(f"{row['label']} — SMOTE {row['ratio']:g}\n80:20 split + 10-fold training CV",fontsize=14,weight="bold",pad=14)
        fig.text(.035,.02,"Reconstructed from historical metrics; no model rerun.\nTest support: Not Bankrupt 1320; Bankrupt 44.",fontsize=9)
        fig.tight_layout(rect=(0,.09,1,1))
        save(fig,f"{row['stem']}_confusion_matrix")
        metrics_chart([row],f"{row['stem']}_metric_chart")
    write_record(rows)
    print("Verified original metrics, unique confusion counts and all plotted values.")
    print("RF: TN=1275 FP=45 FN=14 TP=30")
    print("XGBoost: TN=1305 FP=15 FN=22 TP=22")
    print("Saved 6 PNG figures, 6 SVG figures and source/verification records to",OUT)
