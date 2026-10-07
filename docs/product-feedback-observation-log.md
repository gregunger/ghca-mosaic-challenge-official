# GitHub Copilot App Product Feedback Observation Log

Use this log to preserve hands-on observations and their evidence. Record the App build when known and distinguish archived observations from later replays. The contest's feedback bonus does not require an invented current-build replay; the [prepared response](../submission/product-feedback.txt) states the actual provenance and limits.

| Date and app build                 | Scenario                       | Observed strength or limitation                                                                                                                                                           | Evidence captured                                                                                                                            | Impact                                                                                                  | Suggested improvement                                                                                                                                                                     | Reproduced                                                                                                      |
| ---------------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
|                                    | Issue to Plan-mode session     |                                                                                                                                                                                           |                                                                                                                                              |                                                                                                         |                                                                                                                                                                                           |                                                                                                                 |
|                                    | Repository skill discovery     |                                                                                                                                                                                           |                                                                                                                                              |                                                                                                         |                                                                                                                                                                                           |                                                                                                                 |
| 2026-09-15; app build not recorded | Local MCP enable and tool use  | Both tools succeeded in the App after the selected custom agent's tool allowlist was corrected. The earlier failure was a local agent configuration error, not an established App defect. | Original App screenshot and slide detail archived in the [capture record](../presentation/assets/README.md); copied tool responses are below | Approved synthetic evidence was retrieved through App MCP calls without shell or file-read substitution | Show effective tools and the permission/configuration layer responsible for unavailable tools beside the selected agent; suggest narrow corrections without automatic privilege expansion | App MCP verification complete from the supplied screenshot and returned payloads; no independent replay claimed |
|                                    | Parallel isolated sessions     |                                                                                                                                                                                           |                                                                                                                                              |                                                                                                         |                                                                                                                                                                                           |                                                                                                                 |
|                                    | Pull request checks and review |                                                                                                                                                                                           |                                                                                                                                              |                                                                                                         |                                                                                                                                                                                           |                                                                                                                 |

## App MCP Rehearsal: 2026-09-15

Verification status: complete for the two Local / Interactive App MCP calls. The entrant supplied an App screenshot showing both tool entries, the EVD-002 argument, and MOSAIC Orchestrator selected, then copied the returned JSON from each tool's details into the handoff conversation.

Provenance: the responses below are preserved from those copies, with JSON formatting normalized and duplicate formatted/minified presentations removed. They were not reconstructed from source files or shell commands. The [original App screenshot](../presentation/assets/copilot-app-session.png) is now archived unchanged at its native 1920 by 1032 window resolution, with a lossless [slide detail](../presentation/assets/copilot-app-detail.png). The [capture record](../presentation/assets/README.md) records the original hash and crop coordinates. This is a product-use observation, not an additional allowlisted source for the synthetic design.

| Field               | App result supplied by entrant                                     |
| ------------------- | ------------------------------------------------------------------ |
| Server              | `mosaic-synthetic-evidence`                                        |
| Selected agent      | `MOSAIC Orchestrator`                                              |
| First call          | `list_approved_sources`                                            |
| Returned source IDs | `EVD-001`, `EVD-002`, `EVD-003`, `EVD-004`                         |
| Second call         | `read_approved_source` with `source_id="EVD-002"`                  |
| EVD-002 title       | Synthetic AI security standard                                     |
| EVD-002 revision    | `2.1`                                                              |
| EVD-002 SHA-256     | `0421ea4a9cf5958c17ec134db78156f8d555de9a4839e892dc4b567812388db6` |

The installed server was left unchanged. The entrant reported no shell commands, file reads, edits, or release authorization during the verification. The required submission state remains `awaiting_human_review` / `waiting_for_human` / `releaseAuthorized=false`.

Integrity semantics: the [connector](../src/mosaic/connectors/synthetic.py) hashes original file bytes, while the [MCP tool](../src/mosaic/mcp_server.py) returns newline-normalized text. Preserve the returned digest as source-byte metadata; hashing only the normalized `content` string is not an equivalent check. Later local connector hardening and tests do not rewrite this historical observation or constitute an independent App replay.

Installed-version observation: on 2026-09-15, the installed `github.exe` file's Windows version metadata reported product **GitHub Copilot**, product version **1.1.21**, file version **1.1.21**. The application was not launched and no authentication or MCP replay occurred. This records the current installation, not the historical screenshot's unrecorded build. Keep those two facts separate in any feedback response.

### Returned Source List

Tool: `mosaic-synthetic-evidence/list_approved_sources`.

```json
{
  "mode": "read-only",
  "dataBoundary": "synthetic",
  "networkAccess": false,
  "sources": [
    {
      "id": "EVD-001",
      "title": "Synthetic employee policy assistant intake",
      "classification": "SYNTHETIC",
      "owner": "Synthetic Business Services",
      "revision": "1.0",
      "sha256": "62e02b10d1f8fc6cec12ac6069fc89bc7e2588dfbe90cc3924ba7a3434d566e5"
    },
    {
      "id": "EVD-002",
      "title": "Synthetic AI security standard",
      "classification": "SYNTHETIC",
      "owner": "Synthetic Security Office",
      "revision": "2.1",
      "sha256": "0421ea4a9cf5958c17ec134db78156f8d555de9a4839e892dc4b567812388db6"
    },
    {
      "id": "EVD-003",
      "title": "Synthetic data classification policy",
      "classification": "SYNTHETIC",
      "owner": "Synthetic Data Governance Council",
      "revision": "3.0",
      "sha256": "7a7faa59714094c2c9502070b51e539937bd7934179200bf83e7c94d2215f602"
    },
    {
      "id": "EVD-004",
      "title": "Synthetic architecture and evidence standard",
      "classification": "SYNTHETIC",
      "owner": "Synthetic Architecture Review Board",
      "revision": "1.4",
      "sha256": "a345a006ac9957fdc6959cb5251fc0f717bb876c11856b131ff3a5b6c145fa58"
    }
  ]
}
```

### Returned EVD-002 Source

Tool: `mosaic-synthetic-evidence/read_approved_source` with `source_id="EVD-002"`.

```json
{
  "id": "EVD-002",
  "title": "Synthetic AI security standard",
  "classification": "SYNTHETIC",
  "revision": "2.1",
  "sha256": "0421ea4a9cf5958c17ec134db78156f8d555de9a4839e892dc4b567812388db6",
  "content": "# Synthetic AI Security Standard\n\nConnected sources use least privilege and read-only access by default. The workflow records source identity and content integrity. Qualified humans approve architecture, risk disposition, external communication, and release. Automation may prepare evidence and recommendations but cannot make those decisions.\n",
  "provenance": "allowlisted synthetic fixture"
}
```

The authentic Local MCP screenshot remains archived as evidence for this observation. Slide 2 uses separate authentic crops from the published October 7 App workflow recording. Neither capture proves hosted review or native multi-agent collaboration. No independent replay or historical build identification is claimed.

## Feedback Rules

- Describe observed behavior, not assumptions about product architecture.
- Record strengths as well as limitations.
- Separate tenant policy or local configuration issues from product limitations.
- Do not claim competitor limitations from memory.
- Remove screenshots or details that reveal accounts, tokens, tenant information, or unrelated repositories.
- Do not invent an observation or replay. Use captured evidence with explicit date, build and scope limitations when independent reproduction has not been performed.
