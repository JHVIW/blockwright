"""View definitions, auto-framing, storey detection, orchestration and contact sheet."""
from __future__ import annotations

import contextlib
import math
import os
import sys
import pathlib
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import assets
from .mesh import Scene, build_scene, guess_ground, state_info
from .raster import Atlas, build_atlas, build_shadow_map, look_camera, render

DEFAULT_W, DEFAULT_H = 1600, 1200
SKY_TOP = np.array([0.53, 0.69, 0.93], np.float32)
SKY_BOTTOM = np.array([0.89, 0.93, 0.97], np.float32)

ISO_ELEV = 32.0
VIEW_PRESETS = {
    "iso_se": dict(type="ortho", azimuth=45, elevation=ISO_ELEV),
    "iso_sw": dict(type="ortho", azimuth=315, elevation=ISO_ELEV),
    "iso_ne": dict(type="ortho", azimuth=135, elevation=ISO_ELEV),
    "iso_nw": dict(type="ortho", azimuth=225, elevation=ISO_ELEV),
    "elev_s": dict(type="ortho", azimuth=0, elevation=10),
    "elev_e": dict(type="ortho", azimuth=90, elevation=10),
    "elev_n": dict(type="ortho", azimuth=180, elevation=10),
    "elev_w": dict(type="ortho", azimuth=270, elevation=10),
    "top": dict(type="ortho", azimuth=0, elevation=90),
}
CUT_ELEV = 55.0


def cam_dir(azimuth: float, elevation: float) -> np.ndarray:
    """Unit vector from the target towards the camera. azimuth 0 = camera south (+z), 90 = east."""
    a, e = math.radians(azimuth), math.radians(elevation)
    return np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])


# ----------------------------------------------------------------------------------------------
# storeys / entrances


def detect_storeys(blocks: dict, size, meta: dict | None) -> list[int]:
    """Cut levels (y, inclusive) for per-floor cutaways, lowest first."""
    meta = meta or {}
    ground = meta.get("ground")
    if ground is None:
        ground = guess_ground(blocks, size)
    rooms = meta.get("rooms") or {}
    cuts = []
    if rooms:
        for name, p in rooms.items():
            try:
                x, y, z = (int(v) for v in p[:3])
            except Exception:
                continue
            s = blocks.get((x, y, z))
            stand = y
            if s is not None and state_info(s).full_collision:
                stand = y + 1
            cuts.append(stand + 1)
        cuts = sorted(set(cuts))
        merged = []
        for c in cuts:
            if not merged or c - merged[-1] >= 3:
                merged.append(c)
        if merged:
            return merged
    # floor-layer detection
    if not blocks:
        return []
    arr = np.array(list(blocks.keys()))
    mn, mx = arr.min(0), arr.max(0)
    dims = mx - mn + 1
    solid = np.zeros(dims, bool)
    occ = np.zeros(dims, bool)
    for (x, y, z), s in blocks.items():
        info = state_info(s)
        g = (x - mn[0], y - mn[1], z - mn[2])
        occ[g] = True
        if info.full_collision or info.cls == "SlabBlock":
            solid[g] = True
    above = np.zeros(dims[[0, 2]], bool)
    for yi in range(dims[1]):
        if yi + mn[1] > ground:
            above |= occ[:, yi, :]
    area = max(int(above.sum()), 1)
    cands = []
    for yi in range(dims[1] - 3):
        y = yi + mn[1]
        if y < ground - 1:
            continue
        floor = solid[:, yi, :] & above
        open1 = ~solid[:, yi + 1, :]
        open2 = ~solid[:, yi + 2, :]
        n = int((floor & open1 & open2).sum())
        if n >= 0.25 * area:
            cands.append(y)
    top = int(mx[1])
    cuts = []
    for y in cands:
        c = y + 2
        if c >= top:
            continue
        if not cuts or c - cuts[-1] >= 3:
            cuts.append(c)
    if not cuts:
        cuts = [int(ground) + 2]
    return cuts


