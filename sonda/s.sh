set -x
H=download.inep.gov.br
echo | openssl s_client -connect $H:443 -servername $H -showcerts 2>/dev/null | grep -E "s:|i:|CA Issuers" | head
echo | openssl s_client -connect $H:443 -servername $H 2>/dev/null | openssl x509 -noout -text | grep -A2 "Authority Information" 
for u in https://download.inep.gov.br/ideb/resultados/divulgacao_anos_iniciais_municipios_2025.zip https://download.inep.gov.br/ideb/resultados/divulgacao_anos_iniciais_municipios_2023.zip; do
  curl -sS -o /dev/null -w "%{http_code} %{size_download}\n" -A Mozilla/5.0 "$u"
  curl -sSk -o /dev/null -w "insecure %{http_code} %{size_download}\n" -A Mozilla/5.0 "$u"
done
curl -sSL -A Mozilla/5.0 https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados | grep -oE 'https?://[^"]+\.(zip|xlsx)' | sort -u | head -40
