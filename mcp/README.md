# MCP Evidence Connector

MOSAIC is AI-first business process automation for solution engineering; approved evidence is one governed input to that process. The bundled `mosaic-synthetic-evidence` server uses the MCP Python SDK 2.x and exposes two local, read-only tools for the contest scenario. It makes the evidence boundary visible in GitHub Copilot App without requiring network access, credentials, a customer tenant, or real customer records. The SDK major version is not a claim about a protocol named "MCP v2".

| Property       | Value                                                      |
| -------------- | ---------------------------------------------------------- |
| Purpose        | Retrieve approved evidence for the synthetic MOSAIC intake |
| Data accessed  | Four files under `examples/synthetic/sources/`             |
| Authentication | None; local synthetic content only                         |
| Operations     | List approved sources; read one source by evidence ID      |
| Writes         | None                                                       |
| Network access | None                                                       |
| Owner          | Greg Unger (`gregunger@microsoft.com`)                     |

## Tools

- `list_approved_sources` returns source identity, classification, owner, revision, and SHA-256.
- `read_approved_source` accepts an evidence ID such as `EVD-002`. Unknown IDs and arbitrary paths fail closed.

The connector rejects duplicate source IDs and paths that resolve outside the evidence root. It hashes original file bytes; the tool's `content` is newline-normalized text, so hashing that string is not an equivalent integrity check. Git attributes preserve the captured fixture bytes across checkouts. This is a trusted local synthetic fixture boundary, not protection against a hostile local administrator.

## Enable

Install the optional SDK dependency in the active environment:

```powershell
python -m pip install -e ".[mcp]"
```

The shared [Copilot App and CLI configuration](../.github/mcp.json) exposes only the two tools listed above. Start a trusted local session at the repository root with an interpreter that has the MCP extra installed. The configuration sets `PYTHONPATH=src` and `PYTHONNOUSERSITE=1` so an inherited source path or user-site package cannot take precedence over this checkout.

For a per-checkout interpreter, use a repository-root `.mcp.json` override with the same `mcpServers` structure. On Windows, set its `command` to `./.venv/Scripts/python.exe`; on macOS or Linux, use `./.venv/bin/python`. This local override is ignored by Git and takes precedence over the shared configuration.

The [VS Code configuration](../.vscode/mcp.json) is separate: Copilot CLI does not read it or support its top-level `servers` key. See [GitHub's project-level MCP instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers#adding-per-repository-mcp-servers).

After changing configuration, start a fresh local app session and check **Customize > MCP > Installed**. Approve only this repository and this local server if prompted. A configuration file or successful CLI run is not proof that the app session has exposed the tools: call `list_approved_sources`, then `read_approved_source` with `EVD-002`, in the app itself. If either tool is unavailable, stop and report it instead of substituting file reads.

For this entrant's checkout, that verification is already complete and archived in the [observation log](../docs/product-feedback-observation-log.md). Do not repeat it or replace the working installed registration for this audit. The setup instructions above are for a new authorized installation.

## Disable

Disable `mosaic-synthetic-evidence` under **Customize > MCP > Installed**. To remove the project configuration entirely, remove both the shared configuration and any local override after stopping the server. No remote service remains to decommission.

## Production Boundary

This server is demonstration infrastructure. A customer connector requires independent identity, privacy, security, retention, source-authorization, and audit approval. Optional tools such as Work IQ remain read-only and disabled until that review is complete.
