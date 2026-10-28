"""Deterministic noise for natural material variation (never ``random``).

* ``hash3(x, y, z, seed)`` -> 32-bit unsigned int; ``hash01`` -> float in [0, 1).  Per-block "white" noise:
  use it for sparse sprinkles (``chance``), never for large-scale transitions.
* ``value2(x, z, seed, scale)`` / ``value3(x, y, z, seed, scale)`` -> smooth value noise in [0, 1]
  (lattice values from ``hash3``, smoothstep interpolation).  ``fbm2`` / ``fbm3`` add octaves.
* ``gradient(choices_by_height, x, y, z, seed, jitter)`` -> the material for this block of a vertical
  transition whose band boundaries wobble smoothly (mossy at the base fading upward).

Everything is pure integer/float math -> identical results on every run and platform.
"""
from __future__ import annotations

import math

_M32 = 0xFFFFFFFF


def _mix(h: int) -> int:
    # lowbias32 (Chris Wellons) -- good avalanche, cheap
    h &= _M32
    h ^= h >> 16
    h = (h * 0x7FEB352D) & _M32
    h ^= h >> 15
    h = (h * 0x846CA68B) & _M32
    h ^= h >> 16
    return h


def hash3(x: int, y: int, z: int, seed: int = 0) -> int:
    """Deterministic 32-bit hash of integer coordinates and a seed."""
    h = _mix((seed * 0x9E3779B1) ^ 0x85EBCA6B)
    h = _mix(h ^ ((int(x) * 0x27D4EB2F) & _M32))
    h = _mix(h ^ ((int(y) * 0x165667B1) & _M32))
    h = _mix(h ^ ((int(z) * 0x61C88647) & _M32))
    return h


def hash01(x: int, y: int, z: int, seed: int = 0) -> float:
    """Per-block uniform value in [0, 1)."""
    return hash3(x, y, z, seed) / 4294967296.0


def chance(p: float, x: int, y: int, z: int, seed: int = 0) -> bool:
    """True with probability ``p`` for this block (deterministic)."""
    return hash01(x, y, z, seed) < p


def pick(choices, x: int, y: int, z: int, seed: int = 0, weights=None):
    """Deterministic weighted choice for this block."""
    choices = list(choices)
    if not choices:
        raise ValueError("pick() needs at least one choice")
    if weights is None:
        weights = [1.0] * len(choices)
    total = float(sum(weights))
    r = hash01(x, y, z, seed) * total
    acc = 0.0
    for c, w in zip(choices, weights):
        acc += w
        if r < acc:
            return c
    return choices[-1]


def _smooth(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def _lerp(a, b, t):
    return a + (b - a) * t


def value2(x: float, z: float, seed: int = 0, scale: float = 4.0) -> float:
    """2D value noise in [0, 1]; ``scale`` = blocks per lattice cell (bigger = smoother)."""
    fx, fz = x / scale, z / scale
    x0, z0 = math.floor(fx), math.floor(fz)
    tx, tz = _smooth(fx - x0), _smooth(fz - z0)
    v00 = hash01(x0, 0, z0, seed)
    v10 = hash01(x0 + 1, 0, z0, seed)
    v01 = hash01(x0, 0, z0 + 1, seed)
    v11 = hash01(x0 + 1, 0, z0 + 1, seed)
    return _lerp(_lerp(v00, v10, tx), _lerp(v01, v11, tx), tz)


def value3(x: float, y: float, z: float, seed: int = 0, scale: float = 4.0) -> float:
    """3D value noise in [0, 1]."""
    fx, fy, fz = x / scale, y / scale, z / scale
    x0, y0, z0 = math.floor(fx), math.floor(fy), math.floor(fz)
    tx, ty, tz = _smooth(fx - x0), _smooth(fy - y0), _smooth(fz - z0)

    def h(i, j, k):
        return hash01(x0 + i, y0 + j, z0 + k, seed)

    c00 = _lerp(h(0, 0, 0), h(1, 0, 0), tx)
    c10 = _lerp(h(0, 1, 0), h(1, 1, 0), tx)
    c01 = _lerp(h(0, 0, 1), h(1, 0, 1), tx)
    c11 = _lerp(h(0, 1, 1), h(1, 1, 1), tx)
    return _lerp(_lerp(c00, c10, ty), _lerp(c01, c11, ty), tz)


def fbm2(x, z, seed=0, scale=8.0, octaves=3, gain=0.5) -> float:
    """Fractal 2D value noise in [0, 1]."""
    amp, tot, norm, s = 1.0, 0.0, 0.0, scale
    for o in range(octaves):
        tot += amp * value2(x, z, seed + 1013 * o, s)
        norm += amp
        amp *= gain
        s /= 2.0
    return tot / norm


def fbm3(x, y, z, seed=0, scale=8.0, octaves=3, gain=0.5) -> float:
    """Fractal 3D value noise in [0, 1]."""
    amp, tot, norm, s = 1.0, 0.0, 0.0, scale
    for o in range(octaves):
        tot += amp * value3(x, y, z, seed + 1013 * o, s)
        norm += amp
        amp *= gain
        s /= 2.0
    return tot / norm


def gradient(choices_by_height, x: int, y: int, z: int, seed: int = 0, jitter: float = 1.5, scale: float = 3.0):
    """Pick a material for a vertical transition with smoothly wobbling band edges.

    ``choices_by_height``: list of ``(y_start, choice)`` in ascending ``y_start`` -- the choice applies from
    ``y_start`` upward until the next band.  The block's height is offset by smooth 3D noise in
    ``[-jitter, +jitter]`` before the lookup, so boundaries meander instead of being flat lines, and
    neighbouring blocks agree (no salt-and-pepper).  Heights below the first band use the first choice.

        gradient([(0, "mossy_cobblestone"), (2, "cobblestone"), (5, "stone_bricks")], x, y, z, seed=7)
    """
    bands = sorted(choices_by_height, key=lambda t: t[0])
    if not bands:
        raise ValueError("gradient() needs at least one (y_start, choice) band")
    off = (fbm3(x, y, z, seed, scale=scale, octaves=2) - 0.5) * 2.0 * jitter
    h = y + off
    choice = bands[0][1]
    for y0, c in bands:
        if h >= y0:
            choice = c
        else:
            break
    return choice
