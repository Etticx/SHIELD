"""Read-only audit of original Mendeley V2 CSVs. Candidate ratio mappings remain hypotheses."""
from pathlib import Path
import csv,json,hashlib,math,collections
import numpy as np
root=Path(__file__).resolve().parent
metadata=json.loads((root/'files_metadata.json').read_text(encoding='utf-8-sig'))
entries=[];arrays=[];groups=collections.defaultdict(lambda:{'bankrupt':0,'nonbankrupt':0});hashes=collections.Counter()
for entry in metadata:
    path=root/'original_csv'/entry['filename'];blob=path.read_bytes();sha=hashlib.sha256(blob).hexdigest()
    assert sha==entry['content_details']['sha256_hash'],path.name
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f,delimiter=';');header=next(reader);rows=list(reader)
    assert header[1:]==[f'V{i}' for i in range(1,64)]
    arr=np.array([[float(v.replace(',','.')) if v not in ('NA','','NaN') else np.nan for v in row[1:]] for row in rows])
    label='nonbankrupt' if path.name.startswith('nonbankrupt_') else 'bankrupt';pieces=path.stem.split('_');year=2000+int(pieces[2]);sector=pieces[1]
    groups[year][label]+=len(rows)
    for row in rows:hashes[tuple(row[1:])]+=1
    entries.append({'file':path.name,'sha256_verified':True,'rows':len(arr),'predictors':arr.shape[1],'label_from_filename':label,'evaluation_year':year,'sector':sector,'missing_cells':int(np.isnan(arr).sum()),'infinite_cells':int(np.isinf(arr).sum()),'rows_any_missing':int(np.isnan(arr).any(axis=1).sum()),'index_is_just_1_to_n':[row[0] for row in rows]==[str(i+1) for i in range(len(rows))]})
    arrays.append(arr)
all_data=np.vstack(arrays)
statistics={}
for j in range(63):
    data=all_data[:,j];finite=data[np.isfinite(data)]
    statistics[f'V{j+1}']={'missing':int(np.isnan(data).sum()),'min':float(finite.min()),'max':float(finite.max()),'median':float(np.median(finite)),'negative':int(np.sum(finite<0)),'above_one':int(np.sum(finite>1))}
# These equalities explore possible column mappings; they do not independently
# establish those mappings, accounting units or the original financial amounts.
checks={}
for block in range(3):
    offset=21*block
    for name,a,b,target in [('V2 ~= V1 * V13',offset,offset+12,offset+1),('V12 ~= V11 * V13',offset+10,offset+12,offset+11)]:
        lhs=all_data[:,a]*all_data[:,b];rhs=all_data[:,target];valid=np.isfinite(lhs)&np.isfinite(rhs)
        error=np.abs(lhs[valid]-rhs[valid]);tol=.02+.01*np.abs(rhs[valid])
        checks[f'block_{block+1}: {name}']={'valid':int(valid.sum()),'match_with_atol_0_02_rtol_0_01':int(np.sum(error<=tol)),'median_absolute_error':float(np.median(error))}
report={'source':'https://data.mendeley.com/datasets/j89csb932y/2','files':entries,'total_rows':len(all_data),'class_counts':dict(collections.Counter({label:sum(e['rows'] for e in entries if e['label_from_filename']==label) for label in ['bankrupt','nonbankrupt']})),'evaluation_year_counts':dict(groups),'total_missing_cells':int(np.isnan(all_data).sum()),'rows_any_missing':int(np.isnan(all_data).any(axis=1).sum()),'exact_duplicate_feature_vectors_beyond_first':sum(n-1 for n in hashes.values()),'all_63_columns_outside_unit_range':all(v['min']<0 or v['max']>1 for v in statistics.values()),'column_stats':statistics,'candidate_identity_checks_not_verified_mappings':checks}
(root/'audit_summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['files','column_stats']},indent=2))
print('First block selected column stats:',json.dumps({k:statistics[k] for k in ['V1','V2','V11','V12','V13']},indent=2))
print('First row:',all_data[0,:21].tolist())
