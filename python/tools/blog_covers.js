const { chromium } = require('playwright');
const fs = require('fs');
const root = '/home/user/digita-marketing';
const arts = JSON.parse(fs.readFileSync(root + '/database/blog/articles.json', 'utf8'));
const logo = 'data:image/webp;base64,' + fs.readFileSync(root + '/public/assets/images/v2/logo-digita.webp').toString('base64');
const html = a => `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;box-sizing:border-box}
body{width:1200px;height:630px;overflow:hidden;font-family:'Plus Jakarta Sans',sans-serif;color:#fff;
background:#070707;position:relative}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(212,175,55,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(212,175,55,.07) 1px,transparent 1px);background-size:48px 48px;
mask-image:radial-gradient(ellipse at 78% 45%,#000 0%,transparent 70%)}
.glow{position:absolute;width:640px;height:640px;right:-140px;top:-60px;border-radius:50%;background:radial-gradient(circle,rgba(212,175,55,.22),transparent 62%)}
.ring{position:absolute;right:120px;top:115px;width:400px;height:400px;border-radius:50%;border:1.5px solid rgba(212,175,55,.35)}
.ring.r2{right:70px;top:65px;width:500px;height:500px;border-color:rgba(212,175,55,.15)}
.ring.r3{right:175px;top:170px;width:290px;height:290px;border-color:rgba(212,175,55,.55)}
.icon{position:absolute;right:250px;top:245px;width:140px;height:140px;border-radius:50%;display:flex;align-items:center;justify-content:center;
background:linear-gradient(135deg,#f3d77a,#b8901f);color:#0a0a0a;font-size:66px;box-shadow:0 0 60px rgba(212,175,55,.45)}
.dot{position:absolute;width:14px;height:14px;border-radius:50%;background:#D4AF37;box-shadow:0 0 16px #D4AF37}
.content{position:absolute;left:72px;top:0;bottom:0;width:600px;display:flex;flex-direction:column;justify-content:center}
.pole{display:inline-flex;align-items:center;gap:10px;align-self:flex-start;padding:9px 18px;border:1px solid rgba(212,175,55,.6);border-radius:99px;color:#E8C766;font-size:20px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin-bottom:30px}
h1{font-size:62px;line-height:1.08;font-weight:800;letter-spacing:-.02em}
h1 span{color:#E8C766}
.foot{position:absolute;left:72px;bottom:52px;display:flex;align-items:center;gap:18px;color:rgba(255,255,255,.75);font-size:21px;font-weight:500}
.foot img{height:38px}
.bar{position:absolute;left:0;top:0;bottom:0;width:8px;background:linear-gradient(#f3d77a,#b8901f)}
</style></head><body>
<div class="grid"></div><div class="glow"></div><div class="bar"></div>
<div class="ring r2"></div><div class="ring"></div><div class="ring r3"></div>
<div class="dot" style="right:313px;top:108px"></div><div class="dot" style="right:117px;top:410px;width:10px;height:10px"></div><div class="dot" style="right:470px;top:470px;width:9px;height:9px"></div>
<div class="icon"><i class="bi bi-${a.icon}"></i></div>
<div class="content"><div class="pole"><i class="bi bi-${a.icon}"></i>${a.pole}</div>
<h1>${a.visual_title.replace(/(\S+ \S+)$/, '<span>$1</span>')}</h1></div>
<div class="foot"><img src="${logo}" alt="">Le blog · La Réunion</div>
</body></html>`;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const a of arts) {
    await p.setContent(html(a), { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: `cover-${a.slug}.png` });
  }
  await b.close();
})();
