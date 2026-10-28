"""Numpy software rasteriser for textured quads (orthographic and perspective).

Pipeline per view
  1. per quad: 3x3 homography G from (s,t,1) quad parameters to homogeneous pixel coords, inverted;
     back-face culling (quads are one-sided as in the game); screen bbox.
  2. opaque + cutout pass: quads bucketed by bbox size, pixel samples generated in chunks, inside test,
     alpha test (cutout), packed (depth, quad) int64 key, z-buffer via np.minimum.at.
  3. deferred shading of the visible quad per pixel: texel (nearest), tint, per-vertex light
     (AO x directional) interpolated bilinearly, optional sun-shadow lookup (PCF).
  4. translucent pass: samples in front of the opaque depth are sorted per pixel and composited
     back to front.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .models import LAYER_CUTOUT, LAYER_SOLID, LAYER_TRANSLUCENT, SPRITES

KEY_BITS = 23
KEY_MASK = (1 << KEY_BITS) - 1
NOKEY = np.iinfo(np.int64).max
CHUNK = 65_536
SHADE_CHUNK = 65_536


# ----------------------------------------------------------------------------------------------
# atlas


@dataclass
class Atlas:
    rgba: np.ndarray            # (H, W, 4) uint8
    rect: np.ndarray            # (n_sprites_total, 4) int32 x, y, w, h  (indexed by global sprite id)


def build_atlas(sprite_ids) -> Atlas:
    ids = sorted(set(int(i) for i in sprite_ids))
    imgs = {i: SPRITES.image(i) for i in ids}
    width = 1024
    while True:
        x = y = rowh = 0
        place = {}
        for i in sorted(ids, key=lambda k: (-imgs[k].shape[0], k)):
            h, w = imgs[i].shape[:2]
            if w > width:
                break
            if x + w > width:
                x, y, rowh = 0, y + rowh, 0
            place[i] = (x, y)
            x += w
            rowh = max(rowh, h)
        if len(place) == len(ids):
            break
        width *= 2
    height = max(1, y + rowh)
    atlas = np.zeros((height, width, 4), np.uint8)
    rect = np.zeros((max(len(SPRITES.names), max(ids, default=0) + 1), 4), np.int32)
    for i, (px, py) in place.items():
        im = imgs[i]
        h, w = im.shape[:2]
        atlas[py:py + h, px:px + w] = im
        rect[i] = (px, py, w, h)
    return Atlas(atlas, rect)


# ----------------------------------------------------------------------------------------------
# camera


@dataclass
class Camera:
    mode: str                 # "ortho" | "persp"
    W: int
    H: int
    right: np.ndarray
    up: np.ndarray
    fwd: np.ndarray
    center: np.ndarray        # ortho: point at image centre; persp: eye position
    scale: float              # ortho: pixels per block; persp: focal length in pixels
    near: float = 0.05

    def matrix(self) -> np.ndarray:
        """3x4 M: (a, b, w) = M @ (X, 1); pixel = (a/w, b/w)."""
        r, u, f, c = self.right, self.up, self.fwd, self.center
        if self.mode == "ortho":
            s = self.scale
            return np.array([
                [*(s * r), self.W / 2 - s * np.dot(r, c)],
                [*(-s * u), self.H / 2 + s * np.dot(u, c)],
                [0.0, 0.0, 0.0, 1.0]])
        fo = self.scale
        row0 = fo * r + (self.W / 2) * f
        row1 = -fo * u + (self.H / 2) * f
        return np.array([[*row0, -np.dot(row0, c)], [*row1, -np.dot(row1, c)], [*f, -np.dot(f, c)]])

    def depth_row(self) -> np.ndarray:
        return np.array([*self.fwd, -np.dot(self.fwd, self.center)])


def look_camera(mode, W, H, fwd, up_hint, center, scale) -> Camera:
    fwd = np.asarray(fwd, float)
    fwd = fwd / np.linalg.norm(fwd)
    right = np.cross(fwd, np.asarray(up_hint, float))
    if np.linalg.norm(right) < 1e-6:
        right = np.cross(fwd, np.array([0.0, 0.0, -1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return Camera(mode, int(W), int(H), right, up, fwd, np.asarray(center, float), float(scale))


# ----------------------------------------------------------------------------------------------
# quad setup


@dataclass
class Setup:
    idx: np.ndarray       # scene quad index for each set-up quad
    Ginv: np.ndarray      # (n,3,3) float64
    x0: np.ndarray
    y0: np.ndarray
    x1: np.ndarray
    y1: np.ndarray
    dep: np.ndarray       # (n,3) depth linear form in (s,t,1) for ortho
    tri: np.ndarray
    tex: np.ndarray       # (n,6) atlas coords: ax = t0 + s*t1 + t*t2 ; ay = t3 + s*t4 + t*t5
    rect: np.ndarray      # (n,4) sprite rect
    layer: np.ndarray
    bias: np.ndarray


def setup_quads(cam: Camera, pos, uv, sprite, tri, layer, atlas: Atlas, select=None, cull_back=True,
                bias=None) -> Setup:
    n_all = len(pos)
    idx = np.arange(n_all) if select is None else np.flatnonzero(select)
    P = pos[idx].astype(np.float64)
    P0 = P[:, 0]
    A = P[:, 1] - P0
    B = P[:, 3] - P0
    nrm = np.cross(A, B)
    M = cam.matrix()
    keep = np.linalg.norm(nrm, axis=1) > 1e-12
    if cull_back:
        if cam.mode == "ortho":
            keep &= (nrm @ cam.fwd) < 0
        else:
            keep &= np.einsum("ij,ij->i", nrm, P0 - cam.center) < 0
    # vertices to pixel space
    Ph = np.concatenate([P, np.ones(P.shape[:2] + (1,))], axis=2)        # (n,4,4)
    proj = Ph @ M.T                                                      # (n,4,3)
    w = proj[..., 2]
    if cam.mode == "persp":
        keep &= (w > cam.near).all(axis=1)
        w = np.where(w > cam.near, w, 1.0)
    px = proj[..., 0] / w
    py = proj[..., 1] / w
    if tri is not None:
        tsel = tri[idx]
        # triangles only use vertices 0, 1, 3
        px2 = px.copy()
        py2 = py.copy()
        px2[tsel, 2] = px[tsel, 0]
        py2[tsel, 2] = py[tsel, 0]
        px, py = px2, py2
    x0 = np.ceil(px.min(1) - 0.5)
    x1 = np.floor(px.max(1) - 0.5)
    y0 = np.ceil(py.min(1) - 0.5)
    y1 = np.floor(py.max(1) - 0.5)
    x0 = np.clip(x0, 0, cam.W - 1)
    y0 = np.clip(y0, 0, cam.H - 1)
    x1 = np.clip(x1, -1, cam.W - 1)
    y1 = np.clip(y1, -1, cam.H - 1)
    keep &= (x1 >= x0) & (y1 >= y0)
    keep &= (px.max(1) >= 0) & (px.min(1) <= cam.W) & (py.max(1) >= 0) & (py.min(1) <= cam.H)
    # homography
    G = np.empty((len(idx), 3, 3))
    G[:, :, 0] = A @ M[:, :3].T
    G[:, :, 1] = B @ M[:, :3].T
    G[:, :, 2] = P0 @ M[:, :3].T + M[:, 3]
    Ginv, det = inv3(G)
    keep &= np.abs(det) > 1e-9
    Ginv[~keep] = np.eye(3)
    dr = cam.depth_row()
    dep = np.stack([A @ dr[:3], B @ dr[:3], P0 @ dr[:3] + dr[3]], axis=1)
    # texture coefficients
    U = uv[idx].astype(np.float64)
    rect = atlas.rect[sprite[idx]].astype(np.float64)
    sw, sh = rect[:, 2], rect[:, 3]
    u0, v0 = U[:, 0, 0], U[:, 0, 1]
    du1, dv1 = U[:, 1, 0] - u0, U[:, 1, 1] - v0
    du3, dv3 = U[:, 3, 0] - u0, U[:, 3, 1] - v0
    tex = np.stack([rect[:, 0] + u0 * sw, du1 * sw, du3 * sw, rect[:, 1] + v0 * sh, dv1 * sh, dv3 * sh], axis=1)
    k = np.flatnonzero(keep)
    b = np.zeros(len(idx)) if bias is None else bias[idx].astype(np.float64)
    return Setup(idx[k], Ginv[k], x0[k].astype(np.int64), y0[k].astype(np.int64), x1[k].astype(np.int64),
                 y1[k].astype(np.int64), dep[k], (tri[idx][k] if tri is not None else np.zeros(len(k), bool)),
                 tex[k], rect[k].astype(np.int64), layer[idx][k], b[k])


def inv3(G):
    """Batched 3x3 inverse via cofactors (avoids LAPACK/BLAS threading). Returns (inv, det)."""
    a, b, c = G[:, 0, 0], G[:, 0, 1], G[:, 0, 2]
    d, e, f = G[:, 1, 0], G[:, 1, 1], G[:, 1, 2]
    g, h, i = G[:, 2, 0], G[:, 2, 1], G[:, 2, 2]
    A = e * i - f * h
    B = -(d * i - f * g)
    C = d * h - e * g
    det = a * A + b * B + c * C
    safe = np.where(np.abs(det) > 1e-300, det, 1.0)
    inv = np.empty_like(G)
    inv[:, 0, 0] = A / safe
    inv[:, 1, 0] = B / safe
    inv[:, 2, 0] = C / safe
    inv[:, 0, 1] = -(b * i - c * h) / safe
    inv[:, 1, 1] = (a * i - c * g) / safe
    inv[:, 2, 1] = -(a * h - b * g) / safe
    inv[:, 0, 2] = (b * f - c * e) / safe
    inv[:, 1, 2] = -(a * f - c * d) / safe
    inv[:, 2, 2] = (a * e - b * d) / safe
    return inv, det


_SIZES = np.array([1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024, 1536, 2048,
                   3072, 4096, 6144, 8192])


def iter_samples(cam: Camera, su: Setup, atlas_alpha: np.ndarray | None, alpha_test_mask: np.ndarray | None):
    """Yield (local quad index, pixel index, s, t, depth) arrays for all covered pixel samples.
    alpha_test_mask: bool per set-up quad -> drop samples with texel alpha < 128."""
    n = len(su.idx)
    if n == 0:
        return
    bw = (su.x1 - su.x0 + 1)
    bh = (su.y1 - su.y0 + 1)
    cw = _SIZES[np.searchsorted(_SIZES, bw)]
    ch = _SIZES[np.searchsorted(_SIZES, bh)]
    persp = cam.mode == "persp"
    W = cam.W
    eps = 1e-5
    keys = cw.astype(np.int64) * 100000 + ch
    order = np.argsort(keys, kind="stable")
    ks = keys[order]
    starts = np.flatnonzero(np.r_[True, ks[1:] != ks[:-1]])
    ends = np.r_[starts[1:], len(ks)]
    for st, en in zip(starts, ends):
        grp = order[st:en]
        gw, gh = int(cw[grp[0]]), int(ch[grp[0]])
        per = gw * gh
        step = max(1, CHUNK // per)
        lx = (np.arange(gw, dtype=np.float32) + 0.5)[None, None, :]
        ly = (np.arange(gh, dtype=np.float32) + 0.5)[None, :, None]
        ix = np.arange(gw, dtype=np.int64)[None, None, :]
        iy = np.arange(gh, dtype=np.int64)[None, :, None]
        for c0 in range(0, len(grp), step):
            q = grp[c0:c0 + step]
            Gi = su.Ginv[q]
            ox = su.x0[q].astype(np.float64)
            oy = su.y0[q].astype(np.float64)
            # rows of Ginv applied to (ox + lx, oy + ly, 1)
            cs = (Gi[:, 0, 0] * ox + Gi[:, 0, 1] * oy + Gi[:, 0, 2]).astype(np.float32)[:, None, None]
            ct = (Gi[:, 1, 0] * ox + Gi[:, 1, 1] * oy + Gi[:, 1, 2]).astype(np.float32)[:, None, None]
            s = Gi[:, 0, 0].astype(np.float32)[:, None, None] * lx + Gi[:, 0, 1].astype(np.float32)[:, None, None] * ly + cs
            t = Gi[:, 1, 0].astype(np.float32)[:, None, None] * lx + Gi[:, 1, 1].astype(np.float32)[:, None, None] * ly + ct
            if persp:
                cw_ = (Gi[:, 2, 0] * ox + Gi[:, 2, 1] * oy + Gi[:, 2, 2]).astype(np.float32)[:, None, None]
                wq = Gi[:, 2, 0].astype(np.float32)[:, None, None] * lx + Gi[:, 2, 1].astype(np.float32)[:, None, None] * ly + cw_
                inv = 1.0 / wq
                s = s * inv
                t = t * inv
            m = (s >= -eps) & (s <= 1 + eps) & (t >= -eps) & (t <= 1 + eps)
            m &= (ix <= (su.x1[q] - su.x0[q])[:, None, None]) & (iy <= (su.y1[q] - su.y0[q])[:, None, None])
            trq = su.tri[q]
            if trq.any():
                m &= ~(trq[:, None, None] & (s + t > 1 + eps))
            if persp:
                m &= wq > 0
            flat = np.flatnonzero(m)
            if not len(flat):
                continue
            ql = flat // per
            rem = flat - ql * per
            yy = rem // gw
            xx = rem - yy * gw
            ss = s.ravel()[flat]
            tt = t.ravel()[flat]
            qi = q[ql]
            pix = (su.y0[qi] + yy) * W + (su.x0[qi] + xx)
            if persp:
                depth = (1.0 / wq.ravel()[flat]).astype(np.float32)
            else:
                d = su.dep[qi]
                depth = (d[:, 0] * ss + d[:, 1] * tt + d[:, 2]).astype(np.float32)
            depth = depth - su.bias[qi].astype(np.float32)
            if alpha_test_mask is not None and atlas_alpha is not None:
                at = alpha_test_mask[qi]
                if at.any():
                    sel = np.flatnonzero(at)
                    a = sample_alpha(atlas_alpha, su, qi[sel], ss[sel], tt[sel])
                    ok = np.ones(len(qi), bool)
                    ok[sel] = a >= 128
                    if not ok.all():
                        qi, pix, ss, tt, depth = qi[ok], pix[ok], ss[ok], tt[ok], depth[ok]
            yield qi, pix, ss, tt, depth


def texel_xy(su: Setup, qi, s, t):
    tx = su.tex[qi]
    r = su.rect[qi]
    ax = np.floor(tx[:, 0] + s * tx[:, 1] + t * tx[:, 2]).astype(np.int64)
    ay = np.floor(tx[:, 3] + s * tx[:, 4] + t * tx[:, 5]).astype(np.int64)
    ax = np.clip(ax, r[:, 0], r[:, 0] + r[:, 2] - 1)
    ay = np.clip(ay, r[:, 1], r[:, 1] + r[:, 3] - 1)
    return ax, ay


def sample_alpha(alpha, su, qi, s, t):
    ax, ay = texel_xy(su, qi, s, t)
    return alpha[ay, ax]


def interp4(vals, s, t, tri):
    """Bilinear (quads) / barycentric (triangles) interpolation of per-vertex values (n,4)."""
    v0, v1, v2, v3 = vals[:, 0], vals[:, 1], vals[:, 2], vals[:, 3]
    if vals.ndim == 3:                       # (n,4,C) per-vertex vectors (RGB light)
        s, t = s[:, None], t[:, None]
        tri = None if tri is None else tri[:, None]
    bil = (1 - s) * (1 - t) * v0 + s * (1 - t) * v1 + s * t * v2 + (1 - s) * t * v3
    if tri is not None and tri.any():
        bar = (1 - s - t) * v0 + s * v1 + t * v3
        return np.where(tri, bar, bil)
    return bil


# ----------------------------------------------------------------------------------------------
# shadow map


@dataclass
class ShadowMap:
    cam: Camera
    depth: np.ndarray       # (H, W) float32, +inf = empty
    texel: float            # world units per shadow texel


def build_shadow_map(scene, atlas: Atlas, sun_dir, res=2048) -> ShadowMap:
    """sun_dir: unit vector pointing from the scene towards the sun."""
    L = np.asarray(sun_dir, float)
    L /= np.linalg.norm(L)
    fwd = -L
    pts = scene.pos.reshape(-1, 3)
    up_hint = np.array([0.0, 1.0, 0.0]) if abs(fwd[1]) < 0.99 else np.array([0.0, 0.0, -1.0])
    tmp = look_camera("ortho", 2, 2, fwd, up_hint, pts.mean(0), 1.0)
    pr = pts @ tmp.right
    pu = pts @ tmp.up
    ext = max(pr.max() - pr.min(), pu.max() - pu.min()) + 2.0
    scale = res / ext
    center = pts.mean(0) + tmp.right * ((pr.max() + pr.min()) / 2 - pts.mean(0) @ tmp.right) + \
        tmp.up * ((pu.max() + pu.min()) / 2 - pts.mean(0) @ tmp.up)
    cam = look_camera("ortho", res, res, fwd, up_hint, center, scale)
    sel = scene.layer != LAYER_TRANSLUCENT
    su = setup_quads(cam, scene.pos, scene.uv, scene.sprite, scene.tri, scene.layer, atlas, select=sel,
                     cull_back=True)
    depth = np.full(res * res, np.inf, np.float32)
    amask = su.layer == LAYER_CUTOUT
    for qi, pix, s, t, d in iter_samples(cam, su, atlas.rgba[..., 3], amask):
        np.minimum.at(depth, pix, d)
    return ShadowMap(cam, depth.reshape(res, res), 1.0 / scale)


def shadow_lookup(sm: ShadowMap, X: np.ndarray, normal: np.ndarray, sun_dir: np.ndarray) -> np.ndarray:
    """Fraction lit in [0,1] for world points X (n,3) with unit normals (n,3)."""
    L = sun_dir / np.linalg.norm(sun_dir)
    ndl = normal @ L
    Xo = X + normal * (sm.texel * 1.5) + L * (sm.texel * 0.5)
    cam = sm.cam
    M = cam.matrix()
    px = Xo @ M[0, :3] + M[0, 3]
    py = Xo @ M[1, :3] + M[1, 3]
    dz = Xo @ cam.fwd - np.dot(cam.fwd, cam.center)
    H, W = sm.depth.shape
    lit = np.zeros(len(X), np.float32)
    bias = sm.texel * 1.0
    dzb = (dz - bias).astype(np.float32)
    ix0 = np.floor(px).astype(np.int64)
    iy0 = np.floor(py).astype(np.int64)
    flat = sm.depth.ravel()
    for oy in (-1, 0, 1):
        rows = np.clip(iy0 + oy, 0, H - 1) * W
        for ox in (-1, 0, 1):
            lit += dzb <= flat[rows + np.clip(ix0 + ox, 0, W - 1)]
    lit /= 9.0
    lit = np.where(ndl > 0.0, lit, 0.0)
    return lit


# ----------------------------------------------------------------------------------------------
# main render


def render(scene, atlas: Atlas, cam: Camera, background: np.ndarray, sun_dir=None, shadow: ShadowMap | None = None,
           shadow_strength=0.35) -> np.ndarray:
    """Render a scene into float RGB image (H, W, 3) in 0..1 over `background`."""
    W, H = cam.W, cam.H
    alpha = atlas.rgba[..., 3]
    bias = getattr(scene, "bias", None)
    # ---------------- opaque + cutout
    sel = scene.layer != LAYER_TRANSLUCENT
    su = setup_quads(cam, scene.pos, scene.uv, scene.sprite, scene.tri, scene.layer, atlas, select=sel, bias=bias)
    nq = len(su.idx)
    zkey = np.full(W * H, NOKEY, np.int64)
    if nq:
        dmin, dmax = _depth_range(cam, scene)
        dscale = (2 ** 38) / max(dmax - dmin, 1e-6)
        amask = su.layer == LAYER_CUTOUT
        rid = (KEY_MASK - np.arange(nq)).astype(np.int64)     # later quads win ties
        for qi, pix, s, t, d in iter_samples(cam, su, alpha, amask):
            dq = np.clip((d.astype(np.float64) - dmin) * dscale, 0, 2 ** 39).astype(np.int64)
            np.minimum.at(zkey, pix, (dq << KEY_BITS) | rid[qi])
    img = background.reshape(-1, 3).astype(np.float32).copy()
    covered = np.flatnonzero(zkey != NOKEY)
    depth_px = np.full(W * H, np.inf, np.float64)
    if len(covered):
        for c0 in range(0, len(covered), SHADE_CHUNK):
            pix = covered[c0:c0 + SHADE_CHUNK]
            k = zkey[pix]
            qi = KEY_MASK - (k & KEY_MASK)
            depth_px[pix] = (k >> KEY_BITS).astype(np.float64) / dscale + dmin
            img[pix] = _shade(scene, su, atlas, cam, qi, pix, W, sun_dir, shadow, shadow_strength)
    # ---------------- translucent
    tsel = scene.layer == LAYER_TRANSLUCENT
    if tsel.any():
        tu = setup_quads(cam, scene.pos, scene.uv, scene.sprite, scene.tri, scene.layer, atlas, select=tsel,
                         bias=bias)
        P, D, C, Aa = [], [], [], []
        for qi, pix, s, t, d in iter_samples(cam, tu, None, None):
            front = d.astype(np.float64) < depth_px[pix] - 1e-4
            if not front.any():
                continue
            qi, pix, s, t, d = qi[front], pix[front], s[front], t[front], d[front]
            ax, ay = texel_xy(tu, qi, s, t)
            texel = atlas.rgba[ay, ax].astype(np.float32) / 255.0
            a = texel[:, 3]
            ok = a > 0.004
            if not ok.any():
                continue
            qi, pix, s, t, d, texel, a = qi[ok], pix[ok], s[ok], t[ok], d[ok], texel[ok], a[ok]
            col = _light_color(scene, tu, cam, qi, pix, s, t, texel[:, :3], W, sun_dir, shadow, shadow_strength)
            P.append(pix)
            D.append(d)
            C.append(col)
            Aa.append(a)
        if P:
            pix = np.concatenate(P)
            d = np.concatenate(D)
            col = np.concatenate(C)
            a = np.concatenate(Aa)
            order = np.lexsort((-d, pix))
            pix, col, a = pix[order], col[order], a[order]
            start = np.r_[0, np.flatnonzero(pix[1:] != pix[:-1]) + 1]
            grp_start = np.repeat(start, np.diff(np.r_[start, len(pix)]))
            rank = np.arange(len(pix)) - grp_start
            for r in range(int(rank.max()) + 1):
                m = rank == r
                pp = pix[m]
                aa = a[m][:, None]
                img[pp] = img[pp] * (1 - aa) + col[m] * aa
    return img.reshape(H, W, 3)


def _depth_range(cam, scene):
    pts = scene.pos.reshape(-1, 3).astype(np.float64)
    d = pts @ cam.fwd - np.dot(cam.fwd, cam.center)
    lo, hi = float(d.min()) - 2.0, float(d.max()) + 2.0
    if cam.mode == "persp":
        lo = max(lo, cam.near)
    return lo, hi


def _st_for_pixels(su: Setup, local_q, pix, W):
    px = (pix % W).astype(np.float64) + 0.5
    py = (pix // W).astype(np.float64) + 0.5
    G = su.Ginv[local_q]
    hs = G[:, 0, 0] * px + G[:, 0, 1] * py + G[:, 0, 2]
    ht = G[:, 1, 0] * px + G[:, 1, 1] * py + G[:, 1, 2]
    hw = G[:, 2, 0] * px + G[:, 2, 1] * py + G[:, 2, 2]
    s = np.clip(hs / hw, 0.0, 1.0)
    t = np.clip(ht / hw, 0.0, 1.0)
    return s, t


def _shade(scene, su, atlas, cam, local_q, pix, W, sun_dir, shadow, strength):
    s, t = _st_for_pixels(su, local_q, pix, W)
    ax, ay = texel_xy(su, local_q, s, t)
    texel = atlas.rgba[ay, ax, :3].astype(np.float32) / 255.0
    return _light_color(scene, su, cam, local_q, pix, s, t, texel, W, sun_dir, shadow, strength)


def _quad_normals(scene) -> np.ndarray:
    """Unit normals (N,3) float32 of the scene quads (cached on the scene object)."""
    qn = getattr(scene, "_qn", None)
    if qn is None or len(qn) != len(scene.pos):
        P = scene.pos.astype(np.float64)
        n = np.cross(P[:, 1] - P[:, 0], P[:, 3] - P[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        qn = n.astype(np.float32)
        try:
            scene._qn = qn
        except AttributeError:
            pass
    return qn


def _light_color(scene, su, cam, local_q, pix, s, t, texel, W, sun_dir, shadow, strength):
    gi = su.idx[local_q]
    tri = scene.tri[gi]
    s = s.astype(np.float32, copy=False)
    t = t.astype(np.float32, copy=False)
    light = interp4(scene.light[gi], s, t, tri)
    if light.ndim == 1:
        light = light[:, None]
    col = texel * scene.rgb[gi] * light
    if shadow is not None and sun_dir is not None:
        P = scene.pos[gi]
        P0 = P[:, 0]
        X = P0 + s[:, None] * (P[:, 1] - P0) + t[:, None] * (P[:, 3] - P0)
        n = _quad_normals(scene)[gi]
        lit = shadow_lookup(shadow, X, n, np.asarray(sun_dir, float))
        f = 1.0 - strength * (1.0 - lit)
        col = col * f[:, None].astype(np.float32)
    return col
