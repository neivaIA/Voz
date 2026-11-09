S=https://www.contaspublicasbrasil.com.br
for c in 2933307 3550308 5300108 1100015 4314902 2927408 9999999 abc; do curl -sS -o /dev/null -w "/cidade/$c %{http_code} %{time_total}s\n" "$S/cidade/$c"; done
for c in 2933307 5300108 9999999; do curl -sS -o /dev/null -w "/api/og?cod=$c %{http_code} %{time_total}s %{size_download}B\n" "$S/api/og?cod=$c"; done
for t in saude educacao fundeb pessoal ideb campanhas divida bebes saneamento contratos xyz; do curl -sS -o /dev/null -w "/rankings/$t %{http_code} %{time_total}s\n" "$S/rankings/$t"; curl -sS -o /dev/null -w "   og $t %{http_code} %{time_total}s %{size_download}B\n" "$S/api/og?ranking=$t"; done
curl -sS -o /dev/null -w "/api/og %{http_code} %{time_total}s\n" "$S/api/og"
curl -sS -X POST -o b.out -w "POST /api/acessos %{http_code} %{time_total}s\n" "$S/api/acessos"; head -c 200 b.out; echo
curl -sS -o b.out -w "GET /api/acessos %{http_code}\n" "$S/api/acessos"; head -c 200 b.out; echo
for u in /sitemap.xml /robots.txt /favicon.ico /manifest.json /nao-existe; do curl -sS -o /dev/null -w "$u %{http_code}\n" "$S$u"; done
