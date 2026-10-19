// SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const pptxgen = require('pptxgenjs');
const { imageSize } = require('image-size');

const root = path.resolve(__dirname, '..');
const output = path.join(__dirname, 'mosaic-copilot-app-demo-15min.pptx');
const qa = path.join(root, 'build', 'copilot-app-demo-qa');
const revision = '4d1865687cdd0cdf6fe0777ac102085a2f1d5c9e';
const repository = `https://github.com/gregunger/ghca-mosaic-challenge-official/blob/${revision}/`;
const tree = `https://github.com/gregunger/ghca-mosaic-challenge-official/tree/${revision}/`;
const docs = 'https://docs.github.com/en/copilot/';
const verified = '2026-10-19';
const video = 'https://youtu.be/RP4CeCYt4VE';
const videoSeconds = 175.57;
const assets = {
  intake: path.join(__dirname, 'assets', 'contest-app-intake.png'),
  report: path.join(__dirname, 'assets', 'contest-report-review.png'),
  mcp: path.join(__dirname, 'assets', 'copilot-app-detail.png'),
};

const sources = {
  S01: [
    'App overview and shared CLI foundation',
    `${docs}concepts/copilot-surfaces/github-copilot-app`,
  ],
  S02: [
    'App instructions, skills, agents, MCP and plugins',
    `${docs}how-tos/github-copilot-app/customize-github-copilot-app`,
  ],
  S03: [
    'Sessions, modes, worktrees, models, voice and history',
    `${docs}how-tos/github-copilot-app/agent-sessions`,
  ],
  S04: [
    'Complete public App slash-command reference',
    `${docs}reference/github-copilot-app-reference/slash-commands`,
  ],
  S05: [
    'All six GitHub-provided built-in App skills',
    `${docs}reference/github-copilot-app-reference/built-in-skills`,
  ],
  S06: ['Plugin formats, hooks, LSP and marketplaces', `${docs}concepts/agents/about-plugins`],
  S07: [
    'Bidirectional canvases and canvas extensions',
    `${docs}how-tos/github-copilot-app/working-with-canvas-extensions`,
  ],
  S08: [
    'Microsoft Work IQ: all four marketplace plugins',
    'https://github.com/microsoft/work-iq/blob/main/PLUGINS.md',
  ],
  S09: ['Work IQ preview status and tenant consent', 'https://github.com/microsoft/work-iq'],
  S10: ['App BYOK providers and requirements', `${docs}how-tos/github-copilot-app/use-byok-models`],
  S11: [
    'Computer use: capabilities, permissions and risks',
    `${docs}concepts/agent-capabilities/agent-powered-workflows-and-operations/computer-use`,
  ],
  S12: [
    'My work, issues, PRs, checks and agent merge',
    `${docs}how-tos/github-copilot-app/managing-issues-and-pull-requests`,
  ],
  S13: [
    'Enterprise-managed settings and client coverage',
    `${docs}how-tos/administer-copilot/manage-for-enterprise/use-managed-settings/get-started`,
  ],
  S14: ['MCP, server toolsets, Registry and Agent Finder', `${docs}concepts/context/mcp`],
  S15: ['Copilot SDK: programmatic use of the CLI engine', 'https://github.com/github/copilot-sdk'],
  S16: [
    'App deep links from tickets, portals and scripts',
    `${docs}how-tos/github-copilot-app/open-with-deep-links`,
  ],
  S17: ['Reusable project and personal agent skills', `${docs}concepts/agents/about-agent-skills`],
  S18: [
    'Custom agents and profile/tool scopes',
    `${docs}concepts/agents/cloud-agent/about-custom-agents`,
  ],
  S19: ['Playwright MCP browser tools', 'https://github.com/microsoft/playwright-mcp'],
  S20: ['Azure DevOps MCP integration', 'https://github.com/microsoft/azure-devops-mcp'],
  S21: [
    'Claude Desktop: Chat, Cowork and Code capabilities',
    'https://code.claude.com/docs/en/desktop',
  ],
  S22: [
    'VS Code agent harnesses and shared Copilot runtime',
    'https://code.visualstudio.com/docs/agents/run/agent-harnesses',
  ],
  S23: [
    'Visual Studio agent mode and shared SDK foundation',
    'https://learn.microsoft.com/en-us/visualstudio/ide/copilot-agent-mode?view=visualstudio',
  ],
  M01: [
    'Authentic App/report captures and provenance',
    `${repository}presentation/assets/README.md`,
  ],
  M02: ['MOSAIC architecture and implementation boundaries', `${repository}docs/architecture.md`],
  M03: [
    'Canonical synthetic dossier and human-review record',
    `${tree}examples/synthetic/expected`,
  ],
  M04: ['Five configured MOSAIC agent profiles', `${tree}.github/agents`],
  M05: [
    'Illustrative economics and measurement plan',
    `${repository}docs/evaluation-plan.md#planning-economics`,
  ],
  M06: ['Field reuse and adoption path', `${repository}docs/adoption-playbook.md`],
  M07: [
    'Observed App skill and read-only MCP rehearsal',
    `${repository}docs/product-feedback-observation-log.md`,
  ],
};

function capability(name, use, state, refs, mainSlide, commands = [], skills = []) {
  return { name, use, state, refs, mainSlide, commands, skills };
}

