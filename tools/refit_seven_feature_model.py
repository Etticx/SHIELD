"""Refit the seven-feature RF (SMOTE 0.5, 80:20 seed 42) under the backend's pinned scikit-learn 1.6.1.
Usage: python tools/refit_seven_feature_model.py model/SHIELD_RF_7Features_SMOTE050_8020_CV5_sk161.joblib"""
import sys, joblib, pandas as pd, numpy as np
from sklearn.model_selection import train_test_split
from imblearn.pipeline import Pipeline; from imblearn.over_sampling import SMOTE; from sklearn.ensemble import RandomForestClassifier
old=joblib.load('model/SHIELD_RF_7Features_SMOTE050_8020_CV5.joblib'); F=list(old.feature_names_in_)
df=pd.read_csv('data/preprocessed_dataset.csv',encoding='utf-8-sig',float_precision='round_trip'); df.columns=[c.strip() for c in df.columns]
T=[c for c in df.columns if 'Bankrupt' in c][0]
X=df.drop(columns=[T]); y=df[T].astype(int)
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
Xtr,Xte=Xtr[F],Xte[F]; print('rows',len(df),'train',ytr.value_counts().to_dict())
new=Pipeline([('smote',SMOTE(sampling_strategy=0.5,random_state=42,k_neighbors=5)),('model',RandomForestClassifier(**old.steps[1][1].get_params()))]).fit(Xtr,ytr)
print('smote',dict(new.steps[0][1].sampling_strategy_),'orig',dict(old.steps[0][1].sampling_strategy_))
po=old.predict_proba(Xte)[:,1]; pn=new.predict_proba(Xte)[:,1]
print('max abs diff',np.abs(po-pn).max(),'agree@0.5',((po>=.5)==(pn>=.5)).mean())
if len(sys.argv)>1: joblib.dump(new,sys.argv[1]); print('saved')
