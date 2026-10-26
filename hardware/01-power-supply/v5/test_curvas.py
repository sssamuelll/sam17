"""Pruebas de `v5/curvas.py`: series, no-extrapolacion y trazabilidad a PDF.

    python test_curvas.py
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(DIR, "..", "..", ".."))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

import curvas as cv  # noqa: E402


def test_archivos_fuente_existen() -> None:
    for diccionario in (cv.FUENTES_DERATING_V5, cv.FUENTES_PSRR_V5):
        for clave, (rel, pag, desc) in diccionario.items():
            ruta = os.path.join(RAIZ, rel)
            assert os.path.isfile(ruta), f"{clave}: no existe el PDF {ruta}"
            assert pag >= 1, f"{clave}: pagina invalida {pag}"
            assert desc.strip(), f"{clave}: descripcion vacia"


def test_sin_lm2941() -> None:
    assert "LM2941" not in cv.PSRR_DB_V5
    assert "LT1963A" in cv.PSRR_DB_V5
    assert "LT3015" in cv.PSRR_DB_V5
    assert "LT3045" in cv.PSRR_DB_V5
    assert "LT3094" in cv.PSRR_DB_V5


def test_derating_monotono_y_anclado() -> None:
    for nombre, pts in cv.DERATING_V5.items():
        for (_, y0), (_, y1) in zip(pts, pts[1:]):
            assert y1 <= y0 + 1e-12, f"{nombre}: el derating sube con la temperatura"
        assert abs(cv.derating(nombre, 25.0) - 1.0) < 1e-12

    # Puntos exactos de hoja a 65 C (convertidores) y 45 C (ladrillo):
    assert abs(cv.derating("URB2405YMD-20WR3", 65.0) - 1.00) < 1e-12
    assert abs(cv.derating("URB2405YMD-20WR3", 75.0) - 0.75) < 1e-12
    assert abs(cv.derating("THN-20-2411WI", 65.0) - 1.00) < 1e-12
    # Tramo 65,5 C (100 %) -> 79,9 C (50 %): a 72,7 C, punto medio, da 75 %.
    assert abs(cv.derating("THN-20-2411WI", 79.9) - 0.50) < 1e-12
    assert abs(cv.derating("THN-20-2411WI", 72.7) - 0.75) < 1e-12
    assert abs(cv.derating("TE90A2449F01", 45.0) * 90.0 - 82.5) < 1e-9


# Lecturas de las figuras de TRACO en conveccion natural, sin disipador
# (traco_thn30wi_characteristic_curves.pdf p. 11, traco_thn20wi_characteristic_curves.pdf
# p. 7): a cada temperatura, la banda que ocupa el trazo rojo, en fraccion de
# potencia de salida. Solo en el tramo que baja: junto al codo, la raya negra
# del 100 % tapa la roja.
LECTURAS_THN = {
    "THN-30-2422WI": ((55.0, 0.965, 0.985), (60.0, 0.851, 0.876), (62.6, 0.795, 0.811),
                      (65.0, 0.738, 0.754), (70.0, 0.624, 0.641), (75.0, 0.503, 0.527),
                      (80.0, 0.389, 0.418), (85.0, 0.276, 0.292), (90.0, 0.162, 0.182)),
    "THN-20-2413WI": ((65.0, 0.928, 0.957), (70.0, 0.786, 0.821), (75.0, 0.644, 0.669),
                      (80.0, 0.508, 0.531), (85.0, 0.354, 0.392), (90.0, 0.215, 0.246)),
}


def test_thn_dentro_del_trazo() -> None:
    """La curva de cada THN cae dentro del trazo de su figura, nunca por encima."""
    for nombre, lecturas in LECTURAS_THN.items():
        for t, lo, hi in lecturas:
            f = cv.derating(nombre, t)
            assert lo - 0.01 <= f <= hi, (
                f"{nombre} a {t:g} C da {f:.3f}; la figura pone el trazo en {lo:.3f}..{hi:.3f}")


def test_no_extrapola() -> None:
    for fn, arg, x in (
        (cv.derating, "URB2405YMD-20WR3", -50.0),
        (cv.derating, "URB2405YMD-20WR3", 90.0),
        (cv.psrr_db, "LT1963A", 5.0),
        (cv.psrr_db, "LT1963A", 2_000_000.0),
        (cv.psrr_db, "LT3045", 20_000_000.0),
    ):
        try:
            fn(arg, x)
        except ValueError as exc:
            assert "no extrapola" in str(exc)
        else:
            raise AssertionError(f"extrapolo {arg} en {x}")


def main() -> int:
    test_archivos_fuente_existen()
    test_sin_lm2941()
    test_derating_monotono_y_anclado()
    test_thn_dentro_del_trazo()
    test_no_extrapola()
    print("OK: test_curvas.py v5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
