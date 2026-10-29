"""Build a seven-input adaptation of the original SHIELD master experiment flow."""
import json,ast
from pathlib import Path
HERE=Path(__file__).resolve().parent
nb=json.loads((HERE/'SHIELD_Master_Validated_SMOTE.ipynb').read_text())
def setcell(i,s):nb['cells'][i]['source']=s.splitlines(True)
seven=["Net Income to Stockholder's Equity",'Net Income to Total Assets','Retained Earnings to Total Assets',
       'Debt ratio %','Net worth/Assets','Equity to Liability','Liability to Equity']
setcell(0,'''# SHIELD — Seven fixed features | Random Forest and XGBoost

Same preprocessing → experiment/checkpoint → results flow as the original master notebook, restricted to seven predefined features. **No IG selection and no imputation.**

Eight protocols:70:30 only,80:20 only,CV5 only,CV10 only,70:30+CV5,70:30+CV10,80:20+CV5,80:20+CV10. Two models =16 results per ratio. DefaultSMOTE0.25; supported ratios0.1,0.25,0.5,0.75and1.0. Change the ratio and rerun from settings for another16 results,stored separately.

Split-only/CV-only use predefined fixed parameters. Split+CV uses the original RF/XGBoost grids,training-only GridSearchCV scoring bankruptcy F1. Ordinary CV-only performs no tuning and is not nested CV. Headline scores for holdout protocols are test results; CV-only scores are pooled held-out fold predictions,not a separate test set.

Accounting availability research identified these seven as calculator candidates from net income,assets,liabilities,equity and retained earnings in complete incorporated-SME accounts. Exact donor formulas and original input transformation are not verified. This notebook trains existing transformed dataset columns,not raw financial statements,and does not deploy a model. Shared/historical test reuse and historical feature selection mean all comparisons remain exploratory.
''')
setcell(1,'''# PART A — PREPROCESSING
The80:20 example demonstrates training-only SMOTE. Development creates its own partitions from the original seven-column data and never uses the balanced demo arrays as CV input.
''')
setup='''import os, random, json, hashlib, platform, time, tempfile, importlib.metadata
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
try:
    from IPython.display import display
except ImportError:
    display=print
from sklearn.model_selection import train_test_split,GridSearchCV,StratifiedKFold,ParameterGrid
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,roc_curve,confusion_matrix,classification_report
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from xgboost import XGBClassifier

SMOTE_RATIO=0.25       # Choose0.1,0.25,0.5,0.75or1.0
SEED=42
K_FEATURES=7
SMOTE_K_NEIGHBORS=5
N_JOBS=2              # Search parallelism; each estimator uses one worker
USE_PIPELINE_CACHE=True
NOTEBOOK_VERSION='shield-seven-rf-xgb-eight-protocols-v1'
TARGET_COL='Bankrupt'
LABEL_MAP={0:'Not Bankrupt',1:'Bankrupt'}
SEVEN_FEATURES=__SEVEN__
assert SMOTE_RATIO in [.1,.25,.5,.75,1.0], 'Choose0.1,0.25,0.5,0.75or1.0'
random.seed(SEED);np.random.seed(SEED)
try:
    from google.colab import drive
    drive.mount('/content/drive')
    PROJECT=Path('/content/drive/MyDrive/SHIELD_Project')
except ImportError:
    PROJECT=Path.cwd()
    if PROJECT.name=='notebooks':PROJECT=PROJECT.parent
RAW_PATH=str(PROJECT/'data'/'bankruptcy_italian_companies_2023.xlsx')
BASE_REPORT_DIR=str(PROJECT/'reports')
BASE_MODEL_DIR=str(PROJECT/'models_research')
PACKAGE_VERSIONS={name:importlib.metadata.version(name) for name in ['numpy','pandas','scikit-learn','imbalanced-learn','xgboost','joblib']}
print('Seed:',SEED,'SMOTE:',SMOTE_RATIO,'Packages:',PACKAGE_VERSIONS)
'''.replace('__SEVEN__',repr(seven))
setcell(2,'''## A1. Setup
Configure SMOTE_RATIO to0.1 for the next run;0.25,0.5,0.75and1.0 are also supported. Run the installation/setup cell. If changing versions already loaded in Colab,restart the runtime after installing. Edit Drive paths to match your folders.
''')
# Keep indices stable for builders/tests; pip magic inserted at end after verification.
setcell(3,setup)
setcell(5,'''df_raw=pd.read_excel(RAW_PATH) if Path(RAW_PATH).suffix.lower() in ['.xlsx','.xls'] else pd.read_csv(RAW_PATH,float_precision='round_trip')
df_raw.columns=df_raw.columns.str.strip()
RAW_SHA256=hashlib.sha256(Path(RAW_PATH).read_bytes()).hexdigest()
print('Raw shape:',df_raw.shape)
display(df_raw.head())
''')
setcell(6,'''## A3. Clean and restrict to the seven features
Drop the identifier from model inputs; validate target,unique column names,numeric finite predictors and missingness. Do not remove companies simply because seven ratios coincide. Repeated Company IDs or duplicate full financial records require investigation. No outlier clipping or estimated replacement values.
''')
setcell(7,'''assert not df_raw.columns.duplicated().any(), 'Duplicate column names'
assert TARGET_COL in df_raw and set(df_raw[TARGET_COL].dropna().unique())=={0,1}, 'Expected binary Bankrupt target'
assert not df_raw[TARGET_COL].isna().any(), 'Missing target'
assert all(c in df_raw for c in SEVEN_FEATURES), 'Required seven features missing'
if 'Company' in df_raw:
    assert not df_raw.Company.duplicated().any(), 'Repeated Company IDs: investigate grouped splitting'
full_predictors=df_raw.drop(columns=['Company',TARGET_COL],errors='ignore')
assert not full_predictors.duplicated().any(), 'Repeated full financial records: investigate before CV'
df=df_raw[SEVEN_FEATURES+[TARGET_COL]].copy()
for c in SEVEN_FEATURES:df[c]=pd.to_numeric(df[c],errors='raise')
assert not df.isna().any().any(), 'Missing inputs: this experiment does not impute'
assert np.isfinite(df[SEVEN_FEATURES].to_numpy(dtype=float)).all(), 'Nonfinite inputs'
before_shape=df_raw.shape
dropped_cols=[c for c in df_raw if c not in df]
print('Before:',before_shape,'Seven inputs + target:',df.shape)
print('Repeated seven-input combinations (reported,not removed):',df[SEVEN_FEATURES].duplicated().sum())
''')
setcell(12,'## A6. Fixed seven-feature schema — NO IG\nThe seven remain identical across all models,folds and protocols. Original IG positions are historical references only.')
setcell(13,'''selected_cols_demo=SEVEN_FEATURES.copy()
X_train_sel_demo=X_train_demo[SEVEN_FEATURES].copy()
X_test_sel_demo=X_test_demo[SEVEN_FEATURES].copy()
feature_reference=pd.DataFrame({'Feature':SEVEN_FEATURES,'Historical_IG_Rank':[5,7,13,14,16,17,20],
    'Historical_IG_Score':[.036753,.035144,.032738,.032479,.032132,.031732,.030660]})
display(feature_reference)
print('Fixed seven inputs;no IG fitted or recalculated.')
''')
setcell(17,'''print('=== PREPROCESSING SUMMARY ===')
print('Raw:',df_raw.shape,'Clean fixed-input table:',df.shape)
print('Target:',LABEL_MAP)
print('Fixed features:',SEVEN_FEATURES)
print('Demo training shapes:',X_train_sel_demo.shape,'→',X_train_bal_demo.shape)
print('Test unchanged:',X_test_sel_demo.shape)
print('PartB uses original X_full/y_full,not balanced demo arrays.')
''')
setcell(18,'''# PART B — MODEL DEVELOPMENT

Split-only:one train/test fit with fixed parameters.
CV-only:ordinary5/10-fold CV on all original companies with fixed parameters. Each company is held out once;export-only final refit does not generate evaluation scores.
Split+CV:hold out30%or20%,then training-only5/10-fold GridSearchCV. Choose hyperparameters by mean bankruptcy F1,refit the training partition,and evaluate once on its test partition.

No nested CV,no IG,no threshold tuning. A higher test score from a different partition does not establish that partition is intrinsically superior. CV-only and holdout metrics describe different evaluation populations.

Checkpoints save completed experiments and individual CV-only folds. **An interrupted GridSearchCV restarts that particular search**,not the whole notebook. Other completed experiments are reused. SMOTE fits only training subsets.
''')
setcell(19,'## B1. Two models,eight protocols and isolated checkpoints')
config='''PROTOCOLS=[
 {'name':'70-30 only','slug':'7030_only','split':.30,'cv':None},
 {'name':'80-20 only','slug':'8020_only','split':.20,'cv':None},
 {'name':'CV=5 only','slug':'cv5_only','split':None,'cv':5},
 {'name':'CV=10 only','slug':'cv10_only','split':None,'cv':10},
 {'name':'70-30 + CV=5','slug':'7030_cv5','split':.30,'cv':5},
 {'name':'70-30 + CV=10','slug':'7030_cv10','split':.30,'cv':10},
 {'name':'80-20 + CV=5','slug':'8020_cv5','split':.20,'cv':5},
 {'name':'80-20 + CV=10','slug':'8020_cv10','split':.20,'cv':10}]
MODELS=['RandomForest','XGBoost']
SCALED_MODELS=[]
MODEL_LABELS={'RandomForest':'Random Forest','XGBoost':'XGBoost'}
SCORE_TYPES={m:'predict_proba' for m in MODELS}
FIXED_PARAMS={
 'RandomForest':{'n_estimators':200,'max_depth':10,'min_samples_split':2},
 'XGBoost':{'n_estimators':200,'max_depth':6,'learning_rate':.1}}
ESTIMATOR_OPTIONS={
 'RandomForest':{'random_state':SEED,'n_jobs':1,'min_samples_leaf':1,'max_features':'sqrt','class_weight':None},
 'XGBoost':{'random_state':SEED,'n_jobs':1,'eval_metric':'logloss'}}
PARAM_GRIDS={
 'RandomForest':{'model__n_estimators':[100,200],'model__max_depth':[6,10,None],'model__min_samples_split':[2,5]},
 'XGBoost':{'model__n_estimators':[100,200],'model__max_depth':[3,6,9],'model__learning_rate':[.01,.1,.2]}}
RATIO_TAG=str(SMOTE_RATIO).replace('.','p')
RUN_SPEC={'version':NOTEBOOK_VERSION,'data_fingerprint':DATA_FINGERPRINT,'raw_sha256':RAW_SHA256,
 'features':SEVEN_FEATURES,'smote_ratio':SMOTE_RATIO,'smote_neighbors':SMOTE_K_NEIGHBORS,'seed':SEED,
 'protocols':PROTOCOLS,'models':MODELS,'fixed':FIXED_PARAMS,'grid':PARAM_GRIDS,
 'estimator_options':ESTIMATOR_OPTIONS,'packages':PACKAGE_VERSIONS,'python':platform.python_version(),
 'threshold':.5,'feature_selection':'fixed7,noIG','scaling':'none',
 'cv_only':'fixedparameter ordinaryCV','split_cv':'training-only GridSearchCV,f1'}
RUN_ID=hashlib.sha256(json.dumps(RUN_SPEC,sort_keys=True).encode()).hexdigest()[:16]
report_dir=f'{BASE_REPORT_DIR}/seven_features_smote_{RATIO_TAG}/{RUN_ID}'
ckpt_dir=f'{report_dir}/checkpoints_master'
model_dir=f'{BASE_MODEL_DIR}/seven_features_smote_{RATIO_TAG}/{RUN_ID}'
for folder in [report_dir,ckpt_dir,model_dir]:os.makedirs(folder,exist_ok=True)
with open(f'{report_dir}/run_config.json','w') as f:json.dump(RUN_SPEC,f,indent=2)
pipeline_memory=joblib.Memory(location=f'{tempfile.gettempdir()}/shield_seven_cache/{RUN_ID}',verbose=0) if USE_PIPELINE_CACHE else None
pd.DataFrame({'Input_Order':range(1,8),'Feature':SEVEN_FEATURES}).to_csv(f'{report_dir}/seven_features.csv',index=False)
for p in PROTOCOLS:
 if p['split'] is not None:
  tr,te=train_test_split(np.arange(len(y_full)),test_size=p['split'],random_state=SEED,stratify=y_full)
  pd.DataFrame({'row_index':np.arange(len(y_full)),'partition':np.where(np.isin(np.arange(len(y_full)),tr),'training','test')}).to_csv(f"{report_dir}/{p['slug']}_partitions.csv",index=False)
print('16 experiments per SMOTE ratio. Full original grids require approximately946 model fits per ratio including CV/refits.')
print('Output:',report_dir)
print('Fixed parameters:',FIXED_PARAMS,'Grids:',PARAM_GRIDS)
'''
setcell(20,config)
setcell(21,'## B2. Experiment runner — training-only SMOTE, fixed seven inputs')
runner=''.join(nb['cells'][22]['source'])
a=runner.index('def make_estimator(');b=runner.index('def make_cv(')
runner='''def make_estimator(model_name,params=None):
    constructors={'RandomForest':RandomForestClassifier,'XGBoost':XGBClassifier}
    return constructors[model_name](**{**ESTIMATOR_OPTIONS[model_name],**(params or {})})

def make_training_pipeline(model_name,params=None):
    return ImbPipeline([('smote',SMOTE(sampling_strategy=SMOTE_RATIO,random_state=SEED,k_neighbors=SMOTE_K_NEIGHBORS)),
        ('model',make_estimator(model_name,params))],memory=pipeline_memory)

'''+runner[b:]
a=runner.index('def predict_outputs(');b=runner.index('def checkpoint_paths(')
runner=runner[:a]+'''def predict_outputs(fitted_pipeline,X):
    classes=fitted_pipeline.named_steps['model'].classes_.tolist()
    assert classes==[0,1]
    score=np.asarray(fitted_pipeline.predict_proba(X)[:,1],dtype=float)
    return (score>=.5).astype(int),score

def selected_features(fitted_pipeline):
    columns=fitted_pipeline.feature_names_in_.tolist()
    assert columns==SEVEN_FEATURES,'Checkpoint/model feature order mismatch'
    return columns

'''+runner[b:]
a=runner.index("print('Runner defined:")
runner=runner[:a]+"print('Runner:fixed7→training-onlySMOTE→model;noIG. CV-only=fixedparameter;split+CV=training-onlytuning.')\n"
# Save CV-only membership and fold truth for traceability.
runner=runner.replace("np.savez_compressed(fold_npz, val_idx=val_idx, y_pred=fold_pred, y_score=fold_score)","np.savez_compressed(fold_npz,val_idx=val_idx,train_idx=train_idx,y_true=y_full.iloc[val_idx],y_pred=fold_pred,y_score=fold_score)")
setcell(22,runner)
setcell(23,'## B3. Run16 experiments\nResume completed checkpoints. Search results include selected parameters and full candidate CV scores. Model checkpoints are research artifacts and do not replace production files.')
# Original runner/report/table and save formats retained.
charts=''.join(nb['cells'][28]['source'])
charts=charts.replace('plt.subplots(2, 2, figsize=(12, 10))','plt.subplots(1, 2, figsize=(12, 5))')
charts=charts[charts.index('metrics_labels ='): ]
charts="MODEL_COLORS={'RandomForest':'#4C93E0','XGBoost':'#D866F5'}\nMODEL_CMAPS={'RandomForest':'Blues','XGBoost':'Purples'}\n"+charts
charts=charts.replace('Healthy (0)','Not Bankrupt (0)').replace('(Target: Bankrupt SMEs)','(Target: Bankrupt class)')
for chart in ['bar_comparison','confusion_matrices','roc_curve']:
 text=f"plt.savefig(f'{{report_dir}}/{{slug}}_{chart}.png', dpi=300);"
 charts=charts.replace(text,text+f" plt.savefig(f'{{report_dir}}/{{slug}}_{chart}.svg',bbox_inches='tight');")
