python3 - <<'PY'
import json,urllib.request,urllib.parse,time
from concurrent.futures import ThreadPoolExecutor
IDS=json.loads('''{"E": [2911857, 2928307, 2920700, 2905206, 2932606, 2925956, 2926657, 2924900, 2904308, 2903706, 2926707, 2923209, 2903953, 2900108, 2905156, 2919504, 2928208, 2909000, 2924702, 2901809, 2900504, 2902401, 2900405, 2903904, 2902807, 2924652, 2912202, 2915502, 2928505, 2903003, 2926301, 2901502, 2908200, 2914901, 2919108, 2919603, 2933307, 2929008, 2917003, 2901304, 2920205, 2931202, 2931301, 2932101, 2911907, 2922706, 2932903, 2930709, 2908507, 2909703, 2900306, 2928802], "P": [2929602, 2910008, 2907806, 2916401, 2932200, 2927705, 2903607, 2913705, 2922706, 2931053, 2918803, 2926509, 2925931, 2923902, 2905602, 2902401], "S": [2900108, 2901809, 2900504, 2929354, 2910404, 2906873, 2901957, 2908606, 2933174, 2916302, 2923902]}''')
def api(p,**q):
  u="https://apidatalake.tesouro.gov.br/ords/siconfi/tt"+p+"?"+urllib.parse.urlencode(q)
  for k in range(5):
    try: return json.loads(urllib.request.urlopen(u,timeout=90).read())
    except Exception as e: time.sleep(3)
  return {}
def a14(c):
  r={}
  for tipo in ("RREO","RREO Simplificado"):
    for i in api("/rreo",an_exercicio=2025,nr_periodo=6,co_tipo_demonstrativo=tipo,no_anexo="RREO-Anexo 14",id_ente=c).get("items",[]):
      if (i.get("coluna") or "").startswith("% Aplicado"):
        cc=(i.get("conta") or "")
        if "Manu" in cc: r["e"]=i["valor"]
        if "Saúde" in cc: r["s"]=i["valor"]
    if r: return c,tipo,r
  return c,None,r
def rgf(c):
  for n in (3,2):
    for tipo in ("RGF","RGF Simplificado"):
      it=api("/rgf",an_exercicio=2025,in_periodicidade="Q",nr_periodo=n,co_tipo_demonstrativo=tipo,co_esfera="M",co_poder="E",no_anexo="RGF-Anexo 01",id_ente=c).get("items",[])
      v=[i["valor"] for i in it if "DESPESA TOTAL COM PESSOAL - DTP" in (i.get("conta") or "").upper() and "%" in (i.get("coluna") or "")+(i.get("conta") or "") ]
      w=[(i["conta"][:50],i["coluna"][:40],i["valor"]) for i in it if "% SOBRE A RCL" in ((i.get("coluna") or "")+(i.get("conta") or "")).upper()]
      if it: return c,n,tipo,v[:3],w[:3]
  return c,None
with ThreadPoolExecutor(6) as ex:
  for x in ex.map(a14,IDS["E"]+IDS["S"]): print("A14",json.dumps(x,ensure_ascii=False))
  for x in ex.map(rgf,IDS["P"]): print("RGF",json.dumps(x,ensure_ascii=False))
PY
