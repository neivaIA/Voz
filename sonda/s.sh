sleep 30
pip install -q playwright >/dev/null 2>&1 && python -m playwright install --with-deps chromium >/dev/null 2>&1
cat > c.py <<'P'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={"width":390,"height":844},accept_downloads=True)
    for c in ("2933307","1720002"):
        pg=ctx.new_page();pg.goto("https://www.contaspublicasbrasil.com.br/#cidade-"+c);pg.wait_for_timeout(6000)
        with pg.expect_download() as dw: pg.click("#cdImagem")
        dw.value.save_as(f"sonda/card_{c}.png");print("ok",c)
    b.close()
P
python c.py
