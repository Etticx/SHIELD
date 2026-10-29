"""Simulation of approximate encodings; no recovered scaler or real-SME accuracy."""
from pathlib import Path
import json
import warnings
import hashlib
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer
from sklearn.model_selection import train_test_split
from synthetic_ratio_sanity import generate_cases, feature_frame, verdict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'approximate_mapping_experiment'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model_path = ROOT/'model/SHIELD_RF_7Features_SMOTE050_8020_CV5.joblib'
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model = joblib.load(model_path)
    names = list(model.feature_names_in_)
    data = pd.read_csv(ROOT/'data/preprocessed_dataset.csv')
    data.columns = data.columns.str.strip()
    train, _ = train_test_split(data, test_size=.2, stratify=data.Bankrupt, random_state=42)
    target = train[[str(n).strip() for n in names]].to_numpy()
    target_q = QuantileTransformer(n_quantiles=1000, output_distribution='uniform', subsample=None, random_state=42).fit(target)
    cases = generate_cases(1000, 42)
    raw = feature_frame(cases, names).to_numpy()
    reference_cases = [c for c in generate_cases(4000, 123) if c['variant']=='base']
    groups = {'mixed_reference': reference_cases,
              'strong_reference': [c for c in reference_cases if c['profile']=='strong'],
              'weak_reference': [c for c in reference_cases if c['profile']=='weak']}
    mapped = {'identity': raw}
    metadata = {}
    for group, ref in groups.items():
        source = feature_frame(ref, names).to_numpy()
        mm = MinMaxScaler().fit(source)
        qt = QuantileTransformer(n_quantiles=min(1000,len(ref)), output_distribution='uniform', subsample=None, random_state=42).fit(source)
        mapped[group+'/minmax'] = mm.transform(raw)
        mapped[group+'/quantile'] = target_q.inverse_transform(qt.transform(raw))
        metadata[group] = {'count':len(ref), 'raw_min':mm.data_min_.tolist(), 'raw_max':mm.data_max_.tolist()}
        joblib.dump({'minmax':mm,'source_quantiles':qt,'target_quantiles':target_q,'features':names}, OUT/(group+'.joblib'))
    records = []; summaries = []; scores = {}
    for method, values in mapped.items():
        assert np.isfinite(values).all()
        score = model.predict_proba(pd.DataFrame(values,columns=names))[:,list(model.classes_).index(1)]
        scores[method] = score
        base = {c['base_id']:float(s) for c,s in zip(cases,score) if c['variant']=='base'}
        method_records = []
        for i,(case,s) in enumerate(zip(cases,score)):
            status,reason = verdict(case['variant'],case['profile'],float(s),base[case['base_id']])
            row = dict(method=method,**case,score_pct=float(s)*100,verdict=status,reason=reason,
                       outside_unit_range=bool(((values[i]<0)|(values[i]>1)).any()))
            row.update({'mapped_'+str(n).strip():float(v) for n,v in zip(names,values[i])})
            method_records.append(row)
        records.extend(method_records)
        for profile in ['all','strong','weak','mixed']:
            subset=[r for r in method_records if r['variant']=='base' and (profile=='all' or r['profile']==profile)]
            summaries.append(dict(method=method,group='base/'+profile,count=len(subset),mean_score_pct=np.mean([r['score_pct'] for r in subset]),low_band=sum(r['score_pct']<30 for r in subset),flagged=sum(r['score_pct']>=50 for r in subset),high_or_critical=sum(r['score_pct']>=60 for r in subset),counterintuitive=sum(r['verdict']=='counterintuitive' for r in subset)))
        for variant in ['profit_up','debt_down','retained_up','combined_improvement']:
            subset=[r for r in method_records if r['variant']==variant]
            summaries.append(dict(method=method,group=variant,count=len(subset),consistent=sum(r['verdict']=='consistent' for r in subset),counterintuitive=sum(r['verdict']=='counterintuitive' for r in subset),unchanged=sum(r['verdict']=='unchanged' for r in subset)))
    sensitivity=[]
    for method in ['minmax','quantile']:
        a=scores['mixed_reference/'+method]
        for ref in ['strong_reference','weak_reference']:
            b=scores[ref+'/'+method]
            sensitivity.append(dict(method=method,alternative=ref,binary_flips=int(np.sum((a>=.5)!=(b>=.5))),mean_absolute_change_pp=float(np.mean(np.abs(a-b))*100),max_absolute_change_pp=float(np.max(np.abs(a-b))*100)))
    pd.DataFrame(records).to_csv(OUT/'all_35000_predictions.csv',index=False)
    pd.DataFrame(summaries).to_csv(OUT/'summary.csv',index=False)
    report={'target':'Existing dataset labelled Italian (Taiwanese-origin release)', 'target_reference_rows':len(train),'synthetic_evaluation_cases':len(cases),'synthetic_reference_seed':123,'evaluation_seed':42,'model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),'features':names,'reference_bounds':metadata,'sensitivity':sensitivity,'warnings':sorted(set(str(w.message) for w in caught)), 'limitations':['Raw references are SYNTHETIC, not real external financial statements. This is a simulation only.','No Polish data used. Existing dataset supplies target quantiles; original trained RF stays fixed.','Synthetic profiles have no bankruptcy outcomes: precision/recall/accuracy cannot be computed.','Minmax uses synthetic raw bounds with no clipping. Quantile mapping saturates outside source tails.','Marginal quantile matching does not recover joint feature relationships or original normalization.','Results are sensitive to arbitrary reference population and do not validate Malaysian SME use.','The source dataset partition used for target quantiles is deterministic; exact original artifact training membership is not verified.','Model version compatibility warnings are retained.']}
    (OUT/'metadata.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=['APPROXIMATE MAPPING SIMULATION — SHIELD','Target: existing seven-feature dataset and existing RF. Website unchanged.','Reference: independent synthetic accounting profiles, NOT real external data.','No accuracy / precision / recall: no true bankruptcy labels for synthetic cases.','',pd.DataFrame(summaries).to_string(index=False),'','REFERENCE SENSITIVITY',pd.DataFrame(sensitivity).to_string(index=False),'','LIMITATIONS',*report['limitations']]
    (OUT/'FINDINGS.txt').write_text('\n'.join(lines),encoding='utf-8')
    print(pd.DataFrame(summaries).to_string(index=False))
    print(json.dumps(sensitivity,indent=2))

if __name__=='__main__':
    main()
