import json,tempfile,unittest
from pathlib import Path
import pandas as pd
from sklearn.datasets import make_classification
import matplotlib
matplotlib.use('Agg')
PATH=Path(__file__).with_name('SHIELD_RF_Financial_Statement_30_vs_Twenty.ipynb')
def code_cells():
 nb=json.loads(PATH.read_text(encoding='utf-8'))
 return [''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code']
class NotebookCheck(unittest.TestCase):
 def test_scenarios(self):
  cells=code_cells();ns={}
  for s in cells:
   if not s.startswith('%'):compile(s,str(PATH),'exec')
  exec(cells[2],ns)
  self.assertEqual({k:len(v) for k,v in ns['scenarios']().items()},{'baseline_20':20,'financial_statement_30':30})
  self.assertEqual(len(ns['FEATURES']),43)
  self.assertNotIn('Bankrupt',ns['FEATURES']);self.assertNotIn('Company',ns['FEATURES'])
  self.assertNotIn('Net Income Flag',ns['STATEMENT_FEATURES'])
  self.assertEqual(len(set(ns['STATEMENT_FEATURES'])),30)
 def test_execution_resume_both_ratios(self):
  cells=code_cells()
  for ratio in [.25,1.]:
   ns={'display':lambda *a:None,'print':lambda *a,**k:None}
   exec(cells[2],ns)
   original=ns['make_model'];ns['make_model']=lambda r,small=False:original(r,small=True)
   X,y=make_classification(n_samples=360,n_features=43,n_informative=10,weights=[.9,.1],random_state=42)
   parent=Path('reports').resolve()
   with tempfile.TemporaryDirectory(prefix='.thirty_verification_',dir=parent) as temp:
    root=Path(temp).resolve();self.assertTrue(root.is_relative_to(parent))
    data=pd.DataFrame(X,columns=ns['FEATURES']);data['Bankrupt']=y
    path=root/'raw.csv';data.to_csv(path,index=False)
    ns.update(RAW_PATH=path,OUTPUT_BASE=root/'output',SMOTE_RATIO=ratio)
    ns['plt'].show=lambda:ns['plt'].close('all')
    for s in cells[3:]:exec(s,ns)
    before=ns['results'].copy()
    for s in cells[3:]:exec(s,ns)
    pd.testing.assert_frame_equal(before,ns['results'],check_dtype=False)
    self.assertEqual(len(ns['results']),4)
    self.assertTrue((ns['OUT']/'financial_statement_30'/'test_roc_pr.png').exists())
    self.assertTrue((ns['OUT']/'financial_statement_feature_manifest.csv').exists())
    self.assertTrue((ns['OUT']/'RESULTS.txt').exists())
if __name__=='__main__':unittest.main()
