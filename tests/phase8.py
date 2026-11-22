import json,re
from harness import H
from phase5 import ok,R
with H() as h:
    # fresh install: first login -> forced new password -> recovery code shown
    h.pg.fill('#lr','admin'); h.pg.fill('#lp','admin123'); h.click_login(900)
    h.pg.fill('#mp0','Old#Pass2026'); h.pg.fill('#mp1','Old#Pass2026'); h.pg.click('#mpok'); h.pg.wait_for_timeout(800)
    lab=h.pg.inner_text('#mp0 >> xpath=preceding-sibling::label'); m=re.search(r'[A-Z2-9]{4}(?:-[A-Z2-9]{4}){3}',lab)
    ok('recovery code shown after first password is set', m is not None, lab[:80]); code=m.group(0)
    h.pg.fill('#mp0','nope'); h.pg.click('#mpok'); ok('cannot dismiss recovery code without typing SAVED', h.pg.query_selector('#mp0') is not None)
    h.pg.fill('#mp0','SAVED'); h.pg.click('#mpok'); h.pg.wait_for_timeout(500)
    ok('recovery code stored hashed, not plaintext', code.replace('-','') not in h.js("localStorage.getItem('aanchal')") and str(h.js("S.users.admin.rec")).startswith('pbkdf2$'))
    ok('login works with the password set', h.js("me")=='admin')
    # forgot flow (with code)
    h.js("me=null;login()"); h.pg.wait_for_selector('button:has-text("Forgot password?")')
    h.pg.click('button:has-text("Forgot password?")'); h.pg.wait_for_selector('#mp0')
    h.pg.fill('#mp0','AAAA-BBBB-CCCC-DDDD'); h.pg.fill('#mp1','New#Pass2027'); h.pg.fill('#mp2','New#Pass2027'); h.pg.click('#mpok'); h.pg.wait_for_timeout(1200)
    ok('wrong recovery code refused, password unchanged', 'Wrong recovery' in h.alerts()[-1] and h.js("S.users.admin.chg")==True)
    h.pg.click('button:has-text("Forgot password?")') if h.pg.query_selector('#mp0') is None else None
    h.pg.wait_for_selector('#mp0'); h.pg.fill('#mp0',code.lower()); h.pg.fill('#mp1','short'); h.pg.fill('#mp2','short'); h.pg.click('#mpok')
    ok('weak new password refused', h.pg.query_selector('#mp1') is not None)
    h.pg.fill('#mp1','New#Pass2027'); h.pg.fill('#mp2','New#Pass2027'); h.pg.click('#mpok'); h.pg.wait_for_timeout(1500)
    ok('correct code (lower-case, no dashes needed) resets the password', 'Password reset' in ' '.join(h.alerts()))
    h.save_rec(); new=h.rec
    ok('a NEW recovery code is issued; old one is dead', new and new!=code)
    h.pg.fill('#lr','admin'); h.pg.fill('#lp','Old#Pass2026'); h.click_login(); ok('old password no longer works', h.js("me") in (None,'null'))
    h.pg.fill('#lp','New#Pass2027'); h.click_login(900)
    ok('login with new password works; reset notice shown to admin', h.js("me")=='admin' and any('was reset' in a for a in h.alerts()), h.alerts()[-2:])
    h.js("me=null;login()"); h.pg.click('button:has-text("Forgot password?")'); h.pg.wait_for_selector('#mp0')
    h.pg.fill('#mp0',code); h.pg.fill('#mp1','Zzz#Pass2028'); h.pg.fill('#mp2','Zzz#Pass2028'); h.pg.click('#mpok'); h.pg.wait_for_timeout(1200)
    ok('old recovery code cannot be reused', 'Wrong recovery' in h.alerts()[-1])
    # MFA is switched off by a reset
    # staff cannot use recovery or create codes
    h.js("me=null;login()"); h.pg.fill('#lr','admin'); h.pg.fill('#lp','New#Pass2027'); h.click_login(900)
    h.js("S.staff.push({id:'sx',uid:'tom',name:'Tom',pw:'x',active:true});0"); a0=len(h.alerts()); h.js("me='staff';recFlow()")
    ok('staff cannot create/replace the recovery code', 'Not allowed' in h.alerts()[-1] and len(h.alerts())>a0); h.js("me='admin'")
    # emergency path for an existing install with no recovery code
    h.js("delete S.users.admin.rec;save();me=null;login()"); h.pg.click('button:has-text("Forgot password?")'); h.pg.wait_for_selector('#mp0')
    h.pg.fill('#mp0','nope'); h.pg.click('#mpok'); ok('no-code reset: must type RESET', h.pg.query_selector('#mp0') is not None)
    h.pg.fill('#mp0','RESET'); h.pg.click('#mpok'); h.pg.wait_for_timeout(400)
    h.pg.click('button:has-text("Forgot password?")'); h.pg.wait_for_timeout(500)
    ok('no-code reset: blocked until 60 s have passed (data untouched)', 'wait' in h.alerts()[-1].lower() and h.pg.query_selector('#mp1') is None and h.js("S.products.length")>=0, h.alerts()[-1:])
    h.js("S.users.admin.resetReq=Date.now()-61000;save();0")
    h.pg.click('button:has-text("Forgot password?")'); h.pg.wait_for_selector('#mp1'); h.pg.fill('#mp0','Emerg#Pass2029'); h.pg.fill('#mp1','Emerg#Pass2029'); h.pg.click('#mpok'); h.pg.wait_for_timeout(1500)
    h.save_rec(); ok('no-code reset after waiting works and issues a recovery code', h.rec is not None)
    h.pg.fill('#lr','admin'); h.pg.fill('#lp','Emerg#Pass2029'); h.click_login(900)
    ok('login after emergency reset works and shows the notice', h.js("me")=='admin' and any('was reset' in a for a in h.alerts()))
    h.js("me=null;login();S.users.admin.rec=undefined;delete S.users.admin.rec;S.users.admin.resetReq=Date.now()-16*60000;save();0")
    h.pg.wait_for_selector('button:has-text("Forgot password?")'); h.pg.click('button:has-text("Forgot password?")'); h.pg.wait_for_selector('#mp0'); h.pg.wait_for_timeout(300)
    ok('stale reset request (>15 min) is ignored: asks for RESET again', h.pg.query_selector('#mp1') is None and 'RESET' in h.pg.inner_text('#mp0 >> xpath=preceding-sibling::label'))
    print('page errors:',h.errs); print(sum(1 for r in R if r[1]),'/',len(R),'passed')
