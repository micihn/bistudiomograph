const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('file://'+__dirname+'/teaser.html');await p.evaluate(()=>document.fonts.ready);
 const T=await p.evaluate(()=>window.T);const cues=await p.evaluate(()=>window.CUES);
 fs.writeFileSync('cues.json',JSON.stringify({T,cues}));
 fs.mkdirSync('frames',{recursive:true});fs.mkdirSync('tex',{recursive:true});
 const N=Math.round(T.total*24);const only=process.argv[2];
 for(let i=0;i<N;i++){const t=i/24;const id=String(i).padStart(5,'0');
  if(t<T.C||(t>=T.Ein&&t<T.Eout))continue;
  if(t<T.D){if(only==='frames')continue;await p.evaluate(t=>renderTexture(t),t);await p.screenshot({path:`tex/${id}.png`});}
  else{if(only==='tex')continue;await p.evaluate(t=>render(t),t);await p.screenshot({path:`frames/${id}.jpg`,type:'jpeg',quality:95});}
  if(i%100===0)console.log('frame',i,'/',N);}
 await b.close();console.log('done',N);})();
