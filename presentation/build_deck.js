"use strict";

const fs = require("node:fs");
const path = require("node:path");
const pptxgen = require("pptxgenjs");
const { imageSize } = require("image-size");

const OUTPUT = path.join(__dirname, "mosaic-challenge-deck.pptx");
const HTML_OUTPUT = path.join(__dirname, "mosaic-challenge-deck.html");
const APP_INTAKE_CAPTURE = path.join(__dirname, "assets", "contest-app-intake.png");
const REPORT_REVIEW_CAPTURE = path.join(__dirname, "assets", "contest-report-review.png");
const expandedName = "Multi-customer Orchestration System for Adaptive Intake and Continuous Delivery";

for (const asset of [APP_INTAKE_CAPTURE, REPORT_REVIEW_CAPTURE]) {
  if (!fs.existsSync(asset)) throw new Error(`Missing required presentation asset: ${asset}`);
}

const story = [
  {
    title: "MOSAIC",
    expandedName,
    subtitle: "From business need to governed\nsolution dossier—in minutes, not days.",
    premise: "Business user -> GitHub Copilot App -> governed analysis -> 23-file dossier -> human decisions.",
    outcomes: [
      ["Before", "Repeated discovery, copied notes and inconsistent handoffs."],
      ["With MOSAIC", "Adaptive intake, approved evidence and one review package."],
      ["Business value", "Less preparation and rework; experts focus on decisions."],
    ],
    takeaway: "Scale the expertise. Keep the accountability.",
  },
  {
    title: "One governed flow, proven in the App.",
    subtitle: "Synthetic example: trusted travel-policy guidance for 250 field employees.",
    intakeCaption: "GitHub Copilot App: plain-language request -> adaptive intake.",
    reportCaption: "Generated dossier: unselected discussion draft -> awaiting human review.",
    stages: [
      ["1 INTAKE", "Need, scope\n+ risks"],
      ["2 GOVERN", "Approved evidence\n+ bounded plan"],
      ["3 PREPARE", "Three options\n+ 23 files"],
      ["4 REVIEW", "Select architecture;\napprove revision later"],
    ],
    takeaway: "Authentic 2:55 recording. Architecture selection and design approval remain separate.",
  },
  {
    title: "Adoption motion and expected value.",
    subtitle: "Illustrative planning model—not measured savings or a customer forecast.",
    metrics: [
      ["96 hours", "Manual preparation"],
      ["16 hours", "Retained human review"],
      ["80 hours", "Potential effort saved: 83%"],
    ],
    value: "At $200/hour: $16,000 gross capacity per request.",
    scale: "$1.6M at 100 requests/year, before additional effort and operating costs.",
    reuse: "Adoption: synthetic proof -> customer benchmark -> isolated rollout -> scale.",
    fit: "Customer-specific evidence, templates, roles and approval rules.",
    takeaway: "Scale the expertise. Keep the accountability.",
  },
];

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Greg Unger";
pptx.company = "Microsoft";
pptx.subject = "FY27 GitHub Copilot App Enterprise Challenge";
pptx.title = `MOSAIC: ${expandedName}`;
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Bahnschrift",
  bodyFontFace: "Bahnschrift",
  lang: "en-US",
};
pptx.defineSlideMaster({
  title: "MOSAIC",
  background: { color: "FAFAFA" },
  objects: [
    { text: { text: "MICROSOFT / CUSTOMER ENGINEERING", options: { x: 0.64, y: 0.2, w: 7.1, h: 0.22, fontSize: 11, bold: true, color: "515151", margin: 0, charSpacing: 0 } } },
    { rect: { x: 11.62, y: 0.2, w: 0.32, h: 0.22, fill: { color: "78E3EA" }, line: { color: "78E3EA" } } },
    { rect: { x: 11.98, y: 0.2, w: 0.32, h: 0.22, fill: { color: "FF785D" }, line: { color: "FF785D" } } },
    { rect: { x: 12.34, y: 0.2, w: 0.32, h: 0.22, fill: { color: "F4CA58" }, line: { color: "F4CA58" } } },
    { line: { x: 0.64, y: 7.12, w: 12.02, h: 0, line: { color: "C8C8C8", width: 0.8 } } },
    { text: { text: "Synthetic reference. Impact not yet measured. Human approval required.", options: { x: 0.64, y: 7.22, w: 11.0, h: 0.2, fontSize: 11, color: "515151", margin: 0, charSpacing: 0 } } },
  ],
  slideNumber: { x: 12.15, y: 7.22, w: 0.5, h: 0.2, color: "515151", fontSize: 11, align: "right" },
});

