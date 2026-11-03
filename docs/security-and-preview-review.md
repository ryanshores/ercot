# Historical review — preview proposal deferred

Current decision: main-only production deployments. See [current setup](portainer-deployments.md). The observations below predate the proxy hardening recorded there.

# Portainer exposure review and PR preview design

Reviewed November 2, 2026 (America/Chicago). Read-only checks; no remote configuration or deployments changed.

## Observed findings

- https://pt.ryanshores.us responds through Cloudflare. Public HTTP redirects to HTTPS. Portainer is CE 2.45.3, matching the upstream latest release checked during this review.
- Unauthenticated requests to /api/endpoints, /api/users, /api/settings, and /api/stacks returned 401. /api/status is public and reveals the version and instance ID. No authentication bypass was found in these limited checks.
- The Portainer container mounts the host Docker socket read/write. Compromise of an administrative account or deployment credential therefore has host-level consequences.
- The entire Portainer UI/API is publicly reachable with no additional proxy access gate in the inspected Nginx host configuration. Prefer an identity gate with MFA for operators, with a narrowly scoped machine path for automation. Public reachability of the whole dashboard is unnecessary for deployment.
- Nginx Proxy Manager publishes port 9000's upstream over HTTP. Portainer itself binds host port 9000 on all host interfaces. The proxy host accepts both HTTP and HTTPS and has no origin-side forced-HTTPS directive. The public Cloudflare HTTP redirect was verified, but direct-origin/port-forward reachability was not verified from a separate external network. Restrict direct origin access and do not forward management ports 81/9000 externally. Use a private Docker network for the proxy-to-Portainer hop where practical.
- Asset caching is enabled in the Portainer proxy host. The asset rule ignores upstream Cache-Control and Set-Cookie headers. The public entry page also advertises a year-long max-age. Disable proxy asset caching for this management UI and bypass edge caching for the host; confirm policies before changing them. This review did not demonstrate authenticated-content leakage.
- Public HTTPS request to ercot-pr-987654321.ryanshores.us returned Cloudflare 525. Unknown-host fallback currently fails TLS before reaching a hello-world response. Wildcard DNS alone does not establish working wildcard HTTPS.

Not inspected: passwords, MFA/account policy, user/API-key inventory, Cloudflare account rules, router forwarding/firewall, authenticated audit history, or all vulnerability classes. This is a configuration/exposure review, not a full penetration test or a guarantee of safety.

## Recommended release model

PR previews and release tags solve separate needs. Do not keep a shared staging branch/site. Each approved PR gets a temporary Portainer stack. A protected release tag on a commit reachable from main selects production. Use immutable image digests and record the source commit.

Example:
- PR 42 -> ercot-pr-42.ryanshores.us, Portainer stack ercot-pr-42.
- A new PR commit tests/builds a new image, then updates only that preview.
- PR closed or merged -> remove its route, stack, and explicitly owned temporary database volume.
- Version tag v1.2.0 -> test/verify the main commit, publish/select its immutable artifact, deploy production via Portainer.

If the exact tested PR artifact must be promoted, require the same source commit and immutable digest. A merge commit or squash merge is a different commit; test and build that main revision before release instead of claiming it is the PR-tested image.

## Routing with Nginx Proxy Manager

Use single-label hostnames, for example ercot-pr-42.ryanshores.us, covered by *.ryanshores.us. A name such as pr-42.ercot.ryanshores.us needs a different wildcard certificate.

Keep existing production/admin hostnames as explicit proxy hosts. Add a single wildcard proxy host and valid wildcard origin certificate for preview/fallback traffic. Forward that wildcard host to a small preview gateway on an internal Docker network. Its exact-host allowlist maps only active, ready preview stacks to their internal service addresses. Unknown and closed previews serve the basic hello-world response. Do not turn arbitrary Host strings into upstream addresses.

This avoids editing Nginx Proxy Manager's generated files or allocating a public host port per PR. A central gateway is shared infrastructure managed as its own Portainer stack. PR apps attach to its internal network and their own database network; they do not receive Docker socket access or production secrets. Protect admin hostnames and reject spoofed Host routing. Use no shared parent-domain authentication cookies across previews and production; an isolated preview parent domain is preferable for untrusted projects.

## Provisioning and trust boundaries

A fixed trusted controller creates/updates/deletes Portainer stacks using a server-owned Compose template. Inputs are a validated repository identity, numeric PR number, and verified image digest. Never deploy a Compose file supplied by PR code with administrative credentials. Per-stack webhooks update existing resources; dynamic create/delete needs Portainer API orchestration.

Build/test PR code on GitHub-hosted runners without Portainer credentials. The privileged deployment controller must verify repository, approval, PR state and current head commit, then consume only the verified image identity. Do not execute PR code in a credentialed pull_request_target job or install a self-hosted build runner on the production Docker host. For an initial version, accept trusted same-repository PRs; require explicit review for forks.

Preview runtime limits: separate disposable DB, memory/CPU/PID limits, non-root where supported, no privileged mode, no host mounts/socket, dropped capabilities, no production credentials, and network restrictions against the LAN/control plane. A shared Docker network alone is not an isolation boundary. For other projects that execute less-trusted code, use a separate preview Docker environment/VM registered in Portainer.

## Cleanup and lifecycle

On PR close/merge, remove the hostname mapping first, stop/delete the owned stack through Portainer, and remove only its labelled disposable volumes. Do not prune globally. Do not assume deleting a stack deletes named volumes.

Serialize operations per repository/PR and re-check PR state before exposing the route so an older build cannot recreate a closed preview. A scheduled reconciler compares labelled preview resources with open PRs, handles missed close events, cleans up partial failures, and enforces expiry. Limit simultaneous previews. Container cleanup and registry image retention are separate policies.

## Preparation status

The earlier compose.staging.yml and main/staging webhook workflow are superseded drafts and must not be activated as the final architecture. PORTAINER_DEPLOY_ENABLED remains disabled unless set externally; this review did not change repository variables. No PR stacks, wildcard gateway, routes, secrets, releases, or remote security settings were created.

References:
- https://github.com/portainer/portainer/releases/tag/2.45.3
- https://github.com/portainer/portainer/security/advisories/GHSA-j3mf-q9qf-5qf8
- https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
