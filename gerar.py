"""Gera UMA tomada (frase x semente) com o Chatterbox Multilingual e já confere a tomada.

Uso: python gerar.py PEDIDO.json FRASE_ID SEMENTE
Saída: out/<tema>/<id>_s<semente>.wav  e  out/<tema>/<id>_s<semente>.json (métricas)
"""
import json, os, re, sys, unicodedata

pedido, fid, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
P = json.load(open(pedido))
F = {f["id"]: f for f in P["frases"]}[fid]
par = {"exaggeration": 0.55, "cfg_weight": 0.35, "temperature": 0.8, **P.get("params", {}), **F.get("params", {})}
out = f"out/{P['tema']}"; os.makedirs(out, exist_ok=True)
base = f"{out}/{fid}_s{seed}"

# ---------- geração ----------
import torch, torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
torch.set_num_threads(os.cpu_count() or 4)
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
torch.manual_seed(seed)
kw = dict(language_id="pt", **par)
if P.get("referencia") and os.path.exists(P["referencia"]):
    kw["audio_prompt_path"] = P["referencia"]
w = m.generate(F["fala"], **kw)
ta.save(base + ".wav", w, m.sr)

# ---------- conferência ----------
import numpy as np, librosa
from faster_whisper import WhisperModel
from num2words import num2words

def norm(s):
    s = s.lower().replace("€", " euros ").replace("%", " por cento ").replace("r$", " ")
    s = re.sub(r"(\d+)\.(\d{3})", r"\1\2", s)
    s = re.sub(r"(\d+),(\d+)", lambda m_: m_.group(1) + " virgula " + m_.group(2), s)
    s = re.sub(r"\d+", lambda m_: " " + num2words(int(m_.group()), lang="pt_BR") + " ", s)
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z ]", " ", s)
    return [x for x in s.split() if x not in ("e", "pra", "para")]

def wer(ref, hyp):
    d = list(range(len(hyp) + 1))
    for i, a in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, b in enumerate(hyp, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (a != b)); prev, d[j] = d[j], cur
    return d[-1] / max(1, len(ref))

NUM = set("um dois tres quatro cinco seis sete oito nove dez onze doze treze catorze quinze dezesseis dezessete dezoito dezenove vinte trinta "
          "quarenta cinquenta sessenta setenta oitenta noventa cem cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos "
          "oitocentos novecentos mil milhao milhoes bilhao bilhoes".split())
def chaves(fala):
    k = {x for x in norm(fala) if x in NUM}
    for x in fala.split():
        if x[:1].isupper(): k.update(norm(x))
    k.update(norm(" ".join(F.get("chaves", []))))
    return k

y, sr = librosa.load(base + ".wav", sr=16000)
y, _ = librosa.effects.trim(y, top_db=40)
dur = len(y) / sr
wm = WhisperModel(os.environ.get("WHISPER", "small"), device="cpu", compute_type="int8")
segs, _ = wm.transcribe(y, language="pt", beam_size=5, initial_prompt=P.get("vocabulario"))
txt = " ".join(s.text for s in segs).strip()
ref, hyp = norm(F["fala"]), norm(txt)
e = wer(ref, hyp)
falt = sorted(chaves(F["fala"]) - set(hyp))
cps = len(F["fala"]) / max(dur, .1)
iv = librosa.effects.split(y, top_db=40)
gaps = [(iv[i + 1][0] - iv[i][1]) / sr for i in range(len(iv) - 1)]
multi = "..." in F["fala"] or len(re.findall(r"[.,:?]", F["fala"][:-1])) >= 1
pausa = float(max(gaps or [0]))
f0, _, _ = librosa.pyin(y, fmin=70, fmax=400, sr=sr)
f0 = f0[~np.isnan(f0)]
st = float(np.std(12 * np.log2(f0 / np.median(f0)))) if len(f0) > 10 else 0.0
lo = 9 if len(F["fala"]) < 40 else 10.5
ok = bool(e <= 0.12 and not falt and lo <= cps <= 22 and pausa <= (0.95 if multi else 0.6))
res = {"id": fid, "seed": seed, "arq": os.path.basename(base) + ".wav", "ok": ok, "wer": round(e, 3), "faltam": falt,
       "cps": round(cps, 1), "pausa": round(pausa, 2), "f0_st": round(st, 2), "dur": round(dur, 2), "txt": txt}
json.dump(res, open(base + ".json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
