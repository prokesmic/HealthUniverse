/**
 * Screenshot every public route at desktop + mobile viewports.
 * Run:
 *   npm run shots         # against http://127.0.0.1:8000 (start uvicorn first)
 *   npm run shots:prod    # against the Vercel production
 *
 * Outputs to data/screenshots/{viewport}/{route}.png
 */
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8000';
const OUT  = path.join(__dirname, '..', 'data', 'screenshots');

const ROUTES = [
  '/',
  '/discoveries',
  '/explore',
  '/explore?focus=magnesium',
  '/myths',
  '/changes',
  '/me',
  '/search?q=sleep',
  '/tier/A',
  '/tier/B',
  '/category/nutrition',
  '/category/cardiovascular',
  '/edge/1',
];

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900,  deviceScaleFactor: 1 },
  { name: 'mobile',  width: 375,  height: 812,  deviceScaleFactor: 2, isMobile: true },
];

const slug = (r) => r.replace(/^\//, '').replace(/[/?=&]/g, '_') || 'home';

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  for (const vp of VIEWPORTS) {
    fs.mkdirSync(path.join(OUT, vp.name), { recursive: true });
    const page = await browser.newPage();
    await page.setViewport(vp);
    for (const route of ROUTES) {
      const url = BASE + route;
      try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
        const file = path.join(OUT, vp.name, slug(route) + '.png');
        await page.screenshot({ path: file, fullPage: true });
        const stat = fs.statSync(file);
        console.log(`[${vp.name}] ${route} -> ${file} (${(stat.size/1024).toFixed(1)} KB)`);
      } catch (e) {
        console.error(`[${vp.name}] FAIL ${route}: ${e.message}`);
      }
    }
    await page.close();
  }
  await browser.close();
})();
