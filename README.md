# Voz

Gera narração em português para os vídeos explicativos, já conferida automaticamente (transcrição, palavras-chave, ritmo, pausas e entonação). Tudo gratuito.

## Motores de voz

| motor | qualidade | velocidade | licença | vozes |
|---|---|---|---|---|
| `chatterbox` (padrão) | a mais expressiva | lento em CPU, rápido em GPU | MIT | voz padrão ou clone de uma referência autorizada |
| `chatterbox-ptbr` | igual, ajustado para o português do Brasil | igual | MIT | idem (cai para o `chatterbox` se não carregar) |
| `kokoro` | natural, menos emoção | rápido em CPU | Apache-2.0 | `pf_dora` (fem.), `pm_alex`, `pm_santa` (masc.) |
| `piper` | mais "certinha" | muito rápido, qualquer PC | vozes MIT | `pt_BR-faber-medium` e outras do rhasspy/piper-voices |
| `edge` | muito natural | rápido, precisa de internet | sem licença comercial formal | `pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, `pt-BR-ThalitaMultilingualNeural` |

Um vídeo usa **um motor só**: as frases nunca misturam vozes.

## Pedido

`pedidos/<tema>.json`:

```json
{"tema": "docinhos",
 "motor": "chatterbox",
 "voz": "",
 "modo": "",
 "sementes": [11, 22],
 "vocabulario": "nomes próprios para ajudar o transcritor",
 "params": {"exaggeration": 0.55, "cfg_weight": 0.35, "temperature": 0.8},
 "refazer": ["n4"],
 "frases": [{"id": "n1", "fala": "...", "leg": "...", "fim": "pergunta", "chaves": ["Jaci"]}]}
```

- `motor` (opcional): padrão `chatterbox`. `voz`: voz do motor (vazio = padrão).
- `modo: "rapido"`: o pedido roda numa máquina só (workflow `narrar-rapido`) em vez da matriz.
- `refazer`: gera de novo só essas frases; as tomadas antigas continuam no ramo.
- Parâmetros por motor em `params`: Chatterbox `exaggeration`, `cfg_weight`, `temperature`; Kokoro `speed`; Piper `length_scale`, `noise_scale`; edge `rate` (ex.: `"-5%"`).

## Três jeitos de gerar (se um travar, use o próximo)

### 1. GitHub Actions, em paralelo (`narrar`)
Push do pedido em `main`. Cada frase × semente vira uma tarefa (até 20 juntas, ~4 min). Resultado no ramo `saida-<tema>` (chatterbox) ou `saida-<tema>-<motor>`.
Para outro motor sem editar o pedido: **Actions → narrar → Run workflow** e preencha `motor`.

### 2. GitHub Actions, numa máquina só (`narrar-rapido`)
**Actions → narrar-rapido → Run workflow** (pedido, motor, voz). Com `kokoro`, `piper` ou `edge` sai em poucos minutos. Publica no mesmo esquema de ramos.

### 3. Fora do GitHub: Colab ou seu PC (não depende da fila do GitHub)
- **Google Colab (GPU grátis):** abra `Voz_no_Colab.ipynb` no Colab (colab.research.google.com → GitHub → `neivaIA/Voz`), escolha o motor e rode as células. No fim, baixe o `.zip` ou publique no ramo `saida-…` com um token.
- **Windows:** instale o Python 3.11 e o ffmpeg; rode `instalar_windows.bat kokoro pedidos\docinhos.json` (Kokoro e Piper precisam do espeak-ng).
- **Linux/Mac:** `bash scripts/instalar.sh kokoro` e depois `~/venv/bin/python voz.py pedidos/docinhos.json --motor kokoro --zip`.

`voz.py` escreve um WAV e um JSON por tomada, `escolha.json` (a melhor tomada de cada frase) e `resumo.md`. Com `--motor auto` ele tenta chatterbox → kokoro → piper → edge e usa o primeiro que funcionar.

## Robustez
- Todas as tarefas têm tempo-limite (nada fica girando para sempre) e a geração tenta 3 vezes.
- Instalação e downloads de modelos tentam de novo com espera crescente; o cache é separado por motor (`venv-<motor>-v2-py311`).
- Se a **fila do próprio GitHub** travar (execução "queued" sem começar, ou "startup failure"), nenhum workflow consegue rodar: use o Colab ou o PC (opção 3).

## Arquivos
- `motores.py`: os motores. `conferir.py`: a conferência e a escolha da melhor tomada.
- `gerar.py`: uma tomada (usado pela matriz). `voz.py`: o pedido inteiro (local, Colab e `narrar-rapido`).
- `scripts/instalar.sh`, `instalar_windows.bat`, `scripts/aquecer.py` (baixa e testa um motor).
- `requisitos/`: dependências por motor.
