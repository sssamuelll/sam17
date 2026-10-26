"""La carga de cada convertidor contra su derating, al aire del cajon (#478).

    python hardware/01-power-supply/v5/derating_budget.py

Cruza tres cosas que viven en sitios distintos y que nadie cruzaba:

  * la carga de cada riel, de `ladrillo_budget.rieles()`;
  * la curva de derating de cada convertidor, de `curvas.derating()` (cada
    curva cita su figura de hoja);
  * el aire del cajon: la sala de diseno del case (`T_SALA_DISENO_K`, 45 C) mas
    el salto de su chimenea con el C_D pesimista, escalado a esa sala, como lo
    escala `case/clearance_budget.guarda_aire()`. El salto sale de
    `potencia_disipada` en `params.scad`, que clearance_budget cruza con
    `ladrillo_budget.calor_del_cajon_w()`.

La carga de un convertidor es la potencia de todas sus salidas juntas contra su
nominal, que es el eje de las figuras de derating ("OUTPUT POWER (%)" en las
notas de TRACO). Es la lectura de la junta de piezas v5 (sec. 4.7) para `PS1`,
cuyas dos salidas van desiguales. Pasa si esa fraccion cabe bajo la curva a la
temperatura del aire. Aparte, y sin derating, ninguna salida pasa de la
corriente nominal de su hoja: la curva no autoriza a cargar una salida mas alla.

Nominales (todas en la p. 1 de su hoja, `docs/reference/datasheets/`):
  PS1 THN 30-2422WI   +-12 V, +-1250 mA, 30 W    traco_thn30wi.pdf
  PS2 URB2405YMD-20WR3   5 V,  4000 mA, 20 W     mornsun_urb_ymd20wr3.pdf
  PS3 THN 20-2411WI      5 V,  4000 mA, 20 W     traco_thn20wi.pdf
  PS4, PS5 THN 20-2413WI 15 V, 1330 mA, 20 W     traco_thn20wi.pdf

LO QUE ESTE CALCULO NO CUBRE (se imprime al final):
  * El aire junto a cada convertidor puede ir por encima del salto medio de la
    chimenea, que es una media de la columna de aire.
  * Las curvas son las de la hoja sin disipador ni flujo forzado; el cajon
    tiene tiro natural, que es la condicion de la hoja.
  * Las de los THN son lecturas de figura, tipicas. Y la del THN 30-2422WI no
    dice si vale por potencia total con las salidas desiguales: esa lectura
    espera la confirmacion escrita de TRACO, y mientras tanto la carcasa de
    `PS1` se mide (`medidas.csv`, paso 7, criterio 100 C).
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(DIR, "..", "..", "..", "case")
TOOLS = os.path.join(DIR, "..", "..", "tools")
for _d in (DIR, CASE, TOOLS):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import clearance_budget as cb       # noqa: E402
import ladrillo_budget as lb        # noqa: E402
from canario import borde_rojo      # noqa: E402
from curvas import DERATING_V5, derating  # noqa: E402

#   ref: (curva de curvas.py, A nominales por salida, W nominales, rieles de rieles())
CONVERTIDORES = {
    "PS1": ("THN-30-2422WI", 1.25, 30.0,
            ("+12 rack (bus fila B + pantalla)", "-12 rack (bus fila B)")),
    "PS2": ("URB2405YMD-20WR3", 4.0, 20.0, ("+5 digital (4 x N657 + host USB)",)),
    "PS3": ("THN-20-2411WI", 4.0, 20.0, ("+5 rack (bus fila B + +5V_AUX)",)),
    "PS4": ("THN-20-2413WI", 1.33, 20.0, ("crudo +cascada (a U1)",)),
    "PS5": ("THN-20-2413WI", 1.33, 20.0, ("crudo -cascada (a U2)",)),
}


def aire_cajon_c() -> float:
    """La sala de diseno del case mas el salto pesimista de su chimenea."""
    p = cb.leer_params()
    f_sala = cb.T_SALA_DISENO_K / cb.T_AMB
    return cb.T_SALA_DISENO_K - 273.15 + cb._tiro_pesimista(p)["dt"] * f_sala


def _salidas(ref: str) -> list[dict]:
    nombres = CONVERTIDORES[ref][3]
    rieles = {r["nombre"]: r for r in lb.rieles()}
    assert all(n in rieles for n in nombres), (
        f"{ref}: rieles() ya no tiene {[n for n in nombres if n not in rieles]}")
    return [rieles[n] for n in nombres]


def carga(ref: str, x_carga: float = 1.0) -> float:
    """La fraccion de potencia nominal que piden todas las salidas de `ref` juntas."""
    p_nom = CONVERTIDORES[ref][2]
    return sum(abs(r["v"]) * r["a"] for r in _salidas(ref)) * x_carga / p_nom


def corriente(ref: str, x_carga: float = 1.0) -> float:
    """La mayor fraccion de corriente nominal entre las salidas de `ref`."""
    i_nom = CONVERTIDORES[ref][1]
    return max(r["a"] for r in _salidas(ref)) * x_carga / i_nom


def _guarda(p: dict[str, float], solo: str | None = None) -> None:
    for ref, (curva, *_resto) in CONVERTIDORES.items():
        if solo and ref != solo:
            continue
        f = carga(ref, p["x_carga"])
        tope = derating(curva, p["t_aire_c"])
        assert f <= tope, (
            f"{ref} ({curva}) pide el {f:.0%} de su potencia nominal y a "
            f"{p['t_aire_c']:.1f} C su derating deja el {tope:.0%}: se sale de su derating")


def _guarda_corriente(p: dict[str, float]) -> None:
    for ref, (curva, *_resto) in CONVERTIDORES.items():
        f = corriente(ref, p["x_carga"])
        assert f <= 1.0, (
            f"{ref} ({curva}) pide el {f:.0%} de su corriente nominal en una salida: "
            "pasa de su corriente nominal")


def _fin(ref: str) -> float:
    """El final de la curva de `ref`: mas alla curvas.derating() no extrapola."""
    return DERATING_V5[CONVERTIDORES[ref][0]][-1][0]


def _guarda_de(ref: str):
    def guarda(p: dict[str, float]) -> None:
        _guarda(p, solo=ref)
    guarda.__name__ = f"_guarda_{ref}"
    return guarda


def _autocomprobacion() -> None:
    # A mano, PS3: 0,80 A a 5 V son 4 W, el 20 % de sus 20 W. La curva del
    # THN 20-2411WI baja del 50 % en 79,9 C al 10 % en 91,5 C
    # (traco_thn20wi_characteristic_curves.pdf p. 3, curvas.py): el 20 % llega
    # en 79,9 + (0,50 - 0,20) / 0,40 * 11,6 = 88,6 C.
    assert abs(carga("PS3") - 0.20) < 1e-9, f"PS3 pide {carga('PS3'):.3f}, no 0,20"
    borde = borde_rojo(_guarda_de("PS3"), {"t_aire_c": 20.0, "x_carga": 1.0},
                       "t_aire_c", 20.0, _fin("PS3"), "se sale de su derating")
    assert abs(borde - 88.6) < 0.2, f"el borde de PS3 sale en {borde:.2f} C, no 88,6"
    # A mano, PS1: +12 V a 1,05 A y -12 V a 0,50 A son 18,6 W, el 62 % de sus
    # 30 W, aunque el +12 V lleve el 84 % de su corriente. La curva del THN 30
    # baja del 100 % en 54 C al 50 % en 75,5 C (curvas.py): el 62 % llega en
    # 54 + (1 - 0,62) / 0,5 * 21,5 = 70,34 C. Con la mayor fraccion, el 84 %,
    # llegaria en 60,9 C.
    assert abs(carga("PS1") - 0.62) < 1e-9, f"PS1 pide {carga('PS1'):.3f}, no 0,62"
    assert abs(corriente("PS1") - 0.84) < 1e-9, f"PS1 pide {corriente('PS1'):.3f}, no 0,84"
    borde = borde_rojo(_guarda_de("PS1"), {"t_aire_c": 20.0, "x_carga": 1.0},
                       "t_aire_c", 20.0, _fin("PS1"), "se sale de su derating")
    assert abs(borde - 70.34) < 0.2, f"el borde de PS1 sale en {borde:.2f} C, no 70,34"


def demo() -> int:
    _autocomprobacion()
    t = aire_cajon_c()
    p = {"t_aire_c": t, "x_carga": 1.0}
    print(f"Derating de los convertidores con el aire del cajon a {t:.1f} C "
          f"(sala de {cb.T_SALA_DISENO_K - 273.15:.0f} C + chimenea pesimista)\n")
    print(f"  {'':4} {'pieza':<18} {'pide':>6} {'deja':>6} {'I max':>6}   rojo con el aire a")
    _guarda_corriente(p)
    for ref, (curva, *_resto) in CONVERTIDORES.items():
        _guarda(p, solo=ref)
        borde = borde_rojo(_guarda_de(ref), p, "t_aire_c", t, _fin(ref), "se sale de su derating")
        print(f"  [verde] {ref} {curva:<18} {carga(ref):>5.0%} {derating(curva, t):>5.0%}"
              f" {corriente(ref):>5.0%}   {borde:.1f} C (+{borde - t:.1f} K)")
    x = borde_rojo(_guarda, p, "x_carga", 1.0, 3.0, "se sale de su derating")
    print(f"\n  canario: con las cargas x {x:.2f} algun convertidor se sale de su derating")
    x = borde_rojo(_guarda_corriente, p, "x_carga", 1.0, 3.0, "pasa de su corriente nominal")
    print(f"  canario: con las cargas x {x:.2f} alguna salida pasa de su corriente nominal")

    print("\n  LO QUE NO CUBRE:")
    print("    - el aire junto a cada convertidor por encima del salto medio de la chimenea")
    print("    - curvas de hoja sin disipador ni flujo forzado (el cajon va por tiro natural)")
    print("    - las curvas de los THN son lecturas de figura, tipicas")
    print("    - PENDIENTE: que TRACO confirme por escrito que la curva del THN 30 vale por")
    print("      potencia total con las salidas desiguales; hasta entonces, la carcasa de PS1")
    print("      se mide (medidas.csv, paso 7, criterio 100 C)")
    print("\nOK: derating_budget.py v5 (#478)")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
