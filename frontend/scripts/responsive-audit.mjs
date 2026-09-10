import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/fairn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

const baseUrl = 'http://127.0.0.1:5173';
const widths = [1920, 1440, 1366, 1024, 768, 430, 390, 375];
const routes = [
  '/', '/dashboard', '/fishing', '/marine-conditions', '/safety', '/maps',
  '/earth-observation', '/navigation', '/operations', '/ask',
  '/decision-intelligence', '/what-if', '/agents', '/data-sources',
  '/analytics', '/reports', '/settings',
];
const screenshotRoutes = new Set(['/dashboard', '/maps', '/data-sources', '/reports']);
const outputDir = path.resolve('tmp', 'responsive-audit');
fs.mkdirSync(outputDir, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const results = [];

for (const width of widths) {
  const context = await browser.newContext({ viewport: { width, height: width <= 430 ? 844 : 900 } });
  const page = await context.newPage();
  for (const route of routes) {
    const consoleErrors = [];
    const onConsole = (message) => {
      if (message.type() === 'error') consoleErrors.push(message.text());
    };
    page.on('console', onConsole);
    let navigationError = null;
    try {
      await page.goto(`${baseUrl}${route}`, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await page.waitForTimeout(350);
    } catch (error) {
      navigationError = String(error);
    }

    const metrics = navigationError ? null : await page.evaluate(() => {
      const viewportWidth = document.documentElement.clientWidth;
      const ignored = (element) => {
        if (element.closest('.leaflet-map-pane, .leaflet-control-container, [aria-hidden="true"]')) return true;
        const sidebar = element.closest('.oceanis-sidebar');
        if (sidebar && !sidebar.classList.contains('mobile-open')) return true;
        let ancestor = element.parentElement;
        while (ancestor && ancestor !== document.body) {
          const overflowX = getComputedStyle(ancestor).overflowX;
          if (['auto', 'scroll', 'hidden', 'clip'].includes(overflowX)) return true;
          ancestor = ancestor.parentElement;
        }
        return false;
      };
      const offenders = [...document.querySelectorAll('body *')]
        .filter((element) => {
          const style = getComputedStyle(element);
          if (style.display === 'none' || style.visibility === 'hidden' || ignored(element)) return false;
          const rect = element.getBoundingClientRect();
          return rect.width > 1 && (rect.left < -2 || rect.right > viewportWidth + 2);
        })
        .slice(0, 12)
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return {
            tag: element.tagName.toLowerCase(),
            className: typeof element.className === 'string' ? element.className.slice(0, 120) : '',
            left: Math.round(rect.left),
            right: Math.round(rect.right),
            width: Math.round(rect.width),
          };
        });
      return {
        viewportWidth,
        documentWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
        bodyWidth: document.body.getBoundingClientRect().width,
        offenders,
      };
    });

    const failed = navigationError || (metrics && (metrics.documentWidth > width + 2 || metrics.offenders.length > 0));
    if (failed || (screenshotRoutes.has(route) && [1920, 768, 430, 375].includes(width))) {
      const safeRoute = route === '/' ? 'home' : route.slice(1).replaceAll('/', '-');
      await page.screenshot({ path: path.join(outputDir, `${safeRoute}-${width}.png`), fullPage: true });
    }
    results.push({ width, route, navigationError, metrics, consoleErrors: [...new Set(consoleErrors)].slice(0, 8) });
    page.off('console', onConsole);
  }
  await context.close();
}

await browser.close();
fs.writeFileSync(path.join(outputDir, 'results.json'), JSON.stringify(results, null, 2));

const failures = results.filter((item) => item.navigationError || item.metrics?.documentWidth > item.width + 2 || item.metrics?.offenders.length);
console.log(JSON.stringify({ checks: results.length, failures }, null, 2));
process.exitCode = failures.length ? 1 : 0;
