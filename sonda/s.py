import json,urllib.request,urllib.parse,collections
API="https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
def api(p,**q):
    u=API+p+"?"+urllib.parse.urlencode(q)
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"contas-publicas"}),timeout=90) as r: return json.load(r)
    except Exception as e: return {"erro":repr(e)}
out={}
for cod in (3108909,3140407,4108205,3525003):
    for tipo in ("RREO","RREO Simplificado"):
        for per in (6,):
            j=api("/rreo",an_exercicio=2025,nr_periodo=per,co_tipo_demonstrativo=tipo,id_ente=cod)
            it=j.get("items",[])
            out[f"rreo {cod} {tipo} {per}"]=[j.get("erro"),dict(collections.Counter(i.get("anexo") for i in it))]
            a14=[i for i in it if "14" in (i.get("anexo") or "") or "Simplif" in (i.get("anexo") or "")]
            out[f"rreo {cod} {tipo} {per} a14amostra"]=[(i.get("anexo"),i.get("cod_conta"),i.get("coluna"),i.get("valor")) for i in a14 if "Saude" in (i.get("cod_conta") or "") or "Ensino" in (i.get("cod_conta") or "")][:20]
    for tipo in ("RGF","RGF Simplificado"):
        for per,n in (("Q",3),("S",2)):
            j=api("/rgf",an_exercicio=2025,in_periodicidade=per,nr_periodo=n,co_tipo_demonstrativo=tipo,co_esfera="M",co_poder="E",id_ente=cod)
            it=j.get("items",[])
            out[f"rgf {cod} {tipo} {per}{n}"]=[j.get("erro"),dict(collections.Counter(i.get("anexo") for i in it)),[(i.get("cod_conta"),i.get("coluna"),i.get("valor")) for i in it if "Pessoal" in (i.get("cod_conta") or "") and "RCL" in (i.get("coluna") or "")][:6]]
json.dump(out,open("sonda/res.json","w"),ensure_ascii=False,indent=1)