// Each public command and built-in skill is mapped, including unsafe-to-enable defaults.
const groups = [
  {
    title: 'Intake and direction',
    features: [
      capability(
        'Chats before a workspace',
        'Scope a need before opening an implementation workstream.',
        'Extension',
        ['S01', 'S03'],
        2,
      ),
      capability(
        'Interactive sessions',
        'Ask relevant business questions in the App; keep the requester involved.',
        'App proof',
        ['S03', 'M01'],
        4,
        ['/interactive'],
      ),
      capability(
        'Plan mode',
        'Declare sources, tools, output and stop conditions before generation.',
        'Configured',
        ['S03', 'M02'],
        12,
        ['/plan'],
      ),
      capability(
        'Autopilot mode',
        'Run an approved, bounded preparation task; never bypass customer decisions.',
        'Extension',
        ['S03', 'M02'],
        12,
        ['/autopilot'],
      ),
      capability(
        'File and folder attachments',
        'Bring approved briefs into context; @ files and # issues reduce re-entry.',
        'Extension',
        ['S03', 'S04'],
        2,
        ['/attach-files', '/attach-folder'],
      ),
      capability(
        'Voice dictation',
        'Speak an intake prompt, then review the locally transcribed text before sending.',
        'Extension',
        ['S03'],
        2,
      ),
    ],
  },
  {
    title: 'Workspaces and reach',
    features: [
      capability(
        'Parallel sessions and worktrees',
        'Prepare independent workstreams on separate branches, then reconcile changes.',
        'Extension',
        ['S01', 'S03'],
        7,
      ),
      capability(
        'Local folders and Git URLs',
        'Reuse the workflow in an approved local repo, including non-GitHub Git hosts.',
        'Extension',
        ['S03'],
        14,
      ),
      capability(
        'Cloud sandboxes + setup skill',
        'Move suitable work off the laptop; configure the cloud environment explicitly.',
        'Extension',
        ['S03', 'S05'],
        14,
        [],
        ['customize-cloud-agent'],
      ),
      capability(
        'Local sandbox controls',
        'Limit tool access to files, networks and credentials where supported.',
        'Extension',
        ['S03', 'S04'],
        12,
        ['/sandbox on', '/sandbox off'],
      ),
      capability(
        'Remote session control',
        'Steer an authorized session from GitHub.com or GitHub Mobile, subject to policy.',
        'Extension',
        ['S04'],
        11,
        ['/remote'],
      ),
      capability(
        'Deep links into the App',
        'Launch a scoped intake from an internal portal or ticket; never put secrets in URLs.',
        'Extension',
        ['S16'],
        15,
      ),
    ],
  },
  {
    title: 'Models and the shared runtime',
    features: [
      capability(
        'Copilot CLI agent harness',
        'Reuse planning and tool execution; MOSAIC supplies domain rules and validation.',
        'App + worker',
        ['S01', 'S15', 'M02'],
        8,
      ),
      capability(
        'Model selection',
        'Choose a permitted model for the task instead of tying the workflow to one model.',
        'Extension',
        ['S03', 'S04'],
        8,
        ['/model', '/models'],
      ),
      capability(
        'Auto model selection',
        'Let the App select a model for task complexity; evaluate quality and consumption.',
        'Extension',
        ['S03'],
        8,
      ),
      capability(
        'Reasoning effort',
        'Allocate more reasoning to difficult tradeoffs, less to straightforward preparation.',
        'Extension',
        ['S03'],
        8,
      ),
      capability(
        'Bring your own key (BYOK)',
        'Evaluate approved hosted or local providers; this is a preview App capability.',
        'Extension',
        ['S10'],
        8,
      ),
      capability(
        'Copilot SDK integration',
        'Embed the same CLI engine in a future service; separate from this App experience.',
        'SDK path',
        ['S15', 'M02'],
        8,
      ),
    ],
  },
  {
    title: 'Connected business context',
    features: [
      capability(
        'Local / remote MCP and toolsets',
        'Connect approved tools. App proof: two read-only tools, four synthetic sources.',
        'App proof',
        ['S02', 'S14', 'M07'],
        5,
      ),
      capability(
        'WorkIQ',
        'Propose permissioned M365 evidence retrieval; its full tool surface also has writes.',
        'Extension',
        ['S08', 'S09'],
        5,
      ),
      capability(
        'WorkIQ preview',
        'Evaluate retrieve-first grounding and exact operations; tenant-gated, not automatic.',
        'Extension',
        ['S08', 'S09'],
        5,
      ),
      capability(
        'WorkIQ productivity',
        'Use the ten read-only insight skills for approved project and engagement context.',
        'Extension',
        ['S08'],
        5,
      ),
      capability(
        'Azure DevOps MCP',
        'Bring approved work items, repo, wiki, pipeline and test context into preparation.',
        'Extension',
        ['S20', 'S14'],
        5,
      ),
      capability(
        'Browser tools via Playwright MCP',
        'Inspect and exercise approved report UIs; an optional integration, not App footage.',
        'Extension',
        ['S19', 'M02'],
        9,
      ),
    ],
  },
  {
    title: 'Reusable expertise',
    features: [
      capability(
        'Global App instructions',
        'Set organization-approved expectations for every session, not just one prompt.',
        'Extension',
        ['S02'],
        6,
      ),
      capability(
        'Repository instructions + /init',
        'Version MOSAIC workflow, evidence boundaries and human-review requirements.',
        'Configured',
        ['S02', 'S04', 'M02'],
        6,
        ['/init'],
      ),
      capability(
        'Project and personal skills',
        'Package repeatable intake/review procedures; manage and reload skills as needed.',
        'App proof',
        ['S17', 'S04', 'M07'],
        6,
        ['/skills', '/skills reload'],
      ),
      capability(
        'Custom agents and tool scopes',
        'Select the Orchestrator and reuse four specialist profiles; constrain their tools.',
        'Configured',
        ['S18', 'M04'],
        7,
        ['/agent'],
      ),
      capability(
        'Plugins and marketplaces',
        'Distribute approved skills, agents, hooks, MCP and canvases as a reusable package.',
        'Extension',
        ['S02', 'S06'],
        6,
      ),
      capability(
        'Agent Finder + MCP Registry',
        'Discover relevant tools, agents, skills and servers; inspect before installing.',
        'Extension',
        ['S05', 'S14'],
        6,
        ['/af'],
        ['af'],
      ),
    ],
  },
  {
    title: 'Extension interfaces',
    features: [
      capability(
        'Plugin hooks',
        'Add supported lifecycle checks or audit integrations; validate enforcement behavior.',
        'Extension',
        ['S02', 'S06'],
        6,
      ),
      capability(
        'Plugin LSP configurations',
        'Supply language-aware context for future code work; client support must be verified.',
        'Extension',
        ['S06'],
        6,
      ),
      capability(
        'Canvases and canvas extensions',
        'Build a shared intake, options or evidence board with human and agent actions.',
        'Extension',
        ['S07', 'S05'],
        9,
        ['/create-canvas'],
        ['create-canvas'],
      ),
      capability(
        'Computer use',
        'Reach GUI-only applications on Windows/macOS; opt-in preview, disabled by default.',
        'Extension',
        ['S11'],
        9,
      ),
      capability(
        'M365 Agents Toolkit plugin',
        'Support a later M365 agent build/evaluation handoff under separate implementation authority.',
        'Extension',
        ['S08'],
        5,
      ),
      capability(
        'Customer-specific MCP adapters',
        'Extend to approved knowledge or business systems; no prebuilt adapter is assumed.',
        'Extension',
        ['S14', 'M02'],
        5,
      ),
    ],
  },
  {
    title: 'Delegation and challenge',
    features: [
      capability(
        'Cross-session orchestration',
        'Coordinate child sessions and repositories for a larger, explicitly scoped engagement.',
        'Extension',
        ['S04', 'S05'],
        7,
        ['/orchestrate'],
        ['orchestrate'],
      ),
      capability(
        'Parallel agent fleets',
        'Split an independent task into parallel specialist work, then reconcile the result.',
        'Extension',
        ['S04', 'M04'],
        7,
        ['/fleet'],
      ),
      capability(
        'Focused child sessions',
        'Delegate a bounded evidence or architecture question without losing the parent task.',
        'Extension',
        ['S04'],
        7,
        ['/spawn'],
      ),
      capability(
        'Session fork and merge',
        'Explore a branch of the work and deliberately bring accepted changes back.',
        'Extension',
        ['S04'],
        7,
        ['/fork', '/merge-to-parent'],
      ),
      capability(
        'Cited research',
        'Investigate approved sources and retain citations; findings still need qualified review.',
        'Extension',
        ['S04'],
        8,
        ['/research'],
      ),
      capability(
        'Rubber duck and sparring',
        'Use a different-model critique and adversarial reasoning; neither grants approval.',
        'Extension',
        ['S03', 'S04'],
        8,
        ['/rubber-duck', '/spar'],
      ),
    ],
  },
  {
    title: 'GitHub-native accountability',
    features: [
      capability(
        'My work, filters and inbox',
        'Find requests and review obligations in one App workspace.',
        'Extension',
        ['S12', 'S04'],
        10,
        ['/inbox'],
      ),
      capability(
        'Issue context and templates',
        'Start an intake from an issue, or create a scoped follow-up using repo conventions.',
        'Extension',
        ['S12'],
        10,
      ),
      capability(
        'PRs, diffs and review comments',
        'Open a reviewable change, inspect it, and address feedback using the repo template.',
        'Extension',
        ['S12', 'S04'],
        10,
        ['/pr-open', '/review', '/pr-resolve-comments'],
      ),
      capability(
        'CI checks and targeted fixes',
        'See check results and ask for fixes; local tests are not evidence of hosted CI.',
        'Extension',
        ['S12', 'S04', 'M02'],
        10,
        ['/pr-fix-checks'],
      ),
      capability(
        'Stacked pull requests',
        'Separate dependent changes into reviewable layers with child sessions.',
        'Extension',
        ['S05'],
        10,
        ['/pr-stack'],
        ['pr-stack'],
      ),
      capability(
        'Agent merge and PR merge',
        'App can resolve blockers and merge. MOSAIC does not treat a merge as customer approval.',
        'Restricted',
        ['S12', 'S05', 'S04'],
        10,
        ['/pr-merge'],
        ['agent-merge'],
      ),
    ],
  },
  {
    title: 'Continuity and efficiency',
    features: [
      capability(
        'Scheduled / on-demand automations',
        'Propose recurring evidence-refresh drafts; no automatic customer approval or release.',
        'Extension',
        ['S01', 'M02'],
        11,
      ),
      capability(
        'Chronicle history and insights',
        'Search, summarize, reindex and improve sessions; history is not approved evidence.',
        'Extension',
        ['S03', 'S04'],
        11,
        [
          '/chronicle',
          '/chronicle cost-tips',
          '/chronicle improve',
          '/chronicle reindex',
          '/chronicle search',
          '/chronicle standup',
          '/chronicle tips',
        ],
      ),
      capability(
        'Context usage and compaction',
        'Inspect context pressure and summarize long sessions; retain the authoritative dossier.',
        'Extension',
        ['S04'],
        11,
        ['/context', '/compact'],
      ),
      capability(
        'Session and chat management',
        'Rename, restart, clear, archive, restore, search and manage storage deliberately.',
        'Extension',
        ['S03', 'S04'],
        11,
        ['/rename', '/restart-session', '/clear', '/reset'],
      ),
      capability(
        'Usage and rate-limit visibility',
        'Monitor the App allowance and usage; distinguish it from MOSAIC worker cost records.',
        'Extension',
        ['S01', 'S04', 'M02'],
        13,
        ['/usage'],
      ),
      capability(
        'Terminal and local tool execution',
        'Run approved preparation and validation workers from the App-directed workflow.',
        'App + worker',
        ['S04', 'M02'],
        8,
        ['/terminal'],
      ),
    ],
  },
  {
    title: 'Control and administration',
    features: [
      capability(
        'Tool permissions and auto-approval',
        'Inspect or reset approvals. Broad auto-approval must not override MOSAIC boundaries.',
        'Restricted',
        ['S04', 'M02'],
        12,
        ['/allow-all-tools', '/yolo', '/reset-allowed-tools'],
      ),
      capability(
        'Enterprise-managed settings',
        'Govern supported model, plugin, tool and sandbox settings; check client coverage.',
        'Extension',
        ['S02', 'S13'],
        12,
      ),
      capability(
        'Content exclusion',
        'The App respects configured exclusions; confirm scope and other policy limitations.',
        'Extension',
        ['S01'],
        12,
      ),
      capability(
        'Security-focused review',
        'Use the preview review command for code changes; not a certification or security sign-off.',
        'Extension',
        ['S03', 'S04'],
        12,
        ['/security-review'],
      ),
      capability(
        'Debug logs and transcript export',
        'Debug locally under policy. Never export raw customer context to a gist by default.',
        'Restricted',
        ['S04', 'M02'],
        11,
        ['/debug', '/collect-debug-logs', '/export-gist'],
      ),
      capability(
        'Access, navigation and discovery',
        'App on Windows/macOS/Linux; GitHub sign-in, App policy, keyboard shortcuts and / picker.',
        'Documented',
        ['S01', 'S03', 'S04'],
        14,
      ),
    ],
  },
];

