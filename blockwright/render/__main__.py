"""CLI: python -m blockwright render <file.litematic> <out_dir> [--quick] [--views iso_se,top] [--no-terrain]"""
import argparse
import pathlib
import sys
import time


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m blockwright render", description="Render .litematic previews")
    ap.add_argument("litematic")
    ap.add_argument("out_dir")
    ap.add_argument("--quick", action="store_true", help="iso_se + iso_nw + first cutaway")
    ap.add_argument("--views", default=None, help="comma separated view names (iso_se,elev_n,top,cut_1,eye,...)")
    ap.add_argument("--no-terrain", action="store_true")
    ap.add_argument("--no-shadows", action="store_true")
    ap.add_argument("--size", default="1600x1200")
    ap.add_argument("--ground", type=int, default=None, help="override ground y")
    ap.add_argument("--slug", default=None)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--closeup", action="append", default=[],
                    help="extra close-up view 'x,y,z[,radius[,azimuth[,elevation]]]' (repeatable)")
    a = ap.parse_args(argv)
    from blockwright.render import read_litematic, render_views
    t = time.time()
    blocks, size, meta = read_litematic(a.litematic)
    if a.ground is not None:
        meta["ground"] = a.ground
    if a.slug:
        meta["slug"] = a.slug
    elif not meta.get("slug") or meta.get("slug") == "build":
        meta["slug"] = pathlib.Path(a.litematic).stem
    if a.views:
        views = (["quick"] if a.quick else []) + [v.strip() for v in a.views.split(",") if v.strip()]
    else:
        views = "quick" if a.quick else "all"
    if a.closeup:
        views = [views] if isinstance(views, str) else list(views)
        for c in a.closeup:
            v = [float(t) for t in c.split(",")]
            x, y, z = v[:3]
            views.append({"name": f"closeup_{int(x)}_{int(y)}_{int(z)}", "type": "ortho", "target": (x, y, z),
                          "radius": v[3] if len(v) > 3 else 4.0, "azimuth": v[4] if len(v) > 4 else 45.0,
                          "elevation": v[5] if len(v) > 5 else 30.0})
    w, h = (int(v) for v in a.size.lower().split("x"))
    paths = render_views(blocks, size, a.out_dir, meta=meta, views=views, terrain=not a.no_terrain,
                         width=w, height=h, shadows=not a.no_shadows, workers=a.workers, verbose=True)
    for p in paths:
        print(p)
    print(f"done in {time.time() - t:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
