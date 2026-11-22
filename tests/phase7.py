import json,re,time
from harness import H
from phase1 import GEN
from phase5 import JS_LIB, ok, R
STUB="window.claude={use:async n=>n=='downloads'?{save:async o=>{window.__dl=o;return {status:'saved'}}}:null}; 0"
def modal_ok(h,vals,wait=900):
    h.pg.wait_for_selector('#mp0',timeout=5000)
    for i,v in enumerate(vals): h.pg.fill(f'#mp{i}',v)
    h.pg.click('#mpok'); h.pg.wait_for_timeout(wait)
def feed(h,path):
    h.pg.set_input_files('input[onchange*="bkRestore"]',path); h.pg.wait_for_timeout(500)
with H() as h:
    h.login(); h.js(JS_LIB); h.js(STUB); h.js("go('entry')"); h.js(GEN,1000)
    h.js("""()=>{for(let i=0;i<50;i++)S.products[i].photo=mkImg(320,240,i+3,60).toDataURL('image/jpeg',.6);save()}""")
    n0=h.js("S.products.length"); admin_pw=h.js("S.users.admin.pw"); staff=h.js("JSON.stringify(S.staff)")
    # ---- backup (plain)
    h.js("go('set')"); h.pg.click('button:has-text("Download backup")'); modal_ok(h,[''])
    dl=h.js("window.__dl"); txt=dl['data']; o=json.loads(txt)
    ok('backup offered through downloads capability, .json file', dl['filename'].startswith('omsai-backup-') and dl['filename'].endswith('.json'), dl['filename'])
    ok('backup has all items + 50 photos', o['n']['products']==n0 and sum(1 for p in o['data']['products'] if p.get('photo','').startswith('data:image'))==50, o['n'])
    ok('backup excludes password hashes, MFA secrets and logins', 'pbkdf2' not in txt and 'users' not in o['data'] and 'mfa' not in txt)
    open('/tmp/bk_plain.json','w').write(txt)
    ok('backup size reasonable for 1000 items + 50 photos', len(txt)<3_000_000, f'{len(txt)//1024} KB')
    # ---- backup (encrypted)
    h.js("go('set')"); h.pg.click('button:has-text("Download backup")'); modal_ok(h,['pp-1234'])
    enc=h.js("window.__dl.data"); eo=json.loads(enc)
    ok('encrypted backup: AES-GCM envelope, no readable data', eo.get('enc')==1 and 'Lip Gloss' not in enc and 'products' not in enc)
    open('/tmp/bk_enc.json','w').write(enc)
    ok('last-backup time recorded', h.js("!!S.lastBk"))
    # ---- restore plain
    h.js("S.products=[];S.sales=[];save();go('set')"); ok('(wiped for restore test)', h.js("S.products.length")==0)
    feed(h,'/tmp/bk_plain.json'); modal_ok(h,['nope'],500)
    ok('restore needs the word RESTORE (wrong word does nothing)', h.js("S.products.length")==0 and h.pg.query_selector('#mp0') is not None)
    h.pg.fill('#mp0','RESTORE'); h.pg.click('#mpok'); h.pg.wait_for_timeout(1500)
    ok('restore brings back all items', h.js("S.products.length")==n0, h.js("S.products.length"))
    ok('restore brings back all 50 photos', h.js("S.products.filter(p=>p.photo&&p.photo.startsWith('data:image')).length")==50)
    ok('restore keeps this device passwords and staff logins unchanged', h.js("S.users.admin.pw")==admin_pw and h.js("JSON.stringify(S.staff)")==staff)
    h.pg.reload(); h.pg.wait_for_selector('#lr'); h.pg.fill('#lr','admin'); h.pg.fill('#lp',h.apw); h.click_login(900)
    ok('after reload: items + photos persisted', h.js("S.products.length")==n0 and h.js("S.products.filter(p=>p.photo&&p.photo.startsWith('data:image')).length")==50)
    h.inject()
    # ---- restore encrypted
    h.js(JS_LIB); h.js("S.products=[];save();go('set')")
    feed(h,'/tmp/bk_enc.json'); modal_ok(h,['wrong-pass'],700)
    ok('encrypted restore: wrong passphrase refused', h.js("S.products.length")==0 and 'Wrong passphrase' in h.alerts()[-1], h.alerts()[-1:])
    h.js("go('set')"); feed(h,'/tmp/bk_enc.json'); modal_ok(h,['pp-1234'],700); modal_ok(h,['RESTORE'],1500)
    ok('encrypted restore: right passphrase restores', h.js("S.products.length")==n0)
    # ---- hostile backup files
    def write(name,obj): open(name,'w').write(obj if isinstance(obj,str) else json.dumps(obj))
    good=json.load(open('/tmp/bk_plain.json'))['data']; p0=good['products'][0]
    bad_cases={
     'not JSON':'{{{ nope','wrong app':{'foo':1},'missing sales':{'omsai':1,'data':{'products':[]}},
     'damaged item':{'omsai':1,'data':{'products':[{'name':5,'code':'x'}],'sales':[]}},
     'NaN price':{'omsai':1,'data':{'products':[dict(p0,cp='abc')],'sales':[]}}}
    for k,v in bad_cases.items():
        write('/tmp/bad.json',v); a0=len(h.alerts()); h.js("go('set')"); feed(h,'/tmp/bad.json')
        ok(f'hostile backup rejected: {k}', len(h.alerts())>a0 and h.js("S.products.length")==n0, h.alerts()[-1:])
    evil={'omsai':1,'data':{'products':[dict(p0,photo='javascript:alert(1)',name='EVIL<img src=x onerror=window.__x=1>')],'sales':[],'logo':'data:image/svg+xml;base64,PHN2Zz48c2NyaXB0PmFsZXJ0KDEpPC9zY3JpcHQ+PC9zdmc+','__proto__':{'polluted':1},'constructor':{'prototype':{'p2':1}}}}
    write('/tmp/evil.json',json.dumps(evil).replace('"__proto__"','"__proto__"'))
    h.js("go('set')"); feed(h,'/tmp/evil.json'); modal_ok(h,['RESTORE'],1200)
    ok('hostile backup: javascript:/SVG images stripped', h.js("S.products[0].photo")=='' and h.js("S.logo")=='', h.js("[S.products[0].photo,S.logo]"))
    ok('hostile backup: no prototype pollution', h.js("({}).polluted===undefined&&({}).p2===undefined&&S.polluted===undefined"))
    ok('hostile backup: script in name is inert', h.js("window.__x")!=1 and '<' not in h.js("S.products[0].name"))
    # staff cannot back up / restore
    h.js("S.products.length"); a0=len(h.alerts()); h.js("me='staff'"); h.js("bkSave()"); h.js("bkRestore({files:[{}],value:''})"); h.js("me='admin'")
    ok('staff cannot back up or restore', len(h.alerts())-a0>=2, h.alerts()[-2:])
    print('errors',h.errs)