const slides = [
  {
    title: 'Turn expertise into repeatable work.',
    seconds: 35,
    refs: ['S01', 'M02'],
    kind: 'cover',
    claim: 'recommendation',
    talk: `If GitHub is where your team works, make GitHub Copilot App your agent workspace. It combines native GitHub review, broad model choice and reusable expertise in a dedicated desktop experience. MOSAIC makes that recommendation tangible: a business conversation becomes a governed solution-engineering discussion draft. You bring approved context and decision rights; the App brings the working environment. We recommend it for that combination, not because other tools cannot run agents. Watch the workflow, then identify the expertise your team could package next.`,
  },
  {
    title: 'Give teams their context back.',
    seconds: 45,
    refs: ['S01', 'S03', 'M02', 'M06'],
    kind: 'before',
    claim: 'recommendation',
    talk: `A requester describes a need. A solution engineer searches for the right guidance. Reviewers ask for the missing assumptions and alternatives. Too often, each handoff means rebuilding context. The opportunity is not another chat window. It is a repeatable way to carry intent, evidence and decisions through the work. In the App, a conversation, an attached approved brief or an issue can become the starting point. MOSAIC adds the domain process. The target is less repeated preparation and clearer review, not the removal of the people accountable for the result.`,
  },
  {
    title: 'Why choose Copilot App for GitHub teams?',
    seconds: 55,
    refs: ['S01', 'S02', 'S03', 'S10', 'S12', 'M02'],
    kind: 'positioning',
    claim: 'recommendation',
    talk: `Our recommendation rests on three customer needs. First, GitHub is already your system for engineering work: direct agents and review issues, changes and checks in a first-party GitHub workspace. Second, you want model choice: select permitted models and evaluate approved hosted or local BYOK providers in preview. Third, you want expertise to travel: package procedures and integrations as skills, agents, MCP and plugins. Choose Copilot App when you want those needs served together in a dedicated workspace. This is a best-fit recommendation for that customer profile, not a universal winner claim. MOSAIC shows the reusable workflow pattern.`,
  },
  {
    title: 'Watch the App do the coordinating.',
    seconds: 200,
    refs: ['M01', 'M02', 'M03', 'M07'],
    kind: 'demo',
    claim: 'fact',
    talk: `Watch three things: the App carries the conversation, bounded preparation turns intent into inspectable work, and the requester opens the dossier without writing JSON. This is authentic recorded App use. MOSAIC supplies the domain rules and validation. The result remains a discussion draft.`,
    cue: `Allow 24.43 seconds for this introduction and the playback handoff, then play the complete 2:55.57 published clip: ${video}. Do not add the separate 10:12 walkthrough. If playback is unavailable, use the authentic intake image here, the report image on slide 9, and the MCP crop on slide 5 for a rehearsed 2:55 narration; return to slide 5 afterward. State that these are recorded evidence, not a live run. The MCP crop is a separate September rehearsal, not part of the October video. No model, tenant or deployment action is needed to present the deck.`,
  },
  {
    title: 'Connect business context with WorkIQ + MCP.',
    seconds: 65,
    refs: ['S02', 'S08', 'S09', 'S14', 'S20', 'M07'],
    kind: 'context',
    claim: 'recommendation',
    talk: `Connected context is where a reusable workflow becomes relevant to a customer. MCP is the App's extension interface to tools and data. MOSAIC has already shown a narrow local example: two read-only tools retrieving four approved synthetic sources. WorkIQ opens a much broader possibility: permissioned Microsoft 365 context from documents, meetings, email, Teams and people. Its marketplace also includes WorkIQ preview, productivity insights and the Microsoft 365 Agents Toolkit. Azure DevOps or a customer-specific MCP server can add other approved context. These are extension proposals for MOSAIC, not connected customer systems in this demo. WorkIQ is in public preview, requires tenant consent and can expose writes; our proposed starting point permits only separately authorized reads.`,
  },
  {
    title: 'Package your best way of working.',
    seconds: 55,
    refs: ['S02', 'S05', 'S06', 'S17', 'M02', 'M07'],
    kind: 'packages',
    claim: 'recommendation',
    talk: `The App lets expertise travel with the work. Instructions set expectations. Skills package a repeatable procedure together with the resources it needs. Plugins can distribute skills, agents, hooks, MCP configurations and canvas extensions, while marketplaces and Agent Finder help teams discover the right building blocks. Plugin formats also support language-server configuration, with client-specific support to verify. For MOSAIC, the immediate asset is a reusable intake and review practice rather than a prompt copied between people. A future approved plugin could make field distribution easier. Those packages still need versioning, review and testing; installing one is not evidence that every capability is authorized or has run.`,
  },
  {
    title: 'Add specialists. Keep one conversation.',
    seconds: 50,
    refs: ['S03', 'S04', 'S05', 'S18', 'M04'],
    kind: 'agents',
    claim: 'recommendation',
    talk: `MOSAIC defines an Orchestrator and four specialist profiles: intake, evidence, architecture and engagement. The App provides several ways to make that pattern more powerful: a custom-agent picker, focused child sessions, parallel fleets, orchestration across sessions or repositories, and isolated worktrees. Fork and merge let a team explore a branch of the work deliberately. The opportunity is to parallelize independent preparation, then reconcile the result in one accountable conversation. These profiles are configured; the current footage is not proof that a native specialist fleet executed. Separate branches also do not provide customer or tenant isolation.`,
  },
  {
    title: 'Bring expertise. Reuse the agent engine.',
    seconds: 45,
    refs: ['S01', 'S02', 'S03', 'S04', 'S06', 'S10', 'S15', 'M02'],
    kind: 'harness',
    claim: 'fact',
    talk: `The App builds on Copilot CLI's agent engine, adding the workspace around execution. MOSAIC contributes its eight-stage process, approved evidence and deterministic validation; it does not have to invent the whole agent environment. Choose models, Auto or reasoning effort in the App; evaluate approved BYOK providers in preview. Research and different-model critique can challenge assumptions. The separate MOSAIC worker still needs its own explicit model and limits. The SDK is a future embedding path, not an implemented service. Extensibility lets the workflow evolve without tying its domain expertise to one model.`,
  },
  {
    title: 'Make the work visible, not just conversational.',
    seconds: 45,
    refs: ['S07', 'S11', 'S19', 'M01', 'M03'],
    kind: 'surfaces',
    claim: 'recommendation',
    talk: `The demonstrated output is a browser dossier: ten HTML pages, nine Markdown reports and four JSON records. People can inspect options, evidence and unresolved decisions instead of hunting through a chat. The App's canvases offer a next step: a shared options board or evidence queue that both people and agents can update. Browser tools can help inspect approved interfaces. Opt-in computer use can reach GUI-only applications on supported desktops when a direct tool is unavailable. The image is today's browser handoff; a native MOSAIC canvas and desktop automation remain proposed extensions.`,
  },
  {
    title: 'GitHub is part of the work, not an export.',
    seconds: 45,
    refs: ['S04', 'S05', 'S12', 'M02'],
    kind: 'github',
    claim: 'recommendation',
    talk: `For teams already using GitHub, evaluate the handoff cost. My work brings issues and pull requests into the App. Start a session with issue context, inspect diffs and review activity, respond to comments and failing checks, then reconcile changes through the permitted review process. Other tools integrate with GitHub too; the App's proposition is doing this inside the agent workspace rather than treating review as an export. MOSAIC's hosted issue, PR and CI sequence still needs demonstration. A merge is never customer architecture or dossier approval.`,
  },
  {
    title: 'Turn a good run into a repeatable practice.',
    seconds: 45,
    refs: ['S01', 'S03', 'S04', 'M02'],
    kind: 'continuity',
    claim: 'recommendation',
    talk: `A valuable workflow should be easy to return to and improve. Automations can run recurring tasks on demand or on a schedule. Chronicle can search past work, summarize progress and suggest improvements. Context inspection and compaction help with long conversations; session management keeps work organized. Remote control extends access where policy allows it. For MOSAIC, a useful next step is a proposed evidence-refresh draft, not an automatically approved dossier. Session history is not an approved source, and transcript or debug exports need their own disclosure controls. The customer's authoritative record remains separate from convenience history.`,
  },
  {
    title: 'More autonomy. Clear human authority.',
    seconds: 55,
    refs: ['S01', 'S03', 'S04', 'S11', 'S13', 'M02', 'M03'],
    kind: 'control',
    claim: 'fact',
    talk: `The App gives people choices about session mode, tools, sandboxes and enterprise-managed settings. MOSAIC adds the domain boundary: approved sources, visible unknowns, three alternatives and a blocked review state. Keep two customer decisions distinct. First, an authorized person selects the architecture before a selected full dossier. Later, the customer approves that exact dossier revision in the customer's workflow. This reference records neither decision. Plan approval is only permission for bounded preparation; a pull request is review evidence. Worktrees are not tenant isolation, instructions are not enforcement, and an automated security review is not certification. Customer deployment, training and operations require separate authority.`,
  },
  {
    title: 'Put a value hypothesis behind the demo.',
    seconds: 60,
    refs: ['S01', 'S04', 'M05'],
    kind: 'value',
    claim: 'assumption',
    talk: `Here is a transparent way to discuss value without presenting estimates as results. The planning case assumes ninety-six hours of manual intake and design preparation and sixteen hours of retained human review. That leaves a potential eighty hours of capacity, or about eighty-three percent. At an illustrative two hundred dollars per hour, it is sixteen thousand dollars of gross capacity per request. Additional coordination, corrections, model and platform consumption, integration and operations reduce the opportunity. Capacity is not cash savings. Use the App's usage visibility and a customer baseline to measure actual effort, review quality, rework, elapsed time and all incremental costs before making a business commitment.`,
  },
  {
    title: 'Choose the App when these needs align.',
    seconds: 55,
    refs: ['S01', 'S02', 'S03', 'S10', 'S12', 'M06'],
    kind: 'adoption',
    claim: 'recommendation',
    talk: `Here is the buying decision. If GitHub is your engineering hub, you want broad model choice, and you want reusable team workflows in a dedicated agent workspace, our recommendation is Copilot App. Start with MOSAIC's synthetic example, then one approved pilot. If your current VS Code, Visual Studio or Claude Desktop environment already meets those needs, switching needs a demonstrated benefit. Use the same task and evidence to measure effort, handoffs, quality, corrections and total cost. Retain the IDE and debugger where they help. The recommendation is clear; customer validation determines whether the fit is best for you.`,
  },
  {
    title: 'Make Copilot App your GitHub agent workspace.',
    seconds: 45,
    refs: ['S01', 'S16', 'M02', 'M06'],
    kind: 'close',
    claim: 'recommendation',
    talk: `Make Copilot App your GitHub agent workspace when this customer profile fits. Start with one workflow your team keeps reconstructing. Replay MOSAIC, package your expertise, and bring the result back to accountable human review. The proposition is native GitHub work, broad model choice and reusable team expertise together, not a claim that agents or MCP are exclusive. The next step is one measured pilot with approved context and clear acceptance criteria. MOSAIC is the example. Your team's next repeatable workflow is the opportunity.`,
  },
];