const C = {
  ink: "171717",
  muted: "515151",
  paper: "FAFAFA",
  white: "FFFFFF",
  line: "C8C8C8",
  cyan: "78E3EA",
  coral: "FF785D",
  yellow: "F4CA58",
  blue: "005A9E",
};

const shape = pptx.ShapeType;

function text(slide, value, x, y, w, h, options = {}) {
  slide.addText(value, {
    x, y, w, h,
    fontFace: options.fontFace || "Bahnschrift",
    fontSize: options.fontSize || 14,
    color: options.color || C.ink,
    bold: options.bold || false,
    margin: options.margin === undefined ? 0 : options.margin,
    valign: options.valign || "mid",
    align: options.align || "left",
    breakLine: false,
    charSpacing: 0,
    bullet: options.bullet,
    isTextBox: true,
  });
}

function rect(slide, x, y, w, h, fill, line = fill, width = 0.8, dash = "solid") {
  slide.addShape(shape.rect, {
    x, y, w, h,
    fill: { color: fill },
    line: { color: line, width, dash },
  });
}

function line(slide, x, y, w, h, color = C.line, width = 1) {
  slide.addShape(shape.line, {
    x: Math.min(x, x + w), y: Math.min(y, y + h),
    w: Math.abs(w), h: Math.abs(h), flipH: w < 0, flipV: h < 0,
    line: { color, width, beginArrowType: "none", endArrowType: "none" },
  });
}

function title(slide, value, subtitle) {
  text(slide, value, 0.64, 0.76, 12.0, 0.61, { fontSize: 32, bold: true });
  text(slide, subtitle, 0.66, 1.48, 12.0, 0.53, { fontSize: 20, color: C.muted });
}

function fittedImage(slide, asset, x, y, width, height) {
  const size = imageSize(fs.readFileSync(asset));
  const scale = Math.min(width / size.width, height / size.height);
  const fittedWidth = size.width * scale;
  const fittedHeight = size.height * scale;
  slide.addImage({
    path: asset,
    x: x + (width - fittedWidth) / 2,
    y: y + (height - fittedHeight) / 2,
    w: fittedWidth,
    h: fittedHeight,
  });
}

function takeaway(slide, value) {
  rect(slide, 0, 6.42, 13.333, 0.55, C.ink);
  text(slide, value, 0.66, 6.47, 12.0, 0.44, {
    fontSize: 20, bold: true, color: C.white,
  });
}

