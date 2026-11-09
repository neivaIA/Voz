S=https://www.contaspublicasbrasil.com.br
sleep 45
echo "tabs: $(curl -sS $S/tabs.js | grep -c intro-mais)"
curl -sS "$S/api/tse?e=6258&uf=br" | tr -d ' \n' | grep -oE '"(pst|tf|psa)":"[^"]*"' | head -5
for u in / /cidade/2933307 /rankings/bebes-tmi; do curl -sS -o /dev/null -w "$u %{http_code}\n" "$S$u"; done
