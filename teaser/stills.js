const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async()=>{
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
  p.on('pageerror',e=>console.log('ERR',e.message));p.on('console',m=>console.log('LOG',m.text()));
  await p.goto('file://'+__dirname+'/teaser.html');await p.evaluate(()=>document.fonts.ready);
  const T=await p.evaluate(()=>window.T);console.log(JSON.stringify(T));
  const ts=process.argv.slice(2).map(Number);
  for(const t of ts){await p.evaluate(t=>render(t),t);await p.screenshot({path:`still_${t}.png`});}
  await b.close();})();
