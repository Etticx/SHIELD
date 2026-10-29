import json,tempfile,unittest
from pathlib import Path
import pandas as pd
from sklearn.datasets import make_classification
import matplotlib
matplotlib.use('Agg')
PATH=Path(__file__).with_name('SHIELD_RF_Seven_vs_Twenty_Features.ipynb')
def read_cells():
    nb=json.loads(PATH.read_text(encoding='utf-8'))
    return [''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code']
class NotebookCheck(unittest.TestCase):
    def test_definition_and_cells(self):
        cells=read_cells();ns={}
        for s in cells:
            if not s.startswith('%'):compile(s,str(PATH),'exec')
        exec(cells[2],ns)
        self.assertEqual(list(ns['scenarios']()),['baseline_20','practical_7'])
        self.assertEqual(len(ns['scenarios']()['practical_7']),7)
        self.assertEqual(sorted(ns['HISTORICAL_IG_RANKS'].values()),[5,7,13,14,16,17,20])
        self.assertTrue(set(ns['SEVEN_FEATURES']).issubset(ns['FEATURES']))
    def test_small_run_and_resume_both_ratios(self):
        cells=read_cells()
        for ratio in [.25,1.]:
            ns={'display':lambda *args:None,'print':lambda *args,**kwargs:None}
            exec(cells[2],ns)
            original=ns['make_model']
            ns['make_model']=lambda r,small=False:original(r,small=True)
            X,y=make_classification(n_samples=360,n_features=20,n_informative=8,weights=[.9,.1],random_state=42)
            parent=Path('reports').resolve()
            with tempfile.TemporaryDirectory(prefix='.seven_verification_',dir=parent) as temp:
                root=Path(temp).resolve();self.assertTrue(root.is_relative_to(parent))
                data=pd.DataFrame(X,columns=ns['FEATURES']);data['Bankrupt']=y
                path=root/'original.csv';data.to_csv(path,index=False)
                ns.update(RAW_PATH=path,OUTPUT_BASE=root/'output',SMOTE_RATIO=ratio)
                ns['plt'].show=lambda:ns['plt'].close('all')
                for s in cells[3:]:exec(s,ns)
                expected=ns['results'].copy()
                for s in cells[3:]:exec(s,ns)
                pd.testing.assert_frame_equal(expected,ns['results'],check_dtype=False)
                self.assertEqual(len(ns['results']),4)
                self.assertTrue((ns['OUT']/'RESULTS.txt').exists())
                self.assertTrue((ns['OUT']/'test_comparison.svg').exists())
                for name in ns['scenarios']():
                    self.assertTrue((ns['OUT']/name/'test_roc_pr.png').exists())
if __name__=='__main__':unittest.main()
