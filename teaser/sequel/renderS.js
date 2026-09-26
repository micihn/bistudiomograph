// Sequel renderer: sub-frame motion blur on fast moves, crisp everywhere else.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('file://'+__dirname+'/sequel.html');await p.evaluate(()=>document.fonts.ready);
 const T=await p.evaluate(()=>window.T);const cues=await p.evaluate(()=>window.CUES);
 fs.writeFileSync('cuesS.json',JSON.stringify({T,cues}));
 for(const d of ['fS','subS'])fs.mkdirSync(d,{recursive:true});
 const R=[[T.swipe1,T.D,12],[T.swipe2,T.EX,12],[T.modal,T.modal+.4,6],[T.lift,T.IM+.1,10],[T.dash,T.dash+.9,6],[T.swipe3,T.D2,12],[T.TT,T.END+.8,6]];
 const cuts=[T.D2,T.TT,T.tt2,T.tt3,T.END];
 const N=Math.round(T.total*24),SH=0.5/24;
 const ONLY=process.argv[2]?JSON.parse(process.argv[2]):null;
 for(let i=0;i<N;i++){const t=i/24,id=String(i).padStart(5,'0');if(ONLY&&!ONLY.some(([a,b])=>t>=a&&t<b))continue;const r=R.find(r=>t>=r[0]-.02&&t<r[1]);
  if(r){let lo=t-SH/2,hi=t+SH/2;const c=cuts.find(c=>c>lo&&c<hi);if(c!==undefined){if(t>=c)lo=c+1e-4;else hi=c-1e-4}
    for(let k=0;k<r[2];k++){await p.evaluate(t=>render(t),lo+(hi-lo)*(k+.5)/r[2]);await p.screenshot({path:`subS/${id}_${k}.png`});}}
  else{await p.evaluate(t=>render(t),t);await p.screenshot({path:`fS/${id}.jpg`,type:'jpeg',quality:95});}
  if(i%100===0)console.log('frame',i,'/',N);}
 await b.close();console.log('done',N);})();
