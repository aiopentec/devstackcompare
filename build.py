#!/usr/bin/env python3
"""
DevStackCompare — static site builder.
Same architecture as CareerToolFinder: reads data/tools.yaml, renders Jinja2
templates, outputs to docs/ (GitHub Pages source).

Canonical URL rule: only ONE comparison page per pair, alphabetical by slug.
Reverse URL gets a meta-refresh redirect, never a duplicate page.
"""
import itertools
import os
import shutil
from datetime import date
import yaml
from jinja2 import Environment, FileSystemLoader

SITE_NAME = "DevStackCompare"
SITE_URL = "https://devstackcompare.com"
OUT_DIR = "docs"
DATA_FILE = "data/tools.yaml"

CATEGORY_LABELS = {
    "vps": "VPS Providers",
    "platform": "Managed App Platforms",
    "hosting": "Static & Frontend Hosting",
    "database": "Managed Databases",
}

env = Environment(loader=FileSystemLoader("templates"), autoescape=True)
env.globals["build_date"] = date.today().strftime("%B %d, %Y")


def load_tools():
    with open(DATA_FILE) as f:
        tools = yaml.safe_load(f)
    by_slug = {t["slug"]: t for t in tools}
    return tools, by_slug


def clean_output():
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)
    if os.path.exists("static"):
        shutil.copytree("static", os.path.join(OUT_DIR, "static"))
    if os.path.exists("CNAME"):
        shutil.copy("CNAME", os.path.join(OUT_DIR, "CNAME"))


def build_home(tools):
    tmpl = env.get_template("index.html")
    categories = sorted(set(t["category"] for t in tools))

    all_pairs = []
    for cat in categories:
        cat_tools = sorted([t for t in tools if t["category"] == cat], key=lambda t: t["slug"])
        for a, b in itertools.combinations(cat_tools, 2):
            all_pairs.append({"a": a, "b": b, "category": cat, "category_label": CATEGORY_LABELS[cat]})

    chip_counts = [("all", "All", len(all_pairs))]
    for cat in categories:
        count = sum(1 for p in all_pairs if p["category"] == cat)
        chip_counts.append((cat, CATEGORY_LABELS[cat], count))

    html = tmpl.render(
        site_name=SITE_NAME,
        site_url=SITE_URL,
        categories=[(c, CATEGORY_LABELS[c]) for c in categories],
        tool_count=len(tools),
        comparison_count=len(all_pairs),
        category_count=len(categories),
        pairs=all_pairs,
        chip_counts=chip_counts,
    )
    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(html)


def build_categories(tools):
    tmpl = env.get_template("category.html")
    os.makedirs(os.path.join(OUT_DIR, "category"), exist_ok=True)
    categories = sorted(set(t["category"] for t in tools))
    for cat in categories:
        cat_tools = sorted([t for t in tools if t["category"] == cat], key=lambda t: t["name"])
        cat_tools_by_slug = sorted(cat_tools, key=lambda t: t["slug"])
        pairs = [{"a": a, "b": b} for a, b in itertools.combinations(cat_tools_by_slug, 2)]
        html = tmpl.render(
            site_name=SITE_NAME,
            site_url=SITE_URL,
            category=cat,
            category_label=CATEGORY_LABELS[cat],
            tools=cat_tools,
            pairs=pairs,
        )
        with open(os.path.join(OUT_DIR, "category", f"{cat}.html"), "w") as f:
            f.write(html)


def build_comparisons(tools, by_slug):
    tmpl = env.get_template("comparison.html")
    redirect_tmpl = env.get_template("redirect.html")
    os.makedirs(os.path.join(OUT_DIR, "compare"), exist_ok=True)

    categories = sorted(set(t["category"] for t in tools))
    pair_count = 0
    for cat in categories:
        cat_tools = sorted([t for t in tools if t["category"] == cat], key=lambda t: t["slug"])
        for a, b in itertools.combinations(cat_tools, 2):
            canonical_slug = f"{a['slug']}-vs-{b['slug']}"
            reverse_slug = f"{b['slug']}-vs-{a['slug']}"

            html = tmpl.render(
                site_name=SITE_NAME,
                site_url=SITE_URL,
                tool_a=a,
                tool_b=b,
                canonical_path=f"/compare/{canonical_slug}.html",
                category_label=CATEGORY_LABELS[cat],
            )
            with open(os.path.join(OUT_DIR, "compare", f"{canonical_slug}.html"), "w") as f:
                f.write(html)

            redirect_html = redirect_tmpl.render(site_url=SITE_URL, canonical_path=f"/compare/{canonical_slug}.html")
            with open(os.path.join(OUT_DIR, "compare", f"{reverse_slug}.html"), "w") as f:
                f.write(redirect_html)
            pair_count += 1
    print(f"Generated {pair_count} canonical comparison pages ({pair_count * 2} total URLs with redirects)")


def build_alternatives(tools, by_slug):
    tmpl = env.get_template("alternatives.html")
    for tool in tools:
        same_cat = sorted(
            [t for t in tools if t["category"] == tool["category"] and t["slug"] != tool["slug"]],
            key=lambda t: t["name"],
        )
        alt_entries = []
        for other in same_cat:
            if tool["slug"] < other["slug"]:
                compare_path = f"/compare/{tool['slug']}-vs-{other['slug']}.html"
            else:
                compare_path = f"/compare/{other['slug']}-vs-{tool['slug']}.html"
            alt_entries.append({"tool": other, "compare_path": compare_path})

        html = tmpl.render(
            site_name=SITE_NAME,
            site_url=SITE_URL,
            tool=tool,
            category_label=CATEGORY_LABELS[tool["category"]],
            alternatives=alt_entries,
        )
        with open(os.path.join(OUT_DIR, f"alternatives-to-{tool['slug']}.html"), "w") as f:
            f.write(html)
    print(f"Generated {len(tools)} alternatives hub pages")


def build_static_pages():
    for page in ("about", "contact", "privacy"):
        tmpl = env.get_template(f"{page}.html")
        html = tmpl.render(site_name=SITE_NAME, site_url=SITE_URL)
        with open(os.path.join(OUT_DIR, f"{page}.html"), "w") as f:
            f.write(html)
    print("Generated about.html, contact.html, privacy.html")


def build_sitemap(tools):
    urls = [f"{SITE_URL}/"]
    categories = sorted(set(t["category"] for t in tools))
    for cat in categories:
        urls.append(f"{SITE_URL}/category/{cat}.html")

    for cat in categories:
        cat_tools = sorted([t for t in tools if t["category"] == cat], key=lambda t: t["slug"])
        for a, b in itertools.combinations(cat_tools, 2):
            urls.append(f"{SITE_URL}/compare/{a['slug']}-vs-{b['slug']}.html")

    for t in tools:
        urls.append(f"{SITE_URL}/alternatives-to-{t['slug']}.html")

    for page in ("about", "contact", "privacy"):
        urls.append(f"{SITE_URL}/{page}.html")

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f"  <url><loc>{u}</loc></url>")
    lines.append("</urlset>")
    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w") as f:
        f.write("\n".join(lines))
    print(f"Sitemap: {len(urls)} canonical URLs")


def main():
    tools, by_slug = load_tools()
    clean_output()
    build_home(tools)
    build_categories(tools)
    build_comparisons(tools, by_slug)
    build_alternatives(tools, by_slug)
    build_static_pages()
    build_sitemap(tools)
    print(f"Build complete: {len(tools)} tools -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
