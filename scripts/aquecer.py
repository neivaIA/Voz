"""Baixa e testa um motor (e o transcritor) com uma frase curta. Usado no cache do GitHub e para conferir uma instalação.

Uso: python scripts/aquecer.py MOTOR [VOZ]
"""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from motores import gerar
from conferir import conferir

motor = sys.argv[1] if len(sys.argv) > 1 else "chatterbox"
voz = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
wav = os.path.join(tempfile.gettempdir(), "aquecer.wav")
frase = {"id": "t", "fala": "Olá, este é um teste rápido da voz em português."}
real = gerar(motor, frase["fala"], 11, {}, wav, voz=voz)
print(conferir(wav, frase, 11, motor=real))
