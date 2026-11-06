B=https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas
for f in prestacao_de_contas_eleitorais_candidatos_2024.zip prestacao_de_contas_eleitorais_orgaos_partidarios_2024.zip; do
  curl -sSI $B/$f | grep -iE "^HTTP|content-length|last-modified"
done
curl -sS -o pc.zip $B/prestacao_de_contas_eleitorais_candidatos_2024.zip && unzip -l pc.zip | head -80
for p in receitas_candidatos_2024_BA despesas_contratadas_candidatos_2024_BA despesas_pagas_candidatos_2024_BA receitas_candidatos_doador_originario_2024_BA; do
  n=$(unzip -l pc.zip | grep -o "$p.csv" | head -1); [ -n "$n" ] && { echo "== $n"; unzip -p pc.zip "$n" | iconv -f latin1 -t utf8 | head -3; unzip -p pc.zip "$n" | wc -l; }
done
