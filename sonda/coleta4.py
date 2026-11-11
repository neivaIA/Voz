import json, gzip, os, re, sys, time, urllib.request, urllib.parse, datetime as dt, zipfile, io, csv
# v3
from concurrent.futures import ThreadPoolExecutor
OUT = "out"; os.makedirs(OUT, exist_ok=True)
IBGE = "2933307"
UA = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (dados abertos)"}
def log(*a):
    print(*a, flush=True)
    open("out/log.txt","a").write(" ".join(map(str,a))+"\n")
def get(url, tries=8, raw=False, timeout=150):
    w = 3
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                b = r.read()
                if raw: return b
                return json.loads(b) if b else None
        except urllib.error.HTTPError as e:
            if e.code in (204,): return None
            if e.code in (400, 404, 422): log("HTTP", e.code, url[:160], e.read()[:200]); return None
            time.sleep(w); w = min(w*2, 60)
        except Exception as e:
            time.sleep(w); w = min(w*2, 60)
    log("FALHOU", url[:160]); return None

import subprocess
def etapa4(nome):
    sh = f"""set -e; cd {os.getcwd()}; tar -czf /tmp/{nome}.tgz out; openssl rand -out /tmp/k.bin 32
openssl enc -aes-256-cbc -pbkdf2 -salt -in /tmp/{nome}.tgz -out c4_{nome}.enc -pass file:/tmp/k.bin
openssl pkeyutl -encrypt -pubin -inkey pub.pem -in /tmp/k.bin -out c4_{nome}.key
cd .. && git config user.name bot && git config user.email bot@x.invalid && git add sonda/c4_{nome}.enc sonda/c4_{nome}.key && git commit -qm c4_{nome}
for i in 1 2 3 4 5 6; do git pull -q --rebase origin sonda && git push -q && break; sleep 7; done"""
    r = subprocess.run(["bash", "-c", sh], capture_output=True, text=True); log("etapa", nome, r.returncode, r.stderr[-300:])

def save(nome, obj):
    with gzip.open(f"{OUT}/{nome}.json.gz", "wt", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False)
def meses(a, b):
    d = dt.date(*a)
    while d <= dt.date(*b):
        n = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        yield d.strftime("%Y%m%d"), (n - dt.timedelta(days=1)).strftime("%Y%m%d"); d = n
MES = list(meses((2021,1,1), (2026,11,30)))
ORGS = ["14239578000100", "14645717000103"]
def contratacoes(args):
    org, mod, (i, f) = args; res = []; p = 1
    while True:
        q = urllib.parse.urlencode({"dataInicial": i, "dataFinal": f, "codigoModalidadeContratacao": mod, "cnpj": org, "pagina": p, "tamanhoPagina": 50})
        d = get("https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?" + q)
        if d is None and p == 1: return ("ERRO", args)
        if not d or not d.get("data"): break
        res += d["data"]
        if p >= (d.get("totalPaginas") or 1): break
        p += 1
    return res
jobs = [(o, m, j) for o in ORGS for m in range(1, 15) for j in MES]
cts, erros = [], []
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(contratacoes, jobs):
        if isinstance(r, tuple): erros.append(r[1])
        else: cts += r
log("contratacoes", len(cts), "erros", len(erros), erros[:20])
save("contratacoes4", cts); save("erros4", erros); etapa4("f")
def itens(c):
    cnpj = c["orgaoEntidade"]["cnpj"]; a = c["anoCompra"]; s = c["sequencialCompra"]
    base = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{a}/{s}"
    its = get(base + "/itens?pagina=1&tamanhoPagina=500") or []
    out = []
    for it in its if isinstance(its, list) else []:
        r = None
        if it.get("temResultado"):
            r = get(f"{base}/itens/{it['numeroItem']}/resultados")
        out.append({"i": it, "r": r})
    return {"id": c["numeroControlePNCP"], "itens": out}
with ThreadPoolExecutor(4) as ex: its = list(ex.map(itens, cts))
save("itens4", its); log("itens4", sum(len(x["itens"]) for x in its))
forn = set()
for x in its:
    for it in x["itens"]:
        for r in (it["r"] or []):
            ni = re.sub(r"\D", "", r.get("niFornecedor") or "")
            if len(ni) == 14: forn.add(ni)
def cnpj(n):
    d = get(f"https://minhareceita.org/{n}", tries=3, timeout=30)
    if not d: d = get(f"https://brasilapi.com.br/api/cnpj/v1/{n}", tries=3, timeout=30)
    return n, d
with ThreadPoolExecutor(4) as ex: cad = dict(ex.map(cnpj, sorted(forn)))
save("cnpj4", cad); log("cnpj4", len(cad)); etapa4("g")
