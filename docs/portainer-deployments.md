# Production deployments through Portainer

Only pushes to main publish/deploy. Pull requests run tests without deployment credentials. Staging, release-tag triggers, and PR previews are deferred.

## Flow and activation

1. Commit and review the application fixes and deployment configuration before merging to main.
2. GitHub Actions tests and validates Compose, then builds/publishes ghcr.io/ryanshores/ercot:main and sha-<full commit SHA>. Image labels record the source commit. The image starts with an empty data directory; production retains its external database volume.
3. In Portainer, configure the production Git stack with repository https://github.com/ryanshores/ercot, reference refs/heads/main, Compose path compose.production.yml. Enable GitOps webhook updates, Re-pull image, and Force redeployment. Keep polling disabled so deployments follow CI success. These are GitOps webhooks, not the separate Business Edition editor-stack feature.
4. Create GitHub environment production and store the generated HTTPS callback as its secret PORTAINER_WEBHOOK_URL. Treat it as a deployment credential; never commit it or paste it into public logs. Public GHCR packages need no pull credential; private packages require GHCR read credentials configured in Portainer. Do not enable deployment before confirming Portainer can pull the image.
5. Once access restrictions, registry access, and stack ownership are ready, set repository variable PORTAINER_DEPLOY_ENABLED=true. Until then webhook delivery is disabled. Triggering a workflow manually is allowed only on main.
6. Verify the Portainer deployment result, image revision, container health, website, and latest saved data. A webhook 2xx means accepted, not a completed deployment.

## Existing production stack

Production currently uses port 8000 and volume ercot-energy-mix_ercot_db. compose.production.yml declares that volume external to preserve it independently of stack removal. The latest app was replaced outside Portainer earlier in this session. Reconcile the existing stack in Portainer before enabling automation. If a conversion to Git is unavailable, stop the old app, then recreate the stack in Portainer with the same name ercot-energy-mix and external database volume. Back up the DB first; do not delete volumes or run a second app against port 8000. This cutover is a deployment and must use committed source and a published image.

## Access hardening

Nginx Proxy Manager changes applied to pt.ryanshores.us: Cache Assets off, Force SSL on, proxy caching off, and origin Cache-Control no-cache. Management access protection remains pending the choice between Cloudflare Access with MFA and LAN/VPN-only access. Automation should reach only its specific HTTPS webhook path using POST. Keep the rest of the UI/API behind the chosen operator access gate. Do not broadly exempt /api from authentication. Check direct-origin restrictions and router forwarding separately; do not expose management ports 81/9000 to the internet.

If Cloudflare Access is used, exempt only the exact webhook endpoint from interactive login (its random URL is the bearer credential), or add service-token authentication and corresponding request headers. Do not enable the workflow until this has been verified. Cloudflare settings were not changed by this repository setup. Verification found Cloudflare still applies its own caching policy (max-age=14400 on a fresh URL); add a cache bypass rule for the entire Portainer hostname and purge its existing cache. Origin responses now return no-cache, but edge caching is not yet fixed.

## Rollback

Each image has a sha-<full commit SHA> tag. Normal rollback is a revert merged into main. For an emergency pin, disable automated notifications, select the previous SHA-tagged image in Portainer, and reconcile the desired state in Git before reenabling notifications. Do not move or overwrite SHA tags.

The /health endpoint checks the web server, not import freshness. Check the newest timestamp after releases. ERCOT's rolling feed only recovers three days; the older October data gap is separate work.

References:
- https://docs.portainer.io/user/docker/stacks/add#gitops-updates
- https://docs.portainer.io/faqs/troubleshooting/stacks-deployments-and-updates/how-do-automatic-updates-for-stacks-applications-work