const C = {
  ink: '14202B',
  dark: '0D1117',
  panel: '161F2B',
  light: 'F5F7FA',
  white: 'FFFFFF',
  muted: '526174',
  line: 'D4DDE7',
  dim: 'B8C6D8',
  blue: '0969DA',
  cyan: '79C0FF',
  green: '1A7F37',
  mint: '9BE9A8',
  purple: '8250DF',
  lavender: 'D2BCFF',
  amber: '8B5C00',
};
const W = 13.333333;
const H = 7.5;
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'MOSAIC project';
pptx.subject = 'GitHub Copilot App customer demo and MOSAIC extensibility reference';
pptx.title = 'GitHub Copilot App: turn expertise into repeatable work';
pptx.company = 'MOSAIC';
pptx.lang = 'en-US';
pptx.theme = { headFontFace: 'Bahnschrift', bodyFontFace: 'Segoe UI', lang: 'en-US' };
pptx.addSection({ title: '15-minute customer demo' });
pptx.addSection({ title: 'Feature reference - optional Q&A' });
pptx.addSection({ title: 'Presenter setup and sources' });
const S = pptx.ShapeType;
const manifestSlides = [];
let elapsed = 0;

function box(slide, x, y, w, h, fill, line = fill, radius = false) {
  slide.addShape(radius ? S.roundRect : S.rect, {
    x,
    y,
    w,
    h,
    radius: 0.12,
    rectRadius: 0.12,
    fill: { color: fill },
    line: { color: line, width: 0.7 },
    objectName: 'layout-panel',
  });
}

function text(slide, value, x, y, w, h, size = 20, options = {}) {
  const { name = 'content', ...rest } = options;
  slide.addText(value, {
    x,
    y,
    w,
    h,
    fontFace: 'Segoe UI',
    fontSize: size,
    color: C.ink,
    margin: 0,
    breakLine: false,
    valign: 'mid',
    paraSpaceAfterPt: 0,
    charSpacing: 0,
    isTextBox: true,
    objectName: name,
    ...rest,
  });
}

function rule(slide, x, y, w, color = C.line) {
  slide.addShape(S.line, { x, y, w, h: 0, line: { color, width: 1 } });
}

function pill(slide, value, x, y, w, fill, color = C.white, size = 12) {
  box(slide, x, y, w, 0.32, fill, fill, true);
  text(slide, value, x + 0.08, y + 0.025, w - 0.16, 0.26, size, {
    color,
    bold: true,
    align: 'center',
    name: 'label',
  });
}

function picture(slide, file, x, y, w, h, alt) {
  const dimensions = imageSize(fs.readFileSync(file));
  const scale = Math.min(w / dimensions.width, h / dimensions.height);
  const width = dimensions.width * scale;
  const height = dimensions.height * scale;
  slide.addImage({
    path: file,
    x: x + (w - width) / 2,
    y: y + (h - height) / 2,
    w: width,
    h: height,
    altText: alt,
    objectName: 'authentic-evidence',
  });
}

function card(slide, heading, body, x, y, w, h, accent = C.blue, dark = false) {
  box(slide, x, y, w, h, dark ? C.panel : C.white, dark ? '344256' : C.line, true);
  box(slide, x + 0.2, y + 0.22, 0.36, 0.055, accent);
  text(slide, heading, x + 0.2, y + 0.42, w - 0.4, 0.58, 23, {
    bold: true,
    color: dark ? C.white : C.ink,
  });
  text(slide, body, x + 0.2, y + 1.1, w - 0.4, h - 1.3, 20, {
    color: dark ? C.dim : C.muted,
    valign: 'top',
  });
}

function statement(slide, value, dark = false) {
  box(slide, 0.6, 6.47, 12.13, 0.49, dark ? '233043' : 'E7EEF8', dark ? '233043' : 'E7EEF8', true);
  text(slide, value, 0.82, 6.54, 11.68, 0.32, 17.5, {
    color: dark ? C.cyan : C.blue,
    bold: true,
    name: 'takeaway',
  });
}

function mmss(seconds) {
  return `${Math.floor(seconds / 60)
    .toString()
    .padStart(2, '0')}:${Math.round(seconds % 60)
    .toString()
    .padStart(2, '0')}`;
}

function newSlide(content, index, appendix = false, section = 'Feature reference - optional Q&A') {
  const dark = ['cover', 'harness', 'models', 'close'].includes(content.kind);
  const slide = pptx.addSlide({ sectionTitle: appendix ? section : '15-minute customer demo' });
  slide.hidden = appendix;
  slide.background = { color: dark ? C.dark : C.light };
  text(slide, 'GitHub Copilot App', 0.6, 0.2, 5.4, 0.26, 12.5, {
    bold: true,
    color: dark ? C.cyan : C.blue,
    name: 'label',
  });
  text(
    slide,
    appendix ? 'MOSAIC / OPTIONAL REFERENCE' : 'MOSAIC / CUSTOMER DEMO',
    8.1,
    0.2,
    4.63,
    0.26,
    10.5,
    {
      color: dark ? C.dim : C.muted,
      align: 'right',
      name: 'label',
    },
  );
  if (content.kind !== 'cover' && content.kind !== 'close') {
    text(slide, content.title, 0.6, 0.76, 12.13, 1.0, appendix ? 31 : 34, {
      bold: true,
      fontFace: 'Bahnschrift',
      color: dark ? C.white : C.ink,
    });
  }
  rule(slide, 0.6, 7.12, 12.13, dark ? '344256' : C.line);
  text(
    slide,
    `Sources: ${content.refs.join(', ')}  |  ${appendix ? 'Documented surface snapshot: 19 Oct 2026' : 'Synthetic reference; customer decisions remain with people.'}`,
    0.6,
    7.22,
    11.5,
    0.15,
    9,
    { color: dark ? C.dim : C.muted, name: 'citation' },
  );
  text(slide, String(index), 12.2, 7.19, 0.5, 0.22, 10, {
    align: 'right',
    color: dark ? C.dim : C.muted,
    name: 'label',
  });
  const start = elapsed;
  if (!appendix) elapsed += content.seconds;
  const refs = content.refs
    .map((id) => `${id} - ${sources[id][0]}\n${sources[id][1]}`)
    .join('\n\n');
  const note = [
    `${appendix ? 'OPTIONAL APPENDIX - not part of the timed demo' : `TIMING ${mmss(start)}-${mmss(elapsed)} (${content.seconds} seconds)`}`,
    `Claim framing: ${content.claim || 'fact'}. Public product sources verified ${verified}.`,
    content.talk ? `SPEAKER TALK TRACK\n${content.talk}` : '',
    content.cue ? `PRESENTER ACTION / BOUNDARY\n${content.cue}` : '',
    'EVIDENCE BOUNDARY\nApp proof = authentic recorded use; Configured = assets exist, not execution proof; Extension = proposed MOSAIC use of documented capabilities. A local validation is not App footage. No customer approval, implementation or deployment is claimed.',
    `SOURCES\n${refs}`,
  ]
    .filter(Boolean)
    .join('\n\n');
  slide.addNotes(note);
  manifestSlides.push({
    number: index,
    title: content.title,
    hidden: appendix,
    seconds: content.seconds || 0,
    startSeconds: appendix ? null : start,
    endSeconds: appendix ? null : elapsed,
    refs: content.refs,
    claim: content.claim || 'fact',
    notes: note,
    talk: content.talk || '',
    kind: content.kind || 'appendix',
  });
  return slide;
}

