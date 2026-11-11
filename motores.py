"""Motores de voz. Todos geram um WAV a partir de (texto, semente, params) e têm a mesma interface.

Motores:
  chatterbox       Chatterbox Multilingual (MIT), o mais expressivo. Padrão.
  chatterbox-ptbr  Chatterbox ajustado para português do Brasil (ResembleAI/Chatterbox-Multilingual-pt-br).
                   Se não carregar, cai para o chatterbox base e avisa no JSON (campo motor_real).
  kokoro           Kokoro 82M (Apache-2.0). Vozes: pf_dora (fem.), pm_alex, pm_santa (masc.). Leve e rápido.
  piper            Piper (vozes MIT). Vozes: pt_BR-faber-medium (padrão) e outras do rhasspy/piper-voices. Roda em qualquer CPU.
  edge             Vozes neurais da Microsoft via edge-tts (precisa de internet; sem licença comercial formal).
                   Vozes: pt-BR-FranciscaNeural, pt-BR-AntonioNeural, pt-BR-ThalitaMultilingualNeural.
  teste            Tom sintético, sem dependências. Só para testar o fluxo.

Cada motor é carregado uma vez por processo (cache em _MODELOS), então o modo local (voz.py) não recarrega
o modelo a cada frase.
"""
import os, subprocess, wave, struct, math, random

MOTORES = ["chatterbox", "chatterbox-ptbr", "kokoro", "piper", "edge", "teste"]
# ordem tentada em --motor auto (todas as frases saem do primeiro que funcionar: nunca mistura vozes)
AUTO = ["chatterbox", "kokoro", "piper", "edge"]
VOZ_PADRAO = {"kokoro": "pf_dora", "piper": "pt_BR-faber-medium", "edge": "pt-BR-FranciscaNeural"}
_MODELOS = {}


def dispositivo():
    try:
        import torch
        if torch.cuda.is_available(): return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available(): return "mps"
    except Exception:
        pass
    return "cpu"


def _salvar_wav(caminho, amostras, sr):
    """amostras: lista/array float -1..1 (mono)."""
    import numpy as np
    a = np.clip(np.asarray(amostras, dtype="float32").reshape(-1), -1, 1)
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(int(sr))
        w.writeframes((a * 32767).astype("<i2").tobytes())


# ---------------- Chatterbox ----------------
def _chatterbox(variante):
    chave = "cb-" + variante
    if chave in _MODELOS: return _MODELOS[chave]
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS as M
    dev = dispositivo()
    if dev == "cpu": torch.set_num_threads(os.cpu_count() or 4)
    real = "chatterbox"
    m = None
    if variante == "ptbr":
        try:
            from huggingface_hub import snapshot_download
            pasta = snapshot_download(os.environ.get("CB_PTBR_REPO", "ResembleAI/Chatterbox-Multilingual-pt-br"))
            m = M.from_local(pasta, dev); real = "chatterbox-ptbr"
        except Exception as e:  # repositório com outro formato ou sem rede: usa o base
            print(f"[aviso] chatterbox-ptbr não carregou ({type(e).__name__}: {e}); usando chatterbox base")
    if m is None:
        try:
            m = M.from_pretrained(device=dev, t3_model=os.environ.get("CB_T3", "v3"))
        except TypeError:  # versão antiga do pacote, sem t3_model
            m = M.from_pretrained(device=dev)
    _MODELOS[chave] = (m, real)
    return _MODELOS[chave]


def gerar_chatterbox(texto, semente, par, saida, variante="base", referencia=None):
    import torch, torchaudio as ta
    m, real = _chatterbox(variante)
    torch.manual_seed(semente)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(semente)
    kw = dict(language_id="pt",
              exaggeration=par.get("exaggeration", 0.55),
              cfg_weight=par.get("cfg_weight", 0.35),
              temperature=par.get("temperature", 0.8))
    if referencia and os.path.exists(referencia): kw["audio_prompt_path"] = referencia
    w = m.generate(texto, **kw)
    ta.save(saida, w.cpu(), m.sr)
    return real


# ---------------- Kokoro ----------------
def gerar_kokoro(texto, semente, par, saida, voz=None):
    import numpy as np
    if "kokoro" not in _MODELOS:
        from kokoro import KPipeline
        _MODELOS["kokoro"] = KPipeline(lang_code="p")  # p = português do Brasil
    pipe = _MODELOS["kokoro"]
    # Kokoro é determinístico: a semente varia levemente a velocidade para dar tomadas diferentes
    vel = par.get("speed", 0.95) * (1 + ((semente % 7) - 3) * 0.012)
    partes = [a for _, _, a in pipe(texto, voice=voz or VOZ_PADRAO["kokoro"], speed=vel)]
    audio = np.concatenate([np.asarray(p) for p in partes]) if partes else np.zeros(2400)
    _salvar_wav(saida, audio, 24000)
    return "kokoro"


