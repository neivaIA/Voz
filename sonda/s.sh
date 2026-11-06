curl -sS http://secure.globalsign.com/cacert/rnpicpedugr46ovtlsca2025.crt -o inter.der && openssl x509 -inform der -in inter.der -out inter.pem && cat /etc/ssl/certs/ca-certificates.crt inter.pem > bundle.pem
openssl x509 -in inter.pem -noout -subject -issuer
for et in anos_iniciais anos_finais ensino_medio; do
  curl -sS --cacert bundle.pem -A Mozilla/5.0 -o $et.zip https://download.inep.gov.br/ideb/resultados/divulgacao_${et}_municipios_2025.zip && echo "ok $et" && unzip -l $et.zip
done
pip install -q openpyxl
python3 - <<'P'
import zipfile,openpyxl,io
for et in ("anos_iniciais","anos_finais","ensino_medio"):
    z=zipfile.ZipFile(et+".zip"); n=[x for x in z.namelist() if x.endswith("xlsx")][0]
    wb=openpyxl.load_workbook(io.BytesIO(z.read(n)),read_only=True); ws=wb.active
    print("==",et,n,wb.sheetnames,ws.max_row,ws.max_column)
    for i,r in enumerate(ws.iter_rows(values_only=True)):
        if i<12 or (i<4000 and r and r[1]=="BA" and "Conquista" in str(r[3])): print(i,[str(c)[:30] for c in r])
P
