#!/usr/bin/env bash
# Instala um motor de voz num ambiente virtual (Linux, Mac, Colab e o próprio GitHub Actions).
# Uso: bash scripts/instalar.sh MOTOR [PASTA_VENV]
#   MOTOR: chatterbox | chatterbox-ptbr | kokoro | piper | edge | todos
#   PASTA_VENV: padrão ~/venv ("-" usa o Python atual, sem venv; útil no Colab)
set -euo pipefail
MOTOR="${1:-chatterbox}"; VENV="${2:-$HOME/venv}"
AQUI="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$VENV" = "-" ]; then PY=python3; else
  [ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"; PY="$VENV/bin/python"; fi
PIP="$PY -m pip install -q --retries 10 --timeout 60"

# espeak-ng: Kokoro e Piper usam para fonemizar o português
if [[ "$MOTOR" =~ ^(kokoro|piper|todos)$ ]] && ! command -v espeak-ng >/dev/null 2>&1; then
  if command -v apt-get >/dev/null; then
    SUDO=""; if [ "$(id -u)" != "0" ] && sudo -n true 2>/dev/null; then SUDO=sudo; fi
    { $SUDO apt-get -qq update && $SUDO apt-get -qq install -y espeak-ng >/dev/null; } || echo "[aviso] instale o espeak-ng"
  elif command -v brew >/dev/null; then brew install espeak-ng; else echo "[aviso] instale o espeak-ng manualmente"; fi
fi
command -v ffmpeg >/dev/null || echo "[aviso] o motor edge precisa do ffmpeg no PATH"

$PIP --upgrade pip
$PIP -r "$AQUI/requisitos/base.txt"
instala() {
  case "$1" in
    chatterbox|chatterbox-ptbr)
      if ! $PY -c "import torch" 2>/dev/null; then
        if command -v nvidia-smi >/dev/null 2>&1; then $PIP torch torchaudio
        else $PIP torch torchaudio --index-url https://download.pytorch.org/whl/cpu; fi
      fi
      $PIP -r "$AQUI/requisitos/chatterbox.txt" ;;
    kokoro) $PIP -r "$AQUI/requisitos/kokoro.txt" ;;
    piper)  $PIP -r "$AQUI/requisitos/piper.txt" ;;
    edge)   $PIP -r "$AQUI/requisitos/edge.txt" ;;
    *) echo "motor desconhecido: $1"; exit 2 ;;
  esac
}
if [ "$MOTOR" = "todos" ]; then for m in chatterbox kokoro piper edge; do instala $m || echo "[aviso] $m não instalou"; done
else instala "$MOTOR"; fi
echo "pronto: $MOTOR em $([ "$VENV" = "-" ] && echo 'Python atual' || echo "$VENV")"
