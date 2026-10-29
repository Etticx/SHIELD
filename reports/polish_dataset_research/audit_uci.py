import urllib.request,zipfile,io,json,csv,math
from pathlib import Path
root=Path(__file__).resolve().parent
url='https://archive.ics.uci.edu/static/public/365/polish%2Bcompanies%2Bbankruptcy%2Bdata.zip'
archive=root/'polish_companies_bankruptcy.zip'
if not archive.exists():archive.write_bytes(urllib.request.urlopen(url,timeout=45).read())
z=zipfile.ZipFile(archive);summary=[]
for name in z.namelist():
 if not name.endswith('.arff'):continue
 lines=z.read(name).decode('utf-8-sig').splitlines();start=next(i for i,l in enumerate(lines) if l.strip().lower()=='@data');rows=list(csv.reader(l for l in lines[start+1:] if l.strip() and not l.startswith('%')))
 labels=[r[-1].strip() for r in rows];cols={k:[float(r[k-1]) for r in rows if r[k-1].strip()!='?'] for k in [1,2,6,8,10]};checks=[]
 for r in rows:
  try:
   debt,equity,etol=float(r[1]),float(r[9]),float(r[7])
   if all(math.isfinite(v) for v in [debt,equity,etol]) and debt!=0:checks.append((abs(debt+equity-1),abs(etol-equity/debt)))
  except ValueError:pass
 entry={'file':name,'rows':len(rows),'predictors':len(rows[0])-1,'bankrupt':labels.count('1'),'not_bankrupt':labels.count('0'),'missing_cells':sum(v.strip()=='?' for r in rows for v in r[:-1]),'features':{str(k):{'min':min(v),'max':max(v),'missing':len(rows)-len(v)} for k,v in cols.items()},'accounting_checks':{'rows':len(checks),'debt_plus_equity_within_0_001':sum(a<.001 for a,b in checks),'equity_to_debt_within_0_001':sum(b<.001 for a,b in checks)},'first_row_selected':{str(k):rows[0][k-1] for k in cols}}
 summary.append(entry)
(root/'uci_file_audit.json').write_text(json.dumps({'source':url,'files':summary},indent=2))
print(json.dumps(summary,indent=2))
