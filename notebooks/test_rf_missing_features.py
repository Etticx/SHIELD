import json,unittest
from pathlib import Path
from sklearn.datasets import make_classification
class Check(unittest.TestCase):
 def test_notebooks(self):
  for tag,ratio in [('025',.25),('100',1.)]:
   nb=json.loads(Path(f'notebooks/SHIELD_RF_Missing_Features_SMOTE_{tag}.ipynb').read_text())
   ns={}
   for c in nb['cells']:
    if c['cell_type']=='code':
     s=''.join(c['source'])
     if not s.startswith('%'): compile(s,'notebook','exec')
     if c.get('metadata',{}).get('definitions'): exec(s,ns)
   self.assertEqual(len(ns['FEATURES']),20)
   self.assertEqual(len(ns['scenarios']()),18)
   self.assertEqual(len(ns['scenarios']()['without_share_fields']),16)
   X,y=make_classification(n_samples=220,n_features=20,n_informative=6,weights=[.85,.15],random_state=42)
   p=ns['make_model'](ratio,small=True)
   p.fit(X,y)
   self.assertEqual(p.predict_proba(X[:7]).shape,(7,2))
   self.assertEqual(list(p.named_steps),['smote','model'])
if __name__=='__main__': unittest.main()
