# coleta completa de um município (sinais de alerta) — saídas cifradas por etapa
import json, gzip, os, re, time, urllib.request, urllib.parse, datetime as dt, zipfile, io, csv, subprocess
from concurrent.futures import ThreadPoolExecutor
IBGE, NOME = "2915205", "ITAGIB"
PARES = {"2915205": "Itagibá", "2915106": "Itagi", "2918308": "Jitaúna", "2932309": "Ubatã", "2912905": "Ibirataia", "2910008": "Dário Meira", "2913903": "Ipiaú", "2912707": "Ibirapitanga"}
os.makedirs("out", exist_ok=True)
H = {"Accept": "application/json", "User-Agent": "coleta-dados-abertos"}
def log(*a):
    print(*a, flush=True); open("out/log.txt", "a").write(" ".join(map(str, a)) + "\n")
def get(url, tries=8, raw=False, timeout=150):
    w = 3
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=timeout) as r:
                if r.status == 204: return {} if not raw else b""
                b = r.read()
                return b if raw else (json.loads(b) if b else {})
        except urllib.error.HTTPError as e:
            if e.code in (400, 404, 422): log("HTTP", e.code, url[:150]); return None
        except Exception: pass
        time.sleep(w); w = min(w * 2, 60)
    log("FALHOU", url[:150]); return None
def save(n, o):
    with gzip.open(f"out/{n}.json.gz", "wt", encoding="utf-8") as f: json.dump(o, f, ensure_ascii=False)
def etapa(nome):
    sh = f"""set -e; tar -czf /tmp/{nome}.tgz out; openssl rand -out /tmp/k.bin 32
openssl enc -aes-256-cbc -pbkdf2 -salt -in /tmp/{nome}.tgz -out c7_{nome}.enc -pass file:/tmp/k.bin
openssl pkeyutl -encrypt -pubin -inkey pub.pem -in /tmp/k.bin -out c7_{nome}.key
cd .. && git config user.name bot && git config user.email bot@x.invalid && git add sonda/c7_{nome}.enc sonda/c7_{nome}.key && git commit -qm c7_{nome}
for i in 1 2 3 4 5 6; do git pull -q --rebase origin sonda && git push -q && break; sleep 7; done"""
    r = subprocess.run(["bash", "-c", sh], capture_output=True, text=True); log("etapa", nome, r.returncode, r.stderr[-200:])
def paginas(base, params, tam):
    res, p = [], 1
    while True:
        d = get(base + "?" + urllib.parse.urlencode({**params, "pagina": p, "tamanhoPagina": tam}))
        if d is None: return res, False
        if not d.get("data"): return res, True
        res += d["data"]
        if p >= (d.get("totalPaginas") or 1): return res, True
        p += 1
ANOS = range(2021, 2027)
# 1. SICONFI
def dca(a):
    e, ano, anx = a; items, off = [], 0
    while True:
        d = get("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?" + urllib.parse.urlencode({"an_exercicio": ano, "no_anexo": anx, "id_ente": e, "offset": off}), tries=5, timeout=90)
        if not d: break
        items += d.get("items", [])
        if not d.get("hasMore"): break
        off += len(d.get("items", []))
    return f"{e}|{ano}|{anx}", [[i.get("cod_conta"), i.get("conta"), i.get("coluna"), i.get("valor")] for i in items]
jobs = [(e, a, x) for e in PARES for a in range(2015, 2026) for x in ("DCA-Anexo I-C", "DCA-Anexo I-D", "DCA-Anexo I-E")]
with ThreadPoolExecutor(4) as ex: sic = dict(ex.map(dca, jobs))
for a in range(2019, 2026):
    for anx in ("RREO-Anexo 12", "RREO-Anexo 08"):
        d = get("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo?" + urllib.parse.urlencode({"an_exercicio": a, "nr_periodo": 6, "co_tipo_demonstrativo": "RREO", "no_anexo": anx, "id_ente": IBGE}), tries=4)
        sic[f"{IBGE}|{a}|{anx}"] = [[i.get("cod_conta"), i.get("conta"), i.get("coluna"), i.get("valor")] for i in (d or {}).get("items", [])]
save("siconfi", sic); log("siconfi", sum(1 for v in sic.values() if v)); etapa("s")
# 2. contratações no município
def ctm(a):
    mod, ano = a
    return paginas("https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao", {"dataInicial": f"{ano}0101", "dataFinal": f"{ano}1231", "codigoModalidadeContratacao": mod, "codigoMunicipioIbge": IBGE}, 50)
J = [(m, a) for m in range(1, 15) for a in ANOS]
cts, falhas = [], []
with ThreadPoolExecutor(3) as ex:
    for j, (r, ok) in zip(J, ex.map(ctm, J)):
        cts += r
        if not ok: falhas.append(j)
