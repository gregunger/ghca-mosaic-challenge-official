// SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
// Verify offline report navigation, accessibility, layout and exact transcript rendering.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('@playwright/test');
const { default: AxeBuilder } = require('@axe-core/playwright');

const directory = path.resolve(process.argv[2] || 'examples/synthetic/expected');
const pages = fs.readdirSync(directory).filter((name) => name.endsWith('.html'));
const recordedPackage = JSON.parse(fs.readFileSync(path.join(directory, 'package.json'), 'utf8'));
const captureDirectory = path.resolve(
  __dirname,
  '../build/report-checks',
  path.basename(directory),
);

async function checkAccessibility(page, label) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();
  assert.deepEqual(
    results.violations.map((violation) => ({
      id: violation.id,
      nodes: violation.nodes.map((node) => ({ target: node.target, summary: node.failureSummary })),
    })),
    [],
    label,
  );
}

async function checkOperatorReport(browser) {
  const operatorDirectory = path.dirname(directory);
  const filename = path.join(operatorDirectory, 'processing-report.html');
  if (!fs.existsSync(filename)) return false;
  const metrics = JSON.parse(
    fs.readFileSync(path.join(operatorDirectory, 'processing-report.json'), 'utf8'),
  );
  const events = fs
    .readFileSync(path.join(operatorDirectory, 'pipeline-trace.jsonl'), 'utf8')
    .trim()
    .split('\n')
    .map((line) => JSON.parse(line));
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route(/^https?:\/\//, (route) => {
    errors.push(`Unexpected operator network request: ${route.request().url()}`);
    return route.abort();
  });
  try {
    await page.goto(pathToFileURL(filename).href);
    assert.equal(await page.locator('h1').innerText(), 'Processing Cost & Performance');
    const body = await page.locator('body').innerText();
    assert.ok(!body.includes('Not reported'));
    assert.equal(await page.locator('tbody tr').count(), events.length);
    const displayedSteps = await page.locator('tbody tr td:nth-child(3)').allTextContents();
    assert.deepEqual(
      displayedSteps,
      events.map((event) => event.step),
    );
    const cardText = (await page.locator('.cards').innerText()).trim();
    assert.ok(cardText.includes('Backend elapsed'));
    assert.ok(cardText.includes('Pipeline events'));
    if ((metrics.workerUsage.reportedAICredits ?? 0) > 0) {
      assert.ok(cardText.includes('Backend AI credits'));
      assert.ok(cardText.includes(String(metrics.workerUsage.reportedAICredits)));
    } else {
      assert.ok(!cardText.includes('Backend AI credits'));
    }
    assert.equal(await page.locator('script').count(), 0);
    for (const width of [1440, 1024, 768, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      assert.ok(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
        `Operator report overflow at ${width}`,
      );
      await checkAccessibility(page, `Operator report at ${width}`);
    }
    for (const href of ['processing-report.json', 'pipeline-trace.jsonl', 'status.html']) {
      assert.ok(fs.existsSync(path.join(operatorDirectory, href)));
      assert.equal(await page.locator(`a[href="${href}"]`).count(), 1);
    }
    await page.screenshot({
      path: path.join(captureDirectory, 'processing-report-mobile.png'),
      fullPage: true,
    });
    assert.deepEqual(errors, []);
    return true;
  } finally {
    await context.close();
  }
}

