S=https://www.contaspublicasbrasil.com.br
sleep 40
echo "rankings: $(curl -sS $S/rankings.js | grep -c aiRecente) css: $(curl -sS $S/ | grep -c pointer:coarse)"
for u in / /cidade/2933307 /rankings/pessoal-mais /sitemap.xml /robots.txt /favicon.ico; do curl -sS -o /dev/null -w "$u %{http_code}\n" "$S$u"; done
