"""Enchufe en caliente: el pico en `+24V_RAW` cuando el cordon entra con el TE90 encendido (#494).

    python check_enchufe.py        (sale con codigo 2 mientras haya HUECOS)

`check_absmax.py` (bloque 8) da por hecho que `D1` (`SMBJ33CA`) recorta a
`V_C = 53,3 V` y comprueba que todo lo que cuelga de `+24V_RAW` aguanta eso.
`V_C` es la tension a `I_PP = 11,3 A` (`bourns_smbj.pdf` p. 2): la cuenta vale
mientras `D1` no lleve mas corriente que esa. Lo que faltaba de #494 es saber
cuanta le llega al enchufar.

## El circuito

El ladrillo ya esta en su tension y `C10` en 0 V. Entre los dos hay un lazo de
dos hilos (el cordon del TE90 y el arnes de `X1` a `J1`) que es una L con muy
poca R: sin `D1` el nodo llega a 2 x V, 72 V con el ladrillo en su OVP maximo.

    ladrillo (V_s, C_b) -- L y R del cordon y del arnes -- C10 || D1

Los condensadores del nodo salen de la netlist, no de este texto
(`condensadores_de_entrada()`): de `+24V_RAW` a la vuelta solo va `C10`. `C9`
es la `VCAP` de `U15`, colgada de `SRC`, y `U16` queda detras del diodo de
cuerpo de `Q2`, en `+24V_PROT`, sin condensador y apagado en el arranque.

  * `C_b`, la capacidad de salida del TE90: 2510 uF en sus bornes, contestado
    por AE el 2026-10-28 (caso P-258801, `H-V2-RESERVA`). Se mantiene el barrido
    de sensibilidad de 1 uF a 2510 uF y fuente ideal: una `C_b` finita baja la C
    del lazo y se descarga durante el pulso, y en 2510 uF ya coincide con la
    fuente ideal.
  * L del lazo: linea bifilar de hilos redondos, `L' = (mu0/pi) acosh(D/d)`,
    la inductancia externa por metro. La interna se va con el efecto piel a la
    frecuencia del timbre, y quitarla sube la corriente: pesimista. `d` sale
    del calibre (16 AWG, ASTM B258); la separacion `D` y el largo del cordon
    son ESTIMADO.
  * R: 16 AWG a 0,0132 ohm/m por hilo (`ladrillo_budget.py`), sin efecto piel.
    El contacto Kycon solo tiene maximo (30 mohm, `kycon_KPJX-PM-4S.pdf`
    p. 1); el minimo, que es el que manda en el pico, no esta publicado: 0.
  * `D1`: apagado hasta `V_BR` y luego la recta de `(V_BR, 1 mA)` a
    `(V_C, I_PP)` de p. 2, con `V_BR` en sus dos bordes (36,7 y 40,6 V).
  * `Q7` y `Q2`, como cortos: al enchufar conducen por su diodo de cuerpo, y
    la `V_F` que se le resta a `C10`, `U15` y `U16` no se cuenta (pesimista).

RK4 de paso fijo, 200 pasos por periodo del LC. Antes de nada se valida contra
dos casos cerrados (el LC sin `D1` ni R llega a 2 V; con `C_b` finita, a
2 V C_b / (C_b + C10)), y en cada corrida la energia que da el ladrillo tiene
que cuadrar con la que queda en el lazo, la que quema R y la que se lleva `D1`.

## Lo que se exige (`_guarda_enchufe`), en el peor rincon del barrido

  1. Corriente de `D1` <= `I_PP`. Va primero: por encima la hoja no da tension
     de recorte y la recta extrapola, asi que el pico que sale de ella ya no
     vale. Para un pulso de us es conservador: `I_PP` es del 10/1000 us.
  2. Pico <= cada maximo absoluto que ya usa `check_absmax.py`: `C10`, `VS` de
     `U15`, `IN` de `U16` y `VDS` de `Q2` y `Q7` (el mas bajo, aunque al
     enchufar los dos MOSFET estan en directa).
  3. Energia de `D1` <= la del pulso nominal de su mismo ancho, `P_PK(T_P) *
     T_P`: la curva de p. 4 anclada en los 600 W a 1 ms de p. 1, y rebajada por
     temperatura (p. 4) al aire del cajon. `T_P` como lo define la hoja (p. 4):
     hasta que la corriente cae al 50 % de su pico.
Cada aserto tiene su canario, y se imprime donde muerde.
"""
from __future__ import annotations