# ---------------- Piper ----------------
def _baixar_piper(voz):
    """voz = pt_BR-faber-medium -> baixa .onnx e .onnx.json do rhasspy/piper-voices (com cache)."""
    pasta = os.environ.get("PIPER_DIR", os.path.expanduser("~/.cache/piper"))
    os.makedirs(pasta, exist_ok=True)
    onnx = os.path.join(pasta, voz + ".onnx")
    if os.path.exists(onnx) and os.path.exists(onnx + ".json"): return onnx
    lang, nome, qual = voz.split("-", 2)
    rel = f"{lang.split('_')[0]}/{lang}/{nome}/{qual}/{voz}.onnx"
    try:
        from huggingface_hub import hf_hub_download
        for suf in ("", ".json"):
            p = hf_hub_download("rhasspy/piper-voices", rel + suf)
            import shutil; shutil.copy(p, onnx + suf)
    except Exception:
        # piper1-gpl tem o próprio baixador
        subprocess.run(["python", "-m", "piper.download_voices", "--download-dir", pasta, voz], check=True)
    return onnx


def gerar_piper(texto, semente, par, saida, voz=None):
    voz = voz or VOZ_PADRAO["piper"]
    chave = "piper-" + voz
    if chave not in _MODELOS:
        from piper import PiperVoice
        _MODELOS[chave] = PiperVoice.load(_baixar_piper(voz))
    v = _MODELOS[chave]
    r = random.Random(semente)
    ruido = par.get("noise_scale", 0.667) * (0.9 + 0.2 * r.random())
    comp = par.get("length_scale", 1.05)
    with wave.open(saida, "wb") as wf:
        try:  # API nova (OHF-Voice/piper1-gpl)
            from piper import SynthesisConfig
            v.synthesize_wav(texto, wf, syn_config=SynthesisConfig(noise_scale=ruido, length_scale=comp,
                                                                   noise_w_scale=par.get("noise_w", 0.8)))
        except ImportError:  # API antiga (rhasspy/piper)
            v.synthesize(texto, wf, noise_scale=ruido, length_scale=comp, noise_w=par.get("noise_w", 0.8))
    return "piper"


# ---------------- edge-tts ----------------
def gerar_edge(texto, semente, par, saida, voz=None):
    import asyncio, edge_tts, tempfile
    taxas = {11: "+0%", 22: "-6%", 33: "+5%"}
    taxa = par.get("rate") or taxas.get(semente, "+0%")
    mp3 = tempfile.mktemp(suffix=".mp3")
    for tentativa in range(4):
        try:
            asyncio.run(edge_tts.Communicate(texto, voz or VOZ_PADRAO["edge"], rate=taxa).save(mp3)); break
        except Exception:
            if tentativa == 3: raise
            import time; time.sleep(3 * (tentativa + 1))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-ac", "1", "-ar", "24000", saida], check=True)
    os.remove(mp3)
    return "edge"


# ---------------- teste ----------------
def gerar_teste(texto, semente, par, saida, voz=None):
    """Sílabas sintéticas (~13 caracteres/s) com pausas em vírgulas. Serve só para testar o fluxo."""
    sr = 16000; r = random.Random(semente); a = []
    for ch in texto:
        if ch in ",.?!": a += [0.0] * int(sr * (0.25 if ch == "," else 0.1)); continue
        if ch == " ": a += [0.0] * int(sr * 0.02); continue
        f = 140 + 60 * math.sin(len(a) / sr * 2) + r.uniform(-15, 15); n = int(sr / 13)
        a += [0.4 * math.sin(2 * math.pi * f * i / sr) * math.sin(math.pi * i / n) for i in range(n)]
    _salvar_wav(saida, a, sr)
    return "teste"


def gerar(motor, texto, semente, par, saida, voz=None, referencia=None):
    """Gera uma tomada. Devolve o nome do motor que realmente gerou (útil quando há queda para outro)."""
    if motor == "chatterbox": return gerar_chatterbox(texto, semente, par, saida, "base", referencia)
    if motor == "chatterbox-ptbr": return gerar_chatterbox(texto, semente, par, saida, "ptbr", referencia)
    if motor == "kokoro": return gerar_kokoro(texto, semente, par, saida, voz)
    if motor == "piper": return gerar_piper(texto, semente, par, saida, voz)
    if motor == "edge": return gerar_edge(texto, semente, par, saida, voz)
    if motor == "teste": return gerar_teste(texto, semente, par, saida, voz)
    raise ValueError(f"motor desconhecido: {motor} (use um de {MOTORES})")
