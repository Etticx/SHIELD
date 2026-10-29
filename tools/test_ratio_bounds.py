"""Test candidate raw min/max PAIRS against conditional accounting identities.

Passing is consistency, not recovery of the original preprocessing. No model or
source data is modified. Retained earnings/assets has no independent identity
among these seven features, so its bounds cannot be assessed by this test.
"""
import argparse
import csv
import json
import math
from pathlib import Path

FEATURES = [
    "Net Income to Stockholder's Equity", "Net Income to Total Assets",
    "Retained Earnings to Total Assets", "Debt ratio %", "Net worth/Assets",
    "Equity to Liability", "Liability to Equity",
]
# Multiplication avoids division by zero. Several checks are algebraically
# related, so five matches are not five independent pieces of evidence.
RULES = [
    ('balance', 'Liabilities/assets + Equity/assets = 1', [3,4], lambda v:(v[3]+v[4],1.0)),
    ('reciprocal', '(Equity/liabilities) * (Liabilities/equity) = 1', [5,6], lambda v:(v[5]*v[6],1.0)),
    ('equity', '(Equity/liabilities) * (Liabilities/assets) = Equity/assets', [5,3,4], lambda v:(v[5]*v[3],v[4])),
    ('liabilities', '(Liabilities/equity) * (Equity/assets) = Liabilities/assets', [6,4,3], lambda v:(v[6]*v[4],v[3])),
    ('income', '(Net income/equity) * (Equity/assets) = Net income/assets', [0,4,1], lambda v:(v[0]*v[4],v[1])),
]

def default_bounds():
    return {name:[0.0,1.0] for name in FEATURES}

def validate_bounds(bounds):
    if set(bounds)!=set(FEATURES):
        raise ValueError('Bounds JSON must contain exactly the seven feature names.')
    for name,pair in bounds.items():
        if not isinstance(pair,(list,tuple)) or len(pair)!=2:
            raise ValueError(f'{name}: provide [raw_min, raw_max] together.')
        if any(isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) for n in pair) or pair[1]<=pair[0]:
            raise ValueError(f'{name}: bounds must be finite numbers with raw_max > raw_min.')

def check_row(row,bounds,atol,rtol):
    raw=[]
    for name in FEATURES:
        value=row.get(name)
        lo,hi=bounds[name]
        raw.append(None if value is None or not math.isfinite(value) else value*(hi-lo)+lo)
    results=[]
    for key,label,needed,formula in RULES:
        result={'check':key,'identity':label,'status':'skipped','lhs':None,'rhs':None,'absolute_error':None}
        if all(raw[i] is not None and math.isfinite(raw[i]) for i in needed):
            lhs,rhs=formula(raw)
            if math.isfinite(lhs) and math.isfinite(rhs):
                result.update(lhs=lhs,rhs=rhs,absolute_error=abs(lhs-rhs),status='match' if math.isclose(lhs,rhs,abs_tol=atol,rel_tol=rtol) else 'mismatch')
        results.append(result)
    return results

def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=root/'data'/'preprocessed_dataset.csv')
    parser.add_argument('--bounds',type=Path,help='Optional JSON with one [raw_min, raw_max] pair per feature. Default: [0,1] for all.')
    parser.add_argument('--output',type=Path,default=root/'reports'/'ratio_bounds_hypothesis')
    parser.add_argument('--atol',type=float,default=1e-6)
    parser.add_argument('--rtol',type=float,default=1e-5)
    args=parser.parse_args()
    if any(not math.isfinite(x) or x<0 for x in [args.atol,args.rtol]):parser.error('Tolerances must be finite and nonnegative.')
    bounds=json.loads(args.bounds.read_text(encoding='utf-8-sig')) if args.bounds else default_bounds()
    validate_bounds(bounds)
    args.output.mkdir(parents=True,exist_ok=True)
    counts={k:{'match':0,'mismatch':0,'skipped':0,'max_absolute_error':0.0} for k,*_ in RULES}
    all_match=0;row_count=0
    ranges={n:[] for n in FEATURES}
    with args.input.open(newline='',encoding='utf-8-sig') as source, (args.output/'row_checks.csv').open('w',newline='',encoding='utf-8') as destination:
        reader=csv.DictReader(source)
        columns={name.strip():name for name in reader.fieldnames or []}
        if any(n not in columns for n in FEATURES):raise ValueError('CSV is missing required feature columns.')
        writer=csv.DictWriter(destination,fieldnames=['data_row','check','identity','status','lhs','rhs','absolute_error']);writer.writeheader()
        for row_count,original in enumerate(reader,1):
            row={}
            for name in FEATURES:
                try:value=float(original[columns[name]])
                except (ValueError,TypeError):value=float('nan')
                row[name]=value if math.isfinite(value) else None
                if row[name] is not None:ranges[name].append(value)
            results=check_row(row,bounds,args.atol,args.rtol)
            all_match+=all(r['status']=='match' for r in results)
            for result in results:
                stat=counts[result['check']];stat[result['status']]+=1
                if result['absolute_error'] is not None:stat['max_absolute_error']=max(stat['max_absolute_error'],result['absolute_error'])
                writer.writerow({'data_row':row_count,**result})
    any_failure=any(s['mismatch'] for s in counts.values())
    verdict='INCONSISTENT_WITH_IDENTITIES_UNDER_MATCHING_DEFINITIONS' if any_failure else 'CONSISTENT_NOT_VERIFIED' if all_match else 'INSUFFICIENT_COMPARABLE_DATA'
    report={'input':str(args.input.resolve()),'rows':row_count,'candidate_raw_bounds':bounds,'atol':args.atol,'rtol':args.rtol,'checks':counts,'rows_matching_all_checks':all_match,'verdict':verdict,
        'unconstrained_feature':FEATURES[2],
        'limits':['Checks assume identical entity, reporting period, numerator and denominator definitions.','Mismatch does not prove normalisation or identify which particular bound is incorrect.','Matching all checks does not establish unique or original bounds.','Retained earnings/assets has no independent identity among these seven features.','Several checks are algebraically dependent.','No original raw values or original min/max are recovered by this script.'],
        'stored_ranges':{n:{'min':min(v) if v else None,'max':max(v) if v else None} for n,v in ranges.items()}}
    (args.output/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    (args.output/'candidate_bounds.json').write_text(json.dumps(bounds,indent=2),encoding='utf-8')
    lines=[f'Rows checked: {row_count}',f'Candidate: {"[0,1] raw bounds for every feature" if not args.bounds else args.bounds}',f'Tolerance: absolute {args.atol}; relative {args.rtol}']
    for key,label,*_ in RULES:
        stat=counts[key];lines.append(f'{label}: {stat["match"]} match; {stat["mismatch"]} mismatch; {stat["skipped"]} skipped')
    lines += [f'Rows matching all checks: {all_match}',f'Verdict: {verdict}',*report['limits']]
    text='\n'.join(lines)+'\n';(args.output/'RESULTS.txt').write_text(text,encoding='utf-8');print(text)

if __name__=='__main__':main()
