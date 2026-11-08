for u in "https://apisidra.ibge.gov.br/values/t/6805/n6/2927408" "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/" "https://servicodados.ibge.gov.br/api/v1/localidades/estados/29" "https://sidra.ibge.gov.br/"; do echo "== $u"; curl -sS --max-time 40 -A "Mozilla/5.0" -o x -w "%{http_code} %{size_download}\n" "$u"; head -c 400 x; echo; done
curl -sS --max-time 40 -A "Mozilla/5.0" "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/" | grep -o 'href="[^"]*"' | head -40
python -m pip install -q pyreaddbc dbfread 2>&1|tail -1
python - <<'P'
import pyreaddbc,urllib.request
from dbfread import DBF
for f,u in [("dn","SINASC/1996_/Dados/DNRES/DNAC2024.dbc"),("do","SIM/CID10/DORES/DOAC2024.dbc")]:
  urllib.request.urlretrieve("ftp://ftp.datasus.gov.br/dissemin/publicos/"+u,f+".dbc"); pyreaddbc.dbc2dbf(f+".dbc",f+".dbf")
  t=DBF(f+".dbf",encoding="latin-1"); rs=list(t); print(f,len(rs),t.field_names); print({k:rs[0][k] for k in list(rs[0])[:45]})
P
