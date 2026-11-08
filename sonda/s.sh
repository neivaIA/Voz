U="https://servicodados.ibge.gov.br/api/v3/agregados"
curl -sS --max-time 120 -A "Mozilla/5.0" -o ag.json -w "%{http_code} %{size_download}\n" "$U"; head -c 300 ag.json; echo
python3 - <<'P'
import json
try: d=json.load(open("ag.json"))
except Exception as e: print("erro",e); d=[]
for p in d:
  if "Censo" in p["nome"]:
    for a in p["agregados"]:
      n=a["nome"].lower()
      if any(k in n for k in ["esgot","abastecimento","lixo","banheiro","sanit","água"]): print(p["id"],p["nome"],"|",a["id"],a["nome"])
P
for t in 6805 6803 6892 9542; do curl -sS --max-time 60 -A "Mozilla/5.0" "$U/$t/metadados" | head -c 600; echo; done
python - <<'P'
import pyreaddbc,urllib.request,os
urllib.request.urlretrieve("ftp://ftp.datasus.gov.br/dissemin/publicos/SINASC/1996_/Dados/DNRES/DNAC2024.dbc","dn.dbc")
pyreaddbc.dbc2dbf("dn.dbc","dn.dbf")
from dbfread import DBF
P
pip install -q dbfread 2>&1|tail -1
python - <<'P'
import pyreaddbc,urllib.request
from dbfread import DBF
for f,u in [("dn","SINASC/1996_/Dados/DNRES/DNAC2024.dbc"),("do","SIM/CID10/DORES/DOAC2024.dbc")]:
  urllib.request.urlretrieve("ftp://ftp.datasus.gov.br/dissemin/publicos/"+u,f+".dbc"); pyreaddbc.dbc2dbf(f+".dbc",f+".dbf")
  t=DBF(f+".dbf",encoding="latin-1"); rs=list(t); print(f,len(rs),t.field_names[:60]); print({k:rs[0][k] for k in list(rs[0])[:40]})
P
curl -s --max-time 60 --list-only ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/ | grep 2024 | head -3; curl -sI --max-time 60 ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/DOBR2024.dbc | head -3
