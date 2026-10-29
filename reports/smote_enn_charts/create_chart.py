from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_score,recall_score,f1_score
OUT=Path('reports/smote_enn_charts')
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':10})
names=['Balanced Random Forest','SMOTE-ENN + XGBoost','EasyEnsemble']
colors=['#28699a','#b46627','#48816b']
cm=[np.array([[1191,129],[8,36]]),np.array([[1294,26],[20,24]]),np.array([[1134,186],[4,40]])]
values=np.array([[21.82,81.82,34.45,52.79,94.81],[48,54.55,51.06,53.10,94.17],[17.70,90.91,29.63,49.75,95.01]])
for matrix,row in zip(cm,values):
    tn,fp,fn,tp=matrix.ravel()
    assert matrix.sum()==1364 and tp+fn==44 and tn+fp==1320
    assert abs(100*tp/(tp+fp)-row[0])<.011
    assert abs(100*tp/(tp+fn)-row[1])<.011
    assert abs(200*tp/(2*tp+fp+fn)-row[2])<.011
fig=plt.figure(figsize=(15,10),facecolor='white')
grid=fig.add_gridspec(2,3,height_ratios=[1.15,1],hspace=.55,wspace=.35)
ax=fig.add_subplot(grid[0,:])
x=np.arange(5)
for i,(name,color) in enumerate(zip(names,colors)):
    bars=ax.bar(x+(i-1)*.24,values[i],.23,label=name,color=color)
    ax.bar_label(bars,labels=[f'{v:.2f}' for v in values[i]],fontsize=9,padding=3)
ax.set_xticks(x,['Precision','Recall','F1-score','F2-score','ROC-AUC'])
ax.set_ylim(0,108)
ax.set_ylabel('Score (%)')
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y',alpha=.18)
ax.set_axisbelow(True)
ax.legend(loc='upper center',bbox_to_anchor=(.5,1.20),ncol=3,frameon=False)
ax.set_title('Test performance: bankruptcy is the positive class',pad=48,fontsize=14)
for i,(name,matrix) in enumerate(zip(names,cm)):
    a=fig.add_subplot(grid[1,i])
    a.imshow(matrix,cmap='Blues',vmin=0,vmax=1320)
    for (r,c),v in np.ndenumerate(matrix):
        a.text(c,r,str(v),ha='center',va='center',fontsize=16,color='white' if v>660 else '#172c3b')
    a.set_xticks([0,1],['Not bankrupt','Bankrupt'])
    a.set_yticks([0,1],['Not bankrupt','Bankrupt'])
    a.set_xlabel('Predicted label')
    a.set_ylabel('True label')
    a.set_title(name,pad=12,fontsize=11)
fig.suptitle('SHIELD | Balanced ensembles and SMOTE-ENN',fontsize=19,y=.99,weight='bold')
fig.text(.5,.935,'80:20 split | 5-fold training CV | Test set: 1,320 non-bankrupt + 44 bankrupt companies',ha='center',fontsize=11)
fig.text(.5,.035,'SMOTE ratio 0.1 applies only to SMOTE-ENN + XGBoost; the two ensembles balance internally.\nSource: supplied experiment results. Test results only; training OOF scores excluded. No model rerun.',ha='center',fontsize=10,color='#46535c',linespacing=1.6)
fig.subplots_adjust(left=.075,right=.975,top=.76,bottom=.13)
fig.savefig(OUT/'SHIELD_SMOTEENN_01_test_results.svg',bbox_inches='tight')
fig.savefig(OUT/'SHIELD_SMOTEENN_01_test_results.png',dpi=180,bbox_inches='tight')
print('Verified all three confusion matrices and precision/recall/F1 against supplied metrics.')
print(OUT/'SHIELD_SMOTEENN_01_test_results.svg')
