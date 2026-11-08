A="https://apisidra.ibge.gov.br/values"
for q in "t/6805/n6/2927408/v/all/p/all" "t/6805/n6/2927408/v/all/p/all/c999/all" "t/6803/n6/2927408/v/all/p/all/c999/all" "t/6892/n6/2927408/v/all/p/all/c999/all" "t/6804/n6/2927408/v/all/p/all/c999/all" "t/6806/n6/2927408/v/all/p/all/c999/all"; do echo "== $q"; curl -sS --max-time 40 -A "Mozilla/5.0" "$A/$q" | head -c 1500; echo; done
