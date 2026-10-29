import json
from pathlib import Path
cells=[]
def md(s): cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s,definitions=False): cells.append(dict(cell_type='code',metadata={'definitions':True} if definitions else {},source=s.splitlines(True),execution_count=None,outputs=[]))
md('''# experiment-Smote-ENN-SHIELD

Compare **Balanced Random Forest**, **SMOTE-ENN + XGBoost**, and **EasyEnsemble** for bankruptcy identification.
EasyEnsemble is an ensemble of AdaBoost classifiers trained on balanced undersamples.
BRF and EasyEnsemble balance internally: do **not** add external SMOTE to them.

Default: original financial predictors (95; exclude Company and Bankrupt), stratified **80:20**, **5-fold ordinary training CV**, seed 42, cutoff 0.5. Optional IG top 20 is fitted inside each training fold. SMOTE ratio starts at **0.1**; change it to 0.25, 0.5, or 1.0 for later runs. This ratio applies only to the SMOTE stage of SMOTE-ENN; ENN may change the resulting class counts.

This focused comparison uses fixed parameters, not GridSearchCV or nested CV. CV scores are training OOF estimates; the untouched-in-this-run test set is scored after training CV. Because SHIELD has inspected this historical holdout before, test comparisons remain exploratory. No guarantee of 70% precision and recall.
''')
code('%pip install -q scikit-learn==1.9.0 imbalanced-learn==0.14.2 xgboost==2.0.3 openpyxl matplotlib pandas joblib\n')
md('## 1. Settings and paths\nRun top to bottom in Colab. Update the Drive paths to match your project. Outputs go into a new timestamped folder, preserving earlier results.')
code('''from pathlib import Path
from datetime import datetime, timezone
SEED=42
TEST_SIZE=0.20
CV_FOLDS=5                 # Change to 10 if required
FEATURE_MODE='all'         # 'all' or 'ig20'
TOP_K=20
SMOTE_RATIO=0.1            # Then 0.25, 0.5, 1.0
MODEL_JOBS=2
try:
    from google.colab import drive
    drive.mount('/content/drive')
    BASE=Path('/content/drive/MyDrive/SHIELD_Project')
except ImportError:
    BASE=Path.cwd()
    if BASE.name=='notebooks': BASE=BASE.parent
RAW_PATH=BASE/'data'/'bankruptcy_italian_companies_2023.xlsx'
OUTPUT_BASE=BASE/'reports'/'experiment-Smote-ENN-SHIELD'
''')
md('## 2. Models and reporting functions\nStandardScaler is fitted before distance-based SMOTE-ENN, only on the current training fold. Trees do not require scaling; the other two methods do not use it. IG estimates mutual information with a fixed seed. Scores are model outputs, not calibrated bankruptcy probabilities.')
code('''import hashlib, json, platform, importlib.metadata
from functools import partial
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from sklearn.base import clone
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    fbeta_score, roc_auc_score, average_precision_score, confusion_matrix,
    classification_report, ConfusionMatrixDisplay, RocCurveDisplay, PrecisionRecallDisplay)
from imblearn.pipeline import Pipeline
from imblearn.ensemble import BalancedRandomForestClassifier, EasyEnsembleClassifier
from imblearn.combine import SMOTEENN
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import EditedNearestNeighbours
from xgboost import XGBClassifier

METHODS=['BalancedRandomForest','SMOTEENN_XGBoost','EasyEnsemble']

def make_pipeline(name, small=False):
    if FEATURE_MODE not in ['all','ig20']:
        raise ValueError("FEATURE_MODE must be 'all' or 'ig20'")
    steps=[]
    if FEATURE_MODE=='ig20':
        steps.append(('ig',SelectKBest(partial(mutual_info_classif,random_state=SEED),k=TOP_K)))
    if name=='BalancedRandomForest':
        model=BalancedRandomForestClassifier(n_estimators=5 if small else 200,
            max_depth=10,min_samples_split=2,max_features='sqrt',
            sampling_strategy='all',replacement=True,bootstrap=False,
            random_state=SEED,n_jobs=MODEL_JOBS)
    elif name=='SMOTEENN_XGBoost':
        steps.extend([('scale',StandardScaler()),('resample',SMOTEENN(
            smote=SMOTE(sampling_strategy=SMOTE_RATIO,k_neighbors=5,random_state=SEED),
            enn=EditedNearestNeighbours(sampling_strategy='all',n_neighbors=3,kind_sel='all'),
            random_state=SEED,n_jobs=MODEL_JOBS))])
        model=XGBClassifier(n_estimators=5 if small else 100,max_depth=6,
            learning_rate=.1,eval_metric='logloss',tree_method='hist',
            random_state=SEED,n_jobs=MODEL_JOBS)
    elif name=='EasyEnsemble':
        model=EasyEnsembleClassifier(n_estimators=2 if small else 10,
            estimator=AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1,random_state=SEED),
                n_estimators=5 if small else 50,learning_rate=1.,random_state=SEED),
            sampling_strategy='auto',replacement=False,random_state=SEED,n_jobs=MODEL_JOBS)
    else: raise ValueError(name)
    return Pipeline(steps+[('model',model)])

def metrics(y,score):
    pred=(np.asarray(score)>=.5).astype(int)
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    specificity=tn/(tn+fp)
    recall=recall_score(y,pred,zero_division=0)
    return {'Accuracy (%)':100*accuracy_score(y,pred),
        'Precision (%)':100*precision_score(y,pred,zero_division=0),
        'Recall (%)':100*recall,'F1-Score (%)':100*f1_score(y,pred,zero_division=0),
        'ROC-AUC (%)':100*roc_auc_score(y,score),
        'F2 (%)':100*fbeta_score(y,pred,beta=2,zero_division=0),
        'PR-AUC (AP) (%)':100*average_precision_score(y,score),
        'G-mean (%)':100*np.sqrt(recall*specificity),
        'TN':int(tn),'FP':int(fp),'FN':int(fn),'TP':int(tp)}

def report(name,stage,y,score,out):
    pred=(np.asarray(score)>=.5).astype(int)
    m=metrics(y,score)
    text=f'=== Classification Report: {name} | {stage} ===\\n'
    text+=classification_report(y,pred,labels=[0,1],target_names=['Not Bankrupt','Bankrupt'],digits=4,zero_division=0)
    text+='\\n'+' | '.join(f'{k}: {m[k]:.2f}%' for k in ['Accuracy (%)','Precision (%)','Recall (%)','F1-Score (%)','ROC-AUC (%)'])
    print(text)
    (out/f'{name}_{stage}_report.txt').write_text(text,encoding='utf-8')
    fig,axes=plt.subplots(1,3,figsize=(16,4))
    ConfusionMatrixDisplay.from_predictions(y,pred,labels=[0,1],display_labels=['Not Bankrupt','Bankrupt'],ax=axes[0],cmap='Blues',colorbar=False)
    RocCurveDisplay.from_predictions(y,score,ax=axes[1])
    PrecisionRecallDisplay.from_predictions(y,score,ax=axes[2])
    fig.suptitle(f'{name} | {stage} | cutoff 0.5')
    fig.tight_layout()
    fig.savefig(out/f'{name}_{stage}_plots.png',dpi=200,bbox_inches='tight')
    plt.show()
    return m
''',True)
md('## 3. Load original data and split\nUse original, unresampled data. Numeric conversion is checked, not silently coerced. Missing values, infinite values, duplicate companies or duplicate predictor rows require investigation. No automatic row deletion or clipping. Feature selection remains in the training pipeline.')
code('''raw=pd.read_excel(RAW_PATH) if RAW_PATH.suffix.lower() in ['.xlsx','.xls'] else pd.read_csv(RAW_PATH,float_precision='round_trip')
raw.columns=raw.columns.str.strip()
if raw.columns.duplicated().any(): raise ValueError('Duplicate column names')
if 'Bankrupt' not in raw: raise ValueError('Expected Bankrupt target: 0/1')
if raw.isna().any().any(): raise ValueError('Missing data: investigate before running')
if 'Company' in raw and raw.Company.duplicated().any(): raise ValueError('Duplicate company IDs')
X=raw.drop(columns=['Bankrupt','Company'],errors='ignore').apply(pd.to_numeric,errors='raise')
y=pd.to_numeric(raw.Bankrupt,errors='raise')
if set(y.unique())!={0,1}: raise ValueError('Bankrupt must contain exactly 0 and 1')
y=y.astype(int)
if not np.isfinite(X.to_numpy()).all(): raise ValueError('Non-finite predictors')
if X.duplicated().any(): raise ValueError('Duplicate predictor rows: investigate before splitting')
if FEATURE_MODE=='ig20' and X.shape[1]<TOP_K: raise ValueError('Insufficient financial predictors')
train_idx,test_idx=train_test_split(np.arange(len(y)),test_size=TEST_SIZE,stratify=y,random_state=SEED)
X_train,y_train=X.iloc[train_idx],y.iloc[train_idx]
X_test,y_test=X.iloc[test_idx],y.iloc[test_idx]
print('Financial predictors:',X.shape[1])
print('Training:',y_train.value_counts().sort_index().to_dict())
print('Test:',y_test.value_counts().sort_index().to_dict())
OUT=OUTPUT_BASE/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+f'_{FEATURE_MODE}_smote{SMOTE_RATIO}')
OUT.mkdir(parents=True,exist_ok=False)
settings=dict(seed=SEED,test_size=TEST_SIZE,cv_folds=CV_FOLDS,feature_mode=FEATURE_MODE,
    top_k=TOP_K,smote_ratio=SMOTE_RATIO,cutoff=.5,
    raw_sha256=hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(),
    versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','imbalanced-learn','xgboost']},
    parameters={name:make_pipeline(name).get_params(deep=True) for name in METHODS})
(OUT/'run_settings.json').write_text(json.dumps(settings,indent=2,default=str),encoding='utf-8')
pd.DataFrame({'row_index':np.arange(len(y)),'partition':np.where(np.isin(np.arange(len(y)),train_idx),'training','test'),'Bankrupt':y}).to_csv(OUT/'partitions.csv',index=False)
''')
md('## 4. Ordinary CV on training companies\nAll methods share exactly the same folds. Each training company is predicted once while held out. No hyperparameter or threshold search. CV_F1_Mean is the mean of fold F1 scores; pooled OOF F1 may differ. Fold-level predictions, selected features, and results are saved as each fold completes. ENN removes training rows only. Inspect pre/post resampling counts in fold_details.json.')
code('''cv=StratifiedKFold(n_splits=CV_FOLDS,shuffle=True,random_state=SEED)
folds=list(cv.split(X_train,y_train))
rows=[]
fold_details=[]
for name in METHODS:
    scores=np.full(len(y_train),np.nan)
    fold_f1=[]
    for fold,(tr,va) in enumerate(folds,1):
        pipe=make_pipeline(name)
        pipe.fit(X_train.iloc[tr],y_train.iloc[tr])
        probability=pipe.predict_proba(X_train.iloc[va])[:,1]
        scores[va]=probability
        values=metrics(y_train.iloc[va],probability)
        fold_f1.append(values['F1-Score (%)'])
        features=X.columns[pipe.named_steps['ig'].get_support()].tolist() if 'ig' in pipe.named_steps else X.columns.tolist()
        detail=dict(model=name,fold=fold,training_rows=train_idx[tr].tolist(),validation_rows=train_idx[va].tolist(),
            features=features,metrics=values,training_counts=y_train.iloc[tr].value_counts().to_dict())
        if 'resample' in pipe.named_steps:
            z=X_train.iloc[tr]
            if 'ig' in pipe.named_steps: z=pipe.named_steps['ig'].transform(z)
            z=pipe.named_steps['scale'].transform(z)
            _,resampled_y=clone(pipe.named_steps['resample']).fit_resample(z,y_train.iloc[tr])
            detail['post_ENN_counts']=pd.Series(resampled_y).value_counts().to_dict()
        fold_details.append(detail)
        np.savez_compressed(OUT/f'{name}_fold{fold}_predictions.npz',row_index=train_idx[va],y_true=y_train.iloc[va],y_score=probability)
        (OUT/'fold_details.json').write_text(json.dumps(fold_details,indent=2,default=str),encoding='utf-8')
        print(name,'fold',fold,'F1:',round(values['F1-Score (%)'],2))
    assert np.isfinite(scores).all()
    np.savez_compressed(OUT/f'{name}_training_OOF.npz',row_index=train_idx,y_true=y_train,y_score=scores)
    result=report(name,'training_OOF',y_train,scores,OUT)
    rows.append(dict(Model=name,Experiment=f'{int((1-TEST_SIZE)*100)}-{int(TEST_SIZE*100)} + CV={CV_FOLDS}',
        Stage='Training OOF',Split=TEST_SIZE,CV=CV_FOLDS,SMOTE=SMOTE_RATIO if name=='SMOTEENN_XGBoost' else None,
        **result,CV_F1_Mean=sum(fold_f1)/len(fold_f1),CV_F1_SD=float(np.std(fold_f1,ddof=1))))
    pd.DataFrame(rows).to_csv(OUT/'results.csv',index=False)
''')
md('## 5. Refit and test\nEach fixed pipeline is refitted on all training companies, then evaluated on the original imbalanced test set. No resampling of test companies. Comparing these test results does not make them a fresh final validation set. Save models for research; this notebook does not replace the SHIELD prototype model.')
code('''for name in METHODS:
    pipe=make_pipeline(name)
    pipe.fit(X_train,y_train)
    scores=pipe.predict_proba(X_test)[:,1]
    result=report(name,'test',y_test,scores,OUT)
    cv_row=next(r for r in rows if r['Model']==name and r['Stage']=='Training OOF')
    rows.append(dict(Model=name,Experiment=cv_row['Experiment'],Stage='Test',Split=TEST_SIZE,CV=CV_FOLDS,
        SMOTE=SMOTE_RATIO if name=='SMOTEENN_XGBoost' else None,**result,
        CV_F1_Mean=cv_row['CV_F1_Mean'],CV_F1_SD=cv_row['CV_F1_SD']))
    joblib.dump(pipe,OUT/f'{name}_pipeline.joblib')
    np.savez_compressed(OUT/f'{name}_test_predictions.npz',row_index=test_idx,y_true=y_test,y_score=scores)
    selected=X.columns[pipe.named_steps['ig'].get_support()].tolist() if 'ig' in pipe.named_steps else X.columns.tolist()
    (OUT/f'{name}_features.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
    pd.DataFrame(rows).to_csv(OUT/'results.csv',index=False)
results=pd.DataFrame(rows)
display(results.round(2))
(OUT/'RESULTS.txt').write_text('SHIELD: fixed parameters, threshold 0.5. Bankruptcy=positive class.\\n'+
    'See run_settings.json for all settings; OOF and test stages are distinct.\\n\\n'+results.to_string(index=False),encoding='utf-8')
print('Saved reports:',OUT)
''')
md('''## Interpretation and next runs
- Compare bankruptcy **precision, recall, F1 and F2**, not accuracy alone. G-mean measures the balance of sensitivity and specificity, not precision.
- Change SMOTE_RATIO from 0.1 to 0.25, 0.5 and 1.0 and rerun. This changes only SMOTE-ENN + XGBoost. BRF/EasyEnsemble do not have an external SMOTE ratio.
- Start with all financial predictors; switch FEATURE_MODE to `ig20` for the matched feature-selection arm. Learned top-20 features can differ across folds. Exported final features come from the refit on all training companies.
- Repeating ratios/feature configurations and choosing the winner turns the OOF estimates into selection scores. Use independent future/external validation to substantiate a final performance claim.
- Financial risk bands require separate justification and calibration; these scores alone do not establish distress severity.

### References
[Gnip et al. (2025)](https://link.springer.com/article/10.1007/s10462-025-11107-y) motivates alternatives; this is not an exact reproduction of their study.
[Balanced Random Forest](https://imbalanced-learn.org/stable/references/generated/imblearn.ensemble.BalancedRandomForestClassifier.html), [SMOTEENN](https://imbalanced-learn.org/stable/references/generated/imblearn.combine.SMOTEENN.html), [EasyEnsemble](https://imbalanced-learn.org/stable/references/generated/imblearn.ensemble.EasyEnsembleClassifier.html).
''')
nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version='3.11'),colab=dict(name='experiment-Smote-ENN-SHIELD.ipynb')),nbformat=4,nbformat_minor=5)
for i,c in enumerate(cells): c['id']=f'shield-{i:02d}'
path=Path(__file__).with_name('experiment-Smote-ENN-SHIELD.ipynb')
path.write_text(json.dumps(nb,indent=1,ensure_ascii=False),encoding='utf-8')
print(path)