import csv
import importlib.util
import math
import os
import sys
from functools import lru_cache

DIR = os.path.dirname(os.path.abspath(__file__))


def _por_ruta(ruta: str):
    """Un guion de la v5 por su ruta: la v4 tiene su propio check_absmax.py."""
    spec = importlib.util.spec_from_file_location(
        "_v5_" + os.path.splitext(os.path.basename(ruta))[0], ruta)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


ca = _por_ruta(os.path.join(DIR, "check_absmax.py"))
db = ca._modulo("derating_budget")    # primero: importa ladrillo_budget por nombre,
lb = ca._modulo("ladrillo_budget")    # y _modulo reusa ese
cn = _por_ruta(os.path.join(DIR, "kicad", "check_netlist.py"))

# --- D1 (SMBJ33CA): lo que check_absmax no usaba todavia -------------------
I_PP_D1_A = 11.3                       # bourns_smbj.pdf p. 2: I_PP (10/1000 us), a la que V_C = 53,3 V
P_PK_1MS_W = 600.0                     # bourns_smbj.pdf p. 1: potencia de pico minima con T_P = 1 ms
# p. 4, Pulse Rating Curve: una recta en log-log de 0,1 us a 10 ms. Leida del
# trazado vectorial del PDF: baja 2,10 decadas de potencia en las 5 de tiempo,
# P_PK ~ T_P^-0,42. En 1 ms el trazado da 643 W; se ancla en los 600 W
# garantizados de p. 1, que la deja un 7 % por debajo en todo el tramo.
EXP_CURVA_PULSO = 0.42
T_P_MIN_CURVA_S = 0.1e-6               # p. 4: donde empieza la curva
# p. 4, Pulse Derating Curve: 100 % hasta 25 C y recta a 0 en 150 C (el trazado
# llega a cero en 150,9 C; 150 C es el T_J maximo de p. 1). Rebaja la potencia
# o la corriente de pico (nota 1 de p. 1).
T_REBAJA_DESDE_C = 25.0
T_REBAJA_CERO_C = 150.0

# --- el lazo -----------------------------------------------------------------
MU0_PI_H_M = 4e-7                      # mu0 / pi
D_16AWG_M = 0.127e-3 * 92.0 ** ((36 - 16) / 39)   # ASTM B258: 1,291 mm
# ESTIMADO: separacion entre los centros de los dos hilos. Ni la hoja del TE90
# ni bom-chasis.csv dan como esta hecho el cordon ni el arnes. 2,0 mm: dos
# hilos de 16 AWG tocandose con 0,35 mm de aislamiento; 5,0 mm: los dos
# conductores sueltos dentro de una funda redonda. Vale igual para el arnes.
D_CENTROS_M = (2.0e-3, 5.0e-3)
# ESTIMADO: el largo del cordon del TE90 no esta en su hoja (H-V5-CALIBRE del
# pliego). Se barre de 1,0 m al escenario de 2 m de ladrillo_budget.py; el
# canario dice el cordon mas corto que aguanta.
LARGO_CORDON_MIN_M = 1.0
# ESTIMADO: C10 (X7R de 100 V en 0805) baja con la polarizacion de 30..50 V y
# con la temperatura, y su hoja no esta en el arbol. -50 %..+10 % (la K del
# MPN de Yageo es +-10 %).
TOL_C10 = (-0.50, 0.10)
# Capacidad de salida del TE90: 2510 uF en sus bornes (AE, caso P-258801,
# 2026-10-28). Se barre de 1 uF a 2510 uF y None = fuente ideal.
C_TE90_SALIDA_F = 2510e-6
C_LADRILLO_F = (1e-6, 10e-6, 100e-6, 1000e-6, C_TE90_SALIDA_F, None)
# ESTIMADO: velocidad de la onda en el cordon, 0,6 c (aislamiento de PVC; mas
# lenta da una longitud de onda mas corta, el lado pesimista).
V_ONDA_CORDON_M_S = 0.6 * 299_792_458.0