def main_entrance(meta: dict | None):
    ents = (meta or {}).get("entrances") or []
    if not ents:
        return None
    e = ents[0]
    if isinstance(e, dict):
        e = e.get("pos") or e.get("position")
    try:
        return tuple(int(v) for v in e[:3])
    except Exception:
        return None


def view_list(blocks, size, meta, views="all") -> list[dict]:
    """Expand 'all' / 'quick' / list of names or dicts into view dicts."""
    if isinstance(views, str):
        views = [views]
    cuts = None
    out = []

    def get_cuts():
        nonlocal cuts
        if cuts is None:
            cuts = detect_storeys(blocks, size, meta)
        return cuts

    for v in views:
        if isinstance(v, dict):
            d = dict(v)
            d.setdefault("name", "custom")
            out.append(d)
            continue
        if v == "all":
            for n in VIEW_PRESETS:
                out.append(dict(VIEW_PRESETS[n], name=n))
            for i, c in enumerate(get_cuts()):
                out.append(dict(type="ortho", azimuth=45, elevation=CUT_ELEV, cut=c, name=f"cut_{i + 1}"))
            if main_entrance(meta) is not None:
                out.append(dict(type="eye", name="eye"))
        elif v == "quick":
            out.append(dict(VIEW_PRESETS["iso_se"], name="iso_se"))
            out.append(dict(VIEW_PRESETS["iso_nw"], name="iso_nw"))
            c = get_cuts()
            if c:
                out.append(dict(type="ortho", azimuth=45, elevation=CUT_ELEV, cut=c[0], name="cut_1"))
        elif v in VIEW_PRESETS:
            out.append(dict(VIEW_PRESETS[v], name=v))
        elif v.startswith("cut_"):
            c = get_cuts()
            try:
                k = int(v[4:]) - 1
            except ValueError:
                raise ValueError(f"unknown view {v!r} (cutaways are cut_1 .. cut_{len(c)})") from None
            if 0 <= k < len(c):
                out.append(dict(type="ortho", azimuth=45, elevation=CUT_ELEV, cut=c[k], name=v))
            else:
                print(f"[blockwright.render] WARNING view {v!r} skipped: only {len(c)} storey cut(s) detected "
                      f"(y={', '.join(str(int(x)) for x in c)}); add meta['rooms'] or pass a dict "
                      f"{{'name': ..., 'cut': y}}", file=sys.stderr)
        elif v == "eye":
            out.append(dict(type="eye", name="eye"))
        else:
            raise ValueError(f"unknown view {v!r}")
    # one view per output name (the PNG path is <slug>_<name>.png): exact duplicates are dropped, different
    # views that share a name get a numeric suffix instead of overwriting each other's file
    seen: dict = {}
    uniq = []
    for d in out:
        prev = seen.get(d["name"])
        if prev is not None:
            if prev == d:
                continue
            k = 2
            while f"{d['name']}_{k}" in seen:
                k += 1
            d = dict(d, name=f"{d['name']}_{k}")
        seen[d["name"]] = d
        uniq.append(d)
    return uniq


# ----------------------------------------------------------------------------------------------
# cameras


def _bbox_corners(bmin, bmax):
    xs, ys, zs = (bmin[0], bmax[0]), (bmin[1], bmax[1]), (bmin[2], bmax[2])
    return np.array([[x, y, z] for x in xs for y in ys for z in zs], float)


