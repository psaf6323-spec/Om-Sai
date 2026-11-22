import os
INDEX=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','index.html'))
import json, time, sys
from playwright.sync_api import sync_playwright
HTMLS={}
def html(p):
    if p not in HTMLS: HTMLS[p]=open(p,encoding='utf8').read()
    return HTMLS[p]
QR="window.QRCode=function(el,o){el.innerHTML='<i data-qr></i>'};"
class H:
    def __init__(s,path=INDEX): s.path=path; s.apw='admin123'
    def __enter__(s):
        s.p=sync_playwright().start(); s.b=s.p.chromium.launch()
        s.ctx=s.b.new_context(viewport={'width':420,'height':900}); s.pg=s.ctx.new_page()
        s.errs=[]; s.dialogs=[]
        s.pg.on('pageerror',lambda e:s.errs.append(str(e)))
        s.pg.on('console',lambda m:m.type=='error' and s.errs.append('console:'+m.text))
        s.pg.on('dialog',lambda d:(s.dialogs.append(d.message),d.accept('1')))
        def route(r):
            u=r.request.url
            if 'qrcode' in u: r.fulfill(body=QR,content_type='application/javascript')
            elif u.startswith('https://app.test'): r.fulfill(body=html(s.path),content_type='text/html; charset=utf-8')
            else: r.abort()
        s.pg.route('**/*',route); s.pg.goto('https://app.test/'); s.pg.wait_for_selector('#lr',timeout=10000)
        s.pg.evaluate("window.__alerts=[];window.__toasts=[];window.alert=function(m){window.__alerts.push(String(m))};toast=function(m){window.__toasts.push(String(m))}")
        return s
    def __exit__(s,*a): s.b.close(); s.p.stop()
    def js(s,code,arg=None): return s.pg.evaluate(code,arg) if arg is not None else s.pg.evaluate(code)
    def inject(s): s.pg.evaluate("window.__alerts=[];window.__toasts=[];window.alert=function(m){window.__alerts.push(String(m))};toast=function(m){window.__toasts.push(String(m))};0")
    def alerts(s): return s.pg.evaluate('window.__alerts')
    def click_login(s,wait=700):
        s.pg.click('button:has-text("Login")'); s.pg.wait_for_timeout(wait)
    rec=None
    def save_rec(s):
        import re
        if s.pg.query_selector('#mp0') and not s.pg.query_selector('#mp1'):
            lab=s.pg.inner_text('#mp0 >> xpath=preceding-sibling::label')
            m=re.search(r'[A-Z2-9]{4}(?:-[A-Z2-9]{4}){3}',lab)
            if m:
                s.rec=m.group(0); s.pg.fill('#mp0','SAVED'); s.pg.click('#mpok'); s.pg.wait_for_timeout(400)
    def login(s,u='admin',pw=None):
        if pw is None: pw=s.apw if u=='admin' else 'x'
        s.pg.fill('#lr',u); s.pg.fill('#lp',pw); s.click_login()
        if s.pg.query_selector('#mp0') and s.pg.query_selector('#mp1'):
            s.pg.fill('#mp0','Admin#2026x'); s.pg.fill('#mp1','Admin#2026x'); s.pg.click('#mpok'); s.apw='Admin#2026x'; s.pg.wait_for_timeout(500); s.save_rec()
