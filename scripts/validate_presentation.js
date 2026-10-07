"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("@playwright/test");

const root = path.resolve(__dirname, "..");
const reportDirectory = path.join(root, "examples/synthetic/expected");
const reportUrl = pathToFileURL(path.join(reportDirectory, "intake-report.html")).href;
const optionUrl = pathToFileURL(path.join(reportDirectory, "option-matrix.html")).href;
const reviewUrl = pathToFileURL(path.join(reportDirectory, "human-review.html")).href;
const deckUrl = pathToFileURL(path.join(root, "presentation/mosaic-challenge-deck.html")).href;
const outputDirectory = path.join(root, "build/presentation-qa");

async function inspectLayout(page) {
  return page.evaluate(() => {
    const visible = element => element.getBoundingClientRect().width > 0;
    const overflowing = [...document.querySelectorAll("h1,h2,h3,p,figcaption,li")]
      .filter(visible)
      .filter(element => element.scrollWidth > element.clientWidth + 1)
      .map(element => element.textContent.trim().slice(0, 100));
    const collisions = [];
    for (const slide of document.querySelectorAll(".slide")) {
      const regions = [...slide.querySelectorAll("[data-region]")].filter(visible);
      for (let first = 0; first < regions.length; first += 1) {
        for (let second = first + 1; second < regions.length; second += 1) {
          const firstBox = regions[first].getBoundingClientRect();
          const secondBox = regions[second].getBoundingClientRect();
          if (Math.min(firstBox.right, secondBox.right) - Math.max(firstBox.left, secondBox.left) > 1
              && Math.min(firstBox.bottom, secondBox.bottom) - Math.max(firstBox.top, secondBox.top) > 1) {
            collisions.push([regions[first].dataset.region, regions[second].dataset.region]);
          }
        }
      }
    }
    return {
      width: innerWidth,
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      overflowing,
      collisions,
      imagesLoaded: [...document.images].every(image => image.complete && image.naturalWidth > 0),
    };
  });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 2 });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.message));
    if (process.argv.includes("--capture-report")) {
      await page.goto(reportUrl);
      const unknowns = page.locator('section[aria-labelledby="section-14"]');
      assert.equal(await unknowns.locator(".document-content li").count(), 4);
      await page.goto(optionUrl);
      assert.equal(await page.locator(".option-key").count(), 3);
      await page.goto(reviewUrl);
      assert.match(await page.locator(".review-status").innerText(), /Awaiting human review/i);
      const dimensions = await page.evaluate(() => ({ width: innerWidth, scale: devicePixelRatio }));
      assert.deepEqual(dimensions, { width: 1440, scale: 2 });
      await page.goto(reportUrl);
      await page.locator('section[aria-labelledby="section-14"]').screenshot({
        path: path.join(root, "presentation/mosaic-output.png"),
      });
      console.log(JSON.stringify({ status: "pass", capture: "generated-report-questions", ...dimensions }));
      return;
    }

    fs.mkdirSync(outputDirectory, { recursive: true });
    const checks = [];
    for (const width of [1440, 1024, 768, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(deckUrl);
      assert.equal(await page.locator(".slide").count(), 3);
      if (width === 1440) {
        const slideText = await page.locator(".slide .body").allTextContents();
        assert.match(slideText[0], /business need to governed/);
        assert.match(slideText[0], /GitHub Copilot App/);
        assert.match(slideText[0], /23-file dossier/);
        assert.match(slideText[0], /human decisions/);
        assert.match(slideText[1], /One governed flow, proven in the App/);
        assert.match(slideText[1], /unselected discussion draft/);
        assert.match(slideText[1], /awaiting human review/);
        assert.equal(await page.locator('.slide[data-slide="2"] img').count(), 2);
        assert.match(slideText[2], /Adoption motion and expected value/);
        assert.match(slideText[2], /not measured savings/);
      }
      await page.evaluate(() => Promise.all([...document.images].map(image => image.decode())));
      const layout = await inspectLayout(page);
      assert.equal(layout.documentOverflow, false, `Deck overflow at ${width}px`);
      assert.deepEqual(layout.overflowing, [], `Clipped deck text at ${width}px`);
      assert.deepEqual(layout.collisions, [], `Overlapping deck regions at ${width}px`);
      assert.equal(layout.imagesLoaded, true);
      const readability = await page.locator(".slide .body").evaluateAll(bodies => bodies.map(body => ({
        words: body.innerText.trim().split(/\s+/).length,
        jargon: body.innerText.match(/\b(?:SDLC|IaC|MCP|seeded|artifacts?|disqualifiers)\b/gi) || [],
        smallText: [...body.querySelectorAll("h1,h2,p,figcaption")]
          .filter(element => parseFloat(getComputedStyle(element).fontSize) < (element.tagName === "FIGCAPTION" ? 16 : 20))
          .map(element => element.textContent.trim()),
      })));
      for (const [index, result] of readability.entries()) {
        assert.ok(result.words <= 110, `Slide ${index + 1} has ${result.words} words; limit is 110`);
        assert.deepEqual(result.jargon, [], `Unexplained slide jargon at ${width}px`);
        assert.deepEqual(result.smallText, [], `Small slide text at ${width}px`);
      }
      for (let index = 0; index < 3; index += 1) {
        await page.locator(".slide").nth(index).screenshot({
          path: path.join(outputDirectory, `slide-${index + 1}-${width}.png`),
        });
      }
      checks.push({ surface: "deck", width, status: "pass", wordsPerSlide: readability.map(result => result.words) });
      await page.goto(reportUrl);
      const reportLayout = await inspectLayout(page);
      assert.equal(reportLayout.documentOverflow, false, `Report overflow at ${width}px`);
      assert.deepEqual(reportLayout.overflowing, [], `Clipped report text at ${width}px`);
      checks.push({ surface: "report", width, status: "pass" });
    }
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto(`${deckUrl}?slide=2`);
    assert.equal(await page.locator(".slide:visible").count(), 1);
    assert.equal(await page.locator(".slide:visible").getAttribute("data-slide"), "2");
    assert.deepEqual(pageErrors, []);
    const result = { status: "pass", checks, isolatedSlide: "pass", pageErrors };
    fs.writeFileSync(path.join(outputDirectory, "validation.json"), JSON.stringify(result, null, 2) + "\n");
    console.log(JSON.stringify(result, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});