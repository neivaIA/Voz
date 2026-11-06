curl -sS http://secure.globalsign.com/cacert/rnpicpedugr46ovtlsca2025.crt -o inter.der && openssl x509 -inform der -in inter.der -out inter.pem && cat /etc/ssl/certs/ca-certificates.crt inter.pem > bundle.pem
mkdir -p sonda/x
for et in anos_iniciais anos_finais ensino_medio; do
  curl -sS --retry 6 --retry-all-errors --retry-delay 15 --connect-timeout 40 --cacert bundle.pem -A Mozilla/5.0 -o $et.zip https://download.inep.gov.br/ideb/resultados/divulgacao_${et}_municipios_2025.zip && unzip -o -j $et.zip '*.xlsx' -d sonda/x
done
ls -la sonda/x
