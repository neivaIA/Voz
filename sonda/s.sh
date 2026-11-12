python3 - <<'PY'
import json,urllib.request,urllib.parse,time
def api(p,**q):
  u="https://apidatalake.tesouro.gov.br/ords/siconfi/tt"+p+"?"+urllib.parse.urlencode(q)
  for k in range(5):
    try: return json.loads(urllib.request.urlopen(u,timeout=90).read())
    except Exception as e: time.sleep(3)
  return {}
S=[2900108,2901809,2900504,2929354,2910404,2906873,2901957]
E=[2911857,2928307,2920700,2905206,2932606,2925956,2926657,2924900,2904308,2903706,2926707,2923209]
for lab,lst,anx,kw in (("SAUDE",S,"RREO-Anexo 12","PERCENTUAL"),("EDUC",E,"RREO-Anexo 08","PERCENTUAL")):
  for c in lst:
    out=[]
    for tipo in ("RREO","RREO Simplificado"):
      it=api("/rreo",an_exercicio=2025,nr_periodo=6,co_tipo_demonstrativo=tipo,no_anexo=anx,id_ente=c).get("items",[])
      for i in it:
        if kw in (i.get("conta") or "").upper() and i.get("valor") not in (None,0): out.append((tipo,i["conta"][:70],i["coluna"][:30],i["valor"]))
      it14=api("/rreo",an_exercicio=2025,nr_periodo=6,co_tipo_demonstrativo=tipo,no_anexo="RREO-Anexo 14",id_ente=c).get("items",[])
      for i in it14:
        cc=(i.get("conta") or "").upper()
        if ("SAÚDE" in cc or "MANUTENÇÃO" in cc or "ENSINO" in cc) and "%" in (i.get("coluna") or "")+(i.get("conta") or "") : out.append(("A14",tipo,i["conta"][:60],i["coluna"][:25],i["valor"]))
    print(lab,c,json.dumps(out[:12],ensure_ascii=False))
PY
