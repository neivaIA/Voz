for t in $(seq 6800 6830) 6892 6893 6894 6895 9542 9543 9544; do r=$(curl -sS --max-time 30 -A "Mozilla/5.0" "https://apisidra.ibge.gov.br/desctabapi.aspx?c=$t" | python3 -c "
import sys,re,html
s=sys.stdin.read(); m=re.search(r'id=\"lblNomeTabela\"[^>]*>(.*?)</span>',s,re.S); print(html.unescape(re.sub('<[^>]+>','',m.group(1))).strip()[:160] if m else 'sem titulo '+str(len(s)))"); echo "$t | $r"; done
curl -sS --max-time 30 -A "Mozilla/5.0" "https://apisidra.ibge.gov.br/desctabapi.aspx?c=6805" | python3 -c "
import sys,re,html
s=sys.stdin.read(); t=re.sub(r'<[^>]+>',' ',s); t=re.sub(r'\s+',' ',html.unescape(t)); print(t[:3000])"