# Los maximos absolutos del nodo, con sus claves en check_absmax.P_BASE.
LIMITES = (("C10", "c10_v"), ("VS de U15", "vs_u15_v"), ("IN de U16", "in_u16_v"),
           ("VDS de Q2", "vds_q2_v"), ("VDS de Q7", "vds_q7_v"))

ESTIMADOS = (
    f"separacion entre hilos {D_CENTROS_M[0] * 1e3:.1f}..{D_CENTROS_M[1] * 1e3:.1f} mm, en el cordon "
    "y en el arnes: ninguna hoja da su construccion",
    f"cordon de {LARGO_CORDON_MIN_M:.1f} m como el mas corto del barrido (el canario da el limite)",
    f"C10 {TOL_C10[0]:+.0%}..{TOL_C10[1]:+.0%}: polarizacion y temperatura de un X7R de 100 V; "
    "su hoja no esta en el arbol",
    "contacto Kycon en 0 ohm (la hoja solo da el maximo) y el cobre con su R de continua, sin "
    "efecto piel: las dos amortiguan menos que las reales",
    "velocidad de la onda en el cordon 0,6 c, solo para ver si el modelo concentrado vale",
)
HUECOS = (
    "cordon del TE90: largo, calibre y construccion no estan en su hoja (H-V5-CALIBRE)",
)


def largo_arnes_m() -> float:
    """El tramo de X1 a J1, de bom-chasis.csv (columna quantity, "0.3 m")."""
    with open(os.path.join(DIR, "bom-chasis.csv"), encoding="utf-8", newline="") as f:
        fila = next((r for r in csv.DictReader(f) if r["value"].startswith("Cable 16 AWG")), None)
    assert fila, "bom-chasis.csv ya no tiene el cable de 16 AWG de X1 a J1, y el lazo es de 16 AWG"
    return float(fila["quantity"].split()[0])


def condensadores_de_entrada() -> list[str]:
    """Los condensadores con una pata en +24V_RAW (o en +24V_PROT, que al
    enchufar la sigue por el diodo de cuerpo de Q2) y la otra en su vuelta."""
    nets = cn.leer()
    raw = {p.split(".")[0] for red in ("+24V_RAW", "+24V_PROT") for p in nets[red]}
    vuelta = {p.split(".")[0] for red in ("GND24", "RET24_RAW") for p in nets[red]}
    return sorted(r for r in raw & vuelta if r.startswith("C"))


def rebaja_temperatura(t_aire_c: float) -> float:
    return min(1.0, (T_REBAJA_CERO_C - t_aire_c) / (T_REBAJA_CERO_C - T_REBAJA_DESDE_C))


def p_pk_w(t_p_s: float, p_pk_1ms_w: float = P_PK_1MS_W) -> float:
    """Pulse Rating Curve (p. 4) anclada en p. 1. Por debajo de 0,1 us no hay
    curva y se sostiene su primer punto."""
    return p_pk_1ms_w * (1e-3 / max(t_p_s, T_P_MIN_CURVA_S)) ** EXP_CURVA_PULSO


