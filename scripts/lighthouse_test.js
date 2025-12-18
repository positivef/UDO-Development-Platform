/**
 * Lighthouse Performance Test Script
 *
 * Measures performance metrics for all major pages:
 * - Dashboard (/)
 * - Kanban (/kanban)
 * - Archive (/archive)
 * - Time Tracking (/time-tracking)
 *
 * Usage:
 * 1. Start dev server: cd web-dashboard && npm run dev
 * 2. Run this script: node scripts/lighthouse_test.js
 *
 * Or use with server helper:
 * node scripts/with_server.js --server "cd web-dashboard && npm run dev" --port 3000 -- node scripts/lighthouse_test.js
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:3000';

const PAGES = [
  { name: 'Dashboard', url: '/' },
  { name: 'Kanban Board', url: '/kanban' },
  { name: 'Archive View', url: '/archive' },
  { name: 'Time Tracking', url: '/time-tracking' },
];

const CONFIG = {
  extends: 'lighthouse:default',
  settings: {
    onlyCategories: ['performance', 'accessibility', 'best-practices'],
    formFactor: 'desktop',
    screenEmulation: {
      mobile: false,
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1,
    },
  },
};

async function runLighthouse(url, name) {
  console.log(`\n🔍 Testing: ${name} (${url})`);

  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });

  try {
    const runnerResult = await lighthouse(url, {
      port: chrome.port,
      ...CONFIG,
    });

    const { lhr } = runnerResult;

    // Extract key metrics
    const metrics = {
      name,
      url,
      performance: Math.round(lhr.categories.performance.score * 100),
      accessibility: Math.round(lhr.categories.accessibility.score * 100),
      bestPractices: Math.round(lhr.categories['best-practices'].score * 100),
      fcp: lhr.audits['first-contentful-paint'].numericValue,
      lcp: lhr.audits['largest-contentful-paint'].numericValue,
      tti: lhr.audits['interactive'].numericValue,
      tbt: lhr.audits['total-blocking-time'].numericValue,
      cls: lhr.audits['cumulative-layout-shift'].numericValue,
      speedIndex: lhr.audits['speed-index'].numericValue,
    };

    console.log(`✅ Performance: ${metrics.performance}%`);
    console.log(`✅ Accessibility: ${metrics.accessibility}%`);
    console.log(`✅ Best Practices: ${metrics.bestPractices}%`);
    console.log(`⏱️  FCP: ${(metrics.fcp / 1000).toFixed(2)}s`);
    console.log(`⏱️  LCP: ${(metrics.lcp / 1000).toFixed(2)}s (Target: <2.5s)`);
    console.log(`⏱️  TTI: ${(metrics.tti / 1000).toFixed(2)}s (Target: <3.0s)`);
    console.log(`⏱️  TBT: ${metrics.tbt.toFixed(0)}ms`);
    console.log(`⏱️  CLS: ${metrics.cls.toFixed(3)}`);
    console.log(`⏱️  Speed Index: ${(metrics.speedIndex / 1000).toFixed(2)}s`);

    return metrics;
  } finally {
    await chrome.kill();
  }
}

async function main() {
  console.log('🚀 Lighthouse Performance Testing');
  console.log('====================================\n');
  console.log(`Testing against: ${BASE_URL}`);
  console.log(`Pages: ${PAGES.length}`);

  const results = [];

  for (const page of PAGES) {
    try {
      const metrics = await runLighthouse(`${BASE_URL}${page.url}`, page.name);
      results.push(metrics);
    } catch (error) {
      console.error(`❌ Failed to test ${page.name}:`, error.message);
    }
  }

  // Save results
  const outputDir = path.join(__dirname, '..', 'lighthouse-results');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const outputFile = path.join(outputDir, `lighthouse-${timestamp}.json`);
  fs.writeFileSync(outputFile, JSON.stringify(results, null, 2));

  console.log(`\n\n📊 Summary`);
  console.log('='.repeat(80));
  console.log('Page Name'.padEnd(30) + 'Perf'.padEnd(8) + 'A11y'.padEnd(8) + 'BP'.padEnd(8) + 'LCP'.padEnd(10) + 'TTI');
  console.log('-'.repeat(80));

  for (const result of results) {
    const name = result.name.padEnd(30);
    const perf = `${result.performance}%`.padEnd(8);
    const a11y = `${result.accessibility}%`.padEnd(8);
    const bp = `${result.bestPractices}%`.padEnd(8);
    const lcp = `${(result.lcp / 1000).toFixed(2)}s`.padEnd(10);
    const tti = `${(result.tti / 1000).toFixed(2)}s`;

    console.log(name + perf + a11y + bp + lcp + tti);
  }

  console.log('='.repeat(80));

  // Calculate averages
  const avgPerf = Math.round(results.reduce((sum, r) => sum + r.performance, 0) / results.length);
  const avgA11y = Math.round(results.reduce((sum, r) => sum + r.accessibility, 0) / results.length);
  const avgBP = Math.round(results.reduce((sum, r) => sum + r.bestPractices, 0) / results.length);
  const avgLCP = (results.reduce((sum, r) => sum + r.lcp, 0) / results.length / 1000).toFixed(2);
  const avgTTI = (results.reduce((sum, r) => sum + r.tti, 0) / results.length / 1000).toFixed(2);

  console.log('Average'.padEnd(30) + `${avgPerf}%`.padEnd(8) + `${avgA11y}%`.padEnd(8) + `${avgBP}%`.padEnd(8) + `${avgLCP}s`.padEnd(10) + `${avgTTI}s`);
  console.log('='.repeat(80));

  console.log(`\n✅ Results saved to: ${outputFile}`);

  // Check if targets are met
  const targets = {
    performance: 90,
    lcp: 2.5,
    tti: 3.0,
  };

  console.log(`\n🎯 Target Validation:`);
  console.log(`Performance Score: ${avgPerf}% ${avgPerf >= targets.performance ? '✅' : '❌'} (Target: ${targets.performance}%)`);
  console.log(`LCP: ${avgLCP}s ${parseFloat(avgLCP) <= targets.lcp ? '✅' : '❌'} (Target: <${targets.lcp}s)`);
  console.log(`TTI: ${avgTTI}s ${parseFloat(avgTTI) <= targets.tti ? '✅' : '❌'} (Target: <${targets.tti}s)`);
}

main().catch((error) => {
  console.error('❌ Lighthouse test failed:', error);
  process.exit(1);
});