async function checkRecordedAnalytics(page, name) {
  const prose = (text) => text.replace(/\s+/gu, ' ').trim();
  const packageData = recordedPackage.package;
  const requirements = packageData.normalizedIntake.requirements;
  const claims = packageData.normalizedIntake.claims;
  const plans = packageData.proposedDesign.readinessPlans;
  const sources = packageData.evidenceManifest.sources;
  const blockers = packageData.analysis.unknowns
    .filter((unknown) => packageData.humanReview.blockingUnknownIds.includes(unknown.id))
    .map((unknown) => ({
      ...unknown,
      planIds: plans
        .filter((plan) => plan.blockingUnknownIds.includes(unknown.id))
        .map((plan) => plan.id),
    }))
    .sort(
      (left, right) =>
        right.planIds.length - left.planIds.length || left.id.localeCompare(right.id),
    );
  assert.ok(
    (await page.title()).startsWith(packageData.discovery.initiativeTitle),
    `${name}: use-case title`,
  );
  assert.ok(
    prose(await page.locator('body').innerText()).includes(
      prose(packageData.discovery.businessProblem),
    ),
    `${name}: business context`,
  );
  assert.equal(
    await page.getByText('Problem it solves', { exact: true }).count(),
    0,
    `${name}: noise`,
  );
  const helpText = await page
    .locator('section > .section-heading .help')
    .evaluateAll((elements) => elements.map((element) => element.dataset.definition));
  assert.ok(
    helpText.every((text) => text.length > 45 && !text.includes('Review the recorded')),
    `${name}: specific section help`,
  );
  const expectedCharts = {
    'index.html': [],
    'intake-report.html': ['risk-severity', 'source-dependencies'],
    'option-matrix.html': ['option-conditions'],
    'architecture-brief.html': ['requirement-plan'],
    'evidence-appendix.html': ['requirement-evidence', 'source-dependencies'],
    'human-review.html': blockers.length ? ['blocker-impact', 'blocker-plan'] : [],
    'meeting-request.html': ['meeting-allocation'],
    'meeting-agenda.html': ['meeting-allocation'],
    'talk-track.html': ['meeting-allocation'],
    'intake-transcript.html': packageData.discovery.intakeTranscript?.entries.length
      ? ['conversation-profile']
      : [],
  };
  for (const chart of expectedCharts[name] || []) {
    assert.equal(await page.locator(`[data-analytics="${chart}"]`).count(), 1, `${name}: ${chart}`);
  }
  const countCharts = {
    'source-dependencies': sources.flatMap((source) => [
      requirements.filter((item) => item.evidenceIds.includes(source.id)).length,
      claims.filter((item) => (item.evidenceIds || []).includes(source.id)).length,
    ]),
    'option-conditions': packageData.optionAnalysis.options.flatMap((option) => [
      option.conditions.length,
      option.disqualifiers.length,
    ]),
    'blocker-impact': blockers.map((blocker) => blocker.planIds.length),
  };
  for (const [chart, expected] of Object.entries(countCharts)) {
    const rows = page.locator(`[data-analytics="${chart}"] .count-row`);
    if (!(await rows.count())) continue;
    const actual = await rows.evaluateAll((elements) =>
      elements.map((element) => ({
        count: Number(element.dataset.count),
        maximum: Number(element.dataset.maximum),
        visible: Number(element.querySelector('.count-value').textContent),
        width: parseFloat(element.querySelector('.count-bar').style.width),
      })),
    );
    assert.deepEqual(
      actual.map((item) => item.count),
      expected,
      `${name}: ${chart} source counts`,
    );
    for (const item of actual) {
      assert.equal(item.visible, item.count);
      assert.ok(
        Math.abs(item.width - (item.count / item.maximum) * 100) <= 0.01,
        `${name}: proportional bar`,
      );
    }
  }
  const matrices = {
    'requirement-evidence': requirements.map((requirement) =>
      sources.map((source) => requirement.evidenceIds.includes(source.id)),
    ),
    'requirement-plan': requirements.map((requirement) =>
      plans.map((plan) => plan.requirementIds.includes(requirement.id)),
    ),
    'blocker-plan': blockers.map((blocker) =>
      plans.map((plan) => blocker.planIds.includes(plan.id)),
    ),
  };
  for (const [chart, expected] of Object.entries(matrices)) {
    const matrix = page.locator(`[data-analytics="${chart}"]`);
    if (!(await matrix.count())) continue;
    const actual = await matrix
      .locator('tbody tr')
      .evaluateAll((rows) =>
        rows.map((row) =>
          Array.from(row.querySelectorAll('td')).map((cell) =>
            Boolean(cell.querySelector('.trace-hit')),
          ),
        ),
      );
    assert.deepEqual(actual, expected, `${name}: ${chart} recorded relationships`);
  }
  if (await page.locator('[data-analytics="risk-severity"]').count()) {
    assert.deepEqual(
      await page.locator('.risk-chart .bar-row strong').allTextContents(),
      ['high', 'medium', 'low'].map((severity) =>
        String(
          packageData.analysis.risks.filter((risk) => risk.severity.toLowerCase() === severity)
            .length,
        ),
      ),
      `${name}: risk severity counts`,
    );
  }
  if (await page.locator('[data-analytics="meeting-allocation"]').count()) {
    const meeting = packageData.engagementPackage.meeting;
    const segments = await page.locator('.allocation-segment').evaluateAll((elements) =>
      elements.map((element) => ({
        minutes: Number(element.dataset.minutes),
        width: parseFloat(element.style.width),
      })),
    );
    assert.deepEqual(
      segments.map((segment) => segment.minutes),
      meeting.agenda.map((item) => item.minutes),
    );
    assert.equal(
      segments.reduce((total, segment) => total + segment.minutes, 0),
      meeting.durationMinutes,
    );
    for (const segment of segments)
      assert.ok(Math.abs(segment.width - (segment.minutes / meeting.durationMinutes) * 100) < 0.01);
  }
  if (await page.locator('[data-analytics="conversation-profile"]').count()) {
    const counts = await page
      .locator('[data-analytics="conversation-profile"] .count-row')
      .evaluateAll((elements) => elements.map((element) => Number(element.dataset.count)));
    assert.equal(
      counts.reduce((total, count) => total + count, 0),
      packageData.discovery.intakeTranscript.entries.length,
      'All captured entry types counted',
    );
  }
}