def enchufe(v_s: float, l_h: float, r_ohm: float, c_n_f: float, c_b_f: float | None = None,
            v_br_v: float = ca.V_BR_MAX_SMBJ33CA_V, con_d1: bool = True,
            pasos_periodo: int = 200, periodos: float = 2.0) -> dict[str, float]:
    """RK4 del enchufe. Estado: i (A) del lazo, v_b (V) en C_b y v_n (V) en
    +24V_RAW; arranca con i = 0, v_n = 0 y v_b = v_s. Con c_b_f = None el
    ladrillo es una fuente ideal."""
    r_din = (ca.V_C_SMBJ33CA_V - v_br_v) / I_PP_D1_A
    c_eq = c_n_f if c_b_f is None else c_b_f * c_n_f / (c_b_f + c_n_f)
    dt = 2.0 * math.pi * math.sqrt(l_h * c_eq) / pasos_periodo

    def i_d1(v: float) -> float:
        if not con_d1 or abs(v) <= v_br_v:
            return 0.0
        return math.copysign((abs(v) - v_br_v) / r_din, v)

    def f(i: float, vb: float, vn: float) -> tuple[float, float, float]:
        return ((vb - vn - r_ohm * i) / l_h, 0.0 if c_b_f is None else -i / c_b_f,
                (i - i_d1(vn)) / c_n_f)

    i = vn = t = 0.0
    vb = v_s
    v_pico = i_pico = e_d1 = e_r = q = p_ant = 0.0
    t_on = t_50 = None
    for _ in range(int(periodos * pasos_periodo)):
        k1 = f(i, vb, vn)
        k2 = f(i + 0.5 * dt * k1[0], vb + 0.5 * dt * k1[1], vn + 0.5 * dt * k1[2])
        k3 = f(i + 0.5 * dt * k2[0], vb + 0.5 * dt * k2[1], vn + 0.5 * dt * k2[2])
        k4 = f(i + dt * k3[0], vb + dt * k3[1], vn + dt * k3[2])
        i_ant = i
        i, vb, vn = (x + dt / 6.0 * (a + 2.0 * b + 2.0 * c + d)
                     for x, a, b, c, d in zip((i, vb, vn), k1, k2, k3, k4))
        t += dt
        id1 = i_d1(vn)
        e_d1 += 0.5 * (p_ant + vn * id1) * dt          # trapecios
        p_ant = vn * id1
        e_r += 0.5 * r_ohm * (i_ant * i_ant + i * i) * dt
        q += 0.5 * (i_ant + i) * dt
        v_pico = max(v_pico, vn)
        if id1 > 0.0 and t_on is None:
            t_on = t
        if id1 > i_pico:
            i_pico, t_50 = id1, None
        elif t_50 is None and i_pico > 0.0 and id1 <= 0.5 * i_pico:
            t_50 = t
    assert i_pico == 0.0 or t_50 is not None, (
        "el pulso de D1 no baja al 50 % dentro de la ventana: alarga `periodos`")
    # Lo que dio el ladrillo contra lo que queda y lo que se fue, sobre la
    # energia de C10 a v_s (sin D1 ni R, a los dos periodos la fuente dio 0).
    e_fuente = v_s * q if c_b_f is None else 0.5 * c_b_f * (v_s * v_s - vb * vb)
    e_lazo = 0.5 * c_n_f * vn * vn + 0.5 * l_h * i * i
    return {"v_pico_v": v_pico, "i_d1_a": i_pico, "e_d1_j": e_d1,
            "t_p_s": (t_50 - t_on) if i_pico > 0.0 else 0.0,
            "descuadre": (e_fuente - e_lazo - e_r - e_d1) / (0.5 * c_n_f * v_s * v_s),
            "periodo_s": dt * pasos_periodo}


