set -x
F=ftp://ftp.datasus.gov.br/dissemin/publicos
for d in SIM/CID10/DORES/ SIM/PRELIM/DORES/ SINASC/1996_/Dados/DNRES/ SINASC/PRELIM/DNRES/; do echo "== $d"; curl -s --max-time 60 --list-only $F/$d | grep -E "BA|BR" | tail -6; done
pip install -q pyreaddbc 2>&1 | tail -2; python -c "import pyreaddbc;print('pyreaddbc ok')"
curl -s --max-time 120 "https://servicodados.ibge.gov.br/api/v3/agregados" | python3 -c "
import json,sys
for p in json.load(sys.stdin):
  if 'Censo Demogr' in p['nome'] and '2022' in p['nome']:
    for a in p['agregados']:
      n=a['nome'].lower()
      if any(k in n for k in ['esgot','abastecimento de','lixo','banheiro','sanit']): print(p['nome'],'|',a['id'],a['nome'])
"
