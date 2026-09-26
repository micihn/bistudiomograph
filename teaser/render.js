// Renders every frame; fast-moving parts (Spaces swipe, montage) get 6 sub-frames
// over a 180-degree shutter, averaged later by blur.py for real motion blur.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('file://'+__dirname+'/teaser.html');await p.evaluate(()=>document.fonts.ready);
 const T=await p.evaluate(()=>window.T);const cues=await p.evaluate(()=>window.CUES);
 fs.writeFileSync('cues.json',JSON.stringify({T,cues}));
 for(const d of ['f3','sub3'])fs.mkdirSync(d,{recursive:true});
 const N=Math.round(T.total*24),SH=0.5/24;const only=process.argv[2]==='blur';const FROM=parseFloat(process.argv[3]||'0');
 const blurred=t=>(t>=T.swipe-0.02&&t<T.D+0.02)||(t>=T.M&&t<T.END+0.1);
 for(let i=Math.floor(FROM*24);i<N;i++){const t=i/24,id=String(i).padStart(5,'0');
  if(blurred(t)){const K=t<T.D+0.05?16:6;await p.evaluate(t=>{window.FT=t},t);for(let k=0;k<K;k++){const ts=t-SH/2+SH*(k+.5)/K;await p.evaluate(t=>render(t),ts);await p.screenshot({path:`sub3/${id}_${k}.png`});}}
  else{if(only&&!FROM)continue;await p.evaluate(t=>render(t),t);await p.screenshot({path:`f3/${id}.jpg`,type:'jpeg',quality:95});}
  if(i%100===0)console.log('frame',i,'/',N);}
 await b.close();console.log('done',N);})();
