"""Roda um pedido inteiro num computador só (seu PC, Google Colab ou o workflow narrar-rapido).

Não depende do GitHub Actions: se a fila do GitHub travar, rode isto e mande o .zip.

Uso:
  python voz.py pedidos/docinhos.json                     # motor do pedido (ou chatterbox)
  python voz.py pedidos/docinhos.json --motor kokoro      # força um motor
  python voz.py pedidos/docinhos.json --motor auto        # tenta chatterbox > kokoro > piper > edge
  python voz.py pedidos/docinhos.json --voz pm_alex --sementes 11 --so n3,n4 --zip

Saída: out/<tema> (chatterbox) ou out/<tema>-<motor>, com um WAV e um JSON por tomada,
       escolha.json (melhor tomada de cada frase) e resumo.md (tabela para conferir).
Todas as frases saem do MESMO motor: nunca mistura vozes no mesmo vídeo.
"""
import argparse, json, os, sys, time, zipfile, shutil
from motores import gerar, AUTO, MOTORES
from conferir import conferir, melhor
from gerar import pasta_saida


def rodar(P, motor, sementes, so=None, log=print):
    frases = [f for f in P["frases"] if not so or f["id"] in so]
    out = pasta_saida(P, motor); os.makedirs(out, exist_ok=True)
    res = {}
    for f in frases:
        par = {**P.get("params", {}), **f.get("params", {})}
        for s in sementes:
            base = f"{out}/{f['id']}_s{s}"
            t0 = time.time()
            real = gerar(motor, f["fala"], s, par, base + ".wav", voz=P.get("voz"), referencia=P.get("referencia"))
            r = conferir(base + ".wav", f, s, P.get("vocabulario"), motor=real)
            if real != motor: r["motor_pedido"] = motor
            json.dump(r, open(base + ".json", "w"), ensure_ascii=False, indent=1)
            res.setdefault(f["id"], []).append(r)
            log(f"{f['id']} s{s} [{real}] ok={r['ok']} wer={r['wer']} cps={r['cps']} f0={r['f0_st']} "
                f"({time.time() - t0:.1f}s) {r['txt'][:70]}")
    return out, res


def resumo(P, out, res):
    # junta com tomadas que já estavam na pasta (ex.: rodadas anteriores)
    todas = {}
    for arq in sorted(os.listdir(out)):
        if arq.endswith(".json") and "_s" in arq:
            r = json.load(open(os.path.join(out, arq))); todas.setdefault(r["id"], []).append(r)
    esc = {}
    linhas = ["| frase | melhor tomada | ok | erro | car/s | entonação | transcrição |", "|---|---|---|---|---|---|---|"]
    for f in P["frases"]:
        m = melhor(todas.get(f["id"], []))
        if not m: linhas.append(f"| {f['id']} | (sem tomada) | | | | | |"); continue
        esc[f["id"]] = m["arq"]
        linhas.append(f"| {f['id']} | {m['arq']} | {'sim' if m['ok'] else 'NÃO'} | {m['wer']} | {m['cps']} | {m['f0_st']} | {m['txt'][:80]} |")
    json.dump(esc, open(os.path.join(out, "escolha.json"), "w"), indent=1)
    sem_ok = [k for k in esc if not next(r for r in todas[k] if r["arq"] == esc[k])["ok"]]
    txt = f"# Voz: {P['tema']}\n\n" + "\n".join(linhas) + "\n"
    if sem_ok: txt += f"\nFrases sem tomada aprovada: {', '.join(sem_ok)}. Gere de novo só elas com --so {','.join(sem_ok)} --sementes 33,44\n"
    open(os.path.join(out, "resumo.md"), "w").write(txt)
    return txt, esc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pedido")
    ap.add_argument("--motor", help=f"um de {MOTORES} ou auto")
    ap.add_argument("--voz", help="voz do motor (ex.: pf_dora, pm_alex, pt_BR-faber-medium, pt-BR-AntonioNeural)")
    ap.add_argument("--sementes", help="ex.: 11,22 (padrão: as do pedido)")
    ap.add_argument("--so", help="só estas frases, ex.: n3,n4 (padrão: refazer do pedido, ou todas)")
    ap.add_argument("--zip", action="store_true", help="gera <pasta>.zip para enviar")
    a = ap.parse_args()

    P = json.load(open(a.pedido))
    if a.voz: P["voz"] = a.voz
    sementes = [int(x) for x in (a.sementes.split(",") if a.sementes else P.get("sementes", [11, 22]))]
    so = set(a.so.split(",")) if a.so else (set(P["refazer"]) if P.get("refazer") else None)
    pedido_motor = a.motor or P.get("motor") or "chatterbox"
    candidatos = AUTO if pedido_motor == "auto" else [pedido_motor]

    for i, motor in enumerate(candidatos):
        try:
            print(f"== motor {motor} ==")
            out, res = rodar(P, motor, sementes, so)
            break
        except Exception as e:
            print(f"[falhou] {motor}: {type(e).__name__}: {e}")
            # descarta tomadas parciais desse motor para não misturar vozes
            if len(candidatos) > 1: shutil.rmtree(pasta_saida(P, motor), ignore_errors=True)
            if i == len(candidatos) - 1:
                print("Nenhum motor funcionou. Instale um deles (veja requisitos/) e rode de novo."); sys.exit(1)
    txt, _ = resumo(P, out, res)
    print("\n" + txt)
    if a.zip:
        z = out.rstrip("/") + ".zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for arq in os.listdir(out): zf.write(os.path.join(out, arq), os.path.join(os.path.basename(out), arq))
        print("zip:", z)


if __name__ == "__main__":
    main()
