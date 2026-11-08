B="https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios"
curl -sS --max-time 120 -A "Mozilla/5.0" -o dic.xlsx "$B/dicionario_de_dados_agregados_por_setores_censitarios_20260520.xlsx"
python -m pip install -q openpyxl 2>&1|tail -1
python - <<'P'
import openpyxl
wb=openpyxl.load_workbook("dic.xlsx",read_only=True)
print(wb.sheetnames)
for ws in wb.worksheets:
  for r in ws.iter_rows(values_only=True):
    s=" | ".join(str(x) for x in r if x is not None)
    l=s.lower()
    if any(k in l for k in ["abastecimento","esgot","lixo","rede geral","banheiro"]) : print(ws.title,"::",s[:260])
P
for f in caracteristicas_domicilio1_BR_20261021 caracteristicas_domicilio2_BR_20250417 caracteristicas_domicilio3_BR_20250417; do
 curl -sS --max-time 300 -A "Mozilla/5.0" -o $f.zip "$B/Agregados_por_Municipio_csv/Agregados_por_municipios_$f.zip"; ls -la $f.zip; unzip -l $f.zip | tail -3
 unzip -p $f.zip | head -c 1500 | head -3 | cut -c1-900
 unzip -p $f.zip | grep -m1 "2927408" | cut -c1-900
done
