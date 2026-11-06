# Voz

Gera narração em português para os vídeos explicativos (Chatterbox Multilingual, licença MIT), já conferida automaticamente.

**Como usar**
1. Crie ou edite `pedidos/<tema>.json`: `tema`, `frases` (`id`, `fala`, `leg`, `fim`), `sementes` (padrão 11, 22 e 33) e, opcionalmente, `vocabulario` (ajuda o transcritor com nomes próprios), `params` e `refazer` (lista de ids para gerar de novo só essas frases).
2. Faça o push em `main`. O workflow `narrar` cria uma tarefa por frase e semente, em paralelo.
3. O resultado sai no ramo `saida-<tema>`: um WAV por tomada e um JSON com a conferência (transcrição, erro de palavras, ritmo, pausas e entonação).

As bibliotecas e os modelos ficam no cache do GitHub Actions (chave `CHAVE_CACHE`): só a primeira execução instala tudo.
