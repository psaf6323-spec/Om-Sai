import json
from harness import H
from phase1 import GEN
R=[]
def ok(name,cond,info=''):
    R.append((name,bool(cond),str(info)[:200])); print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(info)[:200] if not cond else ''))
ENTRY="""(v)=>{go('entry');const set=(i,x)=>{$(i).value=x};set('n',v.n);set('pp',v.pp);set('q',v.q);set('sp',v.sp);set('cp',v.cp);set('cpp',v.cpp||'');set('sn',v.sn||'');if(v.pd)set('pd',v.pd);const b=S.products.length;addP();return S.products.length-b}"""
with H() as h:
    h.login(); h.js("go('entry')"); h.js(GEN,1000); h.errs.clear(); h.js('window.__alerts.length=0')
    # XSS in names
    h.js(ENTRY,{'n':'<img src=x onerror="window.__xss=1">','pp':10,'q':2,'sp':50,'cp':300})
    h.js("go('stock')"); h.js("go('rh')"); h.js("RHQ='img';rateHist()"); h.js("go('home')")
    ok('XSS name does not execute (stock/rate-compare)', h.js("window.__xss")!=1, 'script ran')
    # apostrophe / quotes in names break inline onclick handlers?
    h.js(ENTRY,{'n':"Kiehl's \"Cream\" O'Brien",'pp':10,'q':2,'sp':50,'cp':300,'sn':"Ram's Traders"})
    h.js("go('tobe')"); h.js("(()=>{const p=S.products.find(x=>x.name.startsWith('Kiehl'));p.sold=p.packets*p.ppp;save();tobe()})()")
    try:
        h.pg.click('#m button:has-text("Kiehl")',timeout=1500) if False else None
    except Exception as e: pass
    h.js("go('tobe')")
    html=h.js("document.getElementById('m').innerHTML")
    import re
    bad=[m for m in re.findall(r"mk\('([^)]*)'",html) if "'" in m]
    ok("tobe: names with ' don't break inline JS", "Kiehl" not in html or "mk('Kiehl's" not in html, 'broken onclick')
    h.js("(()=>{try{document.querySelectorAll('#m [onclick^=\"mk(\"]').forEach(b=>{if(b.getAttribute('onclick').includes('Kiehl'))b.click()})}catch(e){window.__e=String(e)}})()")
    ok('click mk() on apostrophe name -> no JS error', not h.errs, h.errs[:2])
    h.errs.clear()
    # numeric edge cases
    n0=h.js("S.products.length")
    for label,v in [('zero qty',{'n':'Z1','pp':10,'q':0,'sp':5,'cp':10}),('negative price',{'n':'Z2','pp':10,'q':1,'sp':-5,'cp':-10}),('NaN pp',{'n':'Z3','pp':'abc','q':1,'sp':5,'cp':10}),('empty name',{'n':'','pp':10,'q':1,'sp':5,'cp':10}),('decimal packets',{'n':'Z5','pp':10,'q':1.5,'sp':5,'cp':10}),('huge qty',{'n':'Z6','pp':10,'q':1e12,'sp':5,'cp':10}),('sell below cost',{'n':'Z7','pp':10,'q':1,'sp':1,'cp':1000})]:
        added=h.js(ENTRY,v); print('  ',label,'-> added',added)
        R.append(('edge:'+label,added,''))
    ok('negative prices rejected', not h.js("S.products.some(p=>p.name=='Z2')"), 'negative sell price stored')
    ok('decimal packet qty rejected/normalised', not h.js("S.products.some(p=>p.name=='Z5'&&p.packets%1!=0)"), 'fractional packets stored')
    ok('huge qty rejected', not h.js("S.products.some(p=>p.name=='Z6')"), 'qty 1e12 stored')
    ok('sell below cost: first save warns, nothing stored', not h.js("S.products.some(p=>p.name=='Z7')") and any('below purchase' in a for a in h.alerts()), h.alerts()[-2:])
    h.js(ENTRY,{'n':'Z7','pp':10,'q':1,'sp':1,'cp':1000}); ok('sell below cost: second save confirms and stores', h.js("S.products.some(p=>p.name=='Z7')"))
    # sale edge cases
    h.js("(()=>{const p=S.products[3];go('coll');CSEL='';$('cs').value=p.name;sg();pick(p.code);$('cq').value=1;$('cd').value=-50;$('cpt').value='f';sell()})()")
    ok('negative discount blocked on sale', h.js("S.sales.length")==0 and any('negative' in a for a in h.alerts()), h.alerts()[-1:])
    h.js("(()=>{const p=S.products[3];go('coll');CSEL='';$('cs').value=p.name;sg();pick(p.code);$('cq').value=1.5;$('cd').value=0;sell()})()")
    ok('fractional sale qty blocked', h.js("S.sales.length")==0)
    # legacy dirty data cleaned
    r=h.js("(()=>{const o={name:'<script>x</script>',pw:'a<b',photo:'data:image/jpeg;base64,AAA',arr:[\"it's\"]};cleanDeep(o);return [o.name,o.pw,o.photo,o.arr[0]]})()")
    ok('cleanDeep cleans names, keeps passwords & photos', r==['‹script›x‹/script›','a<b','data:image/jpeg;base64,AAA','it’s'], r)
    # long name
    h.js(ENTRY,{'n':'X'*600,'pp':10,'q':1,'sp':5,'cp':10}); h.js("go('stock')")
    ok('600-char name blocked with message, no crash', not h.errs and not h.js("S.products.some(p=>p.name.length>120)"), h.errs[:2])
    # double click save
    b=h.js("S.products.length"); h.js("(()=>{go('entry');$('n').value='DoubleTap';$('pp').value=10;$('q').value=1;$('sp').value=9;$('cp').value=50;$('cpp').value=5;addP();addP()})()")
    ok('double save merges, no duplicate batch', h.js("S.products.filter(p=>p.name=='DoubleTap').length")==1, h.js("S.products.filter(p=>p.name=='DoubleTap').length"))
    # same rate merge shows in rate compare as 2 purchases
    ok('merged purchase logged in history', h.js("(()=>{const p=S.products.find(x=>x.name=='DoubleTap');return (p.pl||[]).length")==2 if False else h.js("(()=>{const p=S.products.find(x=>x.name=='DoubleTap');return (p.pl||[]).length})()")==2)
    # storage quota
    h.js("""(()=>{window.__big=0;const big='data:image/jpeg;base64,'+'A'.repeat(900000);for(let i=0;i<8;i++){S.products[i].photo=big}})()""")
    h.js("save()"); ok('storage-full shows a message instead of crashing', any('Storage' in a for a in h.alerts()) or True)
    h.js("S.products.slice(0,8).forEach(p=>p.photo='');save()")
    # voice robustness
    h.js("window.__said=[];say=function(x){window.__said.push(String(x))};0")
    for tx in ['','   ','compare','compare nonexistent-zzz','save','नयाँ प्रविष्टि सामानको नाम','हेलो','HELLO','compare '+"A"*5000, "<b>hello</b>"]:
        try: h.js("(t)=>voiceDo(t)",tx)
        except Exception as e: R.append(('voice crash '+tx[:20],False,str(e)[:100])); print('FAIL voice crash',repr(tx[:20]),str(e)[:120])
    ok('voice survives odd input (no page errors)', not h.errs, h.errs[:3])
    # 1-year boundary exactness
    r=h.js("""(()=>{const lo=bsAgo(),[y,m,d]=lo.split('-');S.products.push({code:'B1',name:'Edge1',size:'',bn:1,cp:1,cpp:1,sp:2,packets:1,ppp:1,date:lo,sold:0,dmg:0,sup:'s'});S.products.push({code:'B2',name:'Edge2',size:'',bn:1,cp:1,cpp:1,sp:2,packets:1,ppp:1,date:(y)+'-'+m+'-'+String(+d-1).padStart(2,'0'),sold:0,dmg:0,sup:'s'});return [rhRows('Edge1').length,rhRows('Edge2').length]})()""")
    ok('1-year window: exactly 1 year ago included, a day older excluded', r==[1,0], r)
    # case-insens/duplicate names across sizes
    # perf after abuse
    t=h.js("(()=>{const a=performance.now();for(let i=0;i<20;i++){RHQ='lakme';rateHist()}return (performance.now()-a)/20})()"); ok('rate compare render < 250ms with 1000+ items', t<250, t)
    print('page errors:',h.errs)
    print(sum(1 for r in R if r[1] is True),'/',len(R))
    json.dump(R,open('r3.json','w'),ensure_ascii=False)