{
  const content = story[0];
  const slide = pptx.addSlide("MOSAIC");
  rect(slide, 0, 0.62, 13.333, 3.56, C.ink);
  text(slide, content.title, 0.64, 0.73, 11.9, 1.02, { fontSize: 62, bold: true, color: C.cyan });
  text(slide, content.expandedName, 0.69, 1.78, 11.85, 0.3, { fontSize: 16, color: C.white });
  text(slide, content.subtitle, 0.67, 2.12, 11.9, 1.24, { fontSize: 37, bold: true, color: C.white });
  text(slide, content.premise, 0.69, 3.36, 11.85, 0.65, { fontSize: 20, color: C.white });
  content.outcomes.forEach(([heading, body], index) => {
    const position = 0.68 + index * 4.04;
    rect(slide, position, 4.49, 0.42, 0.08, [C.cyan, C.coral, C.yellow][index]);
    text(slide, heading, position, 4.79, 3.77, 0.42, { fontSize: 23, bold: true });
    text(slide, body, position, 5.25, 3.65, 1.03, { fontSize: 20 });
  });
  takeaway(slide, content.takeaway);
  slide.addNotes("MOSAIC means Multi-customer Orchestration System for Adaptive Intake and Continuous Delivery. It is AI-first business process automation and orchestration for the solution-engineering lifecycle, not merely a chatbot or document generator. In GitHub Copilot App, a business user describes a problem, requirement or opportunity in plain language. Adaptive intake asks relevant questions to clarify outcomes, scope, affected people, constraints and success measures. After explicit approval, MOSAIC acquires approved evidence, normalizes facts and unknowns, analyzes requirements and risks, compares exactly three options, prepares a proposed design and delivery-readiness plans, validates the package, and hands it to qualified people for decisions. The durable result is a 23-artifact dossier covering the business context, scope, requirements, assumptions, unknowns, risks, alternatives, proposed architecture, implementation, verification, interfaces, security, deployment and rollback, operations and adoption, measurement, evidence, validation, transcript, audit trail and meeting materials. This replaces repeated discovery, scattered research and reconstructed handoffs with one governed process. MOSAIC does not approve, implement or deploy the proposed customer solution. People still select the architecture, approve the exact dossier revision and authorize delivery. One isolated installation per customer supports the multi-customer distribution model. Reuse the process and controls, not restricted customer information. The executable reference uses prewritten scenario analysis; actual App evidence remains limited to saved instructions and source-tool calls. Cost, effort, reporting quality and lifecycle efficiency are evaluation targets, with illustrative planning economics on slide 3.");
}

{
  const content = story[1];
  const slide = pptx.addSlide("MOSAIC");
  title(slide, content.title, content.subtitle);
  text(slide, "AUTHENTIC APP INTAKE", 0.7, 2.02, 5.75, 0.22, { fontSize: 13, bold: true, color: C.muted });
  text(slide, "AUTHENTIC GENERATED OUTPUT", 6.88, 2.02, 5.75, 0.22, { fontSize: 13, bold: true, color: C.muted });
  fittedImage(slide, APP_INTAKE_CAPTURE, 0.7, 2.29, 5.75, 2.14);
  fittedImage(slide, REPORT_REVIEW_CAPTURE, 6.88, 2.29, 5.75, 2.14);
  text(slide, content.intakeCaption, 0.7, 4.52, 5.75, 0.56, { fontSize: 16, color: C.muted });
  text(slide, content.reportCaption, 6.88, 4.52, 5.75, 0.56, { fontSize: 16, color: C.muted });
  content.stages.forEach(([label, heading], index) => {
    const position = 0.7 + index * 3.04;
    rect(slide, position, 5.23, 2.81, 0.07, [C.cyan, C.coral, C.yellow, C.line][index]);
    text(slide, label, position, 5.37, 2.8, 0.2, { fontSize: 12, bold: true, color: C.muted });
    text(slide, heading, position, 5.61, 2.86, 0.58, { fontSize: 17, bold: true });
  });
  takeaway(slide, content.takeaway);
  slide.addNotes("Both images are lossless crops from the entrant's authentic 2 minute 55.57 second contest recording captured on October 7, 2026. The left frame shows the selected MOSAIC Orchestrator in GitHub Copilot App accepting the fictional Contoso travel-policy request and presenting an adaptive follow-up with End intake and generate report as option 1. The right frame shows the generated browser dossier from the same recorded run, labeled unselected discussion draft and awaiting human review. The workflow accepts a plain-language need, preserves unknowns, discloses a bounded generation plan, acquires only approved synthetic evidence, and prepares exactly three contrasting options plus the 23-artifact package: ten HTML pages, nine Markdown reports and four JSON records. An authorized customer role must first select the architecture. The selected full dossier then requires separate approval against its exact revision. The reference records neither decision and releaseAuthorized remains false. No solution is implemented, deployed or approved.");
}