def make_camera(view: dict, scene: Scene, W: int, H: int, meta: dict | None, frame_pad=0.06):
    """Camera for a view dict; returns (camera, sun_dir)."""
    typ = view.get("type", "ortho")
    if typ == "eye":
        return _eye_camera(view, scene, W, H, meta)
    az = float(view.get("azimuth", 45))
    el = float(view.get("elevation", ISO_ELEV))
    c = cam_dir(az, el)
    fwd = -c
    if el > 89.0:
        hint = np.array([-math.sin(math.radians(az)), 0.0, -math.cos(math.radians(az))])
    else:
        hint = np.array([0.0, 1.0, 0.0])
    bmin, bmax = scene.bmin.copy(), scene.bmax.copy()
    tmp = look_camera("ortho", W, H, fwd, hint, (bmin + bmax) / 2, 1.0)
    if view.get("target") is not None:
        target = np.asarray(view["target"], float) + 0.5
    else:
        target = None
    pts = scene.frame_pts.astype(np.float64)
    hr = 0.5 * np.abs(tmp.right).sum() + 0.25     # half extent of a unit cube (+ a little terrain)
    hu = 0.5 * np.abs(tmp.up).sum() + 0.25
    pr, pu = pts @ tmp.right, pts @ tmp.up
    rmin, rmax, umin, umax = pr.min() - hr, pr.max() + hr, pu.min() - hu, pu.max() + hu
    ext_r, ext_u = rmax - rmin, umax - umin
    scale = min(W * (1 - 2 * frame_pad) / max(ext_r, 1e-3), H * (1 - 2 * frame_pad) / max(ext_u, 1e-3))
    centre_pt = tmp.right * (rmax + rmin) / 2 + tmp.up * (umax + umin) / 2
    if target is not None:
        centre_pt = target
        if view.get("radius"):
            scale = H / 2.0 / float(view["radius"])
        else:
            scale *= float(view.get("zoom", 3.0))
    elif view.get("zoom"):
        scale *= float(view["zoom"])
    cam = look_camera("ortho", W, H, fwd, hint, centre_pt, scale)
    return cam, _sun_for(az, el)


def _sun_for(az, el):
    """Sun from the camera's front-left, high: visible faces mostly lit, shadows fall back-right."""
    sa = az - 50.0
    se = 55.0 if el < 80 else 60.0
    return cam_dir(sa, se)


def _eye_camera(view, scene: Scene, W, H, meta):
    ent = main_entrance(meta)
    bmin, bmax = scene.bmin, scene.bmax
    centre = (bmin + bmax) / 2
    ground = scene.ground
    if ent is None:
        ent = (int(centre[0]), ground + 1, int(bmax[2]))
    ex, ey, ez = (v + 0.5 for v in ent)
    # outward direction: from footprint centre to the entrance, dominant axis
    dx, dz = ex - centre[0], ez - centre[2]
    rx, rz = (bmax[0] - bmin[0]) / 2, (bmax[2] - bmin[2]) / 2
    if abs(dx) / max(rx, 1) > abs(dz) / max(rz, 1):
        out = np.array([math.copysign(1, dx), 0.0, 0.0])
        half_w = rz
    else:
        out = np.array([0.0, 0.0, math.copysign(1, dz)])
        half_w = rx
    fov = math.radians(float(view.get("fov", 70)))
    vfov = 2 * math.atan(math.tan(fov / 2) * H / W)
    height = max(bmax[1] - (ground + 1), 2.0)
    eye_h = 1.62
    face = np.array([ex, 0.0, ez]) + out * 0.5
    # distance so that the facade width and the whole height fit
    d_w = (half_w + 1.5) / math.tan(fov / 2)
    d_h = (height * 0.62) / math.tan(vfov / 2)
    dist = float(view.get("distance", max(d_w, d_h, 8.0)))
    eye = np.array([face[0], ground + 1 + eye_h, face[2]]) + out * dist
    side = np.cross(out, [0.0, 1.0, 0.0])
    eye += side * float(view.get("side_offset", dist * 0.15))
    look = np.array([ex, ground + 1 + height * 0.45, ez])
    fwd = look - eye
    focal = (W / 2) / math.tan(fov / 2)
    cam = look_camera("persp", W, H, fwd, [0.0, 1.0, 0.0], eye, focal)
    horiz = -out
    az = math.degrees(math.atan2(-horiz[0], -horiz[2]))
    return cam, _sun_for(az, 15.0)