# ---- price-rise alerts
with H() as h:
    h.login(); h.js(JS_LIB); h.js("go('entry')"); h.js(GEN,1000); h.errs.clear()
    mk="""()=>{const [ty,tm,td]=T.split('-').map(Number);const back=n=>{let y=ty,m=tm,d=td;while(n-->0){d--;if(d<1){m--;if(m<1){m=12;y--}d=BD[y][m-1]}}return `${y}-${p2(m)}-${p2(d)}`};let k=0;
     const add=(name,cpp,days,sup)=>S.products.push({code:'ZA'+(k++),name,size:'',bn:k,cp:cpp*12,cpp,sp:cpp*2,packets:5,ppp:12,date:back(days),sold:0,dmg:0,sup});
     add('AlertA',10,200,'Ram');add('AlertA',10,120,'Ram');add('AlertA',10,60,'Ram');add('AlertA',12.5,5,'Ram');
     add('Stable',10,200,'Ram');add('Stable',10.2,60,'Ram');add('Stable',10,5,'Ram');
     add('CheapElsewhere',15,150,'Sita');add('CheapElsewhere',15,100,'Sita');add('CheapElsewhere',20,10,'Ram');
     add('Single',99,5,'Ram');
     add('OldSpike',500,700,'Ram');add('OldSpike',10,100,'Ram');add('OldSpike',10,5,'Ram');
     save();ALK='';return alerts().map(a=>a.n)}"""
    names=h.js(mk)
    ok('alert: item whose latest rate rose 25%', 'AlertA' in names, names[:6])
    ok('alert: cheaper supplier exists', 'CheapElsewhere' in names)
    ok('no alert: stable price', 'Stable' not in names)
    ok('no alert: only one purchase', 'Single' not in names)
    ok('no alert: spike older than 1 year is ignored', 'OldSpike' not in names)
    t=h.js("(()=>{ALK='';const a=performance.now();alerts();return performance.now()-a})()"); ok('alerts compute < 800 ms with 1000+ items', t<800, f'{t:.0f} ms')
    h.js("go('home')"); ok('home shows alert count card', 'price alerts' in h.js("$('m').innerText"), h.js("$('m').innerText")[:120])
    h.js("go('rh')"); txt=h.js("$('m').innerText")
    ok('Rate Compare shows alert card listing AlertA', 'Price alerts' in txt and 'AlertA' in txt)
    ok('item list marks alert items with ▲', h.js("[...document.querySelectorAll('#rhl div')].some(d=>d.innerText.includes('▲')&&d.innerText.includes('AlertA'))"))
    h.js("RHQ='AlertA';rateHist();rhPick(0)"); ok('detail shows price-alert banner with % and average', 'Price alert' in h.js("$('rhd').innerText") and '25' in h.js("$('rhd').innerText"), h.js("$('rhd').innerText")[:160])
    h.js("S.alertPct=30;save();RHQ='';rateHist()"); n30=h.js("alerts().map(a=>a.n)"); ok('threshold 30% hides the 25% rise', 'AlertA' not in n30 and 'CheapElsewhere' in n30, n30)
    h.js("S.alertPct=5;save();ALK=''"); 
    h.js("window.__said=[];say=function(x){window.__said.push(String(x))};0"); h.js("voiceDo('price alerts')"); s=h.js("window.__said")
    ok('voice: "price alerts" opens Rate Compare and speaks top alerts', h.js("tab")=='rh' and s and 'price alerts' in s[0] and 'AlertA' in s[0], s[:1])
    h.js("me='staff'"); a0=len(h.alerts()); h.js("voiceDo('price alerts')"); s2=h.js("window.__said")
    ok('voice: staff refused', 'Only admin' in s2[-1], s2[-1:]); h.js("me='admin'")
    print('errors',h.errs); ok('no page errors', not h.errs, h.errs[:2])
print(sum(1 for r in R if r[1]),'/',len(R),'passed'); json.dump(R,open('r7.json','w'),ensure_ascii=False)
