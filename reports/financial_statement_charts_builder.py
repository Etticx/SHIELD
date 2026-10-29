from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
out=Path('reports/financial_statement_charts');out.mkdir(exist_ok=True)
names=['20-feature baseline','30 financial-statement candidates']
matrices=[np.array([[1246,74],[12,32]]),np.array([[1234,86],[13,31]])]
auc=[93.83,92.70]
values=[]
for cm,a in zip(matrices,auc):
 tn,fp,fn,tp=cm.ravel()
 assert tn+fp==1320 and fn+tp==44
 values.append([100*tp/(tp+fp),100*tp/(tp+fn),200*tp/(2*tp+fp+fn),a])
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':11})
fig=plt.figure(figsize=(12,9),facecolor='white')
gs=fig.add_gridspec(2,2,height_ratios=[1,.95],hspace=.55,wspace=.4)
ax=fig.add_subplot(gs[0,:]);x=np.arange(4)
for i,(name,vals,color) in enumerate(zip(names,values,['#28699a','#b46627'])):
 bars=ax.bar(x+(i-.5)*.34,vals,.33,label=name,color=color)
 ax.bar_label(bars,labels=[f'{v:.2f}' for v in vals],padding=4,fontsize=10)
ax.set_xticks(x,['Precision','Recall','F1-score','ROC-AUC']);ax.set_ylim(0,108)
ax.set_ylabel('Score (%)');ax.grid(axis='y',alpha=.17);ax.set_axisbelow(True)
ax.spines[['top','right']].set_visible(False)
ax.legend(loc='upper center',bbox_to_anchor=(.5,1.18),ncol=2,frameon=False)
for i,(name,cm) in enumerate(zip(names,matrices)):
 a=fig.add_subplot(gs[1,i]);a.imshow(cm,cmap='Blues',vmin=0,vmax=1320)
 for (r,c),v in np.ndenumerate(cm):a.text(c,r,str(v),ha='center',va='center',fontsize=17,color='white' if v>660 else '#172c3b')
 a.set_xticks([0,1],['Not bankrupt','Bankrupt']);a.set_yticks([0,1],['Not bankrupt','Bankrupt'])
 a.set_xlabel('Predicted label');a.set_ylabel('True label');a.set_title(name,pad=12)
fig.suptitle('SHIELD | Random Forest: 30 versus 20 inputs',fontsize=17,weight='bold',y=.99)
fig.text(.5,.945,'SMOTE 1.0 | 80:20 split | 10-fold training CV | Test cutoff 0.5',ha='center')
fig.text(.5,.035,'Test set: 1,320 non-bankrupt and 44 bankrupt companies.\nSource: user-supplied Colab results. Historical holdout; exploratory comparison. No model rerun.',ha='center',fontsize=9,color='#46535c',linespacing=1.5)
fig.subplots_adjust(top=.82,bottom=.14,left=.09,right=.97)
fig.savefig(out/'RF_30_vs_20_SMOTE_1_test.svg',bbox_inches='tight')
fig.savefig(out/'RF_30_vs_20_SMOTE_1_test.png',dpi=160,bbox_inches='tight')
(out/'RF_30_vs_20_SMOTE_1_test.json').write_text(json.dumps({'source':'User supplied Colab aggregate results; no rerun','threshold':.5,'smote':1.,'models':[{'name':n,'confusion_matrix':c.tolist(),'precision_recall_f1_auc_percent':v} for n,c,v in zip(names,matrices,values)]},indent=2),encoding='utf-8')
p=Path('reports/SME_INPUT_AVAILABILITY_CHECKPOINT_2026-10-28.txt')
heading='THIRTY VERSUS TWENTY - USER RESULTS - SMOTE 1.0'
entry='''

THIRTY VERSUS TWENTY - USER RESULTS - SMOTE 1.0
Recorded28October2026 from userColab reports/tables/figures. RF80:20,CV10,SMOTE1.0,threshold0.5,fixedparams,no newIG,noimputation. No modelrerun.
TEST baseline20:Accuracy93.70%;Precision30.19%;Recall72.73%;F142.67%;ROC-AUC93.83%;F256.74%;AP43.66%;TN1246;FP74;FN12;TP32.
TEST financial_statement30:Accuracy92.74%;Precision26.50%;Recall70.45%;F138.51%;ROC-AUC92.70%;F252.90%;AP35.72%;TN1234;FP86;FN13;TP31.
Supports1320nonbankrupt,44bankrupt for both.
TRAINING OOF baseline20:PooledF139.16%;ROC-AUC91.95%;F252.79%;AP36.03%;TN4958;FP321;FN55;TP121;foldF1mean39.44%,SD7.40points.
TRAINING OOF financial_statement30:PooledF137.46%;ROC-AUC91.96%;F251.53%;AP28.87%;TN4930;FP349;FN55;TP121;foldF1mean37.30%,SD6.12points.
30foldF1reported45.45,32.73,32.84,46.67,33.33,33.33,35.82,43.84,39.44,29.51 (rounded).
INTERPRETATION:30versusmatched20detects1fewerbankruptcy andproduces12morefalsealarms. Both trainingOOF models detect121of176;30produces28morefalsealarms.30testprecisionfalls3.69points,recall2.27points,F14.16points.
Within30:SMOTE0.25had27TP50FP17FN1270TN;SMOTE1.0has31TP86FP13FN1234TN. Fullbalancingdetects4additionalbankruptcies for36additionalfalsealarms;precision35.06to26.50%,F144.63to38.51%. Higherrecall70.45%doesnotmeanbetterbalancedperformance.
30isbelowmatched20onprecision/recall/F1atbothtestedratios. Thisisnotproofall30featuremodelsareinferior. Optionalnextcontrolledexperiment:IGinsideeachtrainingfoldwithinpredefined30pool;do not select features usingtestlabels. Definitionandtransformationchecks stillneeded. No productionmodelreplacement.
SVG:reports/financial_statement_charts/RF_30_vs_20_SMOTE_1_test.svg
'''
if heading not in p.read_text(encoding='utf-8'):
 with p.open('a',encoding='utf-8') as f:f.write(entry)
assert (out/'RF_30_vs_20_SMOTE_1_test.svg').stat().st_size>1000
print('Test counts/metrics verified, SVG exported, and research notes updated.')
