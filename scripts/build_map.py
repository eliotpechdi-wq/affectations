"""Génère la carte interactive autonome output/carte_affectations.html.

Usage : .venv/bin/python scripts/build_map.py   (après build.py)
"""
import datetime
import json
import sqlite3
from pathlib import Path

from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parent.parent
GEO = ROOT / "data" / "raw" / "geo"
OUT = ROOT / "output"


def round_coords(obj, nd):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(obj[0], nd), round(obj[1], nd)]
        return [round_coords(o, nd) for o in obj]
    return obj


def simplify(path, tol, nd, keep=None, props=()):
    src = json.load(open(path))
    feats = []
    for f in src["features"]:
        if keep and not keep(f["properties"]):
            continue
        g = shape(f["geometry"]).simplify(tol, preserve_topology=True)
        if g.is_empty:
            continue
        geom = mapping(g)
        feats.append({"type": "Feature", "properties": {k: f["properties"].get(k) for k in props},
                      "geometry": {"type": geom["type"], "coordinates": round_coords(geom["coordinates"], nd)}})
    return {"type": "FeatureCollection", "features": feats}


def make_icon(size):
    """Icône d'application : pastille de carte blanche sur fond vert."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (size, size), (31, 94, 87))
    d = ImageDraw.Draw(img)
    u = size / 100
    d.ellipse([30 * u, 16 * u, 70 * u, 56 * u], fill="white")
    d.polygon([(33 * u, 46 * u), (67 * u, 46 * u), (50 * u, 80 * u)], fill="white")
    d.ellipse([41 * u, 27 * u, 59 * u, 45 * u], fill=(31, 94, 87))
    d.rounded_rectangle([22 * u, 84 * u, 78 * u, 88 * u], radius=2 * u, fill=(224, 178, 28))
    return img


def write_site(page):
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(page)
    (docs / ".nojekyll").write_text("")
    for name, size in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)):
        make_icon(size).save(docs / name)
        make_icon(size).save(OUT / name)
    manifest = {
        "name": "Affectations SSA", "short_name": "Affectations", "lang": "fr",
        "start_url": "./", "display": "standalone", "background_color": "#eef1ef", "theme_color": "#1f5e57",
        "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }
    for d in (docs, OUT):
        (d / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    xlsx = OUT / "affectations.xlsx"
    if xlsx.exists():
        (docs / "affectations.xlsx").write_bytes(xlsx.read_bytes())


def main():
    data = json.loads((OUT / "sites.json").read_text())
    con = sqlite3.connect(ROOT / "data" / "affectations.db")
    villes = con.execute("select nom, lat, lon, population from ref_grandes_villes").fetchall()
    data["villes"] = [[n, round(a, 4), round(o, 4), 1] for n, a, o, _ in villes]
    # Repères secondaires : communes de 15 000 à 80 000 habitants, affichées en zoomant
    communes = json.load(open(ROOT / "data" / "raw" / "communes.json"))
    data["villes"] += [[c["nom"], round(c["centre"]["coordinates"][1], 4), round(c["centre"]["coordinates"][0], 4), 2]
                       for c in communes if c.get("centre") and 15_000 <= (c.get("population") or 0) < 80_000]
    data["maj"] = datetime.date.today().strftime("%m/%Y")

    dep = simplify(GEO / "dep.geojson", 0.004, 3, props=("code", "nom"))
    world = simplify(GEO / "world50.geojson", 0.03, 2,
                     keep=lambda p: p.get("ADMIN") != "Antarctica", props=("ADMIN",))

    html = (ROOT / "scripts" / "template.html").read_text()
    css = (GEO / "leaflet.css").read_text()
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    # Connexion à la base des choix (Supabase) : URL et clé publique « anon », faites pour être dans la page.
    cfg_path = ROOT / "config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    html = (html.replace("/*__LEAFLET_CSS__*/", css)
                .replace("__CONFIG__", dump({k: cfg[k] for k in ("supabase_url", "supabase_anon_key") if cfg.get(k)}))
                .replace("__DATA__", dump(data))
                .replace("__GEO_DEP__", dump(dep))
                .replace("__GEO_WORLD__", dump(world)))
    # Version à publier en ligne (le service de publication ajoute lui-même l'enveloppe HTML)
    (OUT / "publication").mkdir(exist_ok=True)
    (OUT / "publication" / "carte.html").write_text(html)
    # Version autonome à ouvrir d'un double-clic, et version mise en ligne (GitHub Pages, dossier docs/)
    head = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="theme-color" content="#1f5e57">'
            '<meta name="apple-mobile-web-app-capable" content="yes">'
            '<meta name="mobile-web-app-capable" content="yes">'
            '<meta name="apple-mobile-web-app-title" content="Affectations">'
            '<meta name="apple-mobile-web-app-status-bar-style" content="default">'
            '<link rel="icon" type="image/png" href="icon-192.png">'
            '<link rel="apple-touch-icon" href="apple-touch-icon.png">'
            '<link rel="manifest" href="manifest.webmanifest">'
            '</head><body>')
    page = head + html + "</body></html>"
    out = OUT / "carte_affectations.html"
    out.write_text(page)
    write_site(page)
    print(f"{out} : {out.stat().st_size / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()