@lru_cache(maxsize=None)
def barrido(v_s: float, largo_min_m: float, con_d1: bool = True) -> tuple[dict, ...]:
    """C_b del ladrillo x cordon (el mas corto y 2 m) x separacion x C10 x V_BR de D1."""
    out = []
    arnes = largo_arnes_m()
    for c_b in C_LADRILLO_F:
        for largo in (largo_min_m, lb.LARGO_CORDON_M):
            for d in D_CENTROS_M:
                l_h = MU0_PI_H_M * math.acosh(d / D_16AWG_M) * (largo + arnes)
                r_ohm = lb.r_cordon_ohm(largo_m=largo + arnes)
                for tol in TOL_C10:
                    for v_br in (ca.V_BR_MIN_SMBJ33CA_V, ca.V_BR_MAX_SMBJ33CA_V):
                        r = enchufe(v_s, l_h, r_ohm, ca.valor("C10") * (1.0 + tol), c_b, v_br, con_d1)
                        r.update(c_b_f=c_b, largo_m=largo, d_m=d, tol_c10=tol, v_br_v=v_br, l_h=l_h)
                        out.append(r)
    return tuple(out)


def _e_limite_j(r: dict, p: dict[str, float]) -> float:
    return rebaja_temperatura(p["t_aire_c"]) * p_pk_w(r["t_p_s"], p["p_pk_1ms_w"]) * r["t_p_s"]


P_BASE: dict[str, float] = {
    **{clave: ca.P_BASE[clave] for _, clave in LIMITES},
    "v_fuente_v": ca.V_OVP_MAX_TE90_V,
    "largo_cordon_min_m": LARGO_CORDON_MIN_M,
    "con_d1": 1.0,
    "i_pp_d1_a": I_PP_D1_A,
    "p_pk_1ms_w": P_PK_1MS_W,
    "t_aire_c": db.aire_cajon_c(),
}


def _guarda_enchufe(p: dict[str, float]) -> None:
    """El peor rincon del barrido con el ladrillo en `v_fuente_v`."""
    rs = barrido(p["v_fuente_v"], p["largo_cordon_min_m"], bool(p["con_d1"]))
    i_max = max(r["i_d1_a"] for r in rs)
    assert i_max <= p["i_pp_d1_a"], (
        f"enchufe en caliente: D1 llega a {i_max:.2f} A > I_PP {p['i_pp_d1_a']:.2f} A, y por "
        "encima la hoja no da su tension de recorte")
    v_max = max(r["v_pico_v"] for r in rs)
    for nombre, clave in LIMITES:
        assert v_max <= p[clave], (
            f"enchufe en caliente: {nombre} aguanta {p[clave]:.1f} V y el pico llega a {v_max:.2f} V")
    for r in rs:
        if r["i_d1_a"] > 0.0:
            e_lim = _e_limite_j(r, p)
            assert r["e_d1_j"] <= e_lim, (
                f"enchufe en caliente: la energia de D1, {r['e_d1_j'] * 1e6:.0f} uJ en T_P = "
                f"{r['t_p_s'] * 1e6:.2f} us, pasa los {e_lim * 1e6:.0f} uJ del pulso nominal de ese ancho")


def _rojo(p: dict[str, float]) -> str:
    try:
        _guarda_enchufe(p)
    except AssertionError as e:
        return str(e)
    return ""


def _peor(rs, clave: str) -> dict:
    return max(rs, key=lambda r: r[clave])


def _c_b(c_b_f: float | None) -> str:
    return "fuente ideal" if c_b_f is None else f"C_b {c_b_f * 1e6:.0f} uF"


def _rincon(r: dict) -> str:
    return (f"{_c_b(r['c_b_f'])}, cordon {r['largo_m']:.1f} m, hilos a {r['d_m'] * 1e3:.1f} mm "
            f"(L {r['l_h'] * 1e6:.2f} uH), C10 {r['tol_c10']:+.0%}, V_BR {r['v_br_v']:.1f} V")


def _cociente_e(r: dict) -> float:
    return r["e_d1_j"] / _e_limite_j(r, P_BASE) if r["i_d1_a"] > 0.0 else 0.0


