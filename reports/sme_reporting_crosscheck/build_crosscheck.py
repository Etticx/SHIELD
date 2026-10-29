from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
import pandas as pd
base=Path('reports/sme_reporting_crosscheck');base.mkdir(exist_ok=True)
raw_path=Path('data/bankruptcy_italian_companies_2023.xlsx')
df=pd.read_excel(raw_path);df.columns=df.columns.str.strip()
features=[c for c in df if c not in ['Company','Bankrupt']]
assert len(features)==95
# Each row records an accounting-feasibility judgement, not a verified donor transformation.
items=[
('C','Adjusted recurring earnings; interest; tax; depreciation/amortisation; opening/closing assets','Specialised ROA(C) definition','Current/previous assets','Current vendor formula is not proof of historical donor mapping.'),
('C','Continuing-operation profit; interest/finance costs; applicable tax; opening/closing assets','Specialised ROA(A) definition','Current/previous assets','Tax adjustment and financial-statement scope need confirmation.'),
('C','Recurring profit; finance costs; tax; depreciation/amortisation; opening/closing assets','Specialised ROA(B) definition','Current/previous assets','Not interchangeable with ordinary net-income/assets.'),
('A','Revenue; cost of sales or gross profit','Gross profit / revenue','One annual period','Confirm gross-profit scope.'),
('C','Revenue; gross profit; any adjustments to realised sales/profit','Adjusted realised gross margin','One annual period','Realised versus ordinary gross profit is unresolved.'),
('A','Operating profit; revenue','Operating profit / revenue','One annual period','Use operating profit, not profit after tax; consistent expense classification.'),
('A','Profit before tax; revenue','Profit before tax / revenue','One annual period','Label appears to mean pretax margin, not bank interest rate.'),
('A','Profit after tax; revenue','Profit after tax / revenue','One annual period','Label appears to mean after-tax margin, not bank interest rate.'),
('B','Non-operating income and expense breakdown; revenue','Net non-operating result / revenue, subject to definition','One annual period','Finance and disposal classification may need notes.'),
('C','Recurring after-tax income adjustments; revenue','Recurring after-tax margin candidate','One annual period','Not a loan interest rate; recurring-profit definition unresolved.'),
('B','Operating expense breakdown; revenue','Eligible operating expenses / revenue','One annual period','Nature/function presentation and cost-of-sales exclusions need mapping.'),
('B','Research and development expense; revenue','R&D expense / revenue','One annual period','R&D is shown in IFRS example and KPMG note; not shown as separate line in every SME. No disclosure does not automatically mean zero.'),
('C','Matching operating cash-flow measure; denominator','Cash-flow rate requires donor definition','One annual period','Do not assume cash-flow rate equals CFO/revenue.'),
('B','Interest expense; eligible interest-bearing debt balances','Debt interest-cost rate candidate','Current and possibly opening debt','Interest expense is not necessarily all finance costs; average debt convention unresolved.'),
('B','Income-tax expense; appropriate pretax profit','Tax expense / pretax profit candidate','One annual period','Statutory, effective, current and deferred tax differ; confirm Tax rate A.'),
('C','Equity components; share counts/classes; treasury shares and adjustments','Book value per share B','Reporting date and share movements','Exact B convention and historical mapping unresolved.'),
('C','Equity components; share counts/classes; treasury shares and adjustments','Book value per share A','Reporting date and share movements','Exact A convention differs from B; Malaysia has no-par shares.'),
('C','Equity components; share counts/classes and adjustments','Book value per share C','Reporting date and share movements','Exact C convention unresolved.'),
('C','Four-quarter recurring earnings; share and ownership adjustments','Specialised four-quarter recurring EPS','Matching trailing four-quarter history','Annual accounts alone do not establish exact value. At an appropriate year-end matching annual recurring figures might suffice only if donor convention is verified.'),
('B','Matching cash-flow measure; appropriate share count','Cash flow / eligible shares','Annual flow and matching share convention','Ending shares may be disclosed; weighted-average shares are not automatically supplied.'),
('B','Revenue; appropriate share count','Revenue / eligible shares','Annual flow and matching share convention','Confirm ending, weighted-average and adjustment convention.'),
('B','Operating profit; appropriate share count','Operating profit / eligible shares','Annual flow and matching share convention','Share details required; not applicable to businesses without shares.'),
('B','Profit before tax; appropriate share count','Pretax profit / eligible shares','Annual flow and matching share convention','Share details required; not simply pretax profit divided by share capital.'),
('C','Comparable realised gross profit current/prior','Growth in realised gross profit','At least two comparable periods','Realised adjustment and growth formula unresolved.'),
('B','Operating profit current/prior','Growth in operating profit','Two comparable annual periods','Exact denominator/sign and period-length convention must be confirmed.'),
('B','Profit after tax current/prior','Growth in after-tax profit','Two comparable annual periods','Zero/negative prior profits require explicit convention.'),
('C','Matching regular earnings current/prior','Growth in regular earnings','Two comparable periods','Regular earnings definition unresolved.'),
('C','Matching recurring earnings current/prior','Growth in recurring earnings','Two comparable periods','Continuous/recurring adjustment unresolved.'),
('B','Total assets current/prior','Growth in total assets','Two comparable reporting dates','Comparative balances usually available after first year; verify restatements.'),
('B','Matching equity/net-worth balances current/prior','Growth in net worth','Two comparable reporting dates','Confirm net-worth definition, sign treatment and equity scope.'),
('C','Matching ROA current/prior','Growth in total-asset return','Two matching earnings/asset periods','Requires original ROA and growth conventions.'),
('C','Cash generation; dividends; investment and working-capital components','Cash reinvestment measure','Period and balance conventions required','PPE cash purchases alone do not reconstruct this vendor ratio.'),
('A','Current assets; current liabilities','Current assets / current liabilities','Same reporting date','Requires current/non-current presentation or equivalent breakdown.'),
('B','Quick-asset components; current liabilities','Eligible quick assets / current liabilities','Same reporting date','Current assets minus inventory is not always sufficient; prepayments and other exclusions may apply.'),
('C','Interest/finance costs; exact denominator','Interest expense ratio','Matching annual period','Vendor has several versions; do not assume interest/revenue for this specific column.'),
('B','Eligible debt or liabilities; appropriate net worth','Debt / net worth candidate','Same reporting date','Total debt may mean borrowings or liabilities; sign and absolute-equity treatment need verification.'),
('A','Total liabilities; total assets','Total liabilities / total assets','Same reporting date','Confirm percent/fraction convention; not interest-bearing debt only.'),
('A','Total equity; total assets','Equity / total assets','Same reporting date','Confirm total equity versus parent-only equity.'),
('B','Long-term liability; equity; fixed-asset components','Long-term funding / eligible fixed assets candidate','Same reporting date','Fixed-asset and long-term-funding definitions require verification.'),
('B','Short/long-term borrowing breakdown; equity','Eligible borrowings / equity candidate','Same reporting date','Borrowings are a subset of liabilities; donor adjustments must be checked.'),
('B','Quantified contingent liabilities; equity','Eligible contingent liabilities / equity','Same reporting date','Contingencies may be narrative or unquantifiable; absence of a number is not zero.'),
('B','Operating profit; paid-in-capital components','Operating profit / eligible paid-in capital','Annual flow and specified capital date','Exact denominator components differ from total equity; check Malaysian share-capital compatibility.'),
('B','Profit before tax; paid-in-capital components','Pretax profit / eligible paid-in capital','Annual flow and specified capital date','Exact paid-in-capital convention, including applicable adjustments, needs donor confirmation.'),
('B','Inventory; trade receivables; equity','(Inventory + eligible receivables) / equity','Same reporting date','Trade notes/related-party receivables and net-worth scope need mapping.'),
('B','Revenue; opening/closing total assets','Revenue / eligible average assets','Annual flow; opening/closing balance','Confirm average versus ending balance and annualisation.'),
('B','Eligible credit sales; opening/closing trade receivables','Eligible sales / average receivables','Annual flow; opening/closing balance','Credit sales may not be separately reported; do not silently substitute total revenue.'),
('B','Receivables; matching sales; number of days','Collection-days measure','Matching period and balance convention','Requires credit-sales or donor-specific sales basis; verify 360/365 and annualisation.'),
('B','Cost of sales or donor-defined sales; opening/closing inventory','Inventory turnover','Annual flow; opening/closing balance','Numerator convention varies; service businesses may have no inventory.'),
('B','Revenue; eligible opening/closing fixed assets','Fixed-asset turnover','Annual flow; opening/closing balance','Net/gross PPE and average/end balance need definition.'),
('B','Revenue; opening/closing equity','Equity/net-worth turnover','Annual flow; opening/closing balance','Verify equity scope and sign treatment.'),
('B','Revenue; matching employee headcount','Revenue / eligible headcount','Annual flow; average/end headcount','Payroll/HR headcount may be needed; employee benefit expense is not headcount.'),
('B','Operating profit; matching employee headcount','Operating profit / eligible headcount','Annual flow; average/end headcount','Employee count not assured in ordinary statements.'),
('C','Employee headcount; definition of allocation numerator','Allocation per person','Balance/headcount convention unresolved','Possible fixed assets per employee; label alone is insufficient.'),
('A','Current assets; current liabilities; total assets','(Current assets - current liabilities) / assets','Same reporting date','Working capital can be negative; do not clamp.'),
('B','Quick-asset components; total assets','Eligible quick assets / assets','Same reporting date','Requires precise quick-asset exclusions.'),
('A','Current assets; total assets','Current assets / assets','Same reporting date','Consistent entity scope.'),
('A','Eligible cash/cash equivalents; total assets','Cash / assets','Same reporting date','Confirm whether equivalents/restricted deposits belong in numerator.'),
('B','Quick-asset components; current liabilities','Eligible quick assets / current liabilities','Same reporting date','Definition may overlap Quick Ratio; verify before deduplicating.'),
('A','Eligible cash/cash equivalents; current liabilities','Cash / current liabilities','Same reporting date','Confirm cash definition and nonzero denominator.'),
('A','Current liabilities; total assets','Current liabilities / assets','Same reporting date','Current/non-current classifications needed.'),
('C','Operating-funds measure; liabilities','Operating funds / liabilities','Period and balance convention required','Funds from operations is not automatically cash from operations.'),
('A','Inventory; current assets; current liabilities','Inventory / (current assets - current liabilities)','Same reporting date','Undefined at zero working capital; negative values may be meaningful.'),
('A','Inventory; current liabilities','Inventory / current liabilities','Same reporting date','Do not assume zero inventory for service firms without checking.'),
('A','Current liabilities; total liabilities','Current liabilities / total liabilities','Same reporting date','Potential duplicate of Current Liability to Liability; definitions must match.'),
('A','Current assets; current liabilities; equity','(Current assets - current liabilities) / equity','Same reporting date','Zero or negative equity needs explicit treatment.'),
('A','Current liabilities; equity','Current liabilities / equity','Same reporting date','Potential duplicate of Current Liability to Equity.'),
('A','Non-current liabilities; current assets','Long-term liabilities / current assets','Same reporting date','Verify long-term liability scope.'),
('A','Retained earnings/accumulated losses; assets','Retained earnings / assets','Same reporting date','Retained earnings is not current-year profit or total reserves.'),
('B','All eligible income and expense components','Total eligible income / total eligible expense','Matching annual period','Revenue alone is not total income; scope and gross/net presentation need checking.'),
('B','All eligible expenses; assets','Total eligible expense / assets','Annual flow and asset-date convention','Cost of sales, finance and tax inclusion require exact definition.'),
('C','Current assets; sales; exact ratio direction','Current-asset turnover or assets-to-sales','Annual flow and balance convention','English turnover label may conflict with donor description; do not assume direction.'),
('C','Quick assets; sales; exact ratio direction','Quick-asset turnover or assets-to-sales','Annual flow and balance convention','Resolve numerator/denominator and quick-asset definition.'),
('C','Working capital; sales; exact ratio direction','Working-capital turnover or capital-to-sales','Annual flow and balance convention','Spelling retained from dataset; direction and negative-denominator handling unresolved.'),
('C','Cash; sales; exact ratio direction','Cash turnover or cash-to-sales','Annual flow and balance convention','Resolve donor ratio direction before implementing.'),
('C','Matching cash-flow measure; sales','Cash flow / sales','Matching annual period','Distinguish CFO, net cash change and adjusted cash flow.'),
('B','Eligible fixed assets; total assets','Fixed assets / total assets','Same reporting date','PPE net carrying value is a candidate, not confirmed definition.'),
('A','Current liabilities; total liabilities','Current liabilities / total liabilities','Same reporting date','Potential duplicate of Current Liabilities/Liability.'),
('A','Current liabilities; equity','Current liabilities / equity','Same reporting date','Potential duplicate of Current Liabilities/Equity.'),
('A','Equity; non-current liabilities','Equity / long-term liabilities','Same reporting date','Undefined if eligible long-term liability is zero.'),
('C','Matching cash-flow measure; assets','Cash flow / assets','Annual flow and balance convention','Donor cash-flow and asset-date definitions unresolved.'),
('C','Matching cash-flow measure; liabilities','Cash flow / liabilities','Annual flow and balance convention','Do not assume the same numerator as CFO.'),
('A','Net cash from operating activities; assets','CFO / assets','Annual cash flow and specified asset balance','Confirm average/end assets; cash flows are shown in MPERS examples.'),
('C','Matching cash-flow measure; equity','Cash flow / equity','Annual flow and balance convention','Cash-flow definition and equity scope unresolved.'),
('A','Current liabilities; current assets','Current liabilities / current assets','Same reporting date','Not a growth or cash-flow measure.'),
('A','Total liabilities; total assets','Indicator based on liabilities exceeding assets','Same reporting date','Confirm encoded direction (0/1); derived flag, not a printed statement field.'),
('A','Net income; assets','Net income / assets','Annual flow and specified asset balance','Confirm average/end assets and continuing/total profit scope.'),
('D','Total assets; external GNP/economic-price measure','Requires an external macroeconomic reference/factor','Country/year/currency alignment','Not supplied by an SME financial statement; direction, reference and method unclear.'),
('C','Eligible liquid assets; operating expenditure/credit components','No-credit interval','Matching balance and daily-flow convention','Specialised definition not recovered from field name.'),
('A','Gross profit; sales','Gross profit / sales','Matching annual period','Potential overlap with Operating Gross Margin; definitions not assumed identical.'),
('A','Net income; shareholders equity','Net income / eligible equity','Annual flow and specified equity balance','Confirm ending/average and parent/total equity.'),
('A','Total liabilities; eligible equity','Liabilities / equity','Same reporting date','Check absolute-equity/sign conventions and scope.'),
('B','Operating profit; actual interest expense','Financial-leverage measure candidate','Matching annual period','Formula and loss/zero-denominator handling must match donor; finance costs may include noninterest items.'),
('C','Interest/finance costs; EBIT','Coverage or inverse coverage','Matching annual period','Parenthetical interest expense to EBIT conflicts with conventional coverage direction.'),
('E','Historical profit/loss periods if defined','Constant feature in this local dataset','Dataset-specific','Exclude from predictive pool: no observed variation in this dataset, not proof of constant future values. UCI describes a two-year negative-income flag, but this local column mapping is not confirmed.'),
('A','Equity; total liabilities','Equity / liabilities','Same reporting date','Undefined at zero liabilities; reciprocal only under matching raw conventions.')
]
assert len(items)==len(features),(len(items),len(features))
root=ET.fromstring(Path(r'C:/Users/User/Downloads/ixbrl-example1-2020-03-16 (1).xhtml').read_bytes())
concepts=sorted(set(e.get('name') for e in root.iter() if e.get('name') and ':' in e.get('name')))
top20=[c.strip() for c in Path('data/X_train_processed_8020.csv').read_text().splitlines()[0].split(',')]
category={'A':'Annual-account calculator candidate','B':'Conditional: notes, history or additional records','C':'Specialised definition or exact mapping unresolved','D':'External information required','E':'Exclude: constant local feature'}
refs={
'SSM':'https://www.ssm.com.my/bm/Pages/Register_Business_Company_LLP/Company/document/FAQ-MBRS_ISSB.pdf#page=12',
'NK':'https://nk.com.my/cdn/pdf/MPERS_Illustrative_Financial_Statements.pdf#page=21',
'KPMG':'https://assets.kpmg.com/content/dam/kpmgsites/my/pdf/2025/01/Wonderful-SME-Sdn-Bhd-Illustrative-Financial-Statements-2016.pdf',
'UCI':'https://archive.ics.uci.edu/dataset/572/taiwanese+bankruptcy+prediction',
'TEJ':'https://www.tej.com.tw/tejdoc/db-document/tw/wim4.html',
'IFRS':'https://www.ifrs.org/issued-standards/ifrs-taxonomy/ifrs-taxonomy-illustrative-examples/'}
rows=[]
for n,(name,item) in enumerate(zip(features,items),1):
 cat,inputs,route,period,caution=item
 rows.append({'number':n,'feature':name,'category':cat,'category_label':category[cat],
    'top20':name in top20,'required_company_information':inputs,'conceptual_calculation':route,
    'time_requirement':period,'caution':caution,
    'directly_printed_ratio_guaranteed':False,'original_model_scale_verified':False,
    'constant_in_local_data':bool(df[name].nunique(dropna=False)<=1),
    'source_refs':['SSM','NK','KPMG','IFRS']+(['UCI','TEJ'] if cat in ['B','C','D','E'] else ['UCI']),
    'evidence_level':'Analyst feasibility assessment; not a confirmed exact donor-to-MPERS match'})
