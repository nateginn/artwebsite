# artwebsite — operating instructions

Django site for acceleratedrehabtherapy.com, a physical-therapy clinic
(client "art" in Nate's other systems). Single Django app
(`acceleratedrehabtherapy/apps/main`), Poetry-managed. Live production site,
single environment — **there is no staging.**

## Deploy — Tier 2, human-only, always

`.github/workflows/deploy.yml` runs on push to `main`: tests -> SSH to the
production host -> `git fetch && git reset --hard origin/main` -> upserts
`META_PIXEL_ID`/`META_CAPI_TOKEN`/`ALLOWED_HOSTS` from GitHub Secrets into
the server's own `.env` -> `poetry install` -> `migrate` -> `collectstatic`
-> restarts gunicorn. **Every push to `main` deploys to production
immediately, with no approval gate.** No automated tool (including MMC,
Looping Agency, or any headless Claude session) may push here — this is a
human-only action, always.

## Meta pixel

Rendered in `acceleratedrehabtherapy/templates/base_landing.html:96-109`,
gated on `settings.META_PIXEL_ID`; server-side CAPI Lead event fires on
landing-form submit (`acceleratedrehabtherapy/apps/main/views.py` —
`_send_capi_lead_event` helper defined at line 398, gated call site at
lines 589-592 on pixel ID + CAPI token both set).
Canonical pixel: `26663797973291582`. As of 2026-07-15 the production
server's `.env` was found missing both pixel vars despite the code/config
being correct and pushed — the deploy workflow now syncs those keys into
the server `.env` on every deploy, which is believed to have fixed it (see
MMC section below — verify independently rather than assuming).

## MMC (shared brain)

Before cross-system work (anything touching another of Nate's four
systems, or client facts shared across them), read `D:\Dev\MMC\MMC.md`
first. This is a manual-read instruction, not automatic context injection —
`@import` auto-load was tested and does not reliably resolve in headless
(`claude -p`) sessions.

The pixel gap above is the canonical example of the drift problem MMC
exists to catch — a fact (pixel firing) that looked fine from this repo's
own commits but was silently wrong in production for weeks because no
system had visibility into both sides. See `D:\Dev\MMC\kb\decisions.md`
(2026-07-15 entry) and `D:\Dev\MMC\registry\clients\art.yaml`.
