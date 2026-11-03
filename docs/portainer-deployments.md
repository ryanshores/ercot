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

Nginx Proxy Manager changes applied to pt.ryanshores.us: Cache Assets off, Force SSL on, proxy caching off, and origin Cache-Control no-cache. Management access now uses the existing Local IPs Only access list (192.168.50.0/24 and 10.6.0.0/24). Only UUID-shaped /api/stacks/webhooks/<uuid> paths accept public POST requests. Other public API requests and webhook GET requests return 403. A dummy webhook POST reaches Portainer and returns its missing-webhook 404; direct LAN /api/status still works. The callback URL remains a bearer credential and must stay secret.

Cloudflare still has older cached UI responses. Purge the cache for this hostname and add a full cache bypass rule in Cloudflare. No Cloudflare account configuration was changed. Router forwarding and direct internet access to management ports 81/9000 remain unverified.

Next steps: sign into Portainer over the LAN/VPN, reconcile its production stack with the committed Compose definition, configure its GitOps webhook, put the URL into the production GitHub environment secret, and enable the repository variable only after image pulls are verified. No real webhook was generated and no deployment was triggered during hardening.

## Rollback

Each image has a sha-<full commit SHA> tag. Normal rollback is a revert merged into main. For an emergency pin, disable automated notifications, select the previous SHA-tagged image in Portainer, and reconcile the desired state in Git before reenabling notifications. Do not move or overwrite SHA tags.

The /health endpoint checks the web server, not import freshness. Check the newest timestamp after releases. ERCOT's rolling feed only recovers three days; the older October data gap is separate work.

References:
- https://docs.portainer.io/user/docker/stacks/add#gitops-updates
- https://docs.portainer.io/faqs/troubleshooting/stacks-deployments-and-updates/how-do-automatic-updates-for-stacks-applications-work
