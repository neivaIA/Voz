python3 - <<'P'
import json,urllib.request,urllib.parse,collections
API="https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
def api(p,**q):
    u=API+p+"?"+urllib.parse.urlencode(q)
    with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"contas-publicas"}),timeout=90) as r: return json.load(r)
for cod,tipo,per,n in ((2933307,"RGF","Q",3),(3108909,"RGF Simplificado","S",2)):
    it=api("/rgf",an_exercicio=2025,in_periodicidade=per,nr_periodo=n,co_tipo_demonstrativo=tipo,co_esfera="M",co_poder="E",id_ente=cod).get("items",[])
    print("==",cod,tipo,len(it),collections.Counter(i["anexo"] for i in it))
    for i in it:
        if i["anexo"] in ("RGF-Anexo 02","RGF-Anexo 05","RGF-Anexo 06"):
            print(i["anexo"],"|",i.get("cod_conta"),"|",(i.get("conta") or "")[:70],"|",i.get("coluna"),"|",i.get("valor"))
P
