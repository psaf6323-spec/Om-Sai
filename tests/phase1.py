import time, json
from harness import H
GEN="""
async (N)=>{
 const brands=["Lakme","Maybelline","Loreal Paris","L'Oréal","Himalaya","Nivea","Garnier","Dove","Ponds","Vaseline","Colgate","Revlon","Mamaearth","Biotique","Wow","Patanjali","Fogg","Axe","Olay","Neutrogena"];
 const prods=["Lipstick","Kajal","Face Wash","Moisturiser","Sunscreen","Shampoo","Conditioner","Nail Polish","Compact Powder","Foundation","Eyeliner","Mascara","Body Lotion","Hair Oil","Face Serum","Lip Balm","Perfume","Deodorant","Face Mask","Talcum Powder"];
 const shades=["Ruby Red","Nude","Coral","Berry","Rose","Plum","Peach","Classic","Matte","Gold"];
 const sups=["Ram Traders","Sita Cosmetics Wholesale","Himal Distributors","City Suppliers","Kathmandu Beauty House","Birgunj Importers"];
 const cats=S.cats.filter(c=>c!='Other');
 const [ty,tm,td]=T.split('-').map(Number);
 const back=(n)=>{let y=ty,m=tm,d=td;while(n-->0){d--;if(d<1){m--;if(m<1){m=12;y--}d=BD[y][m-1]}}return `${y}-${p2(m)}-${p2(d)}`};
 entry();
 let r=1,rnd=()=>(r=(r*9301+49297)%233280)/233280,t0=performance.now(),saves=[];
 const set=(id,v)=>{$(id).value=v};
 for(let i=0;i<N;i++){
  const name=`${brands[i%20]} ${prods[Math.floor(i/20)%20]} ${shades[Math.floor(i/400)%10]} ${String(i+1).padStart(4,'0')}`;
  const pp=[6,10,12,24][i%4],cp=Math.round((60+rnd()*900)*pp/6),cpp=+(cp/pp).toFixed(2);
  set('n',name);set('ln','लोकल '+(i+1));set('ct',cats[i%cats.length]);set('sz',['','S','M','L'][i%4]);
  set('cp',cp);set('pp',pp);set('cpp',cpp);set('sp',Math.round(cpp*1.35));set('q',1+Math.floor(rnd()*20));
  set('sn',sups[i%6]);set('pd',back(Math.floor(rnd()*330)));
  const a=performance.now();addP();saves.push(performance.now()-a);
 }
 return {ms:performance.now()-t0,n:S.products.length,seq:S.seq,maxSave:Math.max(...saves),avgSave:saves.reduce((a,b)=>a+b)/saves.length,ls:(localStorage.getItem('aanchal')||'').length};
}
"""
def main():
  with H() as h:
      h.login()
      print('logged in tab:',h.js("tab"))
      h.pg.evaluate("go('entry')")
      res=h.js(GEN,1000)
      print(json.dumps(res,indent=1))
      print('dialogs:',h.dialogs[:5]); print('errors:',h.errs[:5])
      codes=h.js("S.products.map(p=>p.code)"); print('unique codes',len(set(codes)),'of',len(codes))
      for tabn in ['stock','rh','rep','cmp','home','tobe','sold','sal']:
          t=h.js(f"(()=>{{const a=performance.now();go('{tabn}');return performance.now()-a}})()")
          print(f'render {tabn}: {t:.0f} ms', 'errs',len(h.errs))
      h.pg.screenshot(path='s1.png')

if __name__=='__main__': main()