for j in falhas:
    r, ok = ctm(j); cts += r; log("retentativa", j, ok, len(r))
cts = [c for c in cts if (c.get("orgaoEntidade") or {}).get("esferaId") == "M"]
cts = list({c["numeroControlePNCP"]: c for c in cts}.values())
orgs = sorted({c["orgaoEntidade"]["cnpj"] for c in cts})
log("contratacoes", len(cts), "orgaos", [(o, next(c["orgaoEntidade"]["razaoSocial"] for c in cts if c["orgaoEntidade"]["cnpj"] == o)) for o in orgs])
save("contratacoes", cts)
# 3. contratos
ctr = []
for o in orgs:
    for a in ANOS:
        r, ok = paginas("https://pncp.gov.br/api/consulta/v1/contratos", {"dataInicial": f"{a}0101", "dataFinal": f"{a}1231", "cnpjOrgao": o}, 500)
        if not ok:
            for m in range(1, 13):
                f = (dt.date(a, m, 28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
                rr, _ = paginas("https://pncp.gov.br/api/consulta/v1/contratos", {"dataInicial": f"{a}{m:02d}01", "dataFinal": f.strftime("%Y%m%d"), "cnpjOrgao": o}, 500); r += rr
        ctr += r
save("contratos", ctr); log("contratos", len(ctr)); etapa("a")
# 4. itens e resultados
def itens(c):
    cnpj = c["orgaoEntidade"]["cnpj"]; a = c["anoCompra"]; s = c["sequencialCompra"]
    base = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{a}/{s}"
    its = get(base + "/itens?pagina=1&tamanhoPagina=500") or []
    out = []
    for it in its if isinstance(its, list) else []:
        r = get(f"{base}/itens/{it['numeroItem']}/resultados") if it.get("temResultado") else None
        out.append({"i": it, "r": r})
    return {"id": c["numeroControlePNCP"], "itens": out}
with ThreadPoolExecutor(4) as ex: its = list(ex.map(itens, cts))
save("itens", its); log("itens", sum(len(x["itens"]) for x in its)); etapa("b")
# 5. CNPJ e sanções
forn = set()
for c in ctr:
    n = re.sub(r"\D", "", c.get("niFornecedor") or "")
    if len(n) == 14: forn.add(n)
for x in its:
    for it in x["itens"]:
        for r in (it["r"] or []):
            n = re.sub(r"\D", "", r.get("niFornecedor") or "")
            if len(n) == 14: forn.add(n)
def cnpj(n):
    return n, (get(f"https://minhareceita.org/{n}", tries=3, timeout=40) or get(f"https://brasilapi.com.br/api/cnpj/v1/{n}", tries=3, timeout=40))
with ThreadPoolExecutor(4) as ex: cad = dict(ex.map(cnpj, sorted(forn)))
save("cnpj", cad); log("cnpj", len(cad), sum(1 for v in cad.values() if v))
san = {}
for base in ("ceis", "cnep"):
    for k in range(0, 10):
        dia = (dt.date.today() - dt.timedelta(days=k)).strftime("%Y%m%d")
        b = get(f"https://portaldatransparencia.gov.br/download-de-dados/{base}/{dia}", tries=2, raw=True, timeout=300)
        if b and b[:2] == b"PK":
            z = zipfile.ZipFile(io.BytesIO(b)); rows = list(csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin-1"), delimiter=";"))
            ix = [i for i, h in enumerate(rows[0]) if "CPF OU CNPJ" in h.upper()][0]
            san[base] = [rows[0]] + [r for r in rows[1:] if re.sub(r"\D", "", r[ix]) in forn]; break
save("sancoes", san); log("sancoes", {k: len(v) - 1 for k, v in san.items()}); etapa("c")
# 6. TSE 2024
subprocess.run(["curl", "-sSL", "--retry", "5", "-o", "/tmp/pc.zip", "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2024.zip"])
tse = {}
try:
    z = zipfile.ZipFile("/tmp/pc.zip")
    for nm in z.namelist():
        if not nm.endswith("_BA.csv") or not any(k in nm for k in ("receitas_candidatos_2024", "despesas_contratadas_candidatos_2024")): continue
        rd = csv.reader(io.TextIOWrapper(z.open(nm), encoding="latin-1"), delimiter=";"); hdr = next(rd); iu = hdr.index("NM_UE")
        tse[nm] = [hdr] + [r for r in rd if r[iu].upper().startswith(NOME)]; log("tse", nm, len(tse[nm]) - 1)
except Exception as e: log("tse erro", e)
save("tse", tse); etapa("d")
log("FIM")
