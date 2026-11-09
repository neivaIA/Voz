S=https://www.contaspublicasbrasil.com.br
sleep 45
for u in / /cidade.js /tabs.js /rankings.js /data/rankings-t/bebes.json /data/arrecadacao/uf/SP.json /cidade/3550308 /rankings/saude-menos "/api/og?ranking=saude" "/api/og?cod=2933307"; do curl -sS -o /dev/null -w "$u %{http_code} %{size_download}B\n" -H "Accept-Encoding: br" "$S$u"; done
echo "sumario: $(curl -sS $S/cidade.js | grep -c 'function sumario')  tabs: $(curl -sS $S/tabs.js | grep -c tem-dir)"