# ----------------------------------------------------------------------------------------------
# rendering


def sky(W, H) -> np.ndarray:
    t = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
    t = t ** 0.8
    img = SKY_TOP[None, None, :] * (1 - t) + SKY_BOTTOM[None, None, :] * t
    return np.repeat(img, W, axis=1)


def render_scene_view(scene: Scene, atlas: Atlas, view: dict, out_path, meta=None, width=DEFAULT_W,
                      height=DEFAULT_H, supersample=2, shadows=True) -> str:
    """Render one view of an already meshed scene to a PNG. Returns the path."""
    W, H = width * supersample, height * supersample
    cam, sun = make_camera(view, scene, W, H, meta)
    shadow = None
    if shadows and view.get("shadows", True) and len(scene):
        shadow = build_shadow_map(scene, atlas, sun, res=int(view.get("shadow_res", 2048)))
    img = render(scene, atlas, cam, sky(W, H), sun_dir=sun, shadow=shadow)
    img8 = (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    im = Image.fromarray(img8, "RGB")
    if supersample > 1:
        im = im.reduce(supersample)
    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path, optimize=False)
    return str(out_path)


EYE_MARGIN = 48


def _scene_key(v):
    return ("eye" if v.get("type") == "eye" else "ortho", v.get("cut"))


def _scene_for(blocks, size, meta, terrain, v):
    margin = EYE_MARGIN if v.get("type") == "eye" else 4
    return build_scene(blocks, size, meta, terrain=terrain, cut=v.get("cut"), margin=margin)


def _worker(args):
    scene, atlas, view, path, meta, width, height, ss, shadows = args
    t = time.time()
    p = render_scene_view(scene, atlas, view, path, meta, width, height, ss, shadows)
    return p, time.time() - t


_THREAD_ENV = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")


@contextlib.contextmanager
def _no_main_reimport():
    """Windows 'spawn' re-runs the caller's __main__ script in every worker unless it is guarded by
    `if __name__ == "__main__"`. Builder scripts are usually unguarded, and the workers only need
    blockwright.render.views._worker, so hide __main__'s file/spec while the pool spawns its processes."""
    main = sys.modules.get("__main__")
    saved = {}
    if main is not None:
        for attr in ("__file__", "__spec__"):
            if hasattr(main, attr):
                saved[attr] = getattr(main, attr)
        if "__file__" in saved:
            del main.__file__
        main.__spec__ = None
    try:
        yield
    finally:
        if main is not None:
            for attr, val in saved.items():
                setattr(main, attr, val)
            if "__spec__" not in saved and hasattr(main, "__spec__"):
                main.__spec__ = None


def _slug(meta):
    s = (meta or {}).get("slug") or "build"
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(s))


