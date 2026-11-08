B="https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
ls_(){ curl -sS --max-time 40 -A "Mozilla/5.0" "$1" | grep -oE 'href="[^"?/][^"]*"' | grep -v http; }
ls_ $B; for d in $(ls_ $B | grep '/"' | sed 's/href="//;s/"//'); do echo "-- $d"; curl -sS --max-time 40 -A "Mozilla/5.0" "$B$d" | grep -oE 'href="[^"?][^"]*"[^<]*<[^<]*<[^<]*' | grep -v http | sed 's/<[^>]*>/ /g' | head -30; done
