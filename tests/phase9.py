"""PWA + data-persistence checks against the real Node server (service worker, manifest, offline open, data survives reload)."""
import subprocess, time, json, os, sys, urllib.request
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,'..'); PORT=8097; URL=f'http://127.0.0.1:{PORT}/'
R=[]
def ok(n,c,i=''): R.append(bool(c)); print(('PASS ' if c else 'FAIL ')+n+('' if c else ' | '+str(i)[:200]))
srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':str(PORT)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(40):
        try: urllib.request.urlopen(URL); break
        except Exception: time.sleep(.15)
    man=json.load(urllib.request.urlopen(URL+'manifest.webmanifest'))
    ok('manifest valid (name, standalone, 192+512 icons)', man['short_name']=='Om Sai' and man['display']=='standalone' and {i['sizes'] for i in man['icons']}=={'192x192','512x512'})
    ok('icons are served as PNG', all(urllib.request.urlopen(URL+i['src']).headers['Content-Type']=='image/png' for i in man['icons']))
    ok('sw.js served as JavaScript', 'javascript' in urllib.request.urlopen(URL+'sw.js').headers['Content-Type'])
    for bad in ('server.js','package.json','tests/phase1.py'):
        try: urllib.request.urlopen(URL+bad); ok('private file not served: '+bad,False)
        except Exception: ok('private file not served: '+bad,True)
    with sync_playwright() as p:
        b=p.chromium.launch(); ctx=b.new_context(viewport={'width':420,'height':900}); pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        ctx.route('**/qrcode*',lambda r:r.fulfill(body="window.QRCode=function(el){el.innerHTML='<i></i>'};",content_type='application/javascript'))
        ctx.route('**/*cdnjs*',lambda r:r.fulfill(body="window.QRCode=function(el){el.innerHTML='<i></i>'};",content_type='application/javascript'))
        pg.goto(URL); pg.wait_for_selector('#lr',timeout=10000)
        ok('page links the manifest', pg.get_attribute('link[rel=manifest]','href')=='manifest.webmanifest')
        pg.wait_for_function("navigator.serviceWorker.ready.then(()=>true)",timeout=10000)
        pg.reload(); pg.wait_for_selector('#lr'); ok('service worker controls the page', pg.evaluate("!!navigator.serviceWorker.controller"))
        # login, forced pw, recovery modal
        pg.fill('#lr','admin'); pg.fill('#lp','admin123'); pg.click('button:has-text("Login")'); pg.wait_for_selector('#mp1')
        pg.fill('#mp0','Shop#Pass2030'); pg.fill('#mp1','Shop#Pass2030'); pg.click('#mpok'); pg.wait_for_selector('#mp0'); pg.wait_for_timeout(300)
        pg.fill('#mp0','SAVED'); pg.click('#mpok'); pg.wait_for_timeout(400)
        pg.evaluate("go('entry')")
        pg.evaluate("(()=>{$('n').value='Rose Lip Gloss';$('pp').value=12;$('q').value=5;$('cp').value=480;$('cpp').value=40;$('sp').value=60;$('sn').value='Ram Traders';addP()})()")
        ok('item saved', pg.evaluate("S.products.some(p=>p.name=='Rose Lip Gloss')"))
        pg.evaluate("go('set')"); pg.wait_for_selector('#appcard h3'); pg.wait_for_timeout(300)
        ok('Settings shows "App & data safety" with storage status', 'MB' in pg.inner_text('#appcard') and ('Saved data' in pg.inner_text('#appcard') or 'may clear' in pg.inner_text('#appcard')), pg.inner_text('#appcard')[:120])
        # offline reopen + data survives reload
        ctx.set_offline(True); pg.reload(); pg.wait_for_selector('#lr',timeout=10000)
        ok('app opens with NO internet (served by the service worker)', pg.evaluate("!!document.querySelector('#lr')"))
        pg.fill('#lr','admin'); pg.fill('#lp','Shop#Pass2030'); pg.click('button:has-text("Login")'); pg.wait_for_timeout(1200)
        ok('data survives reload and works offline', pg.evaluate("me=='admin'&&S.products.some(p=>p.name=='Rose Lip Gloss')"))
        ctx.set_offline(False); print('page errors:',errs); b.close()
finally:
    srv.terminate()
print(sum(R),'/',len(R),'passed')