function renderCore(content, index) {
  const slide = newSlide(content, index);
  switch (content.kind) {
    case 'cover': {
      box(slide, 9.9, 0.92, 2.8, 5.0, C.panel, '344256', true);
      ['CONTEXT', 'EXPERTISE', 'AGENTS', 'TOOLS', 'CONTROL'].forEach((value, i) => {
        pill(
          slide,
          value,
          10.22,
          1.3 + i * 0.86,
          2.14,
          ['244866', '3D2C62', '1C4934', '244866', '3D2C62'][i],
          C.white,
          13,
        );
      });
      text(slide, 'GitHub Copilot App', 0.66, 1.15, 8.8, 0.75, 36, { color: C.cyan, bold: true });
      text(slide, 'Turn expertise into\nrepeatable work.', 0.6, 2.06, 9.0, 1.92, 53, {
        color: C.white,
        fontFace: 'Bahnschrift',
        bold: true,
      });
      text(
        slide,
        'Your GitHub agent workspace.\nMOSAIC shows expertise becoming workflow.',
        0.66,
        4.32,
        8.65,
        1.02,
        25,
        { color: C.dim },
      );
      statement(slide, 'Connect context. Coordinate expertise. Keep people in control.', true);
      break;
    }
    case 'before': {
      card(
        slide,
        'Before: reconstruct the work',
        'Search scattered guidance.\nRepeat discovery and handoffs.\nRebuild assumptions for review.',
        0.6,
        2.0,
        5.82,
        3.05,
        C.purple,
      );
      card(
        slide,
        'With the App + MOSAIC',
        'Start from one business need.\nApply reusable, approved expertise.\nCarry context into a reviewable draft.',
        6.62,
        2.0,
        6.11,
        3.05,
        C.green,
      );
      text(
        slide,
        'REQUESTER  >  SOLUTION ENGINEER  >  QUALIFIED REVIEWERS',
        0.8,
        5.47,
        11.9,
        0.42,
        20,
        { color: C.blue, bold: true },
      );
      text(
        slide,
        'Chats, attachments, issue context and optional voice input can meet people where work starts.',
        0.8,
        6.01,
        11.7,
        0.32,
        16,
        { color: C.muted, name: 'caption' },
      );
      statement(
        slide,
        'The business target: less repeated preparation, clearer decisions and less rework.',
      );
      break;
    }
    case 'positioning': {
      const choices = [
        [
          'NATIVE GITHUB WORK',
          'Work to review',
          'Issues, agent sessions,\ndiffs, PRs and CI in one App.',
          C.blue,
        ],
        [
          'BROAD MODEL CHOICE',
          'Choose your model',
          'Permitted models + approved\nhosted or local BYOK providers.',
          C.purple,
        ],
        [
          'REUSABLE EXPERTISE',
          'Scale your practice',
          'Skills, agents, MCP and plugins\ncarry your way of working.',
          C.green,
        ],
      ];
      choices.forEach(([heading, focus, body, accent], i) => {
        const x = 0.6 + i * 4.12;
        box(slide, x, 2.0, 3.89, 2.92, C.white, C.line, true);
        text(slide, heading, x + 0.19, 2.22, 3.51, 0.31, 14, {
          color: accent,
          bold: true,
          name: 'label',
        });
        text(slide, focus, x + 0.19, 2.94, 3.51, 0.67, 25, {
          bold: true,
          color: accent,
        });
        text(slide, body, x + 0.19, 3.96, 3.51, 0.67, 18, {
          color: C.muted,
          name: 'diagram',
        });
      });
      text(
        slide,
        'The differentiator is the combined first-party GitHub experience, not exclusive features. BYOK is preview.',
        0.83,
        5.25,
        11.65,
        0.6,
        18,
        { color: C.muted, name: 'caption' },
      );
      statement(
        slide,
        'Our recommendation for GitHub-centered teams: put these needs together in Copilot App.',
      );
      break;
    }
    case 'harness': {
      const layers = [
        ['GITHUB COPILOT APP', 'Sessions  /  Models  /  GitHub  /  Canvases', C.cyan],
        [
          'SHARED COPILOT CLI RUNTIME',
          'Plan  >  use approved tools  >  inspect  >  iterate',
          C.lavender,
        ],
        [
          'MOSAIC PROCESS + VALIDATION WORKER',
          'Eight stages  /  evidence rules  /  three options  /  human handoff',
          C.mint,
        ],
      ];
      layers.forEach(([heading, body, accent], i) => {
        const y = 2.0 + i * 1.22;
        box(slide, 0.65, y, 8.42, 1.03, C.panel, '344256', true);
        text(slide, heading, 0.9, y + 0.12, 7.93, 0.3, 16, {
          color: accent,
          bold: true,
          name: 'label',
        });
        text(slide, body, 0.9, y + 0.53, 7.93, 0.31, 18, { color: C.white, name: 'diagram' });
      });
      text(slide, 'EXTEND THROUGH', 9.4, 2.1, 3.0, 0.3, 14, {
        color: C.cyan,
        bold: true,
        name: 'label',
      });
      text(
        slide,
        'Skills + agents + MCP\nPlugins + hooks + LSP\nCanvases\nModels / Auto / effort\nBYOK + model critique',
        9.4,
        2.68,
        3.0,
        2.86,
        20,
        { color: C.white, valign: 'top' },
      );
      text(
        slide,
        'App models do not configure the separate worker. SDK embedding is a future path, not an implemented service.',
        0.86,
        5.91,
        11.65,
        0.38,
        15,
        { color: C.dim, name: 'caption' },
      );
      statement(
        slide,
        'Reuse the engine and workspace. Keep domain rules, validation and decisions explicit.',
        true,
      );
      break;
    }
    case 'demo': {
      box(slide, 0.6, 1.95, 8.58, 4.35, C.white, C.line, true);
      picture(
        slide,
        assets.intake,
        0.75,
        2.1,
        8.28,
        3.99,
        'Authentic October 7 GitHub Copilot App intake for a fictional travel-policy request.',
      );
      pill(slide, 'AUTHENTIC APP USE', 9.48, 2.02, 2.86, C.green);
      text(
        slide,
        '1  Describe the need\n\n2  Approve bounded\n    preparation\n\n3  Open the dossier',
        9.48,
        2.57,
        3.14,
        2.85,
        21,
        { bold: true, valign: 'top' },
      );
      text(slide, 'Play the 2:55 recording', 9.48, 5.65, 3.08, 0.4, 17, {
        color: C.blue,
        underline: true,
        hyperlink: { url: video },
        name: 'link',
      });
      statement(
        slide,
        'App = conversation + tools. MOSAIC = domain process + validation. People = decisions.',
      );
      break;
    }
    case 'context': {
      const labels = [
        ['WorkIQ', 'M365 questions + entities'],
        ['WorkIQ preview', 'Retrieve-first grounding'],
        ['Productivity', '10 read-only insight skills'],
        ['M365 Agents Toolkit', 'Later build / evaluation'],
      ];
      labels.forEach(([heading, body], i) => {
        const x = 0.6 + i * 3.075;
        box(slide, x, 2.0, 2.9, 1.33, C.white, C.line, true);
        text(slide, heading, x + 0.17, 2.18, 2.56, 0.39, 17, {
          bold: true,
          color: C.blue,
          name: 'diagram',
        });
        text(slide, body, x + 0.17, 2.75, 2.56, 0.36, 15.5, { color: C.muted, name: 'diagram' });
      });
      box(slide, 0.6, 3.68, 6.04, 2.24, C.white, C.line, true);
      text(slide, 'Already demonstrated in the App', 0.82, 3.88, 5.6, 0.45, 22, { bold: true });
      picture(
        slide,
        assets.mcp,
        0.86,
        4.54,
        5.42,
        0.94,
        'Authentic September rehearsal crop showing skill loading and the two completed read-only synthetic MCP tools.',
      );
      text(slide, 'Separate rehearsal: 2 tools / 4 synthetic sources.', 0.87, 5.55, 5.5, 0.2, 12, {
        color: C.muted,
        name: 'caption',
      });
      text(slide, 'EXTEND TO APPROVED CONTEXT', 7.02, 3.83, 5.35, 0.35, 15, {
        color: C.purple,
        bold: true,
        name: 'label',
      });
      text(
        slide,
        'Microsoft 365, Azure DevOps and\ncustomer-specific MCP adapters.',
        7.02,
        4.35,
        5.35,
        0.86,
        23,
        { bold: true },
      );
      text(
        slide,
        'WorkIQ: preview; tenant consent required.\nProposed authorized reads only; WorkIQ can write.',
        7.02,
        5.36,
        5.25,
        0.61,
        15.5,
        { color: C.muted, name: 'caption' },
      );
      statement(
        slide,
        'Connect approved context to the workflow; do not make the requester reconstruct it.',
      );
      break;
    }
    case 'packages': {
      card(
        slide,
        'Instructions',
        'Set the standards that travel with a repository or team.',
        0.6,
        2.0,
        3.9,
        2.66,
        C.blue,
      );
      card(
        slide,
        'Skills',
        'Make a good procedure reusable, discoverable and repeatable.',
        4.72,
        2.0,
        3.9,
        2.66,
        C.green,
      );
      card(
        slide,
        'Plugins',
        'Bundle expertise and integrations for approved distribution.',
        8.84,
        2.0,
        3.89,
        2.66,
        C.purple,
      );
      text(slide, 'DISCOVER', 0.82, 5.02, 2.28, 0.29, 14, {
        color: C.blue,
        bold: true,
        name: 'label',
      });
      text(slide, 'Marketplaces + Agent Finder', 0.82, 5.53, 5.4, 0.41, 21, { bold: true });
      text(slide, 'EXTEND', 6.62, 5.02, 2.28, 0.29, 14, {
        color: C.purple,
        bold: true,
        name: 'label',
      });
      text(slide, 'Agents + hooks + MCP + LSP + canvases', 6.62, 5.53, 5.91, 0.41, 20, {
        bold: true,
      });
      statement(
        slide,
        'Demonstrated skills today. An approved MOSAIC plugin could simplify reuse.',
      );
      break;
    }
    case 'agents': {
      pill(slide, 'FIVE CONFIGURED MOSAIC PROFILES', 0.65, 1.97, 5.52, C.blue);
      box(slide, 0.65, 2.65, 3.6, 2.58, C.dark, C.dark, true);
      text(slide, 'MOSAIC\nOrchestrator', 0.91, 3.02, 3.08, 1.01, 30, {
        color: C.white,
        bold: true,
        fontFace: 'Bahnschrift',
      });
      text(slide, 'One conversation.\nClear accountability.', 0.91, 4.39, 3.08, 0.65, 17, {
        color: C.cyan,
        name: 'diagram',
      });
      const roles = [
        ['Intake Analyst', 'Need + constraints'],
        ['Evidence Curator', 'Approved sources'],
        ['Solution Architect', 'Three alternatives'],
        ['Engagement Planner', 'Human handoff'],
      ];
      roles.forEach(([heading, detail], i) => {
        const x = 4.6 + (i % 2) * 4.08;
        const y = 2.63 + Math.floor(i / 2) * 1.45;
        box(slide, x, y, 3.84, 1.18, C.white, C.line, true);
        text(slide, heading, x + 0.2, y + 0.16, 3.44, 0.35, 21, { bold: true });
        text(slide, detail, x + 0.2, y + 0.71, 3.44, 0.27, 16, { color: C.muted, name: 'diagram' });
      });
      text(
        slide,
        'Agent picker  /  child sessions  /  fleets  /  orchestration  /  fork + merge  /  worktrees',
        0.84,
        5.83,
        11.6,
        0.38,
        17,
        { color: C.blue, name: 'diagram' },
      );
      statement(
        slide,
        'Extension opportunity, not recorded fleet execution. Parallel worktrees are not customer isolation.',
      );
      break;
    }
    case 'models': {
      card(
        slide,
        'Choose',
        'Model picker\nAuto selection\nReasoning effort',
        0.6,
        2.0,
        3.9,
        2.89,
        C.cyan,
        true,
      );
      card(
        slide,
        'Connect',
        'BYOK providers\nHosted or local models\nYour policy + credentials',
        4.72,
        2.0,
        3.9,
        2.89,
        C.lavender,
        true,
      );
      card(
        slide,
        'Challenge',
        'Cited research\nDifferent-model critique\nAdversarial sparring',
        8.84,
        2.0,
        3.89,
        2.89,
        C.mint,
        true,
      );
      text(
        slide,
        'BYOK preview: OpenAI, Azure OpenAI, Microsoft Foundry, Anthropic, Ollama,\nFoundry Local, LM Studio and OpenAI-compatible HTTP endpoints.',
        0.88,
        5.28,
        11.67,
        0.72,
        17,
        { color: C.dim, name: 'caption' },
      );
      statement(
        slide,
        'The differentiator to evaluate is the complete workflow experience, not an unproven model ranking.',
        true,
      );
      break;
    }
    case 'surfaces': {
      pill(slide, 'TODAY: BROWSER DOSSIER', 0.65, 1.97, 5.4, C.green);
      picture(
        slide,
        assets.report,
        0.66,
        2.54,
        7.26,
        3.6,
        'Authentic generated browser dossier showing an unselected discussion draft and awaiting human review.',
      );
      pill(slide, 'NEXT: APP EXTENSIONS', 8.25, 1.97, 4.18, C.purple);
      text(
        slide,
        'A shared options board.\nAn evidence review queue.\nAn interactive intake canvas.',
        8.25,
        2.65,
        4.15,
        1.93,
        23,
        { bold: true, valign: 'top' },
      );
      text(slide, 'Canvas + browser tools\nOpt-in computer use', 8.25, 4.99, 4.15, 0.86, 20, {
        color: C.muted,
      });
      statement(
        slide,
        '23 artifacts: 10 HTML + 9 Markdown + 4 JSON. A native MOSAIC canvas is proposed, not shown.',
      );
      break;
    }
    case 'github': {
      const flow = [
        ['Find work', 'My work\nIssues + inbox'],
        ['Direct work', 'Issue context\nRepository templates'],
        ['Inspect work', 'Diffs + comments\nCI checks + fixes'],
        ['Reconcile work', 'Stacked PRs\nControlled merge'],
      ];
      flow.forEach(([heading, body], i) =>
        card(
          slide,
          heading,
          body,
          0.6 + i * 3.075,
          2.03,
          2.9,
          2.92,
          [C.blue, C.purple, C.green, C.blue][i],
        ),
      );
      text(
        slide,
        'Documented App capability; MOSAIC hosted issue / PR / CI scenes are not claimed.',
        0.86,
        5.49,
        11.6,
        0.62,
        20,
        { color: C.muted },
      );
      statement(
        slide,
        'Evaluate the handoffs from request to review, not just the quality of one answer.',
      );
      break;
    }
    case 'continuity': {
      card(
        slide,
        'Repeat',
        'Scheduled or on-demand automations can propose fresh work.',
        0.6,
        2.0,
        3.9,
        2.88,
        C.blue,
      );
      card(
        slide,
        'Remember',
        'Chronicle, session history and context tools help teams pick up the thread.',
        4.72,
        2.0,
        3.9,
        2.88,
        C.green,
      );
      card(
        slide,
        'Improve',
        'Usage insights, session management and remote access support a working habit.',
        8.84,
        2.0,
        3.89,
        2.88,
        C.purple,
      );
      text(
        slide,
        'MOSAIC extension: approved source change  >  proposed refreshed dossier  >  qualified review',
        0.87,
        5.32,
        11.65,
        0.66,
        20,
        { bold: true, color: C.blue },
      );
      statement(
        slide,
        'History is context, not evidence. A schedule cannot approve a customer decision.',
      );
      break;
    }
    case 'control': {
      pill(slide, 'APP CONTROLS', 0.62, 1.99, 3.35, C.blue);
      text(
        slide,
        'Session modes\nTool permissions\nLocal / cloud sandboxes\nManaged settings\nContent exclusion',
        0.82,
        2.64,
        3.64,
        2.85,
        22,
        { valign: 'top' },
      );
      box(slide, 4.63, 2.0, 8.09, 3.92, C.white, C.line, true);
      text(slide, 'TWO CUSTOMER DECISIONS', 4.88, 2.23, 7.61, 0.32, 16, {
        color: C.purple,
        bold: true,
        name: 'label',
      });
      text(slide, '1  Select the architecture', 4.9, 2.87, 7.52, 0.49, 28, { bold: true });
      text(slide, 'Before a selected full dossier.', 5.36, 3.48, 6.96, 0.36, 20, {
        color: C.muted,
      });
      text(slide, '2  Approve the exact dossier revision', 4.9, 4.16, 7.52, 0.49, 25, {
        bold: true,
      });
      text(slide, 'In the customer workflow, with authorized people.', 5.36, 4.82, 6.93, 0.63, 20, {
        color: C.muted,
      });
      text(
        slide,
        'Neither decision is recorded by this reference. Security review is assistance, not certification.',
        0.85,
        6.05,
        11.65,
        0.23,
        14,
        { color: C.muted, name: 'caption' },
      );
      statement(
        slide,
        'MOSAIC stops at awaiting_human_review. No implementation, deployment or release authority.',
      );
      break;
    }
    case 'value': {
      pill(slide, 'ILLUSTRATIVE PLANNING CASE - NOT MEASURED', 0.65, 1.96, 8.41, C.amber);
      text(slide, '96h', 0.75, 2.61, 2.41, 0.93, 48, { bold: true, color: C.muted });
      text(slide, 'Manual preparation', 0.8, 3.64, 3.56, 0.42, 21);
      text(slide, '16h', 4.62, 2.61, 2.3, 0.93, 48, { bold: true, color: C.blue });
      text(slide, 'Retained human review', 4.68, 3.64, 4.02, 0.42, 21);
      text(slide, '80h', 9.18, 2.61, 2.56, 0.93, 48, { bold: true, color: C.green });
      text(slide, 'Potential capacity', 9.21, 3.64, 3.18, 0.42, 21);
      box(slide, 0.8, 4.53, 11.59, 0.42, 'DCE4EF');
      box(slide, 0.8, 4.53, 11.59 / 6, 0.42, C.blue);
      box(slide, 0.8 + 11.59 / 6, 4.53, (11.59 * 5) / 6, 0.42, '9BE9A8');
      text(
        slide,
        'About 83% potential effort reduction.\n$16,000 gross capacity at an assumed $200/hour.',
        0.83,
        5.14,
        11.61,
        0.78,
        21,
        { bold: true },
      );
      text(
        slide,
        'Extra retained effort is zero in this base case. Subtract added effort and all incremental costs; capacity is not cash savings.',
        0.84,
        6.02,
        11.6,
        0.28,
        13.5,
        { color: C.muted, name: 'caption' },
      );
      statement(
        slide,
        'Measure effort, elapsed time, corrections, reviewer quality and total incremental cost.',
      );
      break;
    }
    case 'adoption': {
      const steps = [
        ['GitHub is home', 'Your requests, code\nand reviews already\nlive in GitHub.'],
        ['Choice matters', 'You want permitted\nmodels and approved\nprovider options.'],
        ['Expertise scales', 'You want reusable\nteam workflows in a\ndedicated agent App.'],
        [
          'Start one pilot',
          'Same task and evidence.\nMeasure effort, handoffs,\nquality and total cost.',
        ],
      ];
      steps.forEach(([heading, body], i) =>
        card(
          slide,
          heading,
          body,
          0.6 + i * 3.075,
          2.0,
          2.9,
          3.33,
          [C.blue, C.purple, C.green, C.blue][i],
        ),
      );
      text(
        slide,
        'Already satisfied by your IDE or another agent app? Require a measured benefit before switching.',
        0.85,
        5.72,
        11.61,
        0.49,
        17,
        { color: C.muted, name: 'caption' },
      );
      statement(
        slide,
        'When these needs align, choose Copilot App for a measured pilot. Keep the IDE where it helps.',
      );
      break;
    }
    case 'close': {
      text(slide, 'Make Copilot App your\nGitHub agent workspace.', 0.65, 1.14, 11.94, 1.72, 47, {
        color: C.white,
        bold: true,
        fontFace: 'Bahnschrift',
      });
      const links = [
        ['Explore the App', 'Product capabilities', 'https://github.com/features/ai/github-app'],
        ['Replay MOSAIC', 'Authentic 2:55 workflow', video],
        [
          'Start your pilot',
          'One workflow. Prove value.',
          `${repository}docs/adoption-playbook.md`,
        ],
      ];
      links.forEach(([heading, body, url], i) => {
        const x = 0.65 + i * 4.13;
        box(slide, x, 3.5, 3.87, 1.93, C.panel, '344256', true);
        text(slide, heading, x + 0.22, 3.83, 3.43, 0.52, 25, {
          color: C.cyan,
          bold: true,
          hyperlink: { url },
          underline: true,
        });
        text(slide, body, x + 0.22, 4.57, 3.43, 0.58, 18, { color: C.dim, name: 'diagram' });
      });
      text(
        slide,
        'Native GitHub work + broad model choice + reusable team expertise.\nMOSAIC is the example. Your workflow is the opportunity.',
        0.85,
        5.77,
        11.67,
        0.55,
        17,
        { color: C.dim, name: 'caption' },
      );
      statement(
        slide,
        'Connect more of the work. Reuse more of the expertise. Keep people accountable.',
        true,
      );
      break;
    }
    default:
      throw new Error(`Unknown slide kind: ${content.kind}`);
  }
}

