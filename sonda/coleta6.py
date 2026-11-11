import json, gzip, os, re, sys, time, urllib.request, urllib.parse, datetime as dt, zipfile, io, csv
# v3
from concurrent.futures import ThreadPoolExecutor
OUT = "out"; os.makedirs(OUT, exist_ok=True)
IBGE = "2933307"
UA = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (dados abertos)"}
def log(*a):
    print(*a, flush=True)
    open("out/log.txt","a").write(" ".join(map(str,a))+"\n")
def get(url, tries=10, raw=False, timeout=180):
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
openssl enc -aes-256-cbc -pbkdf2 -salt -in /tmp/{nome}.tgz -out c6_{nome}.enc -pass file:/tmp/k.bin
openssl pkeyutl -encrypt -pubin -inkey pub.pem -in /tmp/k.bin -out c6_{nome}.key
cd .. && git config user.name bot && git config user.email bot@x.invalid && git add sonda/c6_{nome}.enc sonda/c6_{nome}.key && git commit -qm c6_{nome}
for i in 1 2 3 4 5 6; do git pull -q --rebase origin sonda && git push -q && break; sleep 7; done"""
    r = subprocess.run(["bash", "-c", sh], capture_output=True, text=True); log("etapa", nome, r.returncode, r.stderr[-300:])

def save(nome, obj):
    with gzip.open(f"{OUT}/{nome}.json.gz", "wt", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False)
def meses(a, b):
    d = dt.date(*a)
    while d <= dt.date(*b):
        n = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        yield d.strftime("%Y%m%d"), (n - dt.timedelta(days=1)).strftime("%Y%m%d"); d = n
ORGS = ["14239578000100", "14645717000103"]
def contratacoes(org, mod, ano):
    res = []; p = 1
    while True:
        q = urllib.parse.urlencode({"dataInicial": f"{ano}0101", "dataFinal": f"{ano}1231", "codigoModalidadeContratacao": mod, "cnpj": org, "pagina": p, "tamanhoPagina": 50})
        d = get("https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?" + q)
        if d is None: return res, False
        if not d.get("data"): break
        res += d["data"]
        if p >= (d.get("totalPaginas") or 1): break
        p += 1
    return res, True
for mod in (8, 9, 6, 7):
    cts, ok = [], []
    for org in ORGS:
        for ano in range(2021, 2027):
            r, k = contratacoes(org, mod, ano); cts += r; ok.append((org, ano, k, len(r)))
    log("mod", mod, len(cts), ok)
    save(f"ct_mod{mod}", cts)
    def itens(c):
        cnpj = c["orgaoEntidade"]["cnpj"]; a = c["anoCompra"]; s = c["sequencialCompra"]
        base = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{a}/{s}"
        its = get(base + "/itens?pagina=1&tamanhoPagina=500") or []
        out = []
        for it in its if isinstance(its, list) else []:
            r = get(f"{base}/itens/{it['numeroItem']}/resultados") if it.get("temResultado") else None
            out.append({"i": it, "r": r})
        return {"id": c["numeroControlePNCP"], "itens": out}
    with ThreadPoolExecutor(3) as ex: its = list(ex.map(itens, cts))
    save(f"it_mod{mod}", its); log("itens mod", mod, sum(len(x["itens"]) for x in its))
    etapa4(f"m{mod}")
