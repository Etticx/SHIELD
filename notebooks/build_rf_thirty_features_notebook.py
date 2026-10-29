"""Build the self-contained financial-statement30 versus historical20 Colab."""
import ast,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
nb=json.loads((HERE/'SHIELD_RF_Seven_vs_Twenty_Features.ipynb').read_text(encoding='utf-8'))
codes=[''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code']
research=json.loads((ROOT/'reports/sme_reporting_crosscheck/feature_crosscheck.json').read_text(encoding='utf-8'))
manifest=[r for r in research['rows'] if r['category']=='A']
financial=[r['feature'] for r in manifest]
assert len(financial)==30
old_source=codes[2]
parsed=ast.parse(old_source)
baseline=next(ast.literal_eval(node.value) for node in parsed.body if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='FEATURES')
union=list(dict.fromkeys(baseline+financial))
assert len(union)==43
begin=old_source.index('FEATURES=');end=old_source.index('def make_model(')
source=old_source[:begin]+f'''BASELINE_FEATURES={baseline!r}
STATEMENT_FEATURES={financial!r}
FEATURES={union!r}  # Union for input validation only; each model uses its own list.
STATEMENT_MANIFEST={manifest!r}

def scenarios():
    return {{'baseline_20':BASELINE_FEATURES.copy(),'financial_statement_30':STATEMENT_FEATURES.copy()}}

'''+old_source[end:]
load=codes[3]
load=load[:load.index('\nrank_table=')]
load=load.replace('all 20 financial features','all43 comparison features')
load=load.replace('Duplicate predictor rows','Duplicate predictor rows')
load=load.replace('shield-rf-seven-vs-twenty-v1','shield-rf-financial-statement30-v1')
load=load.replace('fixed historical20 versus predefined7; no IG reselection','fixed historical20 versus accounting-candidate30; no IG reselection')
old_manifest="manifest=[{'Scenario':name,'Features':len(cols),'Removed':'; '.join(c for c in FEATURES if c not in cols)} for name,cols in SCENARIOS.items()]"
new_manifest="manifest=[{'Scenario':name,'Features':len(cols),'Removed':'; '.join(c for c in BASELINE_FEATURES if c not in cols),'Added':'; '.join(c for c in cols if c not in BASELINE_FEATURES)} for name,cols in SCENARIOS.items()]"
assert old_manifest in load
load=load.replace(old_manifest,new_manifest)
load+='''\nfeature_evidence=pd.DataFrame([{'Feature':r['feature'],
    'In historical20':r['top20'],'Required accounting amounts':r['required_company_information'],
    'Candidate calculation':r['conceptual_calculation'],'Remaining definition checks':r['caution'],
    'Exact original-model scale verified':r['original_model_scale_verified']} for r in STATEMENT_MANIFEST])
feature_evidence.to_csv(OUT/'financial_statement_feature_manifest.csv',index=False)
display(feature_evidence)
print('Shared financial features:',len(set(BASELINE_FEATURES)&set(STATEMENT_FEATURES)))
print('No new IG selection. Thirty means30 dataset columns, not30 guaranteed reported ratios.')
'''
cv=codes[4]
test=codes[5].replace('SHIELD: no imputation; retrained reduced-input Random Forests.','SHIELD: fixed20 versus financial-statement-candidate30 Random Forests; no imputation.')
comparison=codes[6].replace('Seven versus twenty inputs: RF','Thirty versus twenty inputs: RF')
comparison=comparison.replace("cols=['Scenario','Features','Removed',","cols=['Scenario','Features','Removed','Added',")
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s,definitions=False):cells.append(dict(cell_type='code',metadata={'definitions':True} if definitions else {},source=s.splitlines(True),execution_count=None,outputs=[]))
md('''# SHIELD — RF with30 financial-statement candidates versus20 historical inputs

**Question:** does the broader pool of30 dataset features potentially calculable from ordinary SME annual-account amounts preserve more predictive information than our seven-input trial, compared with the matched20-input baseline?

One self-contained notebook; two models per run. **Stratified80:20,10-fold ordinary training CV,seed42,threshold0.5.** Start with SMOTE0.25, change it to1.0 for the second run. Both settings save separately.

**No imputation, new IG selection, hyperparameter search or threshold tuning.** All30 candidates are used in the30-input arm. The20-input arm uses the historical predefined list. No prototype/model deployment changes.

## What 'financial-statement candidates' means
All30 names are actual columns in the local dataset. We identified their underlying accounting amounts in reporting structures/examples. This does **not** mean every SME must print each ratio, every company has all required breakdowns, or all exact donor formulas have been verified. The target population for the availability research is incorporated SMEs supplying complete annual accounts and relevant notes.

The calculations in the evidence manifest are conceptual, not implemented here. This notebook selects existing dataset columns. It does not accept raw financial statements, reconstruct raw ratios, invent unavailable company amounts, or establish the original donor's raw-to-model transformation. That transformation, exact definitions and real SME availability remain deployment gates.

Some columns may overlap (e.g. current-liability ratios); do not assume30 independent signals. Potential duplicates are deliberately retained for this initial fixed-pool experiment and labelled in the manifest.
''')
md('## 1. Install dependencies\nIf Colab imported a different modelling version before installation, restart the runtime after installing and continue from settings.')
code(codes[0])
md('## 2. Settings\nChange only SMOTE_RATIO to1.0 for the second experiment, then rerun from this cell onward. Use original unresampled data. Update Drive paths if needed.')
code(codes[1].replace("'rf_seven_vs_twenty'","'rf_financial_statement30_vs_twenty'"))
md('''## 3. Fixed candidates and identical model settings
RF:200trees,max_depth10,min_samples_split2,min_samples_leaf1,max_features sqrt,no class weights. SMOTE:k_neighbors5,random_state42. No new scaling, matching the controlled historical RF+SMOTE setup. With a different number of input columns, sqrt naturally changes the absolute split-feature count.

SMOTE is fitted **only on each training fold**; validation/test rows retain their original class distribution. The test set has been inspected in earlier experiments, so comparisons are exploratory. The accounting shortlist was not selected by optimising this test set, but it intersects the historical IG selection and inherits its limitations.

The baseline is refitted in the same environment; use its fresh results for comparison. Same RF parameters are retained for both ratios rather than reproducing differently tuned historical winners.
''')
code(source,True)
md('## 4. Validate source and create one matched partition\nValidate the43-column union of both feature sets:20+30-7shared. The models use20 and30 respectively. Company and Bankrupt are excluded. No silent row dropping, missing-value filling or label changes. Export the accounting-candidate evidence manifest, exact parameters, data fingerprint, package versions and fold membership.')
code(load)
md('## 5. Ordinary10-fold training CV\nTwo feature sets ×10 folds; each company has one out-of-fold prediction. These are fixed-parameter evaluations. Mean fold F1 and pooled OOF F1 differ. Completed fold predictions are checked/reused for identical settings; changing ratio produces a separate run folder.')
code(cv)
md('## 6. Final training refits and test reports\nTwo more fits: one per feature set on the complete80% training portion. Total22fits per SMOTE ratio. No test resampling. Existing20/7production pipelines are not changed, and no replacement production model is exported.')
code(test)
md('## 7. Baseline comparison\nRemoved/Added are relative to the historical20 inputs. Changes in percentage metrics are percentage points. Compare precision,recall,F1,missed bankruptcies and false alarms, not accuracy alone. No automatic winner is chosen from test results.')
code(comparison)
md('''## Reading results
- First compare30 with20 at the same SMOTE ratio. Then repeat with1.0. Do not assume more inputs necessarily improve precision or recall.
- Use prior seven-input results as context; this notebook trains the30 and20 arms only. Compare prior runs cautiously if package versions, data precision or settings differ.
- If the30-input model is promising, the next optional comparison is training-fold IG within the eligible pool. IG is not futile; it is simply omitted from this initial all30 comparison.
- The hypothetical30 ratios may be derived from fewer underlying financial amounts. A practical form would collect those amounts after definition/scale verification rather than assume users know every ratio.
- One of44 bankrupt test companies corresponds to2.27percentage points of recall. Independent validation is needed after selecting the final model and input policy.

## Evidence sources
[SSM MBRS FAQ v2.8,PDFp12](https://www.ssm.com.my/bm/Pages/Register_Business_Company_LLP/Company/document/FAQ-MBRS_ISSB.pdf#page=12): reporting components, not a guarantee of each ratio.
[Malaysian MPERS illustrative accounts,PDFpp21-25](https://nk.com.my/cdn/pdf/MPERS_Illustrative_Financial_Statements.pdf#page=21): example amounts and notes, not proof every business supplies them.
[IFRS illustrative examples](https://www.ifrs.org/issued-standards/ifrs-taxonomy/ifrs-taxonomy-illustrative-examples/): supplementary accounting-format evidence; user's supplied iXBRL example was inspected in research.
[UCI dataset](https://archive.ics.uci.edu/dataset/572/taiwanese+bankruptcy+prediction): historical financial-ratio benchmark; local filename alone does not establish country provenance.

The manifest distinguishes accounting feasibility from exact historical donor-field equivalence. No new accounting-formula implementation is included.
''')
for i,c in enumerate(cells):c['id']=f'shield-thirty-{i:02d}'
path=HERE/'SHIELD_RF_Financial_Statement_30_vs_Twenty.ipynb'
output=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python3',language='python',name='python3'),language_info=dict(name='python'),colab=dict(name=path.name)),nbformat=4,nbformat_minor=5)
path.write_text(json.dumps(output,indent=1),encoding='utf-8')
print(path)