def _autocomprobacion() -> tuple[dict, dict]:
    """Dos casos cerrados, sin D1 ni R: el LC llega a 2 V, y con C_b finita a
    2 V C_b / (C_b + C10)."""
    v, l_h, c = ca.V_OVP_MAX_TE90_V, 1.0e-6, ca.valor("C10")
    lc = enchufe(v, l_h, 0.0, c, con_d1=False)
    assert abs(lc["v_pico_v"] / (2.0 * v) - 1.0) <= 1e-3, (
        f"el integrador no da el LC: {lc['v_pico_v']:.3f} V contra {2.0 * v:.3f} V")
    c_b = 10.0 * c
    dos = enchufe(v, l_h, 0.0, c, c_b, con_d1=False)
    esperado = 2.0 * v * c_b / (c_b + c)
    assert abs(dos["v_pico_v"] / esperado - 1.0) <= 1e-3, (
        f"el integrador no da los dos condensadores: {dos['v_pico_v']:.3f} V contra {esperado:.3f} V")
    return lc, dos


def demo() -> int:
    print("check_enchufe v5: enchufe en caliente del TE90 sobre +24V_RAW (D1 SMBJ33CA, #494)\n")
    assert ca.filas()["D1"]["mpn"] == ca.MPN_D1, (
        f"D1 es {ca.filas()['D1']['mpn']} y las cifras del modelo son de la {ca.MPN_D1}")
    c_in = condensadores_de_entrada()
    assert c_in == ["C10"], (
        f"entre +24V_RAW (o +24V_PROT) y su vuelta hay {c_in}; el modelo solo cuenta C10, y mas C "
        "es mas corriente en D1")

    lc, dos = _autocomprobacion()
    v_ovp = ca.V_OVP_MAX_TE90_V
    print(f"  0. Autocomprobacion del integrador (sin D1 ni R): el LC llega a {lc['v_pico_v']:.3f} V "
          f"= 2 x {v_ovp:.1f} V, y con C_b = 10 x C10 a {dos['v_pico_v']:.3f} V "
          f"= {2.0 * v_ovp * 10.0 / 11.0:.3f} V")

    arnes = largo_arnes_m()
    lp = [MU0_PI_H_M * math.acosh(d / D_16AWG_M) for d in D_CENTROS_M]
    r_din = [(ca.V_C_SMBJ33CA_V - v) / I_PP_D1_A for v in (ca.V_BR_MIN_SMBJ33CA_V, ca.V_BR_MAX_SMBJ33CA_V)]
    print(f"  1. Lazo: cordon {LARGO_CORDON_MIN_M:.1f}..{lb.LARGO_CORDON_M:.1f} m + arnes {arnes:.1f} m "
          f"(bom-chasis.csv), 16 AWG (d = {D_16AWG_M * 1e3:.3f} mm), hilos a "
          f"{D_CENTROS_M[0] * 1e3:.1f}..{D_CENTROS_M[1] * 1e3:.1f} mm: L' {lp[0] * 1e6:.2f}..{lp[1] * 1e6:.2f} uH/m")
    print(f"     entrada: {', '.join(c_in)} ({ca.valor('C10') * 1e9:.0f} nF, {TOL_C10[0]:+.0%}..{TOL_C10[1]:+.0%}); "
          f"D1 con V_BR {ca.V_BR_MIN_SMBJ33CA_V} y {ca.V_BR_MAX_SMBJ33CA_V} V "
          f"(R_din {r_din[0]:.2f} y {r_din[1]:.2f} ohm hasta V_C {ca.V_C_SMBJ33CA_V} V a {I_PP_D1_A} A)")

    # El ladrillo nominal, en su borde alto y en su OVP maximo. La guarda solo
    # mira el OVP maximo; que ahi esta lo peor se comprueba, no se supone.
    v_fuentes = (lb.V_LADRILLO, ca.V_LADRILLO_MAX_V, v_ovp)
    todo = {v: barrido(v, LARGO_CORDON_MIN_M) for v in v_fuentes}
    planos = [r for rs in todo.values() for r in rs]
    descuadre = max(abs(r["descuadre"]) for r in planos)
    assert descuadre <= 0.01, f"la energia no cuadra en el barrido: {descuadre:.2%}"
    guarda = todo[v_ovp]
    for clave in ("v_pico_v", "i_d1_a"):
        assert _peor(planos, clave) in guarda, (
            f"el peor {clave} del barrido no esta en el OVP maximo del TE90: la guarda no lo ve")
    peor_e = max(planos, key=_cociente_e)
    assert peor_e in guarda, "la peor energia del barrido no esta en el OVP maximo del TE90: la guarda no la ve"
    # La L concentrada vale si el lazo es corto frente a la longitud de onda del timbre.
    lam_10 = V_ONDA_CORDON_M_S * min(r["periodo_s"] for r in planos) / 10.0
    assert lb.LARGO_CORDON_M + arnes <= lam_10, (
        f"el lazo mide {lb.LARGO_CORDON_M + arnes:.1f} m y lambda/10 del timbre son {lam_10:.1f} m: "
        "el cordon ya es una linea")
    print(f"     {len(planos)} corridas; la energia cuadra en todas (descuadre <= {descuadre:.2%})")

    _guarda_enchufe(dict(P_BASE))
    rs = guarda
    pv, pi_ = _peor(rs, "v_pico_v"), _peor(rs, "i_d1_a")
    lim_nombre, lim_clave = min(LIMITES, key=lambda nc: P_BASE[nc[1]])
    rebaja = rebaja_temperatura(P_BASE["t_aire_c"])
    print(f"\n  2. Peor caso, el TE90 en su OVP maximo ({v_ovp:.1f} V, ae-TE90-datasheet.pdf p. 2):")
    print(f"    [verde] D1 llega a {pi_['i_d1_a']:.2f} A <= I_PP {I_PP_D1_A} A "
          f"(margen {I_PP_D1_A - pi_['i_d1_a']:.2f} A; {_rincon(pi_)})")
    print(f"    [verde] pico {pv['v_pico_v']:.2f} V <= {P_BASE[lim_clave]:.1f} V de {lim_nombre}, el mas bajo "
          f"del nodo (margen {P_BASE[lim_clave] - pv['v_pico_v']:.2f} V; {_rincon(pv)})")
    print(f"    [verde] energia de D1 {peor_e['e_d1_j'] * 1e6:.0f} uJ en T_P = {peor_e['t_p_s'] * 1e6:.2f} us "
          f"<= {_e_limite_j(peor_e, P_BASE) * 1e6:.0f} uJ del pulso nominal de ese ancho "
          f"(P_PK {p_pk_w(peor_e['t_p_s']):.0f} W al {rebaja:.0%} con el aire del cajon a "
          f"{P_BASE['t_aire_c']:.1f} C; {_rincon(peor_e)})")

    print(f"\n  3. Sensibilidad a C_b (TE90 = {C_TE90_SALIDA_F * 1e6:.0f} uF, AE P-258801), a {v_ovp:.1f} V, lo peor de cada fila:")
    for cb in C_LADRILLO_F:
        r = [x for x in guarda if x["c_b_f"] == cb]
        print(f"       {_c_b(cb):<14} pico {_peor(r, 'v_pico_v')['v_pico_v']:6.2f} V | "
              f"D1 {_peor(r, 'i_d1_a')['i_d1_a']:5.2f} A | {_peor(r, 'e_d1_j')['e_d1_j'] * 1e6:4.0f} uJ | "
              f"energia al {max(map(_cociente_e, r)):.1%} de la nominal")

    print("\n  4. En servicio: D1 conduce en cada enchufe en caliente")
    for v in v_fuentes[:2]:
        r = todo[v]
        print(f"       ladrillo a {v:.1f} V: pico {_peor(r, 'v_pico_v')['v_pico_v']:.2f} V, D1 hasta "
              f"{_peor(r, 'i_d1_a')['i_d1_a']:.2f} A y {_peor(r, 'e_d1_j')['e_d1_j'] * 1e6:.0f} uJ")

    # Canarios: cada aserto de _guarda_enchufe salta por su texto.
    sin_d1 = _rojo(dict(P_BASE, con_d1=0.0))
    assert "aguanta" in sin_d1, "sin D1 el enchufe sale verde: el pico no depende de D1"
    v_sin = _peor(barrido(v_ovp, LARGO_CORDON_MIN_M, False), "v_pico_v")["v_pico_v"]
    lim = {n: ca.borde_rojo(_guarda_enchufe, dict(P_BASE), clave, P_BASE[clave], 10.0, f"{n} aguanta")
           for n, clave in LIMITES}
    largo_min = ca.borde_rojo(_guarda_enchufe, dict(P_BASE), "largo_cordon_min_m",
                              LARGO_CORDON_MIN_M, 0.0, "I_PP")
    i_pp = ca.borde_rojo(_guarda_enchufe, dict(P_BASE), "i_pp_d1_a", I_PP_D1_A, 1.0, "I_PP")
    p_pk = ca.borde_rojo(_guarda_enchufe, dict(P_BASE), "p_pk_1ms_w", P_PK_1MS_W, 1.0, "energia de D1")
    l_min = MU0_PI_H_M * math.acosh(D_CENTROS_M[0] / D_16AWG_M) * (largo_min + arnes)
    print(f"\n  [rojo ] MUTANTE sin D1: el pico llega a {v_sin:.2f} V")
    print("  canario: lo que aguanta cada pieza antes de que el pico la pase: "
          + ", ".join(f"{n} {v:.1f} V" for n, v in lim.items()))
    print(f"  canario: con un cordon de menos de {largo_min:.2f} m (lazo de {l_min * 1e6:.2f} uH con los hilos "
          f"a {D_CENTROS_M[0] * 1e3:.1f} mm) D1 pasa de I_PP; con una I_PP por debajo de {i_pp:.2f} A, tambien")
    print(f"  canario: con un P_PK de menos de {p_pk:.1f} W a 1 ms (la hoja da {P_PK_1MS_W:.0f}) la energia "
          f"de D1 pasaria")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}; HUECO: {len(HUECOS)}")
    for e in ESTIMADOS:
        print(f"    ESTIMADO - {e}")
    for h in HUECOS:
        print(f"    HUECO    - {h}")

    print("\n  LO QUE NO CUBRE:")
    print("    - el rebote del contacto: cada recierre repite el evento con C10 ya cargado, y abrir con "
          "corriente en el cordon pone su L contra el arco")
    print(f"    - el cordon como linea de transmision: el lazo mide {lb.LARGO_CORDON_M + arnes:.1f} m y "
          f"lambda/10 del timbre mas rapido son {lam_10:.0f} m, asi que la L concentrada vale; el frente de "
          "ns del contacto si viaja como onda, y C10 lo ve como un corto")
    print("    - la inductancia interna del TE90 y su filtro de salida: no se cuentan; menos L es mas "
          "corriente y mas pico, pero no mas energia")
    print("    - la curva V-I de D1 entre V_BR y V_C: la hoja da dos puntos y el modelo la recta; V_BR y V_C "
          "son a 25 C y la hoja de Bourns no da su coeficiente de temperatura")
    print("    - si el pico, que pasa por el diodo de cuerpo de Q2, dispara el OVP de U16 en el arranque")

    print("\nHUECO: " + "; ".join(h.split(":")[0] for h in HUECOS))
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
