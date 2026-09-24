import pytest

from astro_core.grahas import RASIS
from vargas.shodashvarga import SHODASHVARGA, compute_vargas, varga_position

R = {name: i for i, name in enumerate(RASIS)}


def rasi(lon, n):
    return RASIS[varga_position(lon, n)[0]]


@pytest.mark.parametrize("lon, n, expected", [
    # D2 Hora
    (10, 2, "Simha"), (20, 2, "Karka"), (40, 2, "Karka"), (50, 2, "Simha"),
    # D3 Drekkana: 1st/5th/9th
    (5, 3, "Mesha"), (15, 3, "Simha"), (25, 3, "Dhanu"),
    # D4: kendras from the rasi
    (35, 4, "Vrishabha"), (45, 4, "Vrischika"), (55, 4, "Kumbha"),
    # D7: even rasi starts from 7th
    (1, 7, "Mesha"), (31, 7, "Vrischika"),
    # D9 Navamsa: element starts
    (1, 9, "Mesha"), (4, 9, "Vrishabha"), (30, 9, "Makara"), (60, 9, "Tula"),
    (90, 9, "Karka"), (119.9, 9, "Meena"), (359.9, 9, "Meena"),
    # D10: even rasi starts from 9th
    (1, 10, "Mesha"), (31, 10, "Makara"),
    # D12: from the rasi
    (29, 12, "Meena"), (31, 12, "Vrishabha"),
    # D16 / D20 / D45 by modality
    (30, 16, "Simha"), (60, 16, "Dhanu"),
    (30, 20, "Dhanu"), (60, 20, "Simha"),
    (30, 45, "Simha"), (60, 45, "Dhanu"),
    # D24: odd from Simha, even from Karka
    (0, 24, "Simha"), (30, 24, "Karka"),
    # D27: fiery Mesha, earthy Karka, airy Tula, watery Makara
    (0, 27, "Mesha"), (30, 27, "Karka"), (60, 27, "Tula"), (90, 27, "Makara"),
    # D40: odd from Mesha, even from Tula
    (0, 40, "Mesha"), (30, 40, "Tula"),
    # D60: from the rasi
    (0, 60, "Mesha"), (29.9, 60, "Meena"), (30.4, 60, "Vrishabha"), (30.6, 60, "Mithuna"),
])
def test_varga_rules(lon, n, expected):
    assert rasi(lon, n) == expected


@pytest.mark.parametrize("deg, odd_target, even_target", [
    (3, "Mesha", "Vrishabha"),
    (7, "Kumbha", "Kanya"),
    (11, "Dhanu", "Kanya"),
    (15, "Dhanu", "Meena"),
    (19, "Mithuna", "Meena"),
    (22, "Mithuna", "Makara"),
    (27, "Tula", "Vrischika"),
])
def test_trimsamsa(deg, odd_target, even_target):
    assert rasi(deg, 30) == odd_target            # Mesha (odd)
    assert rasi(30 + deg, 30) == even_target      # Vrishabha (even)


def test_trimsamsa_exact_boundary():
    assert rasi(5.0, 30) == "Kumbha"              # 5° starts Shani's portion
    assert rasi(35.0, 30) == "Kanya"              # even: 5° starts Budha's


def test_exact_part_boundary_goes_forward():
    assert rasi(10 / 3, 9) == "Vrishabha"         # exactly 3°20'


def test_each_varga_distributes_evenly_for_equal_parts():
    # Uniform coverage holds except Hora (Simha/Karka only), D30 (unequal) and
    # D40/D45 (40 or 45 parts
    # counted from fixed starts cannot cover 12 rasis evenly — inherent to the rule)
    for n in SHODASHVARGA:
        if n in (2, 30, 40, 45):
            continue
        counts = [0] * 12
        size = 30 / n
        for i in range(12 * n):
            counts[varga_position(i * size + size / 2, n)[0]] += 1
        assert len(set(counts)) == 1, f"D{n} uneven: {counts}"


def test_varga_longitude_navamsa():
    # 1°40' Mesha is mid-way through the 1st navamsa -> 15° Mesha in D9
    t, vlon = varga_position(1 + 40 / 60, 9)
    assert (t, vlon) == (0, pytest.approx(15.0))


def test_compute_vargas_shape():
    out = compute_vargas({"Surya": 118.37, "Lagna": 265.98})
    assert set(out["Surya"]) == {f"D{n}" for n in SHODASHVARGA}
    assert out["Lagna"]["D1"]["rasi"] == "Dhanu"
