const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const {spawn}=require('child_process');const fs=require('fs');
const FF=process.env.FF, FPS=30;
(async()=>{
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
  p.on('pageerror',e=>console.log('ERR',e.message));
  await p.goto('file://'+__dirname+'/teaser.html');await p.evaluate(()=>document.fonts.ready);
  const T=await p.evaluate(()=>window.T);const cues=await p.evaluate(()=>window.CUES);
  fs.writeFileSync('cues.json',JSON.stringify({T,cues}));
  const N=Math.ceil(T.total*FPS);
  const ff=spawn(FF,['-y','-f','image2pipe','-framerate',String(FPS),'-c:v','png','-i','-','-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','video_only.mp4'],{stdio:['pipe','ignore','inherit']});
  for(let i=0;i<N;i++){const t=i/FPS;await p.evaluate(t=>render(t),t);const buf=await p.screenshot({type:'png'});
    if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(i%150===0)console.log('frame',i,'/',N);}
  ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();console.log('done');})();
