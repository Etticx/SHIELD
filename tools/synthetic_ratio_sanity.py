"""Synthetic sanity screening, not accuracy evaluation or scaler recovery.

No dataset/test rows are read. All amounts are generated, A=L+E is enforced,
and the application calculator is used. Assumed raw min/max [0,1] makes the
transform an identity; out-of-range ratios are preserved, not clipped.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import sys
import warnings
import numpy as np
import pandas as pd
import joblib
import sklearn

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from experimental_accounting import calculate_features, FEATURES
AMOUNTS=['net_income','total_assets','total_liabilities','equity','retained_earnings']
VARIANTS=['base','profit_up','debt_down','retained_up','combined_improvement']


def generate_cases(base_count=1000,seed=42):
    rng=random.Random(seed);cases=[]
    for i in range(base_count):
        profile='strong' if i%10<4 else 'weak' if i%10<8 else 'mixed'
        assets=10**rng.uniform(5,7)
        if profile=='strong':
            debt=rng.uniform(.05,.30);margin=rng.uniform(.10,.25);retained=rng.uniform(.10,.40)*assets
        elif profile=='weak':
            debt=rng.uniform(.85,1.50)
            if abs(1-debt)<.01:debt=1.02
            margin=rng.uniform(-.20,-.05)
            retained=min(-.05*assets,(1-debt)*assets-.05*assets)-rng.uniform(0,.3)*assets
        else:
            debt=rng.uniform(.30,.85);margin=rng.uniform(-.08,.12);retained=rng.uniform(-.10,.10)*assets
        base=dict(net_income=margin*assets,total_assets=assets,total_liabilities=debt*assets,equity=(1-debt)*assets,retained_earnings=retained)
        for variant in VARIANTS:
            values=base.copy()
            if variant in ['profit_up','combined_improvement']:values['net_income']+=.05*assets
            if variant in ['debt_down','combined_improvement']:
                new_debt=max(.01,debt-.15)
                if abs(1-new_debt)<.01:new_debt=.98
                values['total_liabilities']=new_debt*assets;values['equity']=(1-new_debt)*assets
            if variant in ['retained_up','combined_improvement']:
                values['retained_earnings']=min(values['equity']-.01*assets,retained+.10*assets)
            cases.append(dict(case_id=f'B{i+1:04d}-{variant}',base_id=f'B{i+1:04d}',profile=profile,variant=variant,**values))
    return cases


def verdict(variant,profile,score,base_score,tolerance=.002):
    if variant=='base':
        if profile=='strong':
            return ('consistent' if score<.30 else 'counterintuitive', 'Constructed profitable, low-leverage profile: expected the screen Low Risk band (<30%). This is a heuristic, not a known outcome.')
        if profile=='weak':
            return ('consistent' if score>=.60 else 'counterintuitive', 'Constructed loss-making, high-leverage profile: expected screen High/Critical Risk (>=60%). This is a heuristic, not a known outcome.')
        return 'inconclusive','Mixed financial indicators: no defensible absolute expected risk band from these five amounts alone.'
    expectation={
        'profit_up':'Profit is higher by 5% of assets; other amounts unchanged. Expected score not to rise.',
        'debt_down':'Liabilities are lower and equity higher at fixed assets and profit. Expected score not to rise; ROE and negative-equity effects may complicate interpretation.',
        'retained_up':'Retained earnings are higher with equity fixed, changing equity composition. Expected score not to rise; this is not a simulated accounting transaction.',
        'combined_improvement':'Higher profit, lower liabilities, higher equity and higher retained earnings. Expected score not to rise; some raw ratios may cross zero or extrapolate.'}[variant]
    delta=score-base_score
    if abs(delta)<=tolerance:return 'unchanged',expectation+' Change within 0.2 percentage points: inconclusive, not a confirmed improvement.'
    return ('consistent' if delta<0 else 'counterintuitive'),expectation


def feature_frame(cases,names):
    rows=[calculate_features(**{k:case[k] for k in AMOUNTS}) for case in cases]
    if len(names)!=7 or {str(n).strip() for n in names}!=set(FEATURES):raise ValueError('Unexpected model features')
    return pd.DataFrame([[row[str(n).strip()] for n in names] for row in rows],columns=names)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-count',type=int,default=1000)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--output',type=Path,default=ROOT/'reports'/'synthetic_accounting_sanity')
    args=parser.parse_args()
    if args.base_count<1:parser.error('base-count must be positive')
    path=ROOT/'model'/'SHIELD_RF_7Features_SMOTE050_8020_CV5.joblib'
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always');model=joblib.load(path)
    cases=generate_cases(args.base_count,args.seed);frame=feature_frame(cases,list(model.feature_names_in_))
    scores=model.predict_proba(frame)[:,list(model.classes_).index(1)]
    if not np.all(np.isfinite(scores)) or np.any((scores<0)|(scores>1)):raise ValueError('Invalid model scores')
    baseline={case['base_id']:float(score) for case,score in zip(cases,scores) if case['variant']=='base'}
    records=[]
    for i,(case,score) in enumerate(zip(cases,scores)):
        base_score=baseline[case['base_id']];status,reason=verdict(case['variant'],case['profile'],float(score),base_score)
        ratios={str(name).strip():float(frame.iloc[i,j]) for j,name in enumerate(frame.columns)}
        band='Critical Risk' if score>=.8 else 'High Risk' if score>=.6 else 'Moderate Risk' if score>=.3 else 'Low Risk'
        records.append(dict(**case,score_pct=round(float(score)*100,6),base_score_pct=round(base_score*100,6),change_pp=round((float(score)-base_score)*100,6),screen_band=band,binary_prediction='Bankrupt' if score>=.5 else 'Not Bankrupt',verdict=status,reason=reason,outside_dataset_unit_range=sum(v<0 or v>1 for v in ratios.values()),**ratios))
    by_group={}
    for variant in VARIANTS:
        groups=['strong','weak','mixed'] if variant=='base' else ['all']
        for profile in groups:
            rows=[r for r in records if r['variant']==variant and (profile=='all' or r['profile']==profile)]
            if not rows:continue
            by_group[f'{variant}/{profile}']={'count':len(rows),'verdicts':dict(Counter(r['verdict'] for r in rows)),'screen_bands':dict(Counter(r['screen_band'] for r in rows)),'mean_score_pct':float(np.mean([r['score_pct'] for r in rows])),'min_score_pct':min(r['score_pct'] for r in rows),'max_score_pct':max(r['score_pct'] for r in rows),'mean_change_pp':float(np.mean([r['change_pp'] for r in rows]))}
    summary={'scenario_count':len(records),'base_profiles':args.base_count,'seed':args.seed,'currency':'RM (synthetic)','raw_min':0,'raw_max':1,'transformation':'(raw-0)/(1-0) = raw; no clipping','model_file':path.name,'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sklearn_runtime':sklearn.__version__,'python':platform.python_version(),'load_warnings':sorted(set(str(w.message) for w in captured)),'thresholds':{'binary_bankrupt':.5,'low_below':.3,'high_at':.6,'critical_at':.8},'records_outside_unit_range':sum(r['outside_dataset_unit_range']>0 for r in records),'group_results':by_group,'limitations':['Synthetic scenarios have no bankruptcy ground-truth labels. These are heuristic consistency verdicts, not accuracy, precision or recall.','No dataset/test rows used. No actual company identities or financial statements used.','A=L+E in every scenario. Changes are matched static scenarios, not full financial-statement transaction simulations.','The model was trained on encoded feature values. This test assumes identity conversion to inspect behavior; it cannot recover original scaling.','Ratios outside [0,1] are preserved and represent extrapolation beyond the seven columns observed unit ranges.','Losses divided by negative equity can yield positive ROE; nonlinear or unchanged predictions are not automatically modelling errors.','Retained earnings changes at fixed equity imply a different equity composition.','The supplied artifact was saved using a different sklearn version; warnings retained.','Current website input form remains seven direct values; this offline audit explicitly uses the older five-amount calculator path.']}
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'all_5000_cases.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    (args.output/'all_cases.json').write_text(json.dumps(records,ensure_ascii=True,allow_nan=False),encoding='utf-8')
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    lines=['SYNTHETIC ACCOUNTING SANITY TEST — 29 October 2026',f'Scenarios: {len(records):,}; base profiles: {args.base_count:,}',f'Assumed raw bounds: min=0 max=1. Formula leaves raw ratios unchanged.']
    for name,result in by_group.items():lines.append(f'{name}: {json.dumps(result)}')
    lines+=summary['limitations'];(args.output/'RESULTS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
