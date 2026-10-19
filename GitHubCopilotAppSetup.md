# GitHub Copilot App Setup: From A New Computer To A First MOSAIC Run

**Start here if this computer has never run GitHub Copilot App.** This is the complete setup entry point; you do not need to piece together the contributor guide, MCP notes and demo runbook first.

**Last checked:** October 19, 2026. The main walkthrough is for **Windows**. GitHub also provides the App for macOS and Linux; see [Other operating systems](#other-operating-systems).

## Choose Your Destination

| What you want to do                                                    | Follow                                                                |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Install and try GitHub Copilot App                                     | Steps 1-4                                                             |
| Reproduce MOSAIC's offline synthetic example                           | Fresh Windows clone: bootstrap with `-OfflineOnly`; manual: steps 5-6 |
| Use MOSAIC's agents, skill and local evidence tools in the App         | Steps 1-9                                                             |
| Run a new conversational intake with model-backed document preparation | Steps 1-11                                                            |
| Add WorkIQ or other enterprise integrations later                      | The optional extensions section, after independent authorization      |

The App is the desktop workspace. **GitHub Copilot App, GitHub Desktop, GitHub CLI (`gh`), Copilot CLI (`copilot`) and the VS Code Copilot extension are different products.** Installing or signing in to one is not proof that the others are ready.

The offline reference does not require installing the App or signing into a model service. Continue through the App steps when you want the conversational experience.

MOSAIC is the **Multi-customer Orchestration System for Adaptive Intake and Continuous Delivery**. This repository demonstrates preparation through qualified human review, using fictional requests and approved synthetic evidence. It does not deploy a solution or record customer approval.

## Fast Path: A Fresh Windows Clone

If you have just cloned this repository on a Windows computer and have not set up its tools, run the bootstrap from the **repository root** in PowerShell:

```powershell
.\scripts\setup_mosaic_app.ps1
```

This does not require Python, Node.js, or an activated virtual environment beforehand. The script checks for Python 3.12 and the native Copilot CLI, installing missing packages through WinGet; installs this checkout's Python development/MCP dependencies; creates a local `.mcp.json` only if one does not already exist; guides you through separate Copilot CLI sign-in/model selection and worker configuration; then runs offline generation and tests. It opens the official App download page for you.

Run `.\scripts\setup_mosaic_app.ps1 -OfflineOnly` to prepare the synthetic offline workflow without installing or authenticating the separate CLI worker. Git is expected to be installed already because you cloned the repository.

**There is no unattended “100%” switch:** the GitHub Copilot App installer, GitHub sign-in/SSO, organization policy, project trust, and final MCP tool calls inside the App require human action. WinGet or sign-in may also be blocked by computer-management policy. The script never changes execution policy, does not install WorkIQ, does not run paid analysis, does not overwrite an existing MCP configuration, and records `awaiting_in_app_verification` until you finish the GUI checks. If a step stops, correct the reported prerequisite and rerun; inspect any pre-existing local profile/configuration rather than deleting or replacing it.

The bootstrap is [setup_mosaic_app.ps1](scripts/setup_mosaic_app.ps1). The sections below explain every stage and provide manual alternatives.

## 1. Check Accounts, Permission And Computer Access

Before installing anything:

1. Identify the GitHub account you are authorized to use. If you have personal and work accounts, confirm which one has the intended Copilot entitlement and repository access.
2. Confirm the computer is permitted to install GitHub Copilot App, Git and the development tools below. Use your organization's software portal or IT process if direct installation is restricted.
3. For organization-managed Copilot, ask the administrator to check:
   - **GitHub Copilot app** access is enabled.
   - **Copilot CLI** access is enabled if you will use MOSAIC's model-backed worker. This is a **separate policy**.
   - The intended models, MCP servers and plugins are permitted.
   - Required organization SSO authorization is complete.
4. For the App itself, use a Copilot plan **or** an approved bring-your-own-key (BYOK) model provider. You must still sign in to GitHub when using BYOK in the App.
5. For this guide's model-backed MOSAIC workflow, arrange Copilot CLI authentication and access to an explicit supported model. App BYOK settings do **not** configure MOSAIC's separate worker. Do not silently substitute providers.
6. In Windows **Settings > System > About**, check the system type so you select the correct x64 or ARM64 download.

GitHub Enterprise Cloud with data residency uses the App's **Use GitHub Enterprise** option and the organization's `*.ghe.com` hostname. **GitHub Enterprise Server is not supported by the App** according to the current [official quickstart](https://docs.github.com/en/copilot/get-started/quickstart-copilot-app).

You do **not** need an Azure subscription, Microsoft 365 tenant, Docker, VS Code, WorkIQ or PowerPoint to run the offline MOSAIC reference.

## 2. Install Git And GitHub Copilot App

### Install Git

1. Open the official [Git for Windows download](https://gitforwindows.org/).
2. Download and run the installer, following your organization's installation policy.
3. Keep Git available to command-line and third-party applications when choosing its PATH option.
4. Finish installation and open a **new** terminal window.
5. Run:

   ```powershell
   git --version
   ```

**Checkpoint:** a Git version is printed. If Windows cannot find `git`, reopen the terminal and check the installation/PATH before continuing.

### Install The App

1. Open the [official GitHub Copilot App download page](https://github.com/features/ai/github-app).
2. Choose the installer for your operating system and architecture. The current official Windows links are [Windows x64](https://gh.io/copilot-app-win64) and [Windows ARM64](https://gh.io/copilot-app-win-arm).
3. Run the downloaded installer. Review the publisher and Windows/organization prompts; do not bypass a security block.
4. Launch **GitHub Copilot App** from the Windows Start menu.

Use the official download page rather than a copied installer filename or an unofficial mirror. The App is not the GitHub Desktop client and does not require installing VS Code first.

## 3. Complete First Sign-In And Set Safe Defaults

1. In the App, click **Sign in to GitHub**.
2. Complete the browser sign-in using the account selected in step 1. Inspect the account shown before authorizing.
3. Complete required SSO authorization. Return to the App when the browser flow finishes.
4. If prompted, select your Copilot plan or configure your approved provider. For BYOK, use **Settings > Model providers** and the [official provider setup](https://docs.github.com/en/copilot/how-tos/github-copilot-app/use-byok-models). Do not put keys in repository files or chat.
5. Choose a theme and finish onboarding. You can skip project selection until the next step.
6. Use **Interactive** mode for your first session. Leave broad tool auto-approval, computer use and unattended automations disabled until you have a specific approved need.
7. Record the installed App version from the available About/installed-application information for your own troubleshooting notes. Do not publish screenshots containing account details.

Useful areas of the current UI:

| Area             | Purpose                                                                            |
| ---------------- | ---------------------------------------------------------------------------------- |
| **Projects**     | Connect a repository or folder and see its sessions                                |
| **Chats**        | Brainstorm without creating a dedicated branch or worktree                         |
| **My work**      | Find issues, pull requests, reviews and checks                                     |
| **Customize**    | Manage skills, MCP servers, plugins and canvases                                   |
| **Automations**  | Configure explicitly authorized recurring/on-demand work                           |
| Session controls | Select an agent, mode (Interactive, Plan or Autopilot), model and reasoning effort |

UI labels can change. Follow the current [App quickstart](https://docs.github.com/en/copilot/get-started/quickstart-copilot-app) and [session guide](https://docs.github.com/en/copilot/how-tos/github-copilot-app/agent-sessions) if your build differs.

## 4. Connect A Project And Check Basic App Operation

For an existing approved project:

1. Next to **Projects**, click **+**.
2. Choose **Local folder or repository** and select its root, or choose **GitHub repository** to clone an authorized repository.
3. Review any folder-trust prompt. Trust only a repository you have inspected and are authorized to use.
4. Start a session for that project in **Interactive** mode. For the first MOSAIC setup, use the **local repository** execution location, not a new worktree or cloud sandbox.
5. Select a permitted model. A normal/medium reasoning setting is a reasonable starting point for simple intake; it is not a quality or performance guarantee.
6. For a basic read-only check, use:

   ```text
   Summarize this repository's README. Do not edit files, run commands,
   create GitHub resources, or connect to external business systems.
   ```

This is a model request and may consume usage. An answer proves basic App interaction, **not** MOSAIC setup, MCP availability or worker authentication.

If you do not yet have a project, continue with step 5 to obtain MOSAIC, then perform this step on that checkout. **Stop here if you only wanted general App installation.**

## 5. Install MOSAIC's Local Tools And Obtain The Repository

### Install The Tools

Use official installers or your organization's approved software catalog. Open each required link below, choose the Windows installer matching your system architecture, run it, and keep command-line/PATH integration enabled when offered:

| Tool                             | MOSAIC requirement                                                                                      | Official source                                                                                                              |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| PowerShell 7                     | Recommended for these instructions; Copilot CLI on Windows requires PowerShell 6 or newer               | [Microsoft installation guide](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows) |
| Python 3.12                      | The repository requires Python 3.12 or later; 3.12 is the explicit baseline in this walkthrough         | [Python Windows downloads](https://www.python.org/downloads/windows/)                                                        |
| Node.js LTS, version 22 or newer | Required for repository browser/presentation tooling; also required if using npm to install Copilot CLI | [Node.js downloads](https://nodejs.org/en/download)                                                                          |
| GitHub CLI (`gh`)                | Recommended for checking the GitHub account and Git credentials; not needed for the offline generator   | [GitHub CLI](https://cli.github.com/)                                                                                        |
| Copilot CLI (`copilot`)          | Required only for model-backed MOSAIC analysis; not for the offline example                             | [Official CLI installation](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli)   |

For Python, install the Python launcher when offered so `py -3.12` works. If using a centrally managed Python installation, substitute its verified Python 3.12+ executable when creating the virtual environment.

On a Windows computer with WinGet available, the documented PowerShell and Copilot CLI installation commands are:

```powershell
winget install --id Microsoft.PowerShell --exact
winget install --id GitHub.Copilot --exact
```

The second command installs **Copilot CLI**, not the desktop App. Prefer its native executable for this MOSAIC worker. The official alternative is `npm install -g @github/copilot`, but a Windows npm `.cmd`/`.ps1` launcher is **not** an acceptable worker executable.

After installation, close and reopen your terminal. Launch **PowerShell 7** from Start, or run `pwsh`. Check the tools you installed, skipping lines for deferred optional tools:

```powershell
$PSVersionTable.PSVersion
git --version
py -3.12 --version
node --version
npm.cmd --version
gh --version
copilot --version
```

**Checkpoint:** PowerShell is 7.x, Python is 3.12+, and installed tools print versions. Run the Node/npm checks only if you installed the optional browser/presentation tooling; Node must be 22+. `gh`/`copilot` can be deferred if you are stopping at the offline example. Installing the App's bundled runtime does not prove that a standalone `copilot.exe` is on PATH.

### Check GitHub And Git Authentication Separately

For private repository access or later authorized GitHub writes:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh auth status
gh api user --jq .login
```

Use your approved account in the browser and authorize SSO if required. Do not use insecure credential storage, put a token in a URL, or paste one into the guide/chat.

If you intentionally want Git to use this authenticated GitHub CLI account:

```powershell
gh auth setup-git --hostname github.com
```

That command changes the Git credential helper configuration for the host. Review existing credential-management requirements first. App sign-in alone does not switch the account used by `git push`. A public clone may not require authentication, and successful cloning does not establish write permission.

### Clone Into A User-Writable Folder

Use a short local path outside a cloud-synchronized Documents/Desktop folder. The following creates a new checkout, not an overwrite of an existing one:

```powershell
$workspace = Join-Path $env:USERPROFILE 'source'
$repo = Join-Path $workspace 'mosaic-challenge'
New-Item -ItemType Directory -Path $workspace -Force | Out-Null
if (Test-Path -LiteralPath $repo) {
    throw 'This destination already exists. Inspect it or choose a different new checkout path.'
}
git clone https://github.com/gregunger/ghca-mosaic-challenge-official.git $repo
if ($LASTEXITCODE -ne 0) { throw 'Clone failed. Resolve access before continuing.' }
Set-Location -LiteralPath $repo
git status --short --branch
```

Repository visibility and write access remain owner-controlled. If you need to contribute without write access, obtain authorization for a fork/branch workflow; do not try to push to another person's repository anyway. Merely running the synthetic example does not require a commit or push.

**From here on, run terminal blocks from the repository root.** After opening another terminal, use `Set-Location` to return to your actual checkout.

## 6. Create The Python Environment And Verify Offline Generation

Create a repository-local environment and install the project's declared dependencies:

```powershell
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
& .\.venv\Scripts\python.exe -m pip install -e ".[dev,mcp]"
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& .\.venv\Scripts\python.exe -c "import sys, mosaic, mcp; print(sys.executable); print('MOSAIC and MCP imports: OK')"
```

The editable install is intentional: MOSAIC locates schemas, templates and examples in this checkout. A copied standalone wheel is not the supported runtime.

These commands use the environment's interpreter explicitly, so you do **not** need to activate it or weaken PowerShell execution policy. The optional `windows` extra is only for a separately requested notification compatibility path; default foreground generation does not need it.

Generate a local example into ignored output and run the repository tests:

```powershell
& .\.venv\Scripts\python.exe -m mosaic.cli --output build\setup-check\reference
if ($LASTEXITCODE -ne 0) { throw 'Offline MOSAIC validation failed.' }
& .\.venv\Scripts\python.exe -m pytest
if ($LASTEXITCODE -ne 0) { throw 'Repository tests failed.' }
```

The expected CLI result includes:

```json
{
  "status": "pass",
  "initiativeId": "SYN-001",
  "state": "awaiting_human_review",
  "validation": "pass",
  "artifactCount": 23
}
```

Open the report only when you want to view it:

```powershell
Start-Process -FilePath (Resolve-Path .\build\setup-check\reference\index.html).Path
```

Confirm that you can inspect the evidence, **exactly three** options, unknowns and blocked human-review record. The expected package contains ten HTML pages, nine Markdown reports and four JSON records.

This step performs **no model inference, sign-in or customer-system access**. It proves the local reference engine works; it is not a new-request reasoning demonstration or evidence that the App can call MCP.

### Optional Browser And Presentation Tooling

If you will validate report UIs or build presentation assets:

```powershell
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw 'Node dependency installation failed.' }
npx.cmd playwright install chromium
if ($LASTEXITCODE -ne 0) { throw 'Chromium installation failed.' }
npm.cmd run test:reports -- build\setup-check\reference
```

`npm ci` uses the committed lockfile. Do not run an unplanned dependency upgrade to solve a setup problem. Desktop Microsoft PowerPoint is required only for native deck validation/export, not for the App or MOSAIC generation. See the [presentation guide](presentation/README.md).

## 7. Open MOSAIC In The App And Verify Its Customizations

1. If you have not already done step 4, use **Projects > + > Local folder or repository** to open this exact checkout.
2. Start a **new local repository session** so the App picks up installed tools and project customizations. Restart the App if it was open before PATH changes.
3. Select **Interactive** mode.
4. In **Customize > Skills**, verify the repository's `mosaic-intake` skill is available.
5. In the agent picker, or with `/agent`, select **MOSAIC Orchestrator**.
6. Check that the repository profiles are available:
   - MOSAIC Orchestrator
   - Intake Analyst
   - Evidence Curator
   - Solution Architect
   - Engagement Planner
7. Keep the [repository instructions](.github/copilot-instructions.md) in force. Do not copy these profiles into a global location merely to make them appear.

The [agent profiles](.github/agents/) and [skills](.github/skills/) are already in the repository. They are not separate mandatory marketplace purchases. GitHub documents repository/CLI customization availability in the App's [customization guide](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app).

**Checkpoint:** the intended skill and agent can be selected in the actual App session. Seeing files in Explorer is not sufficient. Do not start the business interview while you are still repairing prerequisites.

## 8. Configure The Local MCP Server

MCP means **Model Context Protocol**: the interface the App uses to call external tools. The bundled `mosaic-synthetic-evidence` server is a **local stdio process**, not a web service. It needs no port, Docker container, API key or customer tenant.

The shared App/CLI configuration is [.github/mcp.json](.github/mcp.json). The similarly named [.vscode/mcp.json](.vscode/mcp.json) is for **VS Code**, not the App/CLI configuration path.

For a **new checkout**, create an ignored local override that points to its actual Python environment. The following copies the shared configuration while retaining its two-tool allowlist:

```powershell
if (Test-Path -LiteralPath .\.mcp.json) {
    throw 'A local MCP override already exists. Inspect it; do not overwrite an existing registration.'
}
$repo = (Get-Location).Path
$configuration = Get-Content -LiteralPath .\.github\mcp.json -Raw -ErrorAction Stop |
    ConvertFrom-Json -ErrorAction Stop
$server = $configuration.mcpServers.'mosaic-synthetic-evidence'
$server.command = (Resolve-Path .\.venv\Scripts\python.exe -ErrorAction Stop).Path
$server.env.PYTHONPATH = Join-Path $repo 'src'
$configuration | ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath .\.mcp.json -Encoding utf8 -ErrorAction Stop
git check-ignore -v .mcp.json
```

**Checkpoint:** `git check-ignore` reports the repository's ignore rule. The override must retain:

- Server: `mosaic-synthetic-evidence`
- Transport: `stdio`
- Arguments: `-m`, `mosaic.mcp_server`
- `PYTHONNOUSERSITE`: `1`
- Tools: `list_approved_sources`, `read_approved_source`

Using absolute interpreter/source paths avoids relying on a GUI application's inherited virtual environment. These paths belong to this checkout only. A new clone/worktree needs its own reviewed setup; never reuse another customer's environment or evidence path.

Next:

1. Start a fresh App session at this repository root.
2. Open **Customize > MCP > Installed**.
3. Find `mosaic-synthetic-evidence`; enable/start it using the controls exposed by your App version.
4. Review any project/server trust prompt and approve only this authorized local server.
5. If it is not listed, check the project root, folder trust and override before adding a second global registration.

The root override takes precedence over the shared configuration. See [official per-repository MCP configuration](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers#adding-per-repository-mcp-servers) and the [connector guide](mcp/README.md).

Do not run the stdio server in a terminal expecting a webpage. The App starts and communicates with it. Do not replace the narrow tool list with `*` to hide a configuration problem.

## 9. Prove MCP Tool Calls In The App

Use a separate setup-verification session, with **MOSAIC Orchestrator** selected, before starting an intake:

```text
Verify only the local mosaic-synthetic-evidence MCP connection.
Call list_approved_sources, then call read_approved_source with source_id EVD-002.
Use the MCP tools, not shell commands or direct file reads.
Do not start an intake, generate reports, connect customer systems or change files.
If either tool is unavailable, stop and state which tool is missing.
```

Inspect the actual App tool activity:

1. `list_approved_sources` returns **EVD-001, EVD-002, EVD-003 and EVD-004**.
2. Its result identifies the boundary as synthetic, read-only and without network access.
3. `read_approved_source` returns EVD-002, classified `SYNTHETIC`, with title, revision, hash and content.
4. Both calls visibly succeed through MCP.

**Checkpoint:** this proves the new installation exposes the two tools to that agent. A terminal test, enabled-looking toggle or another user's archived screenshot is not a substitute. The existing [observation log](docs/product-feedback-observation-log.md) documents an earlier installation, not yours.

If a tool is missing, verify the exact server/tool names against the [Orchestrator profile](.github/agents/mosaic-orchestrator.agent.md). Do not widen its permissions or substitute a file read. The standard business interview should not be used as a setup/debugging session.

## 10. Configure The Separate Copilot Analysis Worker

**Skip this entire step for the offline reference.** Complete it before a live conversational intake that will generate new analysis.

The App hosts the conversation. MOSAIC's preparation engine invokes a **separate Copilot CLI process**, using an explicit model, local profile, run limit and deadline. That worker does not inherit the App's model selector, BYOK provider or permission to spend usage.

### Find The Native Executable

```powershell
$copilotExe = (Get-Command copilot.exe -CommandType Application -ErrorAction Stop).Source
& $copilotExe --version
& $copilotExe login --help
```

The path must resolve to the installed native executable. MOSAIC deliberately rejects `.cmd`, `.bat` and `.ps1` wrappers. If only an npm wrapper is available, use the approved native WinGet installation or resolve an authorized native installation; do not rename a wrapper to `.exe`.

### Sign In Using The Dedicated Profile

The worker profile lives under ignored `build\intake\.copilot-cli`. **Do not install plugins, MCP servers, agents, skills, hooks or BYOK overrides into this profile.** Those belong to the App experience, not the restricted analysis process.

First check for inherited token/provider overrides **without printing their values**:

```powershell
$presentOverrides = @(Get-ChildItem Env: | Where-Object {
    ($_.Name -in @('COPILOT_GITHUB_TOKEN', 'GH_TOKEN', 'GITHUB_TOKEN', 'COPILOT_OFFLINE') `
        -or $_.Name -like 'COPILOT_PROVIDER_*') -and
    -not [string]::IsNullOrEmpty($_.Value)
} | ForEach-Object {
    $_.Name
})
if ($presentOverrides.Count -gt 0) {
    throw "Review these inherited overrides before OAuth setup: $($presentOverrides -join ', ')"
}
```

If this stops, have the operator resolve unintended **process-local** overrides under the organization's credential policy. Do not display their contents, delete shared machine credentials or assume another tool's token is suitable.

Then authenticate and inspect the available model IDs in the same restricted profile. This block restores the shell's environment afterward:

```powershell
$copilotExe = (Get-Command copilot.exe -CommandType Application -ErrorAction Stop).Source
$profileDirectory = Join-Path (Get-Location).Path 'build\intake\.copilot-cli'
if (Test-Path -LiteralPath $profileDirectory) {
    throw 'A dedicated profile already exists. Have the operator review it before signing in again.'
}
New-Item -ItemType Directory -Path $profileDirectory -Force -ErrorAction Stop | Out-Null
$profileEnvironment = @{
    COPILOT_HOME = $profileDirectory
    HOME = $profileDirectory
    USERPROFILE = $profileDirectory
    GH_CONFIG_DIR = Join-Path $profileDirectory 'gh'
    XDG_CONFIG_HOME = Join-Path $profileDirectory '.config'
    COPILOT_ALLOW_ALL = 'false'
}
$previousEnvironment = @{}
foreach ($name in $profileEnvironment.Keys) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
Push-Location -LiteralPath $profileDirectory
try {
    foreach ($name in $profileEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $profileEnvironment[$name], 'Process')
    }
    & $copilotExe login
    if ($LASTEXITCODE -ne 0) { throw 'Dedicated Copilot CLI sign-in failed.' }
    & $copilotExe --no-custom-instructions --disable-builtin-mcps `
        --disable-mcp-server mosaic-synthetic-evidence `
        --available-tools=__mosaic_no_tools__ --no-auto-update --no-remote-export
    if ($LASTEXITCODE -ne 0) { throw 'Copilot CLI exited with an error.' }
}
finally {
    Pop-Location
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
```

In the browser, confirm the authorized account and complete sign-in/SSO. In the subsequent CLI interface:

1. Use `/user` to inspect the selected account.
2. Use `/model` to inspect available model identifiers and note the explicitly approved model.
3. Do **not** enter a business prompt or install customizations.
4. Enter `/exit` to return to PowerShell and allow the environment restoration to finish.

These launch flags keep the account/model inspection from exposing tools, loading project instructions, starting the bundled MCP server or enabling remote export. Do not use this profile for ordinary interactive work.

CLI OAuth normally uses the operating-system credential store, but the current CLI can fall back to a plaintext configuration file if secure storage is unavailable. Verify secure credential-store access with IT before sign-in. If the CLI reports a plaintext fallback, stop, protect the local file and follow IT's credential-remediation process before continuing. `COPILOT_HOME` separates the worker's configuration; it is **not** a separate OS identity or a guarantee of credential/tenant isolation. See [official CLI authentication](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli).

### Save The Explicit Worker Settings

From the repository root:

```powershell
$copilotExe = (Get-Command copilot.exe -CommandType Application -ErrorAction Stop).Source
$modelId = Read-Host 'Enter the exact approved Copilot CLI model ID, not auto'
if ([string]::IsNullOrWhiteSpace($modelId) -or $modelId -eq 'auto') {
    throw 'An explicit approved model ID is required.'
}
& .\.venv\Scripts\python.exe -m mosaic.jobs configure-copilot `
    --copilot-executable $copilotExe `
    --model $modelId `
    --max-ai-credits 30 `
    --model-timeout 600
if ($LASTEXITCODE -ne 0) { throw 'Worker configuration failed.' }
& .\.venv\Scripts\python.exe -m mosaic.jobs copilot-settings
```

The shown run settings are an **example for operator review**, not permission to spend credits. This version accepts a credit-limit integer from 30 to 300 and a deadline from 1 to 1,800 seconds. Start with an approved limit; do not raise it automatically after failure. A CLI usage limit is not a guaranteed hard currency/billing ceiling, and 600 seconds is a deadline, not a promised completion time.

**Checkpoint:** `copilot-settings` reports the chosen native executable/model and limits without exposing secrets. The command validates the configuration and runtime fingerprints; it does not perform inference or prove remote model access. Model access is exercised only by a separately approved generation.

If you update Copilot CLI later, inspect the update and run `configure-copilot` again with reviewed settings. A runtime-fingerprint mismatch is an intentional stop, not a reason to disable integrity checking.

## 11. Run Your First Safe Conversational Intake

Start a **fresh local App session** at this checkout, select **MOSAIC Orchestrator**, and keep **Interactive** mode.

1. Enter:

   ```text
   Menu
   ```

2. Select **1. Submit a new intake request**.
3. Describe a fictional problem, for example:

   ```text
   I manage Employee Services at fictional Contoso Public Services.
   Our field employees keep using old travel-policy guidance.
   Help me compare ways to provide trustworthy answers linked to current policy.
   Keep this to a proposal and design discussion, not implementation or deployment.
   I do not yet have a reliable baseline for repeated questions or rejected claims.
   ```

4. Answer relevant questions in ordinary language. Do not supply customer records, identities, credentials or tenant/subscription IDs. Unknowns should remain unknown.
5. After the first business answer, choose **End intake and generate report** when you are ready. The agent should not keep asking optional questions afterward.
6. Use **Plan** mode to review the bounded generation plan. It must state:
   - The current fictional need and approved EVD-001 through EVD-004 source boundary.
   - Read-only synthetic evidence acquisition.
   - The separate Copilot CLI model, configured credit limit and deadline.
   - Local transcript retention; the transcript itself is excluded from the analysis prompt.
   - Exactly three options and 23 output artifacts.
   - No customer connectors, external writes, implementation, deployment or automatic paid retries.
   - Stop at `awaiting_human_review`.
7. Approve **only if the plan is correct and you authorize that bounded generation**. Switch back to Interactive for execution if the App requires it; retain the same conversation and approval.
8. Let the foreground run complete. Do not start a second run, repeatedly poll, or wait for a Windows notification.
9. When the completed report link appears, select **Open documents in browser** if you want to inspect it.
10. Confirm the report preserves your fictional need, shows evidence and unknowns, compares three options, and remains an `unselected_discussion_draft` awaiting human review.

The **first** business question does not contain the generation option; subsequent business questions do. Numeric answers refer to the currently displayed question, not an earlier menu.

The agent prepares the structured brief and transcript after approval; the business requester is not expected to write JSON. The detailed [generation contract](.github/skills/mosaic-intake/references/generation.md) and [demo runbook](docs/demo-runbook.md) explain this behavior.

Two customer decisions remain separate and **unrecorded by this reference**: authorized architecture selection before a selected full dossier, then approval of the exact dossier revision in the customer's workflow. Generating documents, passing tests, reviewing a PR or merging changes approves neither.

## Optional: WorkIQ, Other Plugins And Additional MCP Servers

**Do not enable these to get the synthetic demo working.** Its evidence is already local.

After separate identity, data, security, retention, source-policy and tool authorization:

1. In **Customize > Plugins**, inspect approved marketplaces. Use marketplace settings to add an approved marketplace repository or Git URL when necessary.
2. The official [Microsoft Work IQ marketplace](https://github.com/microsoft/work-iq) currently documents:
   - `workiq`: Microsoft 365 semantic queries and structured operations.
   - `workiq-preview`: a separately versioned retrieve-first preview.
   - `workiq-productivity`: ten read-only productivity insight skills.
   - `microsoft-365-agents-toolkit`: agent-building and evaluation workflows, not a MOSAIC prerequisite.
3. Inspect the specific plugin, license, tools and authentication flow before installation. WorkIQ is public preview and requires Microsoft 365 tenant/admin consent as documented by Microsoft.
4. Do not describe all WorkIQ tools as read-only. Its full surface can create, update, delete and send; the MOSAIC extension boundary permits **only separately authorized reads**, with write tools not exposed.
5. Verify actual allowed tools in a dedicated, authorized test. A plugin listing does not establish that every tool works or that a source is approved.
6. Keep extensions out of the dedicated MOSAIC analysis profile. Installing an App plugin must not weaken that worker's no-tool boundary.

The same review applies to Azure DevOps MCP, browser tools, custom business-system MCP servers, canvases, computer use and scheduled automations. Do not broaden the synthetic source policy or deploy the designed solution as part of setup.

For current UI steps, see [App customization](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app). The [15-minute demo deck](presentation/mosaic-copilot-app-demo-15min.pptx) contains a feature-to-MOSAIC reference; proposed extensions are not installed capabilities.

## Troubleshooting

| Symptom                                                              | What to check and do                                                                                                                                                                                                                                                      |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| App download or sign-in blocked                                      | Use the official download, correct account/SSO and administrator-enabled App policy. Do not work around an enterprise restriction.                                                                                                                                        |
| App works but CLI generation does not                                | CLI entitlement/policy, authentication/profile, native executable and explicit model are separate. Recheck step 10; App BYOK/model selection does not configure the worker.                                                                                               |
| `git`, `py`, `node`, `gh` or `copilot` not found                     | Reopen PowerShell and the App after installation. Check the selected installer architecture and PATH. `Get-Command` can identify which executable is being used.                                                                                                          |
| `py -3.12` unavailable                                               | Install the launcher and Python 3.12, or use the approved Python 3.12+ interpreter's absolute path to create the environment.                                                                                                                                             |
| PowerShell blocks `Activate.ps1` or `npm.ps1`                        | Use the explicit `.venv\Scripts\python.exe` commands and `npm.cmd`/`npx.cmd` shown here. Do not set unrestricted execution policy.                                                                                                                                        |
| `No module named mosaic` / `mcp`                                     | From the correct root, install `-e ".[dev,mcp]"` using that checkout's environment. Verify the MCP override points to the same interpreter.                                                                                                                               |
| MCP server absent                                                    | Confirm trusted project root, `.mcp.json` precedence, valid JSON, absolute paths and fresh App session. `.vscode/mcp.json` is not the App/CLI configuration.                                                                                                              |
| MCP is listed but tool calls are unavailable                         | Check the selected agent and exact two-tool allowlist. Stop rather than using shell/file reads or enabling all tools.                                                                                                                                                     |
| Terminal server appears to wait forever                              | It is a stdio MCP process awaiting a client, not a browser service. Let the App launch it.                                                                                                                                                                                |
| GitHub 403 or wrong account on push                                  | Inspect `gh auth status`, `gh api user --jq .login`, `git remote -v` and your configured Git credential helper. Use only an account with write permission; switching App sign-in alone does not fix Git credentials. No force push or borrowed credential is appropriate. |
| Only `copilot.cmd` / `copilot.ps1` exists                            | Install or locate the approved native executable. The worker rejects shell wrappers by design.                                                                                                                                                                            |
| Dedicated profile has unapproved automation/overrides                | Stop and inspect it with the operator. Do not copy a customized App/CLI home into the worker profile, bypass validation, or delete unrelated configuration.                                                                                                               |
| Configured Copilot runtime changed                                   | Review the installed update and rerun `configure-copilot` with explicit approved limits. Do not suppress the hash check.                                                                                                                                                  |
| Model unavailable, usage exhausted, deadline or credit limit reached | Stop with the actual error. Confirm policy/model/budget with the operator. Do not fall back to example answers, switch providers or retry paid inference automatically.                                                                                                   |
| Generation failed                                                    | Preserve the exact failed run and diagnostic evidence privately. Repair only the authorized local cause. Use the documented recovery path; do not overwrite a completed revision or invent a success.                                                                     |
| Browser does not open                                                | Use the exact completed report link after checking the run status. A launch attempt is not evidence of customer review.                                                                                                                                                   |
| Package download/TLS/proxy failure                                   | Use approved corporate network and certificate configuration; ask IT. Do not disable certificate checks or security controls.                                                                                                                                             |
| Windows notification never appears                                   | Default generation is foreground and notifications are disabled. Follow the same App run to its report or explicit failure.                                                                                                                                               |

## Ready-To-Use Checklist

- [ ] The correct GitHub account is signed into the App; required policies and SSO are satisfied.
- [ ] Git, the intended Python environment and any chosen optional tools are installed and identifiable.
- [ ] The checkout is trusted and isolated from other customer work.
- [ ] Offline generation reports `pass`, 23 artifacts and `awaiting_human_review`.
- [ ] Repository tests pass; any environment-dependent skips are recorded honestly.
- [ ] `mosaic-intake` and MOSAIC Orchestrator are available in the actual App.
- [ ] Both synthetic MCP tools succeeded in the new App session.
- [ ] If using live analysis: the restricted CLI profile, account, native runtime, explicit model and limits have been reviewed.
- [ ] A first new intake was generated only after approval of its displayed boundary and cost settings.
- [ ] Evidence, three options, unknowns and blocked customer decisions are visible in the exact report revision.
- [ ] No secrets, raw customer context or local worker credentials were committed or exported.

Passing these checks establishes a working synthetic installation, not production readiness, compliance, deployment authority or customer approval. Steps that require interactive sign-in and actual App tool calls must be completed on the new computer; another machine's passing tests cannot establish them.

## Maintenance And Removal

- Update the App and tools through approved channels. Recheck official documentation and preview availability before a customer demo.
- After a Copilot CLI update, review and reconfigure the worker's fingerprinted runtime before live generation.
- Keep `.mcp.json`, `.venv`, `node_modules`, `build` and local execution records out of commits. Check `git status` before any authorized publication.
- To disable synthetic MCP, use **Customize > MCP > Installed**. Do not delete unrelated global server registrations.
- Retire only the specific local job/profile files permitted by retention policy. Do not recursively delete a home directory, shared workspace or another customer's records.

## Other Operating Systems

The App also supports macOS and Linux. Use the correct architecture from the [official download page](https://github.com/features/ai/github-app) and follow the same account, policy, trust and human-review checks.

The PowerShell commands and executable paths above are Windows-specific. Use the [contributor guide](CONTRIBUTING.md#development-setup), [MCP platform notes](mcp/README.md#enable), and [official CLI installation](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli) for the corresponding shell, Python environment and native executable. The native PowerPoint export validator is Windows-specific. This guide does not claim a fresh macOS/Linux installation was tested.

## Sources And Next Steps

- [Official App quickstart and installer links](https://docs.github.com/en/copilot/get-started/quickstart-copilot-app)
- [App sessions, modes, models and sandboxes](https://docs.github.com/en/copilot/how-tos/github-copilot-app/agent-sessions)
- [App customization](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app)
- [App BYOK setup](https://docs.github.com/en/copilot/how-tos/github-copilot-app/use-byok-models)
- [CLI installation](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli)
- [CLI authentication and credential precedence](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli)
- [Project MCP configuration and trust](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)
- [GitHub CLI credential-helper setup](https://cli.github.com/manual/gh_auth_setup-git)
- [MOSAIC runtime requirements](pyproject.toml), [contributor setup](CONTRIBUTING.md) and [local connector](mcp/README.md)
- [MOSAIC first demo](docs/demo-runbook.md) and [generation/recovery contract](.github/skills/mosaic-intake/references/generation.md)
- [15-minute App-first PowerPoint](presentation/mosaic-copilot-app-demo-15min.pptx), [PDF](presentation/mosaic-copilot-app-demo-15min.pdf) and [presenter/build guidance](presentation/README.md)