{
  const content = story[2];
  const slide = pptx.addSlide("MOSAIC");
  title(slide, content.title, content.subtitle);
  content.metrics.forEach(([heading, body], index) => {
    const position = 0.7 + index * 4.04;
    line(slide, position, 2.38, 3.73, 0, [C.cyan, C.coral, C.yellow][index], 3);
    text(slide, heading, position, 2.62, 3.73, 0.64, { fontSize: 38, bold: true });
    text(slide, body, position, 3.36, 3.73, 0.4, { fontSize: 20 });
  });
  text(slide, content.value, 0.7, 4.12, 11.98, 0.49, { fontSize: 27, bold: true });
  text(slide, content.scale, 0.7, 4.73, 11.98, 0.43, { fontSize: 20, color: C.muted });
  text(slide, content.reuse, 0.7, 5.43, 11.98, 0.4, { fontSize: 20 });
  text(slide, content.fit, 0.7, 5.96, 11.98, 0.36, { fontSize: 20 });
  takeaway(slide, content.takeaway);
  slide.addNotes("The value follows from reducing repeated intake and design preparation, not from removing accountable judgment. ECO-001 is the entrant-provided internal planning brief, economic inputs on pages 4, 13-15 and 21-22; the confidential source remains outside Git. The planning range is 48-144 manual hours, with a 96-hour midpoint and assumed retained review of 16 hours. Base arithmetic: 96-16=80 hours returned; 80/96=83.33%; 80*$200/hour=$16,000 gross capacity per eligible request. At an illustrative 100 eligible requests/year, this is 8,000 hours and $1.6 million of gross capacity before additional effort and costs. The displayed base case assumes no other retained effort. Account for actual coordination, correction and exception effort, plus platform, integration, governance, support and operating costs. Do not double-count retained review costs or call released capacity cash savings. Review-time sensitivity at 24/16/8 hours gives 72/80/88 hours returned. These are not measured MOSAIC outcomes, a customer forecast, staffing commitments or a Copilot-versus-Claude benchmark. MOSAIC is designed for adoption from small businesses through large enterprises. Each isolated customer can supply its own evidence policy, terminology, report templates, required document profile, reviewer roles and approval rules while baseline controls remain non-removable. The contest reference demonstrates shared templates, customer-configured roles and document compatibility checks; arbitrary zero-code customization is not claimed. Reuse spans account teams, customer success, solution sales and developers. GitHub's documented issue, instruction, change and review surfaces provide workflow fit; Claude Code supports overlapping patterns. Sources: docs/evaluation-plan.md#planning-economics, docs/adoption-playbook.md, https://docs.github.com/en/copilot/how-tos/github-copilot-app and https://code.claude.com/docs/en/desktop (product documentation accessed September 15, 2026).");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[character]));
}

function htmlSections(sections) {
  return sections.map(([heading, body]) => `<div class="text-block"><h2>${escapeHtml(heading)}</h2><p>${escapeHtml(body)}</p></div>`).join("\n");
}

