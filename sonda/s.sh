S=https://www.contaspublicasbrasil.com.br
for u in "/api/tse?e=6258&uf=br" "/api/tse?e=6257&uf=br" "/api/og?ranking=pessoal"; do curl -sS -o b.out -w "$u %{http_code} %{size_download}B %{time_total}s\n" -D h.txt "$S$u"; grep -iE "^(cache-control|content-type)" h.txt | tr -d '\r' | sed 's/^/   /'; head -c 400 b.out | tr -d '\0' | strings | head -3; echo; done
