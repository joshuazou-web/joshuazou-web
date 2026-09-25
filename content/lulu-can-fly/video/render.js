// 用无头 Chromium 逐帧渲染 scene.html，管道喂给 ffmpeg 输出 H.264 竖屏视频
// 用法：node render.js <ffmpeg路径> <音效wav> <输出mp4> [只渲染某几帧,逗号分隔，输出PNG用于预览]
const path = require('path'), fs = require('fs'), { spawn } = require('child_process');
const { chromium } = require(process.env.PW || 'playwright');
const [ffmpeg, wav, out, frames] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
  await page.goto('file://' + path.resolve(__dirname, 'scene.html'));
  await page.evaluate(() => document.fonts.ready);
  const { FPS, DUR } = await page.evaluate(() => window.META);
  if (frames) {
    for (const f of frames.split(',')) {
      const d = await page.evaluate(i => window.renderFrame(i), +f);
      fs.writeFileSync(path.join(out, `f${f}.jpg`), Buffer.from(d.split(',')[1], 'base64'));
    }
    return browser.close();
  }
  const ff = spawn(ffmpeg, ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-i', wav,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'ignore', 'inherit'] });
  for (let i = 0; i < FPS * DUR; i++) {
    const d = await page.evaluate(i => window.renderFrame(i), i);
    if (!ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
