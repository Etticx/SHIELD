import json,tempfile,unittest
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import pandas as pd
from sklearn.datasets import make_classification
P=Path(__file__).with_name('SHIELD_Seven_Features_RF_XGBoost_Experiments.ipynb')
class Check(unittest.TestCase):
 def test_definitions_and_experiments(self):
  n=json.loads(P.read_text())
  scope={}
  for cell in n['cells']:
   if cell['cell_type']!='code':continue
   s=''.join(cell['source'])
   compile('\n'.join(x for x in s.splitlines() if not x.startswith(('!pip','%pip'))),'colab','exec')
  # Imports/config/runner executed selectively; paths and raw data are supplied below.
  exec('\n'.join(x for x in ''.join(n['cells'][3]['source']).splitlines() if not x.startswith(('%pip','!pip'))),scope)
  scope['print']=lambda *a,**k:None
  scope['display']=lambda *a,**k:None
  exec(''.join(n['cells'][22]['source']),scope)
  self.assertEqual(len(scope['SEVEN_FEATURES']),7)
  parent=Path('reports').resolve()
  for ratio in [.1,.25,1.]:
   with tempfile.TemporaryDirectory(prefix='.seven_protocol_',dir=parent) as temp:
    root=Path(temp).resolve();self.assertTrue(root.is_relative_to(parent))
    X,y=make_classification(n_samples=600 if ratio==.1 else 360,n_features=7,n_informative=5,weights=[.94,.06] if ratio==.1 else [.9,.1],random_state=42)
    d=pd.DataFrame(X,columns=scope['SEVEN_FEATURES']);d['Bankrupt']=y
    scope.update(SMOTE_RATIO=ratio,BASE_REPORT_DIR=str(root/'reports'),BASE_MODEL_DIR=str(root/'models'),
        df=d,X_full=d.drop(columns='Bankrupt'),y_full=d.Bankrupt,DATA_FINGERPRINT='synthetic',
        RAW_SHA256='test',X_train_bal_demo=d.iloc[:10,:7],y_train_bal_demo=d.Bankrupt.iloc[:10],
        X_test_sel_demo=d.iloc[:5,:7],y_test_demo=d.Bankrupt.iloc[:5],selected_cols_demo=scope['SEVEN_FEATURES'],
        USE_PIPELINE_CACHE=False,N_JOBS=1)
    exec(''.join(n['cells'][20]['source']),scope)
    self.assertEqual(len(scope['PROTOCOLS']),8);self.assertEqual(len(scope['MODELS']),2)
    for model in scope['MODELS']:
     scope['FIXED_PARAMS'][model]['n_estimators']=5
     scope['PARAM_GRIDS'][model]={'model__n_estimators':[5],'model__max_depth':[2]}
     self.assertEqual(list(scope['make_training_pipeline'](model).named_steps),['smote','model'])
    for cfg in scope['PROTOCOLS']:
     for model in scope['MODELS']:
      result,yt,yp,ys,fitted=scope['run_experiment'](model,cfg)
      self.assertEqual(result['Selected_Features'],scope['SEVEN_FEATURES'])
      self.assertEqual(len(yt),len(ys))
      scope['save_checkpoint'](cfg['slug'],model,result,yt,yp,ys,fitted)
      self.assertIsNotNone(scope['load_checkpoint'](cfg['slug'],model))
      if cfg['split'] is None:self.assertIn('no tuning',result['Parameter_Source'])
      if cfg['split'] is not None and cfg['cv'] is not None:self.assertIn('GridSearch',result['Parameter_Source'])
    # Verify original-style result/chart/export cells using one cached protocol.
    scope['PROTOCOLS']=[scope['PROTOCOLS'][-1]]
    scope['plt'].show=lambda:scope['plt'].close('all')
    for i in [24,26,28,30,32]:exec(''.join(n['cells'][i]['source']),scope)
    self.assertTrue(Path(scope['report_dir'],'8020_cv10_confusion_matrices.svg').exists())
    self.assertTrue(Path(scope['model_dir'],'seven_input_manifest.json').exists())

if __name__=='__main__':unittest.main()
