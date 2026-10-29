import json, unittest
from pathlib import Path
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

class NotebookTest(unittest.TestCase):
    def test_pipelines_and_validation(self):
        path=Path('notebooks/experiment-Smote-ENN-SHIELD.ipynb')
        nb=json.loads(path.read_text(encoding='utf-8'))
        scope={}
        for cell in nb['cells']:
            if cell['cell_type']=='code':
                source=''.join(cell['source'])
                if not source.startswith('%'):
                    compile(source,str(path),'exec')
                if cell.get('metadata',{}).get('definitions'):
                    exec(source,scope)
        scope.update(SEED=42,FEATURE_MODE='all',TOP_K=20,SMOTE_RATIO=.25,MODEL_JOBS=1)
        X,y=make_classification(n_samples=240,n_features=25,n_informative=8,weights=[.85,.15],random_state=42)
        for mode in ['all','ig20']:
            scope['FEATURE_MODE']=mode
            for name in scope['METHODS']:
                pipe=scope['make_pipeline'](name,small=True)
                pipe.fit(X[:200],y[:200])
                score=pipe.predict_proba(X[200:])[:,1]
                self.assertEqual(len(score),40)
                self.assertTrue(np.isfinite(score).all())
                self.assertEqual('resample' in pipe.named_steps,name=='SMOTEENN_XGBoost')
                self.assertEqual('ig' in pipe.named_steps,mode=='ig20')
        values=scope['metrics'](np.array([0,0,1,1]),np.array([.1,.8,.6,.2]))
        self.assertAlmostEqual(values['Precision (%)'],50)
        self.assertAlmostEqual(values['Recall (%)'],50)

if __name__=='__main__': unittest.main()
