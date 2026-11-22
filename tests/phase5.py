from harness import INDEX
import json, random, time
from harness import H
R=[]
def ok(name,cond,info=''):
    R.append((name,bool(cond),str(info)[:300])); print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(info)[:300] if not cond else ''))
JS_LIB="""
window.mkImg=(w,h,seed,noise)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');let r=seed;const rnd=()=>(r=(r*9301+49297)%233280)/233280;
 const g=x.createLinearGradient(0,0,w,h);g.addColorStop(0,`hsl(${rnd()*360},70%,60%)`);g.addColorStop(1,`hsl(${rnd()*360},60%,40%)`);x.fillStyle=g;x.fillRect(0,0,w,h);
 for(let i=0;i<40;i++){x.fillStyle=`hsla(${rnd()*360},70%,${30+rnd()*50}%,.8)`;x.beginPath();x.arc(rnd()*w,rnd()*h,20+rnd()*h/4,0,7);x.fill()}
 const d=x.getImageData(0,0,w,h),p=d.data;for(let i=0;i<p.length;i+=4){const n=(rnd()-.5)*noise;p[i]+=n;p[i+1]+=n;p[i+2]+=n}x.putImageData(d,0,0);return c};
window.feed=async(fn,bytes,type,name,k,im)=>{const inp=document.querySelector('input[onchange*="ph(this"]');const f=new File([bytes],name,{type});const dt=new DataTransfer();dt.items.add(f);inp.files=dt.files;const before=P[k];inp.dispatchEvent(new Event('change'));for(let i=0;i<200;i++){await new Promise(r=>setTimeout(r,15));if(P[k]&&P[k]!==before)return P[k]}return null};
window.photoFile=async(w,h,seed,noise,type='image/jpeg',q=.92)=>{const c=mkImg(w,h,seed,noise);const b=await new Promise(r=>c.toBlob(r,type,q));return new Uint8Array(await b.arrayBuffer())};
0;
"""
HOSTILE=["'; DROP TABLE products;--",'" OR "1"="1','<script>window.__x=1</script>','<img src=x onerror=window.__x=1>',"${7*7}","{{constructor.constructor('window.__x=1')()}}","\\'); alert(1);//","%27%20OR%201=1--","Robert'); DROP TABLE Students;--","שלום‮evil"]
def run(path,label,photos=True,N=1000):
    out={}
    with H(path) as h:
        h.login(); h.js(JS_LIB); h.js("go('entry')")
        h.errs.clear(); h.js('window.__alerts.length=0')
        gen="""async([N,hostile])=>{const sizes=[],t0=performance.now();let firstFull=-1;const sups=['Ram','Sita','Himal','City'];
         for(let i=0;i<N;i++){go('entry');const nm=(i%20==7)?hostile[(i/20|0)%hostile.length]+' '+i:`Item ${String(i+1).padStart(4,'0')} Lip Gloss`;
          const bytes=await photoFile(900,700,i+1,70);await feed(null,bytes,'image/jpeg','p'+i+'.jpg','prod','pv');
          const ph=P.prod||'';sizes.push(ph.length);
          const set=(id,v)=>{$(id).value=v};set('n',nm);set('pp',12);set('q',1+i%9);set('cp',500+i);set('cpp',((500+i)/12).toFixed(2));set('sp',Math.ceil((500+i)/12*1.4));set('sn',sups[i%4]);
          const a0=window.__alerts.length;addP();if(firstFull<0&&window.__alerts.slice(a0).some(x=>/Storage full/.test(x)))firstFull=i+1}
         return {sizes,firstFull,ms:performance.now()-t0,n:S.products.length,withPhoto:S.products.filter(p=>p.photo&&p.photo.length>100).length,ls:(localStorage.getItem('aanchal')||'').length}}"""
        r=h.js(gen,[N,HOSTILE])
        sz=r['sizes']; out.update(avg=sum(sz)/len(sz),mx=max(sz),mn=min(sz),over10=sum(1 for x in sz if x>10240),firstFull=r['firstFull'],n=r['n'],ls=r['ls'],withPhoto=r['withPhoto'],secs=r['ms']/1000)
        out['xss']=h.js("window.__x")
        out['errs']=len(h.errs)
        # persistence after reload + sampling
        persisted=h.js("(localStorage.getItem('aanchal')||'').length")
        h.pg.reload(); h.pg.wait_for_timeout(1500)
        out['reload_n']=h.js("S.products.length")
        out['reload_with_photo']=h.js("S.products.filter(p=>p.photo&&p.photo.startsWith('data:image')).length")
        out['reload_markers_left']=h.js("S.products.filter(p=>String(p.photo).startsWith('@idb')).length")
        h.pg.fill('#lr','admin'); h.pg.fill('#lp',h.apw); h.click_login(900)
        out['hostile_intact']=h.js("S.products.every(p=>p&&p.code&&typeof p.name=='string')")
        out['drop_found']=h.js("S.products.filter(p=>p.name.includes('DROP')).length")
        out['after_login_ok']=h.js("me")=='admin'
        out['stock_render_ms']=h.js("(()=>{const a=performance.now();go('stock');return performance.now()-a})()")
    return out
if __name__=='__main__':
    b=run(INDEX,'current',N=1000)
    print('RESULT (1000 items with photos):',json.dumps(b,indent=1))