counts={k:sum(r['category']==k for r in rows) for k in category}
result={'date':'2026-10-28','scope':'Incorporated Malaysian SMEs with complete annual accounts and notes; not all businesses',
 'dataset':{'path':str(raw_path.resolve()),'sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
  'rows':len(df),'columns':len(df.columns),'financial_features':len(features),'target_counts':df.Bankrupt.value_counts().to_dict(),
  'excluded_metadata':['Company','Bankrupt'],'constant_features':[c for c in features if df[c].nunique(dropna=False)<=1]},
 'interpretation':'A means credible calculator candidate from ordinary account amounts, not mandatory printed ratio or verified model-ready conversion. B/C are review queues, not automatic exclusions.',
 'categories':category,'counts':counts,'sources':refs,'rows':rows,
 'user_ifrs_file':{'path':r'C:/Users/User/Downloads/ixbrl-example1-2020-03-16 (1).xhtml','tagged_concepts':len(concepts)},
 'all_model_scale_verified':False,'training_performed':False}
(base/'feature_crosscheck.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
summary=f'''SHIELD - FINANCIAL STATEMENT TO DATASET CROSS-CHECK
28 October 2026

SCOPE AND EVIDENCE
Reviewed the actual local original Excel file: {len(df):,} companies, {len(df.columns)} columns,95 financial predictors. Company and Bankrupt are not predictors. Counts:6599 non-bankrupt,220 bankrupt. Net Income Flag is constant and should be excluded. Filename is not reliable country provenance: columns and sample dimensions match UCI Taiwanese benchmark; no raw-UCI file hash comparison was made.

Terra analyst identified SSM's filing components and Malaysian MPERS illustrative accounts. The user's local IFRS iXBRL example was parsed directly: {len(concepts)} distinct tagged concepts, including assets, liabilities, equity, profit, cash flows, retained earnings, R&D and share counts. Concept presence in this example is evidence of possible reporting, not universal mandatory availability. The IFRS example is not proof of Malaysian MPERS requirements or of current historical dataset field equivalence.

REPORTING STRUCTURE
SSM FAQ v2.8(May2025),PDF page12:financial position,profit/loss,cashflows,equity,andnotes. NK illustrative account printed pp17-21(PDF pp21-25): ordinary amounts and comparisons. KPMG illustrative account printed p99(PDF p103)includes R&D. Exact data in notes vary; annual accounts do not necessarily supply quarterly recurring earnings, average share counts or employee headcount.

CATEGORIES
'''
for k,label in category.items():summary+=f'{k}: {counts[k]} - {label}\n'
summary+='''
No category means automatically model-ready. Exact definitions, entity scope, period, denominator zeros/signs, percent/fraction and historical donor transformation must be verified. Current/non-current calculator candidates require the corresponding balance-sheet breakdown; liquidity-only presentation may require extra notes. A core ratio being calculable in conventional accounting does not establish exact equivalence to a transformed UCI field.

MAIN FINDINGS
- Ordinary accounts support a meaningful feature pool beyond the historical top20. Filter for feasibility before IG rather than concluding IG is futile.
- Do not equate share capital with equity; actual shares with capital divided by an assumed par value; finance costs with pure interest; cashflow with profit; or employee costs with employee count.
- R&D is demonstrably reported in the user's IFRS example and KPMG illustration, but an omitted R&D line is not proof of zero.
- The share-field group can be feasible for incorporated businesses with proper share records; it is not automatically available for every SME or applicable to sole proprietors.
- Growth measures require matching history. Comparative annual accounts do not automatically supply every specialised growth formula or trailing-four-quarter recurrence adjustment.
- Total assets to GNP price requires an external economic reference/factor, not simply company accounts; its direction and method remain unresolved.
- B/C review status is not a finding that values are impossible to obtain; investigate definitions and actual supporting records before excluding them.
- Four-quarter EPS is not categorically impossible from annual records: at a matching year-end, sufficient annual recurring-profit/share detail might reconstruct a confirmed convention. The existing donor convention has not been confirmed.

RECOMMENDED CHECKPOINT (NO TRAINING)
Use A as a first-pass accounting-calculator pool. Review B fields for available notes and extra records; review C for exact definitions. Exclude E constant and omit D if restricting to company-only information. Freeze a verified eligible list before new experiments. IG may then select within that pool using training folds only. Removing hard-to-obtain fields does not by itself validate predictions for Malaysian SMEs or solve model input scaling.

ALL95 FEATURE DECISIONS
'''
for r in rows:
 summary+=f"\n{r['number']:02d}. {r['feature']} {'[CURRENT TOP20]' if r['top20'] else ''}\nCategory: {r['category']} - {r['category_label']}\nNeed: {r['required_company_information']}\nCandidate route: {r['conceptual_calculation']}\nPeriod: {r['time_requirement']}\nCheck: {r['caution']}\n"
summary+='\nSOURCE REGISTER\n'+'\n'.join(f'{k}: {v}' for k,v in refs.items())
(base/'SME_DATASET_CROSSCHECK.txt').write_text(summary,encoding='utf-8')
assert len(rows)==95 and len({r['feature'] for r in rows})==95 and sum(counts.values())==95
assert sum(r['top20'] for r in rows)==20
assert rows[93]['feature']=='Net Income Flag' and rows[93]['constant_in_local_data']
print('Counts:',counts,'Current top20:',sum(r['top20'] for r in rows))
print('Core calculator candidates:')
for r in rows:
 if r['category']=='A': print(r['feature'])
print('Cross-check coverage verified:95/95 predictors; no model training.')