function renderHtml() {
  const layouts = [
    `<div class="outcomes">${htmlSections(story[0].outcomes)}</div>`,
    `<div class="proofs"><figure><span>AUTHENTIC APP INTAKE</span><img src="assets/contest-app-intake.png" alt="Authentic GitHub Copilot App adaptive intake from the final contest recording"><figcaption>${escapeHtml(story[1].intakeCaption)}</figcaption></figure><figure><span>AUTHENTIC GENERATED OUTPUT</span><img src="assets/contest-report-review.png" alt="Authentic generated MOSAIC report awaiting human review from the final contest recording"><figcaption>${escapeHtml(story[1].reportCaption)}</figcaption></figure></div><div class="workflow"><div class="stages">${story[1].stages.map(([label, heading]) => `<div class="stage"><span>${escapeHtml(label)}</span><h2>${escapeHtml(heading)}</h2></div>`).join("")}</div></div>`,
    `<div class="metrics">${htmlSections(story[2].metrics)}</div><div class="economic-model"><h2>${escapeHtml(story[2].value)}</h2><p>${escapeHtml(story[2].scale)}</p></div><div class="reuse"><p>${escapeHtml(story[2].reuse)}</p><p>${escapeHtml(story[2].fit)}</p></div>`,
  ];
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>MOSAIC Challenge Deck</title>
  <style>
    :root { --ink:#171717; --muted:#515151; --paper:#fafafa; --line:#c8c8c8; --cyan:#78e3ea; --coral:#ff785d; --yellow:#f4ca58; }
    * { box-sizing:border-box; }
    html,body { margin:0; color:var(--ink); font-family:"Bahnschrift","Trebuchet MS",sans-serif; letter-spacing:0; }
    body { background:#dedede; padding:24px; display:grid; gap:24px; }
    .slide { width:min(1280px,100%); height:720px; margin:auto; display:flex; flex-direction:column; background:var(--paper); }
    .top { height:58px; flex:none; padding:20px 62px; display:flex; justify-content:space-between; align-items:center; gap:18px; color:var(--muted); font-size:12px; font-weight:700; }
    .mark { display:flex; gap:4px; }
    .mark i { display:block; width:30px; height:20px; background:var(--cyan); }
    .mark i:nth-child(2) { background:var(--coral); }
    .mark i:nth-child(3) { background:var(--yellow); }
    .body { flex:1; min-height:0; display:grid; grid-template-rows:132px 1fr 54px; }
    header { padding:16px 62px 0; }
    h1 { margin:0; font-size:40px; line-height:1.13; }
    .subtitle { margin:13px 0 0; font-size:22px; line-height:1.32; color:var(--muted); white-space:pre-line; }
    h2 { margin:0; font-size:26px; line-height:1.2; }
    p { margin:0; font-size:22px; line-height:1.35; }
    .layout { padding:16px 66px 12px; min-height:0; }
    .outcomes,.metrics { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:32px; }
    .text-block { border-top:5px solid var(--cyan); padding-top:18px; }
    .text-block:nth-child(2) { border-color:var(--coral); }
    .text-block:nth-child(3) { border-color:var(--yellow); }
    .text-block p { margin-top:14px; }
    .slide-1 .body { grid-template-rows:342px 1fr 54px; }
    .slide-1 header { background:var(--ink); padding-top:20px; color:white; }
    .slide-1 h1 { font-size:84px; line-height:1; color:var(--cyan); }
    .expanded-name { margin-top:6px; font-size:20px; line-height:1.3; }
    .slide-1 .subtitle { color:white; font-size:46px; font-weight:700; line-height:1.16; margin-top:13px; }
    .premise { margin-top:20px; font-size:22px; }
    .slide-1 .layout { padding-top:30px; }
    .slide-1 .text-block { padding-top:17px; }
    .slide-1 .text-block p { font-size:22px; }
    figure { margin:0; min-height:0; display:flex; flex-direction:column; gap:12px; }
    figure a { display:flex; min-height:0; justify-content:center; }
    figure img { display:block; width:100%; height:100%; min-height:0; object-fit:contain; }
    figure>span { font-size:14px; color:var(--muted); font-weight:700; }
    figcaption { flex:none; font-size:16px; color:var(--muted); line-height:1.35; }
    .flow { display:grid; grid-template-rows:284px 1fr; gap:14px; padding-top:8px; }
    .proofs { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:32px; min-height:0; }
    .proofs figure { gap:8px; }
    .proofs figure img { height:218px; }
    .boundary { font-weight:700; font-size:22px; }
    .workflow .boundary { margin-top:12px; font-size:20px; }
    .stages { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:22px; }
    .stage { border-top:5px solid var(--line); padding-top:13px; }
    .stage:first-child { border-color:var(--cyan); }
    .stage:nth-child(2) { border-color:var(--coral); }
    .stage:nth-child(3) { border-color:var(--yellow); }
    .stage span { font-size:14px; color:var(--muted); font-weight:700; }
    .stage h2 { margin-top:10px; font-size:22px; white-space:pre-line; }
    .example h2 { font-size:24px; }
    .example p { margin-top:12px; font-size:20px; }
    .economics { display:grid; grid-template-rows:142px 106px 1fr; gap:26px; padding-top:30px; }
    .metrics h2 { font-size:40px; }
    .metrics p { font-size:20px; }
    .economic-model h2 { font-size:28px; }
    .economic-model p { margin-top:16px; font-size:22px; color:var(--muted); }
    .reuse p { font-size:20px; }
    .reuse p+p { margin-top:16px; }
    .takeaway { padding:13px 62px; color:white; background:var(--ink); font-size:22px; font-weight:700; line-height:1.25; }
    .footer { margin:14px 62px 10px; padding-top:10px; border-top:1px solid var(--line); font-size:12px; color:var(--muted); display:flex; justify-content:space-between; gap:16px; }
    .footer>span:last-child { white-space:nowrap; flex:none; }
    @media screen and (max-width:1100px) {
      .slide { height:auto; min-height:720px; }
      .body,.slide-1 .body { grid-template-rows:auto 1fr auto; }
      header { padding:22px 32px; }
      h1 { font-size:34px; }
      .top { padding-inline:32px; }
      .slide-1 h1 { font-size:76px; }
      .slide-1 .subtitle { font-size:38px; }
      .layout { padding:24px 32px; }
      .outcomes,.metrics { gap:24px; }
      .flow,.economics { grid-template-rows:auto auto auto; gap:28px; }
      .takeaway { padding-inline:32px; }
      .footer { margin-inline:32px; }
    }
    @media screen and (max-width:800px) {
      body { padding:12px; gap:16px; }
      .slide { min-height:0; }
      .top { height:auto; padding:16px 20px; font-size:10px; gap:12px; }
      .mark i { width:13px; height:13px; }
      header { padding:24px 20px; }
      h1 { font-size:30px; }
      .slide-1 h1 { font-size:64px; }
      .slide-1 .subtitle { font-size:32px; }
      .premise { font-size:20px; margin-top:20px; }
      .layout { padding:24px 20px; }
      .outcomes,.metrics,.proofs { grid-template-columns:minmax(0,1fr); gap:26px; }
      .proofs figure img { height:auto; }
      .stages { grid-template-columns:repeat(2,minmax(0,1fr)); gap:24px; }
      .stage h2 { font-size:20px; }
      figure img { height:auto; }
      .takeaway { padding:16px 20px; font-size:20px; }
      .footer { margin:16px 20px 14px; }
    }
    @page { size:13.333in 7.5in; margin:0; }
    @media print {
      body { padding:0; gap:0; background:white; display:block; }
      .slide { width:13.333in; height:7.5in; break-after:page; }
      .slide:last-child { break-after:auto; }
    }
  </style>
</head>
<body>
${story.map((content, index) => `<section class="slide slide-${index + 1}" data-slide="${index + 1}">
  <div class="top"><span>MICROSOFT / CUSTOMER ENGINEERING</span><span class="mark" aria-hidden="true"><i></i><i></i><i></i></span></div>
  <div class="body">
    <header data-region="heading"><h1>${escapeHtml(content.title)}</h1>${index === 0 ? `<p class="expanded-name">${escapeHtml(content.expandedName)}</p>` : ""}<p class="subtitle">${escapeHtml(content.subtitle)}</p>${index === 0 ? `<p class="premise">${escapeHtml(content.premise)}</p>` : ""}</header>
    <div class="layout ${index === 1 ? "flow" : index === 2 ? "economics" : ""}" data-region="content">${layouts[index]}</div>
    <p class="takeaway" data-region="takeaway">${escapeHtml(content.takeaway)}</p>
  </div>
  <footer class="footer" data-region="footer"><span>Synthetic reference. Impact not yet measured. Human approval required.</span><span>${index + 1} / 3</span></footer>
</section>`).join("\n")}
  <script>
    const requested = new URLSearchParams(location.search).get("slide");
    if (["1", "2", "3"].includes(requested)) {
      document.body.style.padding = "0";
      document.body.style.gap = "0";
      document.querySelectorAll(".slide").forEach(slide => {
        slide.style.display = slide.dataset.slide === requested ? "flex" : "none";
      });
    }
  </script>
</body>
</html>\n`;
}

async function main() {
  await pptx.writeFile({ fileName: OUTPUT });
  fs.writeFileSync(HTML_OUTPUT, renderHtml());
  console.log(JSON.stringify({ status: "pass", slides: story.length, outputs: [OUTPUT, HTML_OUTPUT] }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
