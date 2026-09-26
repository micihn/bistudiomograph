// Re-render frames whose shutter straddles a hard cut, keeping all sub-frames on the frame's own side.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
 await p.goto('file://'+__dirname+'/teaser.html');await p.evaluate(()=>document.fonts.ready);
 const T=await p.evaluate(()=>window.T);const SH=0.5/24,K=6;
 const cuts=[0,2,4,6,8,10,11,12,14,16,18].map(x=>T.M+x*T.BEAT).concat([T.END]);
 const fs=require('fs');fs.rmSync('sub3',{recursive:true,force:true});fs.mkdirSync('sub3');let n=0;
 for(let i=Math.floor(T.M*24);i<Math.round(T.END*24)+2;i++){const t=i/24;
  const c=cuts.find(c=>c>t-SH/2&&c<t+SH/2);if(c===undefined)continue;
  const lo=t>=c?c+1e-4:t-SH/2,hi=t>=c?t+SH/2:c-1e-4;await p.evaluate(t=>{window.FT=t},t);
  for(let k=0;k<K;k++){const ts=lo+(hi-lo)*(k+.5)/K;await p.evaluate(t=>render(t),ts);await p.screenshot({path:`sub3/${String(i).padStart(5,'0')}_${k}.png`});}n++}
 await b.close();console.log('fixed',n);})();