def render_views(blocks: dict, size, out_dir, meta: dict | None = None, views="all", terrain: bool = True,
                 width: int = DEFAULT_W, height: int = DEFAULT_H, supersample: int = 2, shadows: bool = True,
                 workers: int | None = None, sheet: bool = True, verbose: bool = False) -> list[str]:
    """Render preview PNGs. Returns the list of written paths (contact sheet last).

    blocks: {(x,y,z): state string}; size: (sx,sy,sz); meta: structure meta (ground, rooms, entrances, slug...)
    views: "all" | "quick" | list of names ("iso_se", "elev_n", "top", "cut_1", "eye", ...) or view dicts
           (dict keys: name, type "ortho"|"eye", azimuth, elevation, cut, target, zoom, radius, fov; optional
           width/height override the image size for that view, sheet=False keeps it off the contact sheet).
    """
    assets.ensure_assets()
    t0 = time.time()
    meta = dict(meta or {})
    if meta.get("ground") is None:
        meta["ground"] = guess_ground(blocks, size)
    vlist = view_list(blocks, size, meta, views)
    slug = _slug(meta)
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scenes: dict = {}
    for v in vlist:
        key = _scene_key(v)
        if key not in scenes:
            scenes[key] = _scene_for(blocks, size, meta, terrain, v)
    all_sprites = np.unique(np.concatenate([s.sprite for s in scenes.values()] + [np.zeros(1, np.int32)]))
    atlas = build_atlas(all_sprites)
    t_mesh = time.time() - t0
    jobs = []
    for v in vlist:
        path = out_dir / f"{slug}_{v['name']}.png"
        jobs.append((scenes[_scene_key(v)], atlas, v, str(path), meta, int(v.get("width", width)),
                     int(v.get("height", height)), supersample, shadows))
    results = []
    nworkers = workers if workers is not None else min(len(jobs), max(1, (os.cpu_count() or 2) // 2), 8)
    if nworkers <= 1 or len(jobs) == 1:
        for j in jobs:
            results.append(_worker(j))
    else:
        saved_env = {k: os.environ.get(k) for k in _THREAD_ENV}
        os.environ.update({k: "1" for k in _THREAD_ENV})
        try:
            with _no_main_reimport(), ProcessPoolExecutor(max_workers=nworkers) as ex:
                results = list(ex.map(_worker, jobs))
        finally:
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    paths = [p for p, _ in results]
    if verbose:
        print(f"meshing {t_mesh:.1f}s ({', '.join(f'{k}:{len(s)}q' for k, s in scenes.items())})")
        for (p, dt) in results:
            print(f"  {pathlib.Path(p).name}: {dt:.1f}s")
    on_sheet = [(p, v["name"]) for p, v in zip(paths, vlist) if v.get("sheet", True)]
    if sheet and len(on_sheet) > 1:
        sp = out_dir / f"{slug}_sheet.png"
        contact_sheet([p for p, _ in on_sheet], [n for _, n in on_sheet], sp, title=meta.get("title") or slug)
        paths.append(str(sp))
    if verbose:
        print(f"total {time.time() - t0:.1f}s")
    return paths


def render_view(blocks: dict, size, view: dict, out_path, meta: dict | None = None, terrain: bool = True,
                width: int = DEFAULT_W, height: int = DEFAULT_H, supersample: int = 2, shadows: bool = True) -> str:
    """Render a single view dict (see render_views) to out_path."""
    assets.ensure_assets()
    meta = dict(meta or {})
    if meta.get("ground") is None:
        meta["ground"] = guess_ground(blocks, size)
    if isinstance(view, str):
        view = view_list(blocks, size, meta, [view])[0]
    scene = _scene_for(blocks, size, meta, terrain, view)
    atlas = build_atlas(np.unique(np.r_[scene.sprite, 0]))
    return render_scene_view(scene, atlas, view, out_path, meta, width, height, supersample, shadows)


def _font(size):
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def contact_sheet(paths, labels, out_path, title=None, thumb_w=640, cols=None) -> str:
    ims = [Image.open(p).convert("RGB") for p in paths]
    n = len(ims)
    cols = cols or (3 if n <= 9 else 4)
    rows = math.ceil(n / cols)
    tw = thumb_w
    th = int(round(tw * ims[0].height / ims[0].width))
    lab_h = 30
    head = 44 if title else 0
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 8, head + rows * (th + lab_h) + (rows + 1) * 8), (34, 36, 40))
    d = ImageDraw.Draw(sheet)
    f = _font(20)
    if title:
        d.text((12, 10), str(title), fill=(235, 235, 235), font=_font(26))
    for i, (im, lab) in enumerate(zip(ims, labels)):
        r, c = divmod(i, cols)
        x = 8 + c * (tw + 8)
        y = head + 8 + r * (th + lab_h + 8)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y + lab_h))
        d.text((x + 4, y + 4), lab, fill=(240, 240, 240), font=f)
    out_path = pathlib.Path(out_path)
    sheet.save(out_path)
    return str(out_path)
