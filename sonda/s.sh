S=https://www.contaspublicasbrasil.com.br
sleep 60
for u in / /rankings.js /cidade.js /data/rankings-t/saude.json /data/arrecadacao/uf/BA.json /data/rankings.json /cidade/2933307 /rankings/pessoal-mais "/api/og?ranking=bebes"; do
  curl -sS -o /dev/null -H "Accept-Encoding: br, gzip" -w "$u %{http_code} %{size_download}B %{time_total}s\n" -D h.txt "$S$u"; grep -iE "^(cache-control|content-encoding|x-vercel-cache)" h.txt | tr -d '\r' | sed 's/^/   /'
done
curl -sS "$S/rankings.js" | grep -c "rankings-t"
