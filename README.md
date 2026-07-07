# DevStackCompare

Programmatic SEO comparison site for developer infrastructure: VPS providers, managed
app platforms, static/frontend hosting, and managed databases. Built on the same
zero-cost stack as osalfinder.com, emailtoolcompare.com, aitoolalternatives.com, and
careertoolfinder.com.

## Stack
- Python + Jinja2 static site generator (`build.py`)
- Data lives in `data/tools.yaml` — add tools here, no code changes needed
- GitHub Actions (`.github/workflows/pipeline.yml`) builds on push + weekly cron, deploys to `gh-pages` branch
- GitHub Pages serves from `gh-pages`, custom domain via the `CNAME` file

## Local build
```
pip install -r requirements.txt
python build.py
```
Output goes to `docs/` (not committed directly — the `gh-pages` branch is what's published).

## Site structure
- `/` — homepage with stats bar, category grid, and a filterable card grid of every comparison
- `/category/{vps,platform,hosting,database}.html` — one page per category, listing tools and head-to-head comparisons
- `/compare/{a}-vs-{b}.html` — one page per pair, alphabetical by slug only (see Canonical URL handling below)
- `/alternatives-to-{tool}.html` — one hub page per tool, linking every comparison it appears in
- `/about.html`, `/contact.html`, `/privacy.html` — static pages

## Canonical URL handling
Comparison pairs are only generated in alphabetical slug order (e.g.
`digitalocean-vs-vultr.html`, never the reverse as a full page). The reverse URL
(`vultr-vs-digitalocean.html`) exists only as a meta-refresh redirect with a canonical
tag pointing at the real page. Only canonical URLs are included in `sitemap.xml`. This
mirrors the fix that resolved the emailtoolcompare.com indexing incident.

## Affiliate links
DigitalOcean and Vultr are the two pre-approved affiliate partners (`affiliate: true`
in `data/tools.yaml`). Their `affiliate_link` field is used for outbound "Visit site"
links instead of the plain `url` field, and both appear in the dual-partner CTA block
(`templates/_affiliate_cta.html`) shown on the VPS category page and any comparison
page involving either tool. Every other provider listed carries no financial
relationship — see `/about.html` for the full disclosure.

## Growing the site
Currently 17 tools / 28 comparison pairs across 4 categories. To add a tool: add an
entry to `data/tools.yaml` with a unique `slug`, then rebuild — the comparison pages,
category page, alternatives hub, and sitemap all regenerate automatically.

## Before you launch further changes
1. Domain: `devstackcompare.com`, already wired into `build.py` (`SITE_URL`) and `CNAME`
2. GSC: submit `https://devstackcompare.com/sitemap.xml` once DNS/Pages are live
3. Affiliate dashboards: DigitalOcean and Vultr links are the personal Referral Program
   links (not the formal CPA Affiliate Program), confirmed to have no domain-declaration
   requirement — safe to reuse across sites without additional registration
