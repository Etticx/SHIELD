SHIELD - REQUESTED HISTORICAL CANDIDATE CHARTS

Figures recreated on 21 October 2026 (Asia/Kuala_Lumpur) from original pasted experiment tables.
No training or new performance evaluation was performed to produce these figures.
Confusion counts are uniquely reconstructed and checked against full-precision historical metrics.
Supports: 1320 Not Bankrupt; 44 Bankrupt; 1364 test companies.
Both configurations: 80:20 holdout split; 10-fold CV within training; top-20 IG; original default predict() rule.
Rows of each confusion matrix are true labels; columns are predicted labels.
Label order: [Not Bankrupt (0), Bankrupt (1)].

Random Forest | SMOTE 0.25 | 80-20 + CV=10
Accuracy (%): 95.67448680351906 | Precision (%): 40.0 | Recall (%): 68.18181818181817 | F1-Score (%): 50.42016806722689 | ROC-AUC (%): 94.43870523415978
Confusion matrix: [[1275, 45], [14, 30]]
TN=1275; FP=45; FN=14; TP=30
Best_Params: {"model__max_depth": 10, "model__min_samples_split": 2, "model__n_estimators": 200}
Training CV_F1_Mean: 43.29762120163908%
Original source: C:\Users\User\.codex\attachments\b1001435-c810-4838-adea-d3334c789082\Pasted text.txt | table row 40

XGBoost | SMOTE 0.1 | 80-20 + CV=10
Accuracy (%): 97.28739002932552 | Precision (%): 59.45945945945946 | Recall (%): 50.0 | F1-Score (%): 54.32098765432099 | ROC-AUC (%): 93.99276859504133
Confusion matrix: [[1305, 15], [22, 22]]
TN=1305; FP=15; FN=22; TP=22
Best_Params: {"model__learning_rate": 0.1, "model__max_depth": 6, "model__n_estimators": 100}
Training CV_F1_Mean: 44.43943466234489%
Original source: C:\Users\User\.codex\attachments\a9acd921-8a2e-40aa-98cc-a46863fdeb25\Pasted text.txt | table row 41

ROC CURVE STATUS
The reported ROC-AUC values are available and included in the metric charts.
The original per-company prediction scores for these two exact historical runs were not found locally.
AUC and a single confusion matrix cannot uniquely reconstruct a ROC curve. No curve is invented.
Existing PNGs/notebook figures and saved models were checked; they belong to other configurations.

To recover exact ROC curves from the original Colab Google Drive reports, locate:
SMOTE 0.25 / checkpoints_master/8020_cv10_RandomForest_preds.npz
SMOTE 0.1 / checkpoints_master/8020_cv10_XGBoost_preds.npz
Each original NPZ should contain y_true, y_pred and y_score; the adjacent _result.json identifies its run.
Validate its metrics against historical_metrics.json before plotting y_true versus y_score.

Historical results are exploratory: repeated comparison on the holdout is not an untouched final evaluation.
