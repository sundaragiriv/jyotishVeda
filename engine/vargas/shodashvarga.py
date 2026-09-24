"""
Shodashvarga — the sixteen divisional charts of Brihat Parashara Hora Shastra
(BPHS, Shodashavarga-vivechana adhyaya).

Notation: r = rasi index 0-11 (0 = Mesha), d = degrees within the rasi.
Odd rasis (Mesha, Mithuna, ...) have even r. Chara (movable) = r % 3 == 0,
Sthira (fixed) = r % 3 == 1, Dvisvabhava (dual) = r % 3 == 2.

Varga   Parts  Rule (target rasi)
D1      1      the rasi itself
D2      2      Hora: odd rasi 0-15 Simha, 15-30 Karka; even rasi reversed
D3      3      Drekkana: 1st, 5th, 9th from the rasi
D4      4      Chaturthamsa: 1st, 4th, 7th, 10th from the rasi
D7      7      Saptamsa: odd from the rasi, even from the 7th
D9      9      Navamsa: fiery from Mesha, earthy from Makara, airy from Tula,
               watery from Karka (= continuous count from 0° Mesha)
D10     10     Dasamsa: odd from the rasi, even from the 9th
D12     12     Dwadasamsa: from the rasi
D16     16     Shodasamsa: movable from Mesha, fixed from Simha, dual from Dhanu
D20     20     Vimsamsa: movable from Mesha, fixed from Dhanu, dual from Simha
D24     24     Chaturvimsamsa: odd from Simha, even from Karka
D27     27     Bhamsa: fiery from Mesha, earthy Karka, airy Tula, watery Makara
               (= continuous count from 0° Mesha)
D30     5      Trimsamsa (unequal): odd 5 Mangala, 5 Shani, 8 Guru, 7 Budha,
               5 Shukra -> Mesha, Kumbha, Dhanu, Mithuna, Tula;
               even reversed: 5 Shukra, 7 Budha, 8 Guru, 5 Shani, 5 Mangala
               -> Vrishabha, Kanya, Meena, Makara, Vrischika
D40     40     Khavedamsa: odd from Mesha, even from Tula
D45     45     Akshavedamsa: movable from Mesha, fixed from Simha, dual from Dhanu
D60     60     Shashtyamsa: from the rasi itself

Each result also carries a varga longitude: the position is scaled
proportionally within its division onto the 30° of the target rasi.
"""

from __future__ import annotations

from astro_core.grahas import RASIS

SHODASHVARGA = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

VARGA_NAMES = {
    1: "Rasi", 2: "Hora", 3: "Drekkana", 4: "Chaturthamsa", 7: "Saptamsa",
    9: "Navamsa", 10: "Dasamsa", 12: "Dwadasamsa", 16: "Shodasamsa",
    20: "Vimsamsa", 24: "Chaturvimsamsa", 27: "Bhamsa", 30: "Trimsamsa",
    40: "Khavedamsa", 45: "Akshavedamsa", 60: "Shashtyamsa",
}

_EPS = 1e-9

# D30 segments: (end degree, target rasi index)
_D30_ODD = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]
_D30_EVEN = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]

# start offsets by modality (movable, fixed, dual), absolute rasi indices
_BY_MODALITY = {16: (0, 4, 8), 20: (0, 8, 4), 45: (0, 4, 8)}
# start offsets by parity (odd, even); "rel" means relative to the rasi itself
_BY_PARITY = {7: ("rel", 0, 6), 10: ("rel", 0, 8), 24: ("abs", 4, 3), 40: ("abs", 0, 6)}


def _part(d: float, n: int) -> tuple[int, float]:
    """Index of the equal division containing d, and fraction through it."""
    size = 30.0 / n
    p = min(int((d + _EPS) // size), n - 1)
    frac = min(max((d - p * size) / size, 0.0), 1.0)
    return p, frac


def varga_position(longitude: float, n: int) -> tuple[int, float]:
    """Return (target rasi index 0-11, varga longitude 0-360) for varga Dn."""
    lon = longitude % 360.0
    if lon >= 360.0 - _EPS:                   # same wrap rule as classify()
        lon = 0.0
    r = min(int((lon + _EPS) // 30), 11)
    d = max(lon - r * 30, 0.0)
    odd = r % 2 == 0

    if n == 1:
        return r, lon

    if n == 30:
        prev = 0.0
        for end, target in (_D30_ODD if odd else _D30_EVEN):
            if d < end - _EPS or end == 30:
                frac = (d - prev) / (end - prev)
                return target, target * 30 + frac * 30
            prev = end

    p, frac = _part(d, n)

    if n == 2:
        first, second = (4, 3) if odd else (3, 4)
        t = first if p == 0 else second
    elif n == 3:
        t = r + (0, 4, 8)[p]
    elif n == 4:
        t = r + 3 * p
    elif n in (9, 27):
        t = min(int((lon + _EPS) // (30.0 / n)), 12 * n - 1)   # continuous count
    elif n in (12, 60):
        t = r + p
    elif n in _BY_MODALITY:
        t = _BY_MODALITY[n][r % 3] + p
    elif n in _BY_PARITY:
        mode, o, e = _BY_PARITY[n]
        base = (r if mode == "rel" else 0) + (o if odd else e)
        t = base + p
    else:
        raise ValueError(f"D{n} is not a Shodashvarga division")

    t %= 12
    return t, t * 30 + frac * 30


def compute_vargas(longitudes: dict[str, float], vargas: list[int] | None = None) -> dict:
    """
    longitudes: {"Surya": 118.37, ..., "Lagna": 174.7}
    Returns {body: {"D9": {"rasi_index": 1-12, "rasi": ..., "longitude": ...}}}
    """
    vargas = vargas or SHODASHVARGA
    out: dict[str, dict] = {}
    for body, lon in longitudes.items():
        row = {}
        for n in vargas:
            t, vlon = varga_position(lon, n)
            row[f"D{n}"] = {"rasi_index": t + 1, "rasi": RASIS[t],
                            "longitude": round(vlon % 360, 6)}
        out[body] = row
    return out
