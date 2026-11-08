S=https://www.contaspublicasbrasil.com.br
curl -sS -A "WhatsApp/2.23" "$S/rankings/pessoal-mais" | grep -oE '<title>[^<]*|og:(title|description|image)" content="[^"]*|<head><script>[^<]*' 
for t in pessoal saude bebes; do curl -sS -o sonda/og_$t.png -w "$t %{http_code} %{content_type} %{size_download}\n" "$S/api/og?ranking=$t"; done
curl -sS -o /dev/null -w "cidade %{http_code}\n" "$S/cidade/2933307"
