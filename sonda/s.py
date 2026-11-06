import urllib.request,zipfile,io,json
out={}
for et in ("anos_iniciais","anos_finais","ensino_medio"):
  for y in (2025,2023):
    for u in (f"https://download.inep.gov.br/ideb/resultados/divulgacao_{et}_municipios_{y}.zip",
              f"https://download.inep.gov.br/educacao_basica/portal_ideb/planilhas_para_download/{y}/divulgacao_{et}_municipios_{y}.zip"):
        try:
            b=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=120).read()
            z=zipfile.ZipFile(io.BytesIO(b)); out[u]=[len(b),z.namelist()]
            if y==2025:
                import openpyxl
                n=[x for x in z.namelist() if x.endswith(('.xlsx','.xls'))][0]
                wb=openpyxl.load_workbook(io.BytesIO(z.read(n)),read_only=True)
                ws=wb.active; rows=[[c for c in r] for _,r in zip(range(14),ws.iter_rows(values_only=True))]
                out[u].append([[str(c)[:40] for c in r] for r in rows])
            break
        except Exception as e: out[u]=repr(e)[:200]
json.dump(out,open("sonda/res.json","w"),ensure_ascii=False,indent=1)
