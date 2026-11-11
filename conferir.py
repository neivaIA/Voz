"""Conferência automática de uma tomada: texto certo, palavras-chave, ritmo, pausas e entonação.

Mesmas regras de antes (antigo gerar.py). O transcritor é carregado uma vez por processo.
Se faster-whisper não estiver instalado (ou CONFERIR=0), mede só ritmo, pausas e entonação e marca
"conferida": false, para a escolha de tomadas saber que o texto não foi checado.
"""
import json, os, re, unicodedata

_WM = {}
NUM = set("um dois tres quatro cinco seis sete oito nove dez onze doze treze catorze quinze dezesseis dezessete dezoito dezenove vinte trinta "
          "quarenta cinquenta sessenta setenta oitenta noventa cem cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos "
          "oitocentos novecentos mil milhao milhoes bilhao bilhoes".split())


def norm(s):
    from num2words import num2words
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


def chaves(frase):
    k = {x for x in norm(frase["fala"]) if x in NUM}
    for x in frase["fala"].split():
        if x[:1].isupper(): k.update(norm(x))
    k.update(norm(" ".join(frase.get("chaves", []))))
    return k


def _transcrever(y, vocabulario):
    if os.environ.get("CONFERIR", "1") == "0": return None
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    if "wm" not in _WM:
        dev = "cuda" if _cuda() else "cpu"
        _WM["wm"] = WhisperModel(os.environ.get("WHISPER", "small"), device=dev,
                                 compute_type="float16" if dev == "cuda" else "int8")
    segs, _ = _WM["wm"].transcribe(y, language="pt", beam_size=5, initial_prompt=vocabulario)
    return " ".join(s.text for s in segs).strip()


def _cuda():
    try:
        import torch; return torch.cuda.is_available()
    except Exception:
        return False


def conferir(wav, frase, semente, vocabulario=None, motor="chatterbox"):
    import numpy as np, librosa
    y, sr = librosa.load(wav, sr=16000)
    y, _ = librosa.effects.trim(y, top_db=40)
    dur = len(y) / sr
    fala = frase["fala"]
    txt = _transcrever(y, vocabulario)
    if txt is None:
        e, falt, conferida = None, [], False
    else:
        hyp = norm(txt); e = wer(norm(fala), hyp); falt = sorted(chaves(frase) - set(hyp)); conferida = True
    cps = len(fala) / max(dur, .1)
    iv = librosa.effects.split(y, top_db=40)
    gaps = [(iv[i + 1][0] - iv[i][1]) / sr for i in range(len(iv) - 1)]
    multi = "..." in fala or len(re.findall(r"[.,:?]", fala[:-1])) >= 1
    pausa = float(max(gaps or [0]))
    try:
        f0, _, _ = librosa.pyin(y, fmin=70, fmax=400, sr=sr)
        f0 = f0[~np.isnan(f0)]
        st = float(np.std(12 * np.log2(f0 / np.median(f0)))) if len(f0) > 10 else 0.0
    except Exception:
        st = 0.0
    # faixas de ritmo por motor (Kokoro/edge/Piper falam em ritmo mais estável que o Chatterbox)
    lo = 9 if len(fala) < 40 else 10.5
    hi = 22 if motor.startswith("chatterbox") else 24
    ritmo_ok = lo <= cps <= hi and pausa <= (0.95 if multi else 0.6)
    ok = bool(ritmo_ok and (not conferida or (e <= 0.12 and not falt)))
    return {"id": frase["id"], "seed": semente, "arq": os.path.basename(wav), "motor": motor, "ok": ok,
            "conferida": conferida, "wer": None if e is None else round(e, 3), "faltam": falt,
            "cps": round(cps, 1), "pausa": round(pausa, 2), "f0_st": round(st, 2), "dur": round(dur, 2),
            "txt": txt if txt is not None else ""}


def melhor(tomadas):
    """Escolhe a melhor tomada de uma frase: ok primeiro, depois maior entonação, menor erro."""
    if not tomadas: return None
    return sorted(tomadas, key=lambda r: (not r["ok"], -(r["f0_st"] or 0), r["wer"] if r["wer"] is not None else 1))[0]
