"""Exhaust a finite candidate-bound grid against one necessary joint identity.

Both raw bounds vary jointly for each of Equity/Liability and Liability/Equity.
If no candidate satisfies even one row, no complete seven-feature assignment
on this grid can satisfy all accounting checks. This is conditional on matching
ratio definitions. It is not an attempt to identify a unique original scaler.
"""
import argparse
import csv
import json
import time
from pathlib import Path
import numpy as np


def make_pairs(divisions, lower=0.0, upper=1.0):
    if isinstance(divisions,bool) or not isinstance(divisions,int) or divisions<1:
        raise ValueError('divisions must be a positive integer')
    if not np.isfinite(lower) or not np.isfinite(upper) or upper<=lower:
        raise ValueError("Need finite lower < upper")
    grid=np.linspace(lower,upper,divisions+1)
    low,high=np.triu_indices(divisions+1,k=1)
    return np.column_stack((grid[low],grid[high]))


def search_reciprocal(x,y,pairs,atol,block_size=256):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if len(x)!=len(y) or not len(x) or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError('Need matched, nonempty finite vectors.')
    if not np.isfinite(atol) or atol<0:raise ValueError('Invalid tolerance')
    count=len(pairs);survivors=[];best_error=float('inf');best_pair=None
    for start in range(0,count,block_size):
        batch=pairs[start:start+block_size]
        left=batch[:,0]+(batch[:,1]-batch[:,0])*x[0]
        right=pairs[:,0]+(pairs[:,1]-pairs[:,0])*y[0]
        errors=np.abs(left[:,None]*right[None,:]-1.)
        idx=np.unravel_index(np.argmin(errors),errors.shape)
        if float(errors[idx])<best_error:
            best_error=float(errors[idx]);best_pair=(start+int(idx[0]),int(idx[1]))
        a,b=np.nonzero(errors<=atol)
        if len(a):
            a=a+start
            # Only surviving candidates need subsequent rows. This early rejection
            # is exactly equivalent to checking every row for every combination.
            for i in range(1,len(x)):
                left=pairs[a,0]+(pairs[a,1]-pairs[a,0])*x[i]
                right=pairs[b,0]+(pairs[b,1]-pairs[b,0])*y[i]
                keep=np.abs(left*right-1.)<=atol
                a,b=a[keep],b[keep]
                if not len(a):break
            survivors.extend(zip(a.tolist(),b.tolist()))
    return {'tested_combinations':count*count,'survivors':survivors,
            'smallest_first_row_error':best_error,'closest_first_row_pair_indices':best_pair}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    root=Path(__file__).resolve().parents[1]
    parser.add_argument('--divisions',type=int,default=100,help='Number of intervals; step=(upper-lower)/divisions')
    parser.add_argument('--lower',type=float,default=0.0)
    parser.add_argument('--upper',type=float,default=1.0)
    parser.add_argument('--atol',type=float,default=1e-5,help='Absolute error on product=1')
    parser.add_argument('--input',type=Path,default=root/'data'/'preprocessed_dataset.csv')
    parser.add_argument('--output',type=Path,default=root/'reports'/'ratio_bounds_grid_search')
    args=parser.parse_args();began=time.perf_counter()
    with args.input.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);columns={k.strip():k for k in reader.fieldnames}
        names=['Equity to Liability','Liability to Equity'];values=[]
        for line,row in enumerate(reader,2):
            try:pair=[float(row[columns[name]]) for name in names]
            except (KeyError,ValueError,TypeError) as exc:raise ValueError(f'Invalid selected data at CSV line {line}') from exc
            if not all(np.isfinite(pair)):raise ValueError(f'Nonfinite data at line {line}')
            values.append(pair)
    array=np.asarray(values);pairs=make_pairs(args.divisions,args.lower,args.upper)
    result=search_reciprocal(array[:,0],array[:,1],pairs,args.atol)
    candidate_examples=[]
    for a,b in result['survivors'][:20]:candidate_examples.append({names[0]:pairs[a].tolist(),names[1]:pairs[b].tolist()})
    a,b=result.pop('closest_first_row_pair_indices')
    result['surviving_combinations']=len(result.pop('survivors'))
    closest={names[0]:pairs[a].tolist(),names[1]:pairs[b].tolist()}
    l=pairs[a,0]+np.diff(pairs[a])[0]*array[:,0]
    r=pairs[b,0]+np.diff(pairs[b])[0]*array[:,1]
    errors=np.abs(l*r-1)
    result.update(input=str(args.input),rows=len(array),raw_bound_search_interval=[args.lower,args.upper],grid_step=(args.upper-args.lower)/args.divisions,
                  bounds_pairs_per_feature=len(pairs),tolerance=args.atol,
                  candidate_examples=candidate_examples,closest_on_first_row_only=closest,
                  closest_example_all_row_error={'min':float(errors.min()),'max':float(errors.max()),'mean':float(errors.mean()),'mismatch_rows':int(np.sum(errors>args.atol))},
                  elapsed_seconds=time.perf_counter()-began,
                  conclusion='No complete seven-feature solution on this grid can satisfy all checks under identical accounting definitions.' if not candidate_examples else 'Candidate reciprocal pairs exist; additional identities and independent validation are still required.',
                  limits=['This finite grid is not every real number in the chosen interval.',f'Raw bounds outside [{args.lower},{args.upper}] are excluded.','Original bounds are not recovered.','No inference about the original data transformation follows if ratio definitions differ.','Retained earnings/assets cannot be identified from these relationships.'])
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=[f'Raw-bound interval: [{args.lower:g}, {args.upper:g}]',f'Grid step: {(args.upper-args.lower)/args.divisions:g}',f'Raw min/max pairs per feature: {len(pairs):,}',f'Joint combinations checked: {result["tested_combinations"]:,}',f'Dataset rows available for validation: {len(array):,}',f'Absolute tolerance: {args.atol}',f'Surviving combinations: {result["surviving_combinations"]:,}',f'Smallest product error even on first row: {result["smallest_first_row_error"]:.10g}',f'Runtime: {result["elapsed_seconds"]:.3f} seconds',result['conclusion'],*result['limits']]
    text='\n'.join(lines)+'\n';(args.output/'RESULTS.txt').write_text(text,encoding='utf-8');print(text)

if __name__=='__main__':main()
