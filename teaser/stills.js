const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('file://'+__dirname+'/teaser.html');await p.evaluate(()=>document.fonts.ready);
 const T=await p.evaluate(()=>window.T);console.log(JSON.stringify(T,(k,v)=>typeof v=='number'?+v.toFixed(2):v));
 for(const a of process.argv.slice(2)){const tex=a.startsWith('x');const t=+a.replace('x','');
  await p.evaluate(([t,tex])=>tex?renderTexture(t):render(t),[t,tex]);await p.screenshot({path:`s2_${a}.png`});}
 await b.close();})();
