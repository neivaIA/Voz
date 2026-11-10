import json, gzip, os, time, urllib.request, urllib.parse
# v2
os.makedirs("out", exist_ok=True)
ENTES = {"2933307": "Vitória da Conquista", "2910800": "Feira de Santana", "2905701": "Camaçari", "2914802": "Itabuna", "2918407": "Juazeiro", "2927408": "Salvador", "2919207": "Lauro de Freitas", "2913606": "Ilhéus", "2906501": "Barra do Choça"}
def get(u):
    w = 3
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/json"}), timeout=120) as r: return json.loads(r.read())
        except Exception as e: time.sleep(w); w *= 2
    print("falhou", u, flush=True); return None
res = {}
for ente in ENTES:
    for ano in range(2015, 2026):
        for anx in ("DCA-Anexo I-D", "DCA-Anexo I-E", "DCA-Anexo I-F", "DCA-Anexo I-C"):
            items, off = [], 0
            while True:
                d = get("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?" + urllib.parse.urlencode({"an_exercicio": ano, "no_anexo": anx, "id_ente": ente, "offset": off}))
                if not d: break
                items += d.get("items", [])
                if not d.get("hasMore"): break
                off += len(d.get("items", []))
            res[f"{ente}|{ano}|{anx}"] = [[i.get("cod_conta"), i.get("conta"), i.get("coluna"), i.get("valor")] for i in items]
            print(ente, ano, anx, len(items), flush=True)
with gzip.open("out/siconfi.json.gz", "wt", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False)
