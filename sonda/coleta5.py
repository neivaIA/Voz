import json, gzip, os, re, io, csv, zipfile, subprocess, urllib.request, time
os.makedirs("out", exist_ok=True)
def log(*a):
    print(*a, flush=True); open("out/log.txt", "a").write(" ".join(map(str, a)) + "\n")
URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2024.zip"
subprocess.run(["curl", "-sSL", "--retry", "5", "-o", "/tmp/pc.zip", URL]); log("baixado", os.path.getsize("/tmp/pc.zip"))
z = zipfile.ZipFile("/tmp/pc.zip"); nomes = z.namelist(); log([n for n in nomes if "BA" in n])
tse = {}
for nm in nomes:
    if not nm.endswith("_BA.csv"): continue
    if not any(k in nm for k in ("receitas_candidatos_2024", "despesas_contratadas_candidatos_2024", "despesas_pagas_candidatos_2024")): continue
    rd = csv.reader(io.TextIOWrapper(z.open(nm), encoding="latin-1"), delimiter=";")
    hdr = next(rd); iu = hdr.index("NM_UE") if "NM_UE" in hdr else None
    rows = [r for r in rd if iu is None or "CONQUISTA" in r[iu].upper()]
    tse[nm] = [hdr] + rows; log("tse", nm, len(rows))
with gzip.open("out/tse.json.gz", "wt", encoding="utf-8") as f: json.dump(tse, f, ensure_ascii=False)
sh = """set -e; tar -czf /tmp/t.tgz out; openssl rand -out /tmp/k.bin 32
openssl enc -aes-256-cbc -pbkdf2 -salt -in /tmp/t.tgz -out c5_t.enc -pass file:/tmp/k.bin
openssl pkeyutl -encrypt -pubin -inkey pub.pem -in /tmp/k.bin -out c5_t.key
cd .. && git config user.name bot && git config user.email bot@x.invalid && git add sonda/c5_t.enc sonda/c5_t.key && git commit -qm c5
for i in 1 2 3 4 5 6; do git pull -q --rebase origin sonda && git push -q && break; sleep 7; done"""
r = subprocess.run(["bash", "-c", sh], capture_output=True, text=True); print(r.returncode, r.stderr[-400:])