async function run() {
  fs.mkdirSync(captureDirectory, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const issues = [];
  const visited = [];
  let transcriptVerified = false;
  try {
    const context = await browser.newContext();
    await context.route(/^https?:/, (route) => {
      issues.push(`Unexpected network: ${route.request().url()}`);
      return route.abort();
    });
    const page = await context.newPage();
    page.on('pageerror', (error) => issues.push(error.message));
    for (const name of pages) {
      await page.goto(pathToFileURL(path.join(directory, name)).href);
      assert.ok(!(await page.title()).includes('<abbr'), name);
      assert.equal(await page.locator('h1').count(), 1, name);
      assert.equal(await page.getByRole('searchbox').count(), 0, `${name}: no report search`);
      assert.equal(await page.locator('svg abbr, [aria-hidden="true"] abbr').count(), 0, name);
      assert.equal(
        await page.locator('abbr[data-definition^="Abbreviation in the supplied text"]').count(),
        0,
        `${name}: undefined abbreviation`,
      );
      assert.equal(await page.locator('nav[aria-label="Documents"] a').count(), pages.length, name);
      assert.equal(
        await page.locator('section').count(),
        await page.locator('section > .section-heading .help').count(),
        name,
      );
      await checkRecordedAnalytics(page, name);
      if (recordedPackage.package.reportMetadata) {
        assert.equal(
          await page.locator('.brand span').textContent(),
          'Technical intake assessment',
        );
        if (name === 'index.html') {
          assert.deepEqual(
            await page
              .locator('.report-attribution time')
              .evaluateAll((elements) => elements.map((element) => element.dateTime)),
            [
              recordedPackage.package.reportMetadata.generatedAt,
              recordedPackage.metadata.timestamp,
            ],
          );
          assert.ok(
            (await page.locator('.report-submitter').textContent()).includes(
              recordedPackage.package.discovery.submittedBy.displayName,
            ),
          );
        }
      }
      const links = await page
        .locator('a[href]')
        .evaluateAll((elements) => elements.map((element) => element.getAttribute('href')));
      for (const href of links) {
        if (href.startsWith('#'))
          assert.equal(
            await page.locator(`[id="${href.slice(1)}"]`).count(),
            1,
            `${name}: ${href}`,
          );
        else {
          assert.ok(!/^(https?:|javascript:|data:)/i.test(href), `${name}: ${href}`);
          assert.ok(fs.existsSync(path.resolve(directory, href.split('#')[0])), `${name}: ${href}`);
        }
      }
      if (name === 'intake-transcript.html') {
        const transcript = JSON.parse(
          fs.readFileSync(path.join(directory, 'intake-transcript.json'), 'utf8'),
        );
        const expectedBlocks = [...transcript.gaps];
        for (const entry of transcript.entries) {
          if (entry.text !== null) expectedBlocks.push(entry.text);
          if (entry.context) expectedBlocks.push(entry.context);
          for (const option of entry.options) {
            expectedBlocks.push(option);
            if (entry.optionDescriptions?.[option])
              expectedBlocks.push(entry.optionDescriptions[option]);
          }
          expectedBlocks.push(...entry.selected, ...(entry.controls || []));
        }
        const renderedBlocks = await page.locator('.transcript-text > code').allTextContents();
        assert.deepEqual(
          renderedBlocks,
          expectedBlocks.map((value) => value.replace(/\r\n?/g, '\n')),
          'Transcript text and whitespace preserved',
        );
        const renderedTurns = await page.locator('.transcript-turn').evaluateAll((elements) =>
          elements.map((element) => ({
            sequence: Number(element.dataset.sequence),
            role: element.dataset.role,
            kind: element.dataset.kind,
            speaker: element.querySelector('.transcript-speaker').textContent,
            reply: element.querySelector('.transcript-reply')?.getAttribute('href') || null,
          })),
        );
        assert.deepEqual(
          renderedTurns,
          transcript.entries.map((entry) => ({
            sequence: entry.sequence,
            role: entry.role,
            kind: entry.kind,
            speaker:
              entry.role === 'user'
                ? recordedPackage.package.discovery.submittedBy.displayName
                : 'MOSAIC',
            reply: entry.replyTo === null ? null : `#transcript-entry-${entry.replyTo}`,
          })),
          'Transcript chronology, participants and actual reply relationships preserved',
        );
        assert.equal(
          await page.locator('.transcript-fidelity').count(),
          transcript.entries.filter((entry) => entry.fidelity === 'summary').length,
          'Fidelity warnings appear only for summarized capture',
        );
        const offeredChoices = page.locator('.transcript-choices').first();
        if (await offeredChoices.count()) {
          await offeredChoices.locator('summary').focus();
          await page.keyboard.press('Enter');
          assert.ok(
            await offeredChoices.evaluate((element) => element.open),
            'Choices open by keyboard',
          );
          await page.keyboard.press('Enter');
          assert.ok(
            !(await offeredChoices.evaluate((element) => element.open)),
            'Choices close by keyboard',
          );
        }
        transcriptVerified = true;
      }
      for (const width of [1440, 1024, 768, 390]) {
        await page.setViewportSize({ width, height: 1000 });
        const layout = await page.evaluate(() => ({
          overflow: document.documentElement.scrollWidth > innerWidth,
          headings: Array.from(document.querySelectorAll('h1,h2,h3'))
            .filter((element) => element.scrollWidth > element.clientWidth + 1)
            .map((element) => element.textContent),
          overlap: Array.from(document.querySelectorAll('.section-heading')).some((element) => {
            const heading = element.querySelector('h2').getBoundingClientRect();
            const button = element.querySelector('button').getBoundingClientRect();
            return heading.right > button.left + 1;
          }),
        }));
        assert.deepEqual(
          layout,
          { overflow: false, headings: [], overlap: false },
          `${name} at ${width}`,
        );
        if (name === 'index.html' && recordedPackage.package.reportMetadata) {
          const attribution = await page.locator('.report-attribution').boundingBox();
          const title = await page.locator('h1').boundingBox();
          const submitter = await page.locator('.report-submitter').boundingBox();
          const hero = await page.locator('.page-heading').boundingBox();
          assert.ok(
            Math.abs(attribution.x - title.x) < 1 && attribution.y >= title.y + title.height,
            `Attribution is below and left-aligned with title at ${width}`,
          );
          assert.ok(
            submitter.y >= attribution.y + attribution.height &&
              submitter.y + submitter.height <= hero.y + hero.height,
            `Attribution does not overlap nearby content at ${width}`,
          );
        }
      }
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.locator('.help').first().focus();
      await page.keyboard.press('Tab');
      await page.keyboard.press('Shift+Tab');
      assert.equal(
        await page.locator('#report-tooltip').isVisible(),
        true,
        `${name}: keyboard help; focused ${await page.evaluate(() => document.activeElement.outerHTML.slice(0, 500))}`,
      );
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#report-tooltip').isVisible(), false);
      await page.locator('#theme').selectOption('dark');
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
      await checkAccessibility(page, `${name}: dark theme accessibility`);
      await page.locator('#theme').selectOption('light');
      await checkAccessibility(page, `${name}: light theme accessibility`);
      await page.evaluate(() => scrollTo(0, 0));
      if (
        [
          'index.html',
          'evidence-appendix.html',
          'option-matrix.html',
          'intake-transcript.html',
          'architecture-brief.html',
          'human-review.html',
          'meeting-agenda.html',
          'meeting-request.html',
          'talk-track.html',
        ].includes(name)
      ) {
        await page.screenshot({
          path: path.join(captureDirectory, `${name.replace('.html', '')}-desktop.png`),
          fullPage: true,
        });
      }
      visited.push(name);
    }
    const touch = await browser.newContext({
      viewport: { width: 390, height: 844 },
      isMobile: true,
      hasTouch: true,
    });
    const mobilePage = await touch.newPage();
    mobilePage.on('pageerror', (error) => issues.push(error.message));
    await mobilePage.goto(pathToFileURL(path.join(directory, 'index.html')).href);
    await mobilePage.locator('.help').first().tap();
    assert.equal(
      await mobilePage.locator('#report-tooltip').isVisible(),
      true,
      'First touch opens help',
    );
    const tooltipBounds = await mobilePage.locator('#report-tooltip').boundingBox();
    assert.ok(tooltipBounds.x >= 0 && tooltipBounds.x + tooltipBounds.width <= 391);
    await mobilePage.locator('h1').tap();
    assert.equal(await mobilePage.locator('#report-tooltip').isVisible(), false);
    await mobilePage.locator('.open-nav').tap();
    assert.equal(await mobilePage.locator('.open-nav').getAttribute('aria-expanded'), 'true');
    await checkAccessibility(mobilePage, 'Mobile navigation accessibility');
    assert.equal(await mobilePage.getByRole('searchbox').count(), 0);
    assert.equal(
      await mobilePage.locator('.report-link:visible').count(),
      pages.length,
      'All document links remain directly available on mobile',
    );
    await mobilePage.locator('.close-nav').tap();
    assert.equal(await mobilePage.locator('.open-nav').getAttribute('aria-expanded'), 'false');
    await mobilePage.locator('.sidebar').waitFor({ state: 'hidden' });
    await checkAccessibility(mobilePage, 'Mobile overview accessibility');
    await mobilePage.screenshot({
      path: path.join(captureDirectory, 'overview-mobile.png'),
      fullPage: true,
    });
    if (pages.includes('intake-transcript.html')) {
      await mobilePage.goto(pathToFileURL(path.join(directory, 'intake-transcript.html')).href);
      const choices = mobilePage.locator('.transcript-choices').first();
      if (await choices.count()) {
        await choices.locator('summary').tap();
        assert.ok(
          await choices.evaluate((element) => element.open),
          'First touch opens transcript choices',
        );
        await choices.locator('summary').tap();
        assert.ok(
          !(await choices.evaluate((element) => element.open)),
          'Second touch closes transcript choices',
        );
      }
      await checkAccessibility(mobilePage, 'Mobile transcript accessibility');
      await mobilePage.screenshot({
        path: path.join(captureDirectory, 'intake-transcript-mobile.png'),
        fullPage: true,
      });
    }
    for (const name of ['meeting-agenda', 'architecture-brief', 'human-review']) {
      await mobilePage.goto(pathToFileURL(path.join(directory, `${name}.html`)).href);
      await checkAccessibility(mobilePage, `${name}: mobile accessibility`);
      await mobilePage.screenshot({
        path: path.join(captureDirectory, `${name}-mobile.png`),
        fullPage: true,
      });
    }
    const operatorReportVerified = await checkOperatorReport(browser);
    assert.deepEqual(issues, []);
    console.log(
      JSON.stringify({
        status: 'pass',
        pages: visited,
        widths: [1440, 1024, 768, 390],
        offlineLinks: true,
        keyboardAndTouchHelp: true,
        navigationAndThemes: true,
        automatedAccessibility: true,
        definedAbbreviations: true,
        capturedTranscriptPreserved: transcriptVerified,
        recordedAnalyticsVerified: true,
        specificReportAndSectionPurpose: true,
        operatorReportVerified,
      }),
    );
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