function renderCapabilities(group, groupIndex) {
  const refs = [...new Set(group.features.flatMap((feature) => feature.refs))];
  const slide = newSlide(
    {
      title: `Feature reference ${groupIndex + 1}/10: ${group.title}`,
      refs,
      talk: group.features
        .map(
          (f) =>
            `${f.id}: ${f.name}. MOSAIC use: ${f.use} State: ${f.state}. Main story: slide ${f.mainSlide}. Commands: ${f.commands.join(', ') || 'UI/configuration'}. Built-in skills: ${f.skills.join(', ') || 'none'}. Sources: ${f.refs.join(', ')}.`,
        )
        .join('\n\n'),
      cue: 'Optional Q&A. All listed product capabilities are documented; the State column describes MOSAIC adoption, not product availability. Extension rows are proposals, not evidence of installation, authorization or execution.',
    },
    manifestSlides.length + 1,
    true,
  );
  text(slide, 'APP / HARNESS CAPABILITY', 0.69, 1.92, 3.28, 0.29, 12, {
    color: C.blue,
    bold: true,
    name: 'label',
  });
  text(slide, 'HOW IT COULD EXTEND MOSAIC', 4.06, 1.92, 5.85, 0.29, 12, {
    color: C.blue,
    bold: true,
    name: 'label',
  });
  text(slide, 'MOSAIC STATE / SOURCES', 10.0, 1.92, 2.68, 0.29, 11, {
    color: C.blue,
    bold: true,
    name: 'label',
  });
  group.features.forEach((feature, i) => {
    const y = 2.4 + i * 0.64;
    if (i % 2 === 0) box(slide, 0.6, y - 0.05, 12.13, 0.64, C.white);
    text(slide, `${feature.id}  ${feature.name}`, 0.7, y, 3.19, 0.54, 15.5, {
      bold: true,
      name: 'reference',
    });
    text(slide, feature.use, 4.06, y, 5.56, 0.54, 15, { color: C.muted, name: 'reference' });
    text(
      slide,
      `${feature.state}\n${feature.refs.join(', ')} / main ${feature.mainSlide}`,
      10.0,
      y,
      2.65,
      0.54,
      12.5,
      {
        color:
          feature.state === 'App proof'
            ? C.green
            : feature.state === 'Restricted'
              ? C.amber
              : C.blue,
        name: 'reference',
      },
    );
  });
  statement(
    slide,
    'App proof = recorded. Configured = present. Extension = proposed. Commands are in notes.',
  );
}

