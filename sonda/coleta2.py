import json, gzip, os, re, sys, time, urllib.request, urllib.parse, datetime as dt, zipfile, io, csv
# v3
from concurrent.futures import ThreadPoolExecutor
OUT = "out"; os.makedirs(OUT, exist_ok=True)
IBGE = "2933307"
UA = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (dados abertos)"}
def log(*a): print(*a, flush=True)
def get(url, tries=6, raw=False, timeout=120):
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
def save(nome, obj):
    with gzip.open(f"{OUT}/{nome}.json.gz", "wt", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False)
def meses(a, b):
    d = dt.date(*a)
    while d <= dt.date(*b):
        n = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        yield d.strftime("%Y%m%d"), (n - dt.timedelta(days=1)).strftime("%Y%m%d"); d = n
JAN = list(meses((2021,1,1), (2026,11,30)))
# A. contratações publicadas no município, todas as modalidades
def contratacoes(args):
    mod, (i, f) = args; res = []; p = 1
    while True:
        q = urllib.parse.urlencode({"dataInicial": i, "dataFinal": f, "codigoModalidadeContratacao": mod, "codigoMunicipioIbge": IBGE, "pagina": p, "tamanhoPagina": 50})
        d = get("https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?" + q)
        if not d or not d.get("data"): break
        res += d["data"]
        if p >= (d.get("totalPaginas") or 1): break
        p += 1
    return res
jobs = [(m, j) for m in range(1, 15) for j in JAN]
with ThreadPoolExecutor(8) as ex: cts = [r for rr in ex.map(contratacoes, jobs) for r in rr]
save("contratacoes", cts); log("contratacoes", len(cts))
orgs = sorted({c["orgaoEntidade"]["cnpj"] for c in cts if c.get("orgaoEntidade")})
log("orgaos", orgs, [next(c["orgaoEntidade"]["razaoSocial"] for c in cts if c["orgaoEntidade"]["cnpj"] == o) for o in orgs])
# B. contratos dos órgãos
def contratos(args):
    cnpj, (i, f) = args; res = []; p = 1
    while True:
        q = urllib.parse.urlencode({"dataInicial": i, "dataFinal": f, "cnpjOrgao": cnpj, "pagina": p, "tamanhoPagina": 500})
        d = get("https://pncp.gov.br/api/consulta/v1/contratos?" + q)
        if not d or not d.get("data"): break
        res += d["data"]
        if p >= (d.get("totalPaginas") or 1): break
        p += 1
    return res
with ThreadPoolExecutor(8) as ex: ctr = [r for rr in ex.map(contratos, [(o, j) for o in orgs for j in JAN]) for r in rr]
save("contratos", ctr); log("contratos", len(ctr))
its = []
# D. fornecedores (CNPJ)
forn = set()
for c in ctr:
    ni = re.sub(r"\D", "", c.get("niFornecedor") or "")
    if len(ni) == 14: forn.add(ni)
for x in its:
    for it in x["itens"]:
        for r in (it["r"] or []):
            ni = re.sub(r"\D", "", r.get("niFornecedor") or "")
            if len(ni) == 14: forn.add(ni)
log("fornecedores", len(forn))
def cnpj(n):
    d = get(f"https://brasilapi.com.br/api/cnpj/v1/{n}", tries=4)
    if not d: d = get(f"https://minhareceita.org/{n}", tries=3)
    time.sleep(0.3); return n, d
with ThreadPoolExecutor(4) as ex: cad = dict(ex.map(cnpj, sorted(forn)))
save("cnpj", cad); log("cnpj ok", sum(1 for v in cad.values() if v))
# E. CEIS / CNEP
san = {}
for base in ("ceis", "cnep"):
    for k in range(0, 10):
        dia = (dt.date.today() - dt.timedelta(days=k)).strftime("%Y%m%d")
        b = get(f"https://portaldatransparencia.gov.br/download-de-dados/{base}/{dia}", tries=2, raw=True, timeout=300)
        if b and b[:2] == b"PK":
            z = zipfile.ZipFile(io.BytesIO(b)); nm = z.namelist()[0]
            rows = list(csv.reader(io.TextIOWrapper(z.open(nm), encoding="latin-1"), delimiter=";"))
            hdr = rows[0]; log(base, dia, len(rows), hdr)
            ix = [i for i, h in enumerate(hdr) if "CPF OU CNPJ" in h.upper()][0]
            san[base] = [hdr] + [r for r in rows[1:] if re.sub(r"\D", "", r[ix]) in forn]
            break
save("sancoes", san); log("sancoes", {k: len(v) - 1 for k, v in san.items()})
# F. TSE 2024 – prestação de contas dos candidatos da BA, só Vitória da Conquista
url = "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2024_BA.zip"
b = get(url, raw=True, timeout=900, tries=3)
tse = {}
if b:
    z = zipfile.ZipFile(io.BytesIO(b)); log("tse arquivos", [n for n in z.namelist()][:40])
    for nm in z.namelist():
        if not nm.lower().endswith(".csv") or ("receitas" not in nm and "despesas_contratadas" not in nm) or "doador_originario" in nm: continue
        rd = csv.reader(io.TextIOWrapper(z.open(nm), encoding="latin-1"), delimiter=";")
        hdr = next(rd); iu = hdr.index("NM_UE")
        rows = [r for r in rd if r[iu].upper().startswith("VITÓRIA DA CONQUISTA") or r[iu].upper().startswith("VITORIA DA CONQUISTA")]
        tse[nm] = [hdr] + rows; log("tse", nm, len(rows))
save("tse", tse)
log("FIM")
