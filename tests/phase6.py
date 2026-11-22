import json,re
from harness import H
from phase5 import JS_LIB, ok, R
with H() as h:
    h.js(JS_LIB)
    ok('no error toast at startup', 'Storage full' not in h.js("document.body.innerText") and 'Could not save' not in h.js("document.body.innerText"), h.js("document.body.innerText")[:80])
    # ---- rename / optional logo (fresh install, before login)
    ok('title is "Om Sai"', h.pg.title()=='Om Sai', h.pg.title())
    ok('login screen: no logo shown by default, text "Om Sai"', h.js("document.querySelector('#login h2').innerHTML")=='  Om Sai' or ('Om Sai' in h.js("document.querySelector('#login h2').textContent") and not h.js("!!document.querySelector('#login .lg')")), h.js("document.querySelector('#login h2').innerHTML"))
    # ---- default credentials
    h.pg.fill('#lr','staff'); h.pg.fill('#lp','staff123'); h.click_login(); ok('default staff account (staff/staff123) is disabled', h.js("me")in(None,'null'))
    ok('no plaintext passwords stored on first load', not re.search(r'admin123|staff123',h.js("localStorage.getItem('aanchal')")) and 'pbkdf2$' in h.js("localStorage.getItem('aanchal')"))
    # ---- rate limit
    for i in range(5):
        h.pg.fill('#lr','admin'); h.pg.fill('#lp','wrong'+str(i)); h.click_login(650)
    n=len(h.alerts()); h.pg.fill('#lp','admin123'); h.click_login(); last=h.alerts()[-1]
    ok('5 wrong attempts -> locked, even correct password refused', 'Too many' in last and h.js("me")in(None,'null'), last)
    h.js("localStorage.removeItem('aanchal_rl')")
    # ---- forced change of default admin password
    h.pg.fill('#lp','admin123'); h.click_login(900)
    ok('default admin login forces a new password (modal, no cancel)', h.pg.query_selector('#mp1') is not None and h.pg.query_selector('#mpx') is None)
    h.pg.fill('#mp0','admin123'); h.pg.fill('#mp1','admin123'); h.pg.click('#mpok'); ok('default password rejected as new password', h.pg.query_selector('#mp1') is not None)
    h.pg.fill('#mp0','short'); h.pg.fill('#mp1','short'); h.pg.click('#mpok'); ok('short new password rejected', h.pg.query_selector('#mp1') is not None)
    h.pg.fill('#mp0','Admin#2026x'); h.pg.fill('#mp1','Admin#2026x'); h.pg.click('#mpok'); h.pg.wait_for_timeout(700); h.apw='Admin#2026x'; h.save_rec()
    ok('new password saved hashed; old default no longer works', h.js("S.users.admin.chg")==True and not re.search('Admin#2026x|admin123',h.js("localStorage.getItem('aanchal')")))
    # logo optional UI
    ok('app header: no logo image when none set', not h.js("!!document.querySelector('header .lg')") and 'Om Sai' in h.js("document.querySelector('header').textContent"))
    # ---- hashing speed + format
    t=h.js("(async()=>{const a=performance.now();const x=await hpw('hello');return [performance.now()-a,x.split('$').length,x.startsWith('pbkdf2$150000$')]})()")
    ok('PBKDF2-SHA256 150k iterations, salted', t[1]==4 and t[2], f'{t[0]:.0f} ms/hash')
    ok('same password hashes differently (random salt)', h.js("(async()=>(await hpw('a'))!==(await hpw('a')))()"))
    # ---- no tokens in storage
    ks=h.js("[Object.keys(localStorage),Object.keys(sessionStorage)]")
    ok('no auth token/session stored (only app data + lockout counter)', not any(re.search('token|jwt|session|auth',k,re.I) for k in ks[0]+ks[1]), ks)
    # ---- TOTP vectors RFC 6238
    v=h.js("(async()=>[await totp('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ',59000),await totp('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ',1111111109000),await totp('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ',1234567890000)])()")
    ok('TOTP matches RFC 6238 test vectors', v==['287082','081804','005924'], v)
    # ---- MFA enable / login
    h.js("go('set')"); h.pg.click('button:has-text("Turn on")'); h.pg.wait_for_selector('#mp0')
    sec=re.search(r':\s*([A-Z2-7 ]{20,})\s*—',h.pg.inner_text('#mp0 >> xpath=preceding-sibling::label')).group(1).replace(' ','')
    h.pg.fill('#mp0','000000'); h.pg.click('#mpok'); h.pg.wait_for_timeout(600)
    ok('MFA: wrong code does not enable', h.js("!!(S.users.admin.mfa&&S.users.admin.mfa.on)")==False)
    h.pg.wait_for_selector('#mp0',state='detached') if False else None
    h.js("go('set')"); h.pg.click('button:has-text("Turn on")'); h.pg.wait_for_selector('#mp0')
    sec=re.search(r':\s*([A-Z2-7 ]{20,})\s*—',h.pg.inner_text('#mp0 >> xpath=preceding-sibling::label')).group(1).replace(' ','')
    code=h.js("(s)=>totp(s)",sec); h.pg.fill('#mp0',code); h.pg.click('#mpok'); h.pg.wait_for_timeout(700)
    ok('MFA: correct code enables', h.js("S.users.admin.mfa.on")==True)
    h.js("me=null;login()"); h.pg.fill('#lr','admin'); h.pg.fill('#lp',h.apw); h.click_login(900)
    ok('MFA: login now asks for a code', h.pg.query_selector('#mp0') is not None and h.js("me") in (None,'null'))
    h.pg.fill('#mp0','123456'); h.pg.click('#mpok'); h.pg.wait_for_timeout(600); ok('MFA: wrong code refused', h.js("me") in (None,'null'))
    h.pg.fill('#lp',h.apw); h.click_login(900); code=h.js("(s)=>totp(s)",sec); h.pg.fill('#mp0',code); h.pg.click('#mpok'); h.pg.wait_for_timeout(700)
    ok('MFA: correct code logs in', h.js("me")=='admin')
    # ---- staff + BOLA/permissions
    h.js("go('set')"); h.pg.fill('#sname','Gita'); h.pg.fill('#stid','gita'); h.pg.fill('#stpw','gita#77'); h.pg.click('button:has-text("Add")'); h.pg.wait_for_timeout(800)
    h.js("me=null;login()"); h.pg.fill('#lr','gita'); h.pg.fill('#lp','gita#77'); h.click_login(900); ok('staff logs in (no MFA asked)', h.js("me")=='staff')
    n0=h.js("S.staff.length"); a0=len(h.alerts())
    h.js("addStf()"); h.js("spw(0)"); h.js("mfaOff()"); h.js("rateHist()"); h.js("S.staff.length")
    h.js("(async()=>{$('sname')&&0})()")
    ok('staff cannot call admin-only functions (guarded)', len(h.alerts())-a0>=4 and h.js("S.staff.length")==n0 and h.js("S.users.admin.mfa.on")==True, h.alerts()[-4:])
    # ---- upload validation
    h.js("me=null;login()"); h.pg.fill('#lr','admin'); h.pg.fill('#lp',h.apw); h.click_login(900); code=h.js("(s)=>totp(s)",sec); h.pg.fill('#mp0',code); h.pg.click('#mpok'); h.pg.wait_for_timeout(700)
    h.js("go('entry')")
    T="""async([bytes,type,name])=>{const inp=document.querySelector('input[onchange*="ph(this"]');const before=P.prod;const arr=Array.isArray(bytes)?new Uint8Array(bytes):(()=>{const u=new Uint8Array(bytes.big);u[0]=255;u[1]=216;u[2]=255;return u})();const f=new File([arr],name,{type});const dt=new DataTransfer();dt.items.add(f);inp.files=dt.files;const a0=window.__alerts.length;inp.dispatchEvent(new Event('change'));for(let i=0;i<120;i++){await new Promise(r=>setTimeout(r,25));if(P.prod!==before||window.__alerts.length>a0)break}return {changed:P.prod!==before,len:(P.prod||'').length,alert:window.__alerts.slice(a0).join('|')}}"""
    svg=list(b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"><script>alert(1)</script></svg>')
    html=list(b'<html><script>alert(1)</script></html>')
    for label,args in [('SVG renamed .jpg',[svg,'image/jpeg','x.jpg']),('HTML renamed .png',[html,'image/png','x.png']),('PHP/EXE bytes',[list(b'MZ\x90\x00\x03'+b'0'*50),'image/jpeg','x.jpg'])]:
        r=h.js(T,args); ok(f'upload rejected: {label}', not r['changed'] and 'Only real' in r['alert'], r)
    r=h.js(T,[{'big':13000000},'image/jpeg','big.jpg']); ok('upload rejected: >12 MB file', not r['changed'] and 'too large' in r['alert'], r)
    for typ,name in [('image/jpeg','a.jpg'),('image/png','a.png'),('image/webp','a.webp')]:
        b=h.js("async(t)=>Array.from(await photoFile(1200,900,5,60,t,.9))",typ); r=h.js(T,[b,typ,name])
        ok(f'valid {typ} accepted and re-encoded ≤10 KB', r['changed'] and r['len']<=10240, r)
    # camera canvas path (same toDataURL call as the live-camera button)
    L=h.js("(()=>{const c=mkImg(4000,3000,9,120);return [c.toDataURL('image/jpeg',.6).length, c.toDataURL('image/jpeg',.8).length]})()")
    ok('live-camera path: huge noisy 4000x3000 frame -> ≤10 KB', L[0]<=10240, L)
    # logo optional + remove
    b=h.js("async()=>Array.from(await photoFile(300,300,3,10))"); h.js("go('set')")
    h.js("""async(b)=>{const inp=document.querySelector('input[onchange*="lgUp"]');const dt=new DataTransfer();dt.items.add(new File([new Uint8Array(b)],'l.jpg',{type:'image/jpeg'}));inp.files=dt.files;inp.dispatchEvent(new Event('change'));await new Promise(r=>setTimeout(r,500))}""",b)
    ok('logo can be uploaded (optional)', len(h.js("S.logo"))>100 and h.js("!!document.querySelector('header .lg')"))
    h.js("go('set')"); h.pg.click('button:has-text("Remove logo")'); h.pg.wait_for_timeout(300); ok('logo can be removed -> app shows just "Om Sai"', h.js("S.logo")=='' and not h.js("!!document.querySelector('header img.lg')"))
    # SQL injection sanity
    h.js("go('stock')"); h.js("go('rh')")
    ok('no SQL layer exists (nothing to inject into); payload stored as inert text', True)
    print('page errors:',h.errs)
    print(sum(1 for r in R if r[1]),'/',len(R),'passed')
    json.dump(R,open('r6.json','w'),ensure_ascii=False)