setcell(27,'## B5. Comparison bars,confusion matrices and ROC curves\nTwo models per protocol; both PNG and SVG exports. Curves use actual held-out prediction scores. No fabricated ROC curves.')
setcell(28,charts)
setcell(31,'## B7. Research model and fixed seven-input schema\nEach completed experiment already has a fitted research pipeline checkpoint. This cell records the schema and selected RF80:20+CV10 reference;it does not automatically choose a winner or deploy it.')
setcell(32,'''reference=load_checkpoint('8020_cv10','RandomForest')
assert reference is not None,'Complete the experiment first'
manifest={'Run_ID':RUN_ID,'Features':SEVEN_FEATURES,'Input_Count':7,
 'Expected_Input':'Existing dataset feature representation;raw accounting transformation not verified',
 'No_IG':True,'No_Imputation':True,'Threshold':.5,'SMOTE_Ratio':SMOTE_RATIO,
 'Research_Reference_Only':reference[0],'Production_Replaced':False}
with open(f'{model_dir}/seven_input_manifest.json','w') as f:json.dump(manifest,f,indent=2)
print('Research pipelines:',ckpt_dir)
print('Schema manifest:',model_dir)
print('No production model replaced.')
''')
setcell(33,'''## Interpretation and limitations
-16results per ratio;32across0.25and1.0. No50:50,noLR/SVM,noIG. HistoricalIG ranks are references only.
-CV-only is fixed-parameter ordinaryCV,no full-dataset tuning before score reporting. Split+CV uses training-only tuning;its bestCVF1 is a selection score,not an independent test result.
-Threshold0.5 and preprocessing are predefined. No additional scaling introduced;the seven input representation matches the controlled prior experiments.
-The seven-feature fixed models use200trees for bothRF/XGBoost. Prior focused XGBoost comparisons used100in some experiments;do not confuse those configurations.
-Checkpoints protect completed experiments and CV-only folds. Interrupted grid searches restart that search. Full original grids can be slow;keep runtime expectations separate from16result rows.
-Scores from reused historical partitions are exploratory. OrdinaryCV pooled scores and different holdout ratios are not interchangeable evidence that one data split is inherently best. New independent validation remains needed.
-Accounting availability,exact donor feature definition,and correct transformation are separate checks. This experiment does not make the seven automatically available or model-ready for allSMEs.
-[Leakage guidance](https://imbalanced-learn.org/stable/common_pitfalls.html) · [GridSearchCV](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html)
''')
# Installation is its own final metadata-labelled code cell prepended after setup heading
# to preserve source master cell indices used by verification. Execute it manually first.
install={'cell_type':'code','metadata':{'install_first':True},'source':['%pip install -q scikit-learn==1.9.0 imbalanced-learn==0.14.2 xgboost==2.0.3 openpyxl matplotlib pandas joblib\n'],'execution_count':None,'outputs':[],'id':'seven-install'}
# Put install at index2 and move heading into previous markdown while keeping actual builder/tests mapped below.
nb['metadata']['colab']={'name':'SHIELD_Seven_Features_RF_XGBoost_Experiments.ipynb'}
for i,c in enumerate(nb['cells']):
 c['id']=f'seven-experiments-{i:02d}'
 if c['cell_type']=='code':c['execution_count']=None;c['outputs']=[]
# Install command at top of setup cell works in Colab; tests strip magic line before execution.
nb['cells'][3]['source']=install['source']+['\n']+nb['cells'][3]['source']
path=HERE/'SHIELD_Seven_Features_RF_XGBoost_Experiments.ipynb'
path.write_text(json.dumps(nb,indent=1),encoding='utf-8')
print(path)
