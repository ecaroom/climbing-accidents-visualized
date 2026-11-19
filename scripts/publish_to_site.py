"""Copy the built site/ into the eliotcaroom.com repo as a standalone page.

Usage: .venv/bin/python scripts/publish_to_site.py <path-to-eliotcaroomdotcom-clone> [url-path]
Default url-path: climbing-accidents  ->  public/climbing-accidents/  ->  eliotcaroom.com/climbing-accidents/

Per that repo's OPERATIONS.md, a standalone page in public/ needs the site favicon, the theme-sync
script, a back link and the Cloudflare Web Analytics snippet. Those are injected at the
<!-- SITE:... --> markers in site/index.html, so the local/GitHub copy stays free of them.
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
FILES = ["index.html", "sankey.json", "accidents.json", "reports.json"]

HEAD = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        "<script>var t=null;try{t=localStorage.getItem('theme');}catch(e){}"
        "document.documentElement.dataset.theme=t||'light';</script>\n"
        '<style>.backlink{display:inline-block;margin:0 0 14px;font:0.8rem ui-monospace,Menlo,monospace;'
        'color:var(--ink-3);text-decoration:none}.backlink:hover{color:var(--ink)}</style>')
BACKLINK = '<a class="backlink" href="/projects/">&larr; projects</a>'
ANALYTICS = ("<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' "
             "data-cf-beacon='{\"token\": \"fd264bcbb3ed4cf1b5d0f59cb473d84c\"}'></script><!-- End Cloudflare Web Analytics -->")


def main():
    repo = pathlib.Path(sys.argv[1]).resolve()
    url_path = sys.argv[2] if len(sys.argv) > 2 else "climbing-accidents"
    assert (repo / "astro.config.mjs").exists() and (repo / "public").is_dir(), f"{repo} is not the eliotcaroom.com repo"
    dest = repo / "public" / url_path
    dest.mkdir(parents=True, exist_ok=True)
    html = (SITE / "index.html").read_text(encoding="utf-8")
    for marker, value, n in [("<!-- SITE:head -->", HEAD, 1), ("<!-- SITE:backlink -->", BACKLINK, 2),
                             ("<!-- SITE:analytics -->", ANALYTICS, 1)]:
        assert html.count(marker) == n, f"expected {n}x {marker}"
        html = html.replace(marker, value)
    (dest / "index.html").write_text(html, encoding="utf-8")
    for f in FILES[1:]:
        shutil.copy2(SITE / f, dest / f)
    total = sum((dest / f).stat().st_size for f in FILES)
    print(f"wrote {dest} ({len(FILES)} files, {total / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
