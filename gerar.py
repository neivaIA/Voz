"""Gera UMA tomada (frase x semente) e já confere. Usado pelo workflow narrar (uma tarefa por tomada).

Uso: python gerar.py PEDIDO.json FRASE_ID SEMENTE [MOTOR]
Saída: out/<pasta>/<id>_s<semente>.wav  e  .json (métricas)
       <pasta> = <tema> para o chatterbox (compatível com os pedidos antigos) ou <tema>-<motor> para os outros.
O motor vem do argumento, do campo "motor" do pedido, ou é chatterbox.
"""
import json, os, sys
from motores import gerar
from conferir import conferir


def pasta_saida(P, motor):
    return f"out/{P['tema']}" if motor == "chatterbox" else f"out/{P['tema']}-{motor}"


def uma_tomada(P, frase, semente, motor):
    par = {**P.get("params", {}), **frase.get("params", {})}
    out = pasta_saida(P, motor); os.makedirs(out, exist_ok=True)
    base = f"{out}/{frase['id']}_s{semente}"
    real = gerar(motor, frase["fala"], semente, par, base + ".wav", voz=P.get("voz"), referencia=P.get("referencia"))
    res = conferir(base + ".wav", frase, semente, P.get("vocabulario"), motor=real)
    if real != motor: res["motor_pedido"] = motor
    json.dump(res, open(base + ".json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))
    return res


if __name__ == "__main__":
    pedido, fid, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    P = json.load(open(pedido))
    motor = (sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None) or P.get("motor") or "chatterbox"
    F = {f["id"]: f for f in P["frases"]}[fid]
    uma_tomada(P, F, seed, motor)
