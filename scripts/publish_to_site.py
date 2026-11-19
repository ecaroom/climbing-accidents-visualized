"""Copy the built site/ into the eliotcaroom.com repo.

Usage: .venv/bin/python scripts/publish_to_site.py <path-to-eliotcaroomdotcom-clone>

Layout on eliotcaroom.com:
  /climbing-accidents/      src/pages/climbing-accidents.astro (in that repo): the site's own layout
                            (header band, back link, mode button) with the app in an iframe
  /climbing-accidents/app/  public/climbing-accidents/app/: this app, copied here

The app is injected at the <!-- SITE:... --> markers in site/index.html with the site favicon and a
"framed or not" switch: inside the iframe it shows no back link and sends no analytics (the outer
Astro page already counts the visit); opened on its own (full screen) it shows a link back to
eliotcaroom.com and loads the Cloudflare Web Analytics beacon.
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
FILES = ["index.html", "sankey.json", "accidents.json", "reports.json"]
URL_PATH = "climbing-accidents/app"
CF_TOKEN = "fd264bcbb3ed4cf1b5d0f59cb473d84c"   # public by design (see the site's OPERATIONS.md)

HEAD = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        '<link rel="canonical" href="https://eliotcaroom.com/climbing-accidents/">\n'
        "<script>window.CAV_FRAMED = (function () { try { return window.self !== window.top; } catch (e) { return true; } })();\n"
        "document.documentElement.classList.toggle('framed', window.CAV_FRAMED);</script>\n"
        '<style>.backlink{display:inline-block;margin:0 0 14px;font:0.8rem ui-monospace,Menlo,monospace;'
        'color:var(--ink-3);text-decoration:none}.backlink:hover{color:var(--ink)}'
        'html.framed .backlink{display:none}</style>')
BACKLINK = '<a class="backlink" href="/climbing-accidents/">&larr; eliotcaroom.com</a>'
ANALYTICS = ("<script>if (!window.CAV_FRAMED) { var s = document.createElement('script'); s.type = 'module';"
             " s.src = 'https://static.cloudflareinsights.com/beacon.min.js';"
             f" s.setAttribute('data-cf-beacon', '{{\"token\": \"{CF_TOKEN}\"}}'); document.body.appendChild(s); }}</script>")


def main():
    repo = pathlib.Path(sys.argv[1]).resolve()
    assert (repo / "astro.config.mjs").exists() and (repo / "public").is_dir(), f"{repo} is not the eliotcaroom.com repo"
    dest = repo / "public" / URL_PATH
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
