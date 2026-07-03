# GitHub social preview (OG thumbnail)

Use the same Open Graph card that powers link previews on the live site.

## Image URL

**Live (recommended for upload):**

https://kartavya-jharwal.github.io/ganet-project-bwc/assets/og-card.png

**In-repo copy:**

`frontend/assets/og-card.png`

## Manual setup (required)

GitHub does **not** support setting the repository social preview through the `gh` CLI or public REST API. Upload it in the web UI:

1. Open the repository on GitHub.
2. Go to **Settings → General**.
3. Scroll to **Social preview**.
4. Click **Edit**, then upload `og-card.png` (from the URL above or from `frontend/assets/og-card.png` locally).
5. Save. GitHub may take a few minutes to refresh cached previews on shares.

## Verify

Paste the repository URL into a link-preview debugger (Slack, Discord, LinkedIn, or [opengraph.xyz](https://www.opengraph.xyz/)) after saving. The card should show the Adaptive Efficiency branding from the live site asset.

## Related

- Site OG meta: `frontend/index.html`
- Maintainer logos: `frontend/assets/PB_logos/`
- Publication checklist: [REVIEWERS.md](https://github.com/Kartavya-Jharwal/ganet-project-bwc/blob/main/REVIEWERS.md#publication-checklist-archive-seal)
