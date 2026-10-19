// Verify the judges brief without rebuilding held presentation or media assets.
// SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL, fileURLToPath } = require('node:url');
const { chromium } = require('@playwright/test');
const { AxeBuilder } = require('@axe-core/playwright');

const root = path.resolve(__dirname, '..');
const brief = path.join(root, 'presentation', 'mosaic-judges-brief.html');
const url = pathToFileURL(brief).href;
const outputDirectory = path.join(root, 'build', 'judges-brief-qa');

async function checkLayout(page, width, state) {
  const layout = await page.evaluate(() => {
    const visible = (element) => element.getClientRects().length > 0;
    return {
      overflow: document.documentElement.scrollWidth > innerWidth + 1,
      clipped: [...document.querySelectorAll('h1,h2,h3,p,figcaption,label,summary,button')]
        .filter(visible)
        .filter((element) => element.scrollWidth > element.clientWidth + 1)
        .map((element) => element.textContent.trim().slice(0, 100)),
      imagesLoaded: [...document.images].every((image) => image.complete && image.naturalWidth > 0),
    };
  });
  assert.equal(layout.overflow, false, `${state}: document overflow at ${width}px`);
  assert.deepEqual(layout.clipped, [], `${state}: clipped text at ${width}px`);
  assert.equal(layout.imagesLoaded, true, `${state}: missing screenshot at ${width}px`);
}

