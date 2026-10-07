# Security Policy

## Supported Scope

This repository is a synthetic reference implementation. Security fixes target the latest revision on the default branch. No production service or customer connector is operated from this repository.

## Report A Vulnerability Or Sensitive Data

Do not open a public issue for a suspected vulnerability, credential, personal data, customer identifier, or restricted artifact. After publication, use the repository's private security advisory flow. Before publication, contact Greg Unger at `gregunger@microsoft.com` through an approved Microsoft channel.

Include the affected revision, file or component, reproduction steps using synthetic data, expected impact, and any temporary containment already applied. Do not include live secrets or customer records in the report.

## Security Boundary

The offline reference (`python -m mosaic.cli`) and synthetic evidence connector:

- reads four local synthetic sources
- performs no network calls
- requires no credentials
- exposes two read-only MCP tools
- rejects arbitrary source paths and non-allowlisted IDs
- records source revisions and SHA-256 hashes
- stops before release at qualified human review

### Separately Authorized Analysis

The conversational path can make one explicitly approved model call through a separately authenticated, dedicated Copilot CLI profile. That path has network access; it is not covered by the offline reference's no-network claim. Approval must disclose the configured model, credit cap, deadline, submitted brief and allowed synthetic evidence. The local captured transcript is excluded from the analysis prompt. The adapter exposes no tools and does not automatically retry paid inference or switch providers.

Credentials, local settings, sealed inputs, transcripts, retained responses and generated jobs stay in ignored local storage. Ignore rules prevent routine staging, not access by another process or a hostile user on the same computer. Hash checks detect changes relative to recorded digests; they are not signatures or production identity assurance. The example environment flags are documentation, not an enforcement mechanism.

New captures record session timing, not authenticated sender identity. `John Doe` is an explicit unverified default, and a supplied display name is also unverified. Generation approval, browser launch and passing validation do not establish architecture selection, dossier approval or release authority.

The repository does not establish production authentication, authorization, tenancy, data residency, encryption-key ownership, retention, legal hold, monitoring, incident response, backup, or disaster recovery.

## Production Connector Requirements

Before enabling a customer connector, require documented approval for purpose, owner, identity, least-privilege scopes, data classes, source authorization, network path, encryption, retention, logging, audit export, failure behavior, disable procedure, and incident response. Keep customer installations isolated by identity, configuration, storage, workspace, and deployment boundary.

Never place credentials in prompts, policies, fixtures, logs, issues, generated artifacts, screenshots, or pull requests.

## Human Authority

Automated validation is necessary but insufficient. Qualified humans approve evidence access, policy and risk disposition, customer facts, architecture, product fit, commitments, acceptance, and release against an exact repository revision.
