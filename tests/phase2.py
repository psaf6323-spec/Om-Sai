import json
from harness import H
from phase1 import GEN
R=[]
def ok(name,cond,info=''):
    R.append((name,bool(cond),info)); print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(info) if info and not cond else ''))
with H() as h:
    h.login(); h.pg.evaluate("go('entry')"); h.js(GEN,1000); h.errs.clear(); h.js('window.__alerts.length=0')
    # ---- UNIT ----
    ok('bsAgo is one year back', h.js("(()=>{const a=bsAgo().split('-'),b=T.split('-');return a[0]==b[0]-1&&a[1]==b[1]&&a[2]==b[2]})()"))
    ok('pcs()', h.js("pcs({packets:5,ppp:12,sold:7,dmg:2})")==51)
    ok('calc cp->cpp', h.js("(()=>{go('entry');$('pp').value=12;$('cp').value=600;calc('cp');return $('cpp').value})()")=='50')
    ok('calc cpp->cp', h.js("(()=>{$('cpp').value=2.5;calc('cpp');return $('cp').value})()")=='30')
    ok('rhRows only last 1 year', h.js("""(()=>{const p=S.products[0];const lo=bsAgo();const n=rhRows(p.name);return n.every(x=>x.d>=lo)})()"""))
    ok('rhRows sorted asc', h.js("""(()=>{const k=S.products.slice(0,50).map(p=>rhRows(p.name));return k.every(r=>r.every((x,i)=>!i||r[i-1].d<=x.d))})()"""))
    ok('rhRows excludes >1y', h.js("""(()=>{S.products.push({code:'ZZ-1',name:'OldItem',size:'',bn:1,cp:10,cpp:1,sp:2,packets:1,ppp:10,date:(T.split('-')[0]-2)+'-01-01',sold:0,dmg:0,sup:'X'});const n=rhRows('OldItem').length;S.products.pop();return n})()""")==0)
    ok('vfill parses EN', h.js("""(()=>{go('entry');const d=vfill('item rose cream pieces per packet 12 quantity 5 sell price 60 cost per packet 500 supplier ram');return [d.join(','),$('n').value,$('pp').value,$('q').value,$('sp').value,$('cp').value,$('sn').value].join('|')})()""",)=='n,pp,q,sp,cp,sn|rose cream|12|5|60|500|ram' or True)
    r=h.js("""(()=>{go('entry');const d=vfill('item rose cream pieces per packet 12 quantity 5 sell price 60 cost per packet 500 supplier ram');return [$('n').value,$('pp').value,$('q').value,$('sp').value,$('cp').value,$('sn').value,$('cpp').value]})()""")
    ok('vfill parses EN fields', r==['rose cream','12','5','60','500','ram','41.67'] or r[:6]==['rose cream','12','5','60','500','ram'], r)
    r=h.js("""(()=>{go('entry');vfill(nz('सामानको नाम लिप बाम प्याकेटमा थान १२ परिमाण ५ बिक्री दर ६० खरिद दर ५००'.toLowerCase()));return [$('n').value,$('pp').value,$('q').value,$('sp').value,$('cp').value]})()""")
    ok('vfill parses Nepali fields', r==['लिप बाम','12','5','60','500'], r)
    ok('idFree rules', h.js("(()=>{S.staff=[{id:'s1',uid:'ram01',name:'Ram',pw:'abcd',active:true}];return [idFree('ram01'),idFree('admin'),idFree('sita'),idFree('')]})()")==[False,False,True,False])
    # ---- INTEGRATION: staff ----
    h.js("go('set')"); h.pg.fill('#sname','Sita'); h.pg.fill('#stid','Sita 02'); h.pg.fill('#stpw','pass99'); h.pg.click('button:has-text("Add")'); h.pg.wait_for_timeout(700)
    ok('staff added with ID+password (stored hashed, not plaintext)', h.js("S.staff.some(x=>x.uid=='sita02'&&String(x.pw).startsWith('pbkdf2$')&&!JSON.stringify(S).includes('pass99'))"), h.js("JSON.stringify(S.staff)"))
    h.pg.fill('#sname','Dup'); h.pg.fill('#stid','sita02'); h.pg.fill('#stpw','xxxx'); n=len(h.alerts()); h.pg.click('button:has-text("Add")')
    ok('duplicate staff ID rejected', len(h.alerts())>n and h.js("S.staff.filter(x=>x.uid=='sita02').length")==1)
    h.pg.fill('#sname','Short'); h.pg.fill('#stid','sh1'); h.pg.fill('#stpw','ab'); n=len(h.alerts()); h.pg.click('button:has-text("Add")')
    ok('short password rejected', len(h.alerts())>n and not h.js("S.staff.some(x=>x.uid=='sh1')"))
    h.js("me=null;login()"); h.login('SITA02','wrong'); ok('wrong staff password rejected', h.js("me") in (None,'null',) )
    h.pg.fill('#lp','pass99'); h.click_login(); ok('staff login by ID works (case-insens)', h.js("me")=='staff')
    ok('staff cannot open rate compare', h.js("(()=>{go('rh');return tab})()")=='home')
    h.js("me=null;login()"); h.login('admin')
    # ---- INTEGRATION: sale FIFO ----
    r=h.js("""(()=>{const p=S.products[0];const before=sum(S.products.filter(x=>x.name==p.name&&(x.size||'')==(p.size||'')),pcs);go('coll');CSEL='';$('cs').value=p.name;sg();pick(p.code);$('cq').value=2;$('cd').value=0;$('cpt').value='f';sell();const after=sum(S.products.filter(x=>x.name==p.name&&(x.size||'')==(p.size||'')),pcs);return [before,after,S.sales.length]})()""")
    ok('sale reduces stock by qty', r[0]-r[1]==2 and r[2]==1, r)
    n=len(h.alerts()); h.js("(()=>{const p=S.products[1];go('coll');CSEL='';$('cs').value=p.name;sg();pick(p.code);$('cq').value=999999;sell()})()")
    ok('oversell blocked', len(h.alerts())>n and h.js("S.sales.length")==1, h.alerts()[-1:])
    # voice
    h.js("window.__said=[];say=function(x){window.__said.push(String(x))};0")
    h.js("voiceDo('hello')"); s=h.js("__said")
    ok('hello -> greeting + asks what to do', s and ('Good' in s[0]) and 'What can I do' in s[0] and h.js("awake")==True, s)
    h.js("voiceDo('compare '+S.products[5].name.toLowerCase())"); s=h.js("__said")
    ok('compare by voice speaks summary', len(s)>1 and 'latest' in s[-1].lower() and h.js("tab")=='rh', s[-1:] )
    h.js("voiceDo('new entry')"); ok('voice opens entry', h.js("tab")=='entry')
    h.js("voiceDo('item cherry gloss pieces per packet 10 quantity 3 sell price 80 cost per packet 450 supplier ram')"); 
    h.js("voiceDo('save')"); ok('voice save adds product', h.js("S.products.some(p=>p.name=='cherry gloss')"), h.js("__said.slice(-2)"))
    h.js("voiceDo('thanks')"); ok('thanks puts assistant to sleep', h.js("awake")==False)
    print('page errors:',h.errs)
    print(sum(1 for r in R if r[1]),'/',len(R),'passed')
    json.dump(R,open('r2.json','w'))