function renderComparison() {
  const slide = newSlide(
    {
      title: 'Why choose the App over your alternatives?',
      refs: ['S01', 'S02', 'S10', 'S12', 'S21', 'S22', 'S23', 'M02', 'M05'],
      claim: 'recommendation',
      talk: 'The recommendation is Copilot App when a dedicated first-party GitHub workspace, broad model/provider choice and reusable workflows fit the customer. Claude Desktop includes Chat, Cowork and Code; its Code tab supports parallel Git-isolated sessions, connectors, diffs and PR/CI monitoring. Do not describe it as chat-only. VS Code supports orchestration and multiple harnesses, including the shared Copilot runtime; it is not merely an editor. Visual Studio agent mode executes tools and iterates, and its optional newer chat experience uses the shared SDK foundation. The App differentiates its packaged GitHub-centered experience, not exclusive ownership of the engine. Keep the existing tool if it already meets the needs. No same-task benchmark has established superiority here; compare effort, handoffs, quality, time and all costs before scaling. MOSAIC demonstrates the App intake, skill, synthetic MCP and browser handoff; native fleets, WorkIQ, canvas and hosted PR/CI are still extensions.',
    },
    manifestSlides.length + 1,
    true,
  );
  const rows = [
    [
      'Claude Desktop',
      'Chat, Cowork + Code; parallel Git sessions, tools and PR / CI.',
      'GitHub-first workspace and broad model/provider choice.',
    ],
    [
      'VS Code',
      'Orchestration, multiple harnesses and shared Copilot runtime.',
      'Prefer a dedicated GitHub workspace; retain the IDE as needed.',
    ],
    [
      'Visual Studio',
      'Agent tools, iteration and optional shared SDK foundation.',
      'Prefer GitHub-centered supervision; keep IDE debugging.',
    ],
    [
      'Other apps / engines',
      'Capabilities vary; custom apps own their user experience.',
      'Evaluate workflow fit, integration and operating effort.',
    ],
  ];
  text(slide, 'ALTERNATIVE', 0.78, 1.99, 2.7, 0.26, 13, {
    color: C.blue,
    bold: true,
    name: 'label',
  });
  text(slide, 'CAPABILITIES ALREADY AVAILABLE', 3.64, 1.99, 4.15, 0.26, 13, {
    color: C.blue,
    bold: true,
    name: 'label',
  });
  text(slide, 'WHEN TO CHOOSE COPILOT APP', 8.16, 1.99, 4.15, 0.26, 13, {
    color: C.blue,
    bold: true,
    name: 'label',
  });
  rows.forEach(([alternative, fit, evaluate], i) => {
    const y = 2.48 + i * 0.74;
    box(slide, 0.6, y - 0.06, 12.13, 0.72, i % 2 === 0 ? C.white : C.light);
    text(slide, alternative, 0.78, y, 2.6, 0.57, 18, { bold: true, name: 'reference' });
    text(slide, fit, 3.64, y, 4.05, 0.57, 17, { name: 'reference' });
    text(slide, evaluate, 8.16, y, 4.16, 0.57, 17, { name: 'reference' });
  });
  text(
    slide,
    'PROVEN HERE: App intake + skill / synthetic MCP + browser handoff.\nNEXT TO PROVE: native fleets, WorkIQ, canvas and hosted PR / CI workflow.',
    0.83,
    5.63,
    11.65,
    0.65,
    17,
    { color: C.muted, name: 'caption' },
  );
  statement(
    slide,
    'No head-to-head result is claimed. Use comparable tasks and retain the evidence.',
  );
}