async function assertModel(page, { hours, gross, net }) {
  assert.equal(await page.locator('#hours-output').innerText(), hours);
  assert.equal(await page.locator('#gross-output').innerText(), gross);
  assert.equal(await page.locator('#net-output').innerText(), net);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    fs.mkdirSync(outputDirectory, { recursive: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    const errors = [];
    const networkRequests = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('request', (request) => {
      if (/^https?:/i.test(request.url())) networkRequests.push(request.url());
    });
    await page.goto(url);
    assert.deepEqual(errors, [], 'Report initialization errors');
    await page.evaluate(() => Promise.all([...document.images].map((image) => image.decode())));

    const content = await page.evaluate(() => ({
      ids: [...document.querySelectorAll('[id]')].map((element) => element.id),
      links: [...document.querySelectorAll('a')].map((link) => link.href),
      chapters: [...document.querySelectorAll('.chapter')].map((chapter) => ({
        id: chapter.id,
        seconds: Number(chapter.dataset.seconds),
        time: chapter.querySelector('.time').textContent,
        words: [...chapter.querySelectorAll('.script > p')]
          .map((paragraph) => paragraph.textContent)
          .join(' ')
          .trim()
          .split(/\s+/).length,
      })),
      mapRows: document.querySelectorAll('#capability-map tbody tr').length,
      sourceCount: document.querySelectorAll('.source-list > li').length,
      imagePaths: [...document.images].map((image) => image.getAttribute('src')),
      mainText: document.querySelector('main').textContent,
      heroTitle: document.getElementById('hero-title').textContent,
      leverageCards: document.querySelectorAll('.app-leverage > div').length,
      chapterHeadings: [...document.querySelectorAll('.chapter h2')].map((heading) =>
        heading.textContent.replace(/\s+/g, ' ').trim(),
      ),
    }));
    assert.equal(new Set(content.ids).size, content.ids.length, 'Duplicate HTML IDs');
    assert.equal(content.chapters.length, 10);
    assert.match(content.heroTitle, /^GitHub Copilot App/);
    assert.match(content.heroTitle, /Make expertise repeatable/);
    assert.equal(content.leverageCards, 6);
    assert.doesNotMatch(content.chapterHeadings.join(' '), /not a claim|only one model/i);
    assert.doesNotMatch(
      await page.locator('#chapter-9 > .callout').innerText(),
      /allowlist|troubleshoot|failed to invoke/i,
    );
    assert.equal(
      content.chapters.reduce((sum, chapter) => sum + chapter.seconds, 0),
      900,
    );
    const spokenWords = content.chapters.reduce((sum, chapter) => sum + chapter.words, 0);
    assert.ok(
      spokenWords >= 1500 && spokenWords <= 1750,
      `Unexpected script length: ${spokenWords}`,
    );
    let elapsed = 0;
    for (const chapter of content.chapters) {
      const [, startMinute, startSecond, endMinute, endSecond] = chapter.time.match(
        /^(\d{2}):(\d{2})-(\d{2}):(\d{2})/,
      );
      assert.equal(Number(startMinute) * 60 + Number(startSecond), elapsed, chapter.id);
      elapsed += chapter.seconds;
      assert.equal(Number(endMinute) * 60 + Number(endSecond), elapsed, chapter.id);
    }
    assert.equal(content.mapRows, 24);
    assert.equal(content.sourceCount, 23);
    assert.equal(
      await page.locator('#chapter-3 .video-feature').getAttribute('href'),
      'https://youtu.be/dUU2s_N283E',
    );
    assert.match(await page.locator('#chapter-3 .video-feature').innerText(), /10:12/);
    assert.equal(await page.locator('iframe, video').count(), 0);
    const sourceGate = await page.locator('#chapter-6 .gate').first().innerText();
    assert.match(sourceGate, /authorized evidence/i);
    assert.match(sourceGate, /read-only MCP/i);
    assert.doesNotMatch(sourceGate, /synthetic|four allowlisted/i);
    assert.deepEqual(content.imagePaths, []);
    assert.equal(await page.locator('.cue, #rubric-title, #timer').count(), 0);
    assert.doesNotMatch(
      content.mainText,
      /Delivery cue:|Visual allocation:|Discussion backup|earns attention/i,
    );
    assert.equal(await page.locator('main > section .section-info').count(), 14);
    assert.equal(await page.locator('button:not([data-tooltip])').count(), 0);
    assert.ok((await page.locator('abbr[data-tooltip]').count()) > 100);
    assert.match(
      await page
        .locator('abbr')
        .filter({ hasText: /^POSIX$/ })
        .first()
        .getAttribute('data-tooltip'),
      /Portable Operating System Interface/,
    );
    const composition = await page
      .locator('#dossier-chart circle[data-count]')
      .evaluateAll((arcs) =>
        arcs.map((arc) => ({ format: arc.dataset.format, count: Number(arc.dataset.count) })),
      );
    assert.deepEqual(composition, [
      { format: 'HTML', count: 10 },
      { format: 'Markdown', count: 9 },
      { format: 'JSON', count: 4 },
    ]);
    for (const href of content.links) {
      const target = new URL(href);
      if (
        target.hostname === 'github.com' &&
        target.pathname.startsWith('/gregunger/ghca-mosaic-challenge-official/')
      ) {
        const reference = target.pathname.match(
          /^\/gregunger\/ghca-mosaic-challenge-official\/(?:blob|tree)\/([^/]+)\/(.+)$/,
        );
        assert.ok(reference, `Repository link must identify a reviewed revision: ${href}`);
        assert.equal(reference[1], '4d1865687cdd0cdf6fe0777ac102085a2f1d5c9e');
        assert.ok(
          fs.existsSync(path.join(root, ...decodeURIComponent(reference[2]).split('/'))),
          `Missing repository reference: ${href}`,
        );
      }
      if (target.protocol !== 'file:') continue;
      assert.equal(target.pathname, new URL(url).pathname, `Nonportable evidence link: ${href}`);
      assert.ok(fs.existsSync(fileURLToPath(target)), `Missing local link: ${href}`);
      if (target.pathname === new URL(url).pathname && target.hash) {
        assert.ok(
          content.ids.includes(decodeURIComponent(target.hash.slice(1))),
          `Missing anchor: ${href}`,
        );
      }
    }
    for (const required of [
      'not measured',
      'not cash savings',
      'not tenant isolation',
      'not signatures',
      'not customer approval',
      'No head-to-head',
      'unselected discussion draft',
      'second isolated',
      'evaluation',
      'GitHub Copilot App',
    ]) {
      assert.ok(
        content.mainText.replace(/\s+/g, ' ').toLowerCase().includes(required.toLowerCase()),
        `Missing qualification: ${required}`,
      );
    }
    const validation = JSON.parse(
      fs.readFileSync(
        path.join(root, 'examples', 'synthetic', 'expected', 'validation-report.json'),
        'utf8',
      ),
    );
    assert.equal(validation.status, 'pass');
    assert.ok(validation.checks.every((check) => check.status === 'pass'));
    const packageFiles = fs.readdirSync(path.join(root, 'examples', 'synthetic', 'expected'));
    assert.equal(packageFiles.filter((file) => file.endsWith('.html')).length, 10);
    assert.equal(packageFiles.filter((file) => file.endsWith('.md')).length, 9);
    assert.equal(packageFiles.filter((file) => file.endsWith('.json')).length, 4);

    const widths = [1920, 1440, 1024, 768, 390, 320];
    for (const width of widths) {
      await page.setViewportSize({ width, height: 1000 });
      await checkLayout(page, width, 'report');
      await page.locator('#notes-toggle').click();
      assert.equal(await page.locator('.talk-track[open]').count(), 10);
      await checkLayout(page, width, 'expanded narration');
      const accessibility = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .analyze();
      assert.deepEqual(
        accessibility.violations.map((violation) => ({
          id: violation.id,
          nodes: violation.nodes.map((node) => node.target),
        })),
        [],
        `Accessibility violations at ${width}px`,
      );
      await page.locator('#notes-toggle').click();
      assert.equal(await page.locator('.talk-track[open]').count(), 0);
      await page.locator('#focus-toggle').click();
      assert.equal(
        await page.locator('main > .chapter:visible, main > .support:visible').count(),
        1,
      );
      await checkLayout(page, width, 'focused section');
      await page.locator('#focus-toggle').click();
    }

    await assertModel(page, { hours: '80 h', gross: '$1,600,000', net: '$1,600,000' });
    await page.locator('#review').fill('24');
    await assertModel(page, { hours: '72 h', gross: '$1,440,000', net: '$1,440,000' });
    assert.equal(await page.locator('#review-bar').getAttribute('width'), '170');
    assert.equal(await page.locator('#returned-bar').getAttribute('width'), '510');
    await page.locator('#review').fill('8');
    await assertModel(page, { hours: '88 h', gross: '$1,760,000', net: '$1,760,000' });
    await page.locator('#review').fill('16');
    await page.locator('#other').fill('8');
    await page.locator('#cost').fill('250000');
    await assertModel(page, { hours: '72 h', gross: '$1,440,000', net: '$1,190,000' });
    await page.locator('#review').fill('100');
    await assertModel(page, { hours: '-12 h', gross: '-$240,000', net: '-$490,000' });
    assert.equal(await page.locator('#returned-bar').getAttribute('width'), '0');
    assert.ok(Number(await page.locator('#overrun-bar').getAttribute('width')) > 0);
    await page.locator('#volume').fill('0');
    await assertModel(page, { hours: '-12 h', gross: '$0', net: '-$250,000' });
    for (const [selector, value] of [
      ['#baseline', ''],
      ['#baseline', '-1'],
      ['#volume', '1.5'],
    ]) {
      await page.locator('#reset-model').click();
      await page.locator(selector).fill(value);
      assert.equal(await page.locator('#model-results').isVisible(), false);
      assert.equal(await page.locator('#effort-analytics').isVisible(), false);
      assert.ok((await page.locator('#model-error').innerText()).length > 0);
      assert.equal(await page.locator(selector).getAttribute('aria-invalid'), 'true');
    }
    await page.locator('#reset-model').click();
    assert.equal(await page.locator('#model-error').innerText(), '');
    assert.equal(await page.locator('#model-results').isVisible(), true);
    await assertModel(page, { hours: '80 h', gross: '$1,600,000', net: '$1,600,000' });
    await page.locator('#baseline').fill('0');
    await page.locator('#review').fill('0');
    assert.equal(
      await page.locator('#reduction-output').innerText(),
      'No baseline for a percentage',
    );
    assert.equal(await page.locator('#baseline-bar').getAttribute('width'), '0');
    await page.locator('#reset-model').click();

    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.locator('#focus-toggle').click();
    assert.equal(await page.locator('.rail').isVisible(), true);
    for (const id of [
      ...Array.from({ length: 10 }, (_, index) => `chapter-${index + 1}`),
      'capability-map',
      'judge-questions',
      'sources',
    ]) {
      await page.locator(`.rail a[href="#${id}"]`).click();
      assert.equal(
        await page.locator('main > .chapter:visible, main > .support:visible').count(),
        1,
      );
      assert.equal(await page.locator(`#${id}`).isVisible(), true);
      assert.equal(
        await page.locator(`.rail a[href="#${id}"]`).getAttribute('aria-current'),
        'step',
      );
    }
    await page.locator('.rail a[href="#chapter-6"]').click();
    await page.locator('#chapter-6 a[href="#r07"]').click();
    assert.equal(await page.locator('#sources').isVisible(), true);
    assert.equal(await page.locator('#chapter-6').isVisible(), false);
    await page.goBack();
    assert.equal(await page.locator('#chapter-6').isVisible(), true);
    await checkLayout(page, 1440, 'focus view');
    await page.locator('#notes-toggle').click();
    await page.locator('.rail a[href="#chapter-5"]').click();
    assert.equal(await page.locator('#chapter-5 .talk-track[open]').count(), 1);
    await page.screenshot({ path: path.join(outputDirectory, 'focus-dossier.png') });
    await page.locator('.rail a[href="#chapter-7"]').click();
    await page.screenshot({ path: path.join(outputDirectory, 'focus-economics.png') });
    await page.locator('#focus-toggle').click();
    assert.equal(await page.locator('#capability-map').isVisible(), true);
    await page.locator('#notes-toggle').click();

    const tooltip = page.locator('#report-tooltip');
    await page.locator('#focus-toggle').hover();
    assert.equal(await tooltip.isVisible(), true);
    assert.match(await tooltip.innerText(), /selected in the left navigation/);
    await page.keyboard.press('Escape');
    assert.equal(await tooltip.isVisible(), false);
    const info = page.locator('#chapter-7 .section-info');
    await info.hover();
    assert.match(await tooltip.innerText(), /illustrative capacity model/i);
    await page.keyboard.press('Escape');
    const acronym = page.locator('#chapter-6 abbr').filter({ hasText: /^MCP$/ }).first();
    await acronym.focus();
    assert.equal(await tooltip.isVisible(), true);
    assert.match(await tooltip.innerText(), /Model Context Protocol/);
    await page.keyboard.press('Escape');
    const chart = page.locator('#dossier-chart');
    await chart.scrollIntoViewIfNeeded();
    const chartBox = await chart.boundingBox();
    const cursor = { x: chartBox.x + 80, y: chartBox.y + 80 };
    await page.mouse.move(cursor.x, cursor.y);
    const tooltipBox = await tooltip.boundingBox();
    assert.ok(tooltipBox.x >= cursor.x + 10 && tooltipBox.x <= cursor.x + 20);
    assert.ok(tooltipBox.y >= cursor.y + 10 && tooltipBox.y <= cursor.y + 20);
    await page.keyboard.press('Escape');
    await page.locator('#focus-toggle').focus();
    const buttonTooltip = await tooltip.boundingBox();
    assert.ok(buttonTooltip.x >= 0 && buttonTooltip.x + buttonTooltip.width <= 1440);
    assert.ok(buttonTooltip.y >= 0 && buttonTooltip.y + buttonTooltip.height <= 1000);
    await page.keyboard.press('Escape');

    await page.locator('#focus-toggle').click();
    await page.locator('#chapter-8 .implementation-detail').evaluate((detail) => {
      detail.open = true;
    });
    const detailStates = await page
      .locator('main details')
      .evaluateAll((details) => details.map((detail) => detail.open));
    await page.emulateMedia({ media: 'print' });
    await page.evaluate(() => dispatchEvent(new Event('beforeprint')));
    assert.equal(await page.locator('.toolbar').isVisible(), false);
    assert.equal(await page.locator('#chapter-10').isVisible(), true);
    assert.equal(await page.locator('#sources').isVisible(), true);
    assert.equal(await page.locator('main > .chapter:visible').count(), 10);
    assert.equal(await page.locator('.talk-track[open]').count(), 10);
    assert.equal(await page.locator('main details:not([open])').count(), 0);
    await page.evaluate(() => dispatchEvent(new Event('afterprint')));
    assert.equal(await page.locator('.talk-track[open]').count(), 0);
    assert.deepEqual(
      await page
        .locator('main details')
        .evaluateAll((details) => details.map((detail) => detail.open)),
      detailStates,
      'Printing must restore each previously open or closed report detail',
    );
    await page.emulateMedia({ media: 'screen', reducedMotion: 'reduce' });
    await page.reload();
    await page.evaluate(() => document.activeElement.blur());
    await page.keyboard.press('Tab');
    assert.equal(
      await page.locator('.skip').evaluate((element) => element === document.activeElement),
      true,
    );
    await page.keyboard.press('Enter');
    assert.equal(new URL(page.url()).hash, '#main');
    await page.locator('.rail nav a[href="#chapter-7"]').click();
    await page.waitForFunction(
      () =>
        document.querySelector('.rail nav a[href="#chapter-7"]').getAttribute('aria-current') ===
        'step',
    );
    await page.waitForFunction(() => {
      const top = document.getElementById('chapter-7').getBoundingClientRect().top;
      return top >= 0 && top <= 130;
    });
    await page.evaluate(() => scrollTo(0, 0));
    await page.waitForFunction(() => scrollY === 0);
    try {
      await page.waitForFunction(
        () =>
          document.querySelector('.rail nav a[href="#chapter-1"]').getAttribute('aria-current') ===
          'step',
        null,
        { timeout: 3000 },
      );
    } catch (error) {
      console.error(
        'Top-of-report navigation state:',
        await page.evaluate(() => ({
          scrollY,
          viewport: [innerWidth, innerHeight],
          active: document.querySelector('.rail [aria-current]')?.getAttribute('href'),
          bodyClass: document.body.className,
          hero: document.querySelector('.hero').getBoundingClientRect().toJSON(),
          first: document.getElementById('chapter-1').getBoundingClientRect().toJSON(),
          focused: document.activeElement?.id || document.activeElement?.tagName,
        })),
      );
      throw error;
    }
    await page.screenshot({ path: path.join(outputDirectory, 'desktop.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(outputDirectory, 'mobile.png') });
    await page.locator('#focus-toggle').click();
    await page.locator('#section-picker').selectOption('chapter-7');
    assert.equal(await page.locator('#chapter-7').isVisible(), true);
    assert.equal(await page.locator('#chapter-1').isVisible(), false);
    await page.locator('#section-picker').selectOption('sources');
    assert.equal(await page.locator('#sources').isVisible(), true);
    await page.locator('#focus-toggle').click();
    const touchContext = await browser.newContext({
      viewport: { width: 390, height: 844 },
      hasTouch: true,
      isMobile: true,
    });
    const touchPage = await touchContext.newPage();
    await touchPage.goto(url);
    await touchPage.locator('#chapter-1 .section-info').tap();
    assert.equal(await touchPage.locator('#report-tooltip').isVisible(), true);
    assert.match(await touchPage.locator('#report-tooltip').innerText(), /business problem/i);
    await touchContext.close();

    assert.deepEqual(errors, [], 'Browser errors');
    assert.deepEqual(networkRequests, [], 'Report unexpectedly fetched remote resources');
    const result = {
      status: 'pass',
      chapters: 10,
      allocatedSeconds: 900,
      spokenWords,
      capabilityMappings: content.mapRows,
      sources: content.sourceCount,
      widths,
      localLinks: 'pass',
      calculator: 'base, sensitivity, costs, negative results, invalid input',
      controls:
        'ten preserved talk tracks; single-section focus, all navigation, citations, history, mobile selector, keyboard and full-report print',
      tooltips:
        'all buttons and sections, acronyms, cursor positioning, keyboard, Escape, touch and viewport bounds',
      analytics:
        'actual 10/9/4 dossier composition; dynamic effort bars including overrun, zero baseline and invalid input',
      automatedAccessibility: 'pass',
      remoteResourceRequests: 0,
      screenshots: outputDirectory,
    };
    fs.writeFileSync(
      path.join(outputDirectory, 'validation.json'),
      `${JSON.stringify(result, null, 2)}\n`,
    );
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