function renderPresenter() {
  const slide = newSlide(
    {
      title: 'Presenter runbook: a repeatable 15 minutes',
      refs: ['S01', 'S02', 'M01', 'M02', 'M05', 'M06'],
      cue: 'Use slides 1-15 for the timed show. Appendices are hidden from normal slideshow but included in the PDF. Open Presenter View for the timed talk tracks. Rehearse the complete recording and check audio before the meeting. Do not promise a 15-minute live generation SLA.',
      talk: 'Before a customer showing: confirm current App build and feature availability; review sources and preview labels; obtain rights and disclosure approval for all media; pre-open the published video and retain the screenshot fallback. Do not display private accounts, unapproved sources or unrelated windows. The synthetic demo does not require WorkIQ access. A separate live run needs installed dependencies, the intended agent and skill, correct read-only MCP tools, authorized model access, the approved synthetic boundary and explicit generation approval. Check tool scopes without widening privileges. A failure stays visible; do not switch to an invented success. Do not send messages, modify tenant data, approve customer decisions or deploy. At the close, invite a measured pilot; do not claim owner, customer or product-team release approval.',
    },
    manifestSlides.length + 1,
    true,
    'Presenter setup and sources',
  );
  const blocks = [
    ['00:00-02:15', 'Business need + three reasons to choose the App'],
    ['02:15-05:35', 'Authentic 2:55.57 demo + introduction'],
    ['05:35-10:40', 'Context, expertise, agents, shared engine, surfaces, GitHub'],
    ['10:40-13:20', 'Repeatability, human control and value hypothesis'],
    ['13:20-15:00', 'Best-fit customer + recommended pilot'],
  ];
  blocks.forEach(([time, topic], i) => {
    const y = 2.03 + i * 0.73;
    text(slide, time, 0.76, y, 2.41, 0.44, 21, { bold: true, color: C.blue });
    text(slide, topic, 3.26, y, 9.17, 0.44, 20);
  });
  text(
    slide,
    'Preflight: video + audio, Presenter View, source freshness, approved media and screenshot fallback.\nNo connected tenant is needed. Do not improvise a live deployment or a customer approval.',
    0.84,
    5.84,
    11.72,
    0.49,
    14.5,
    { color: C.muted, name: 'caption' },
  );
  statement(
    slide,
    'Discussion draft for owner/product-team review. Customer release is not approved.',
  );
}

function renderSources() {
  const entries = Object.entries(sources);
  for (let offset = 0; offset < entries.length; offset += 6) {
    const batch = entries.slice(offset, offset + 6);
    const slide = newSlide(
      {
        title: `Sources ${Math.floor(offset / 6) + 1}/${Math.ceil(entries.length / 6)}: inspect the evidence`,
        refs: batch.map(([id]) => id),
        talk: batch.map(([id, [label, url]]) => `${id}: ${label}\n${url}`).join('\n\n'),
        cue: `S references are official GitHub/Microsoft public product documentation read on ${verified}; M references are MOSAIC evidence pinned to ${revision}. Product documentation is mutable: reverify availability before reuse. The 60 capability mappings cover all 47 entries in the public App slash-command reference and all six built-in skills at this snapshot. This is not a claim to enumerate every third-party plugin or future release. App docs warn that some policy settings differ by surface, and public-code matches may still be generated despite a blocking suggestions policy.`,
      },
      manifestSlides.length + 1,
      true,
      'Presenter setup and sources',
    );
    batch.forEach(([id, [label, url]], i) => {
      const y = 2.02 + i * 0.7;
      text(slide, id, 0.72, y, 0.68, 0.4, 20, { bold: true, color: C.blue });
      text(slide, label, 1.56, y, 10.81, 0.36, 19, {
        bold: true,
        color: C.ink,
        hyperlink: { url },
        underline: true,
      });
      const display = url.replace('https://', '').replace(revision, `${revision.slice(0, 7)}...`);
      text(slide, display, 1.56, y + 0.41, 10.81, 0.24, 10.5, {
        color: C.muted,
        name: 'citation',
        hyperlink: { url },
      });
    });
    statement(
      slide,
      'Verified 19 Oct 2026. Recheck availability, preview status and policy before reuse.',
    );
  }
}

async function main() {
  for (const file of Object.values(assets))
    assert.ok(fs.existsSync(file), `Missing approved evidence: ${file}`);
  assert.equal(
    slides.reduce((sum, slide) => sum + slide.seconds, 0),
    900,
  );
  const features = groups.flatMap((group) => group.features);
  assert.equal(features.length, 60);
  features.forEach((feature, i) => {
    feature.id = `F${String(i + 1).padStart(2, '0')}`;
    assert.ok(feature.mainSlide >= 1 && feature.mainSlide <= 15);
    for (const ref of feature.refs) assert.ok(sources[ref], `Unknown feature source ${ref}`);
  });
  const skills = [...new Set(features.flatMap((feature) => feature.skills))].sort();
  assert.deepEqual(skills, [
    'af',
    'agent-merge',
    'create-canvas',
    'customize-cloud-agent',
    'orchestrate',
    'pr-stack',
  ]);
  slides.forEach((slide, i) => renderCore(slide, i + 1));
  groups.forEach(renderCapabilities);
  renderComparison();
  renderPresenter();
  renderSources();
  assert.equal(elapsed, 900);
  const spokenWords = slides.reduce((sum, slide) => sum + slide.talk.trim().split(/\s+/).length, 0);
  assert.ok(spokenWords >= 1100 && spokenWords <= 1500, `Check narration length: ${spokenWords}`);
  fs.mkdirSync(qa, { recursive: true });
  await pptx.writeFile({ fileName: output, compression: true });
  const manifest = {
    title: pptx.title,
    verified,
    revision,
    output,
    size: { width: W, height: H },
    mainSlides: 15,
    totalSlides: manifestSlides.length,
    allocatedSeconds: elapsed,
    video,
    videoSeconds,
    spokenWords,
    sources,
    features,
    slides: manifestSlides,
    commands: [...new Set(features.flatMap((feature) => feature.commands))].sort(),
    builtInSkills: skills,
    evidence: Object.entries(assets).map(([name, file]) => ({
      name,
      file,
      sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),
    })),
  };
  fs.writeFileSync(path.join(qa, 'deck-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(
    JSON.stringify({
      status: 'built',
      output,
      mainSlides: 15,
      totalSlides: manifestSlides.length,
      allocatedSeconds: elapsed,
      videoSeconds,
      spokenWords,
      featureMappings: features.length,
      builtInSkills: skills.length,
      sources: Object.keys(sources).length,
    }),
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
