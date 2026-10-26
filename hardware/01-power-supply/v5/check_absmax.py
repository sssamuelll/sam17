"""Supervivencia por riel, modelo RK4 de #334 y crowbars D-F6 en la fuente v5.

    python check_absmax.py

Cierra en codigo ejecutable para la v5 los trabajos **T14, T18, T19, T20, T21**
del censo D-V4 (`2026-09-08-censo-dv4-resolucion.md`) y los issues **#334** y
**#340**, con todas las hojas versionadas en `docs/reference/datasheets/`:

  1. **#334 (`H-V2-CORTO-DCDC`, T18): simulacion RK4 del escalon sobre el LC de `U1`.**
     - El convertidor crudo positivo (`TRACO THN 20-2413WI`, `traco_thn20wi.pdf`
       p. 2) tiene su OVP interno entre el 112 % y el 164 % de 15 V (`16,8 ..
       24,6 V`), y un puente entrada-salida aplicaria hasta `36 V` (o `24 V` del
       ladrillo) al filtro LC (`22 uH` + `47 uF` + `0,68 ohm` + `220 uF`).
     - `U1` es el `LT1963A` (D-F8, `lt1963a-rev-g-2021-02.pdf` p. 2), cuyo
       maximo absoluto de entrada es **+-20,0 V**.
     - El eFuse **TI TPS26631** (`U19`) va **antes del filtro LC, sensando del
       lado del modulo**, y corta por lo PRIMERO que llegue (`tps2663.pdf`):
         * OVP: `V(OVPR) = 1,176 .. 1,224 V` (p. 6; disparo nominal `16,55 V`,
           borde bajo `16,19 V` > maximo sano `16,01 V`, borde alto `16,92 V`),
           corte en `<= 14 us` (p. 8);
         * disparo rapido: `3 x I(OL)` en el TPS26631 (p. 7), con `I(OL)` de
           `R34` y su +-10 % (`recuperacion_budget.py`), respuesta `<= 4,5 us`
           (p. 9, soft short); por encima de `I(SCP) = 45 A`, `<= 1 us` (p. 9).
     - `L2` es una **Bourns SRP1265A-220M** (`bourns_srp1265a.pdf`): 22 uH
       +-20 % (p. 1) y su curva L-I hasta 12 A (p. 3), que el modelo sigue
       punto a punto. Con la `SRR1260-220M` que montaba antes (Isat 3,7 A) el
       modelo llevaba la bobina a 12,7 A con sus 22 uH enteros: una pieza que
       no existe. Con la SRR saturando, el pico dependia de una curva que su
       hoja no publica; con la SRP la corriente se queda dentro de la curva.
     - Peor caso: arranca en el maximo sano en vacio, sin carga, con `L2`,
       `C3` y `C1` en el borde bajo de su tolerancia, y falla de `36 V`:
         * con tope, el pico en `U1 IN` queda por debajo de `20,0 V` y la
           corriente de `L2` dentro de la curva publicada (cifras en demo());
         * sin eFuse, sin disparo rapido, o sin disparo rapido y sensando
           DESPUES del LC: ROJO. El disparo rapido es lo que salva a `U1`, y
           su retardo maximo tiene canario.
       El TVS **Bourns SMBJ16A** (`bourns_smbj.pdf` p. 2: `V_WM = 16,0 V`,
       `V_BR = 17,8..19,7 V`) en `U1 IN` queda de respaldo: con el tope no
       llega a conducir.

  2. **`U2` (`LT3015`, D-F9, T18):**
     - `IN Pin Voltage` maximo absoluto de **+-33,0 V** (`lt3015-rev-b.pdf` p. 2),
       por encima del OVP maximo del `THN 20-2413WI` (`-24,6 V`, margen `+8,40 V`),
       mas diodo Schottky en inversa `OUT-IN >= -0,3 V` (p. 2, Nota 10).

  3. **D-F6 en los tres rieles de rack (T20, #340, M3):**
     - SCR **NXP BT151-500R** (`nxp-bt151-500r.pdf` p. 2: `I_H <= 40 mA`,
       `I_GT <= 15 mA`, `I^2t = 72 A^2s`, `t_gt <= 2 us`) + referencia
       **TI TL431BI** + fusible rapido **Bourns SF-1206F** (`bourns_sf1206f.pdf`).
     - La banda de disparo sale riel a riel de la hoja del TL431BI (`tl431.pdf`
       p. 13): `V_ref` a 25 C, su deriva en temperatura, `I_ref` por la rama
       alta, `dV_ref/dV_KA` y divisores de 0,1 %. La v4 dio `+-0,30 V` para un
       disparo de 14 V, y la v5 copio esos voltios al de 5,8 V.
     - En `+-12 V` (`THN 30-2422WI`, `traco_thn30wi.pdf` p. 2: limitacion de
       corriente `150..205 %` de `1,25 A`, `170 %` tipica; `1,875 A` es el
       minimo) y `+5 V` (`RPMB5.0-2.0` / `K7805T-1000R3`),
       la corriente de pliegue supera en mas de 35 veces los `40 mA` de
       mantenimiento del `BT151-500R`.

  4. **Supervivencia del `+5 V` digital aislado (T19, `H-CENSO-DIGITAL`):**
     - El `Mornsun URB2405YMD-20WR3` (`mornsun_urb_ymd20wr3.pdf` p. 2) declara
       OVP entre `110 %` y `160 %` (`5,50..8,00 V`). El digital no lleva
       crowbar (junta de piezas v5 sec. 4.5): `SCR4` y su disparo quedan sin
       montar, y la entrada de 5 V del modulo 2 aguanta `8,00 V` como
       REQUISITO, igual que en la v4. Con el URB declarando `+-8 %` de
       desviacion ante un escalon de carga del 25 % (p. 2), el disparo de
       `5,66 V` nominal saltaba dentro del transitorio sano.

  5. **`U18` (`TPS709`, el LDO del supervisor M5):** `R64` y el zener `D2`
     sujetan su entrada cuando `D1` recorta un transitorio a `42,1 V`.

  6. **D-F6 por dentro:** la corriente de puerta que el PNP puede dar con
     `R_GK` en el disparo mas bajo, y el `I^2t` de los fusibles contra el del SCR.

Cada fila de `absmax.csv` sale de un modelo o de la BOM y se comprueba contra
el: ninguna se cree.

FUERA DE CONTRATO (se imprime al final): el contrato es de fallo simple
(propuesta de piezas v5 sec. 9.1, #475).
  * Fallo doble en el negativo (`THN-` en OVP y `U2` en corto): `U6`/`U7` verian
    `24,6 V` contra `22 V`. Se acepta, sin TVS ni tope.
  * El fallo doble equivalente en el positivo (`THN+` en OVP y `U1` en corto)
    sale cubierto por M3, no por requisito: la fila `U4,U5` lo guarda.

LO QUE ESTE CALCULO NO CUBRE (se imprime al final):
  * La curva L-I de la SRP1265A-220M es TIPICA (p. 3): se lee de la figura,
    se baja 0,5 uH y se le aplica el -20 % de la tolerancia. Mas alla de 12 A
    no hay curva, y la guarda de `U1` exige no pasar de ahi.
  * `OUT` de `U19` baja a `-V_F` de `D19` (hasta `0,55 V` a `3 A`) durante el
    corte. La hoja da `-0,3 V` absoluto en DC y pide ese Schottky (p. 36, 38),
    sin cifra de transitorio.
  * La pendiente del riel de rack en un enchufe en caliente no esta modelada:
    el SCR aguanta `200 V/us` con `R_GK = 100 ohm` (`nxp-bt151-500r.pdf` p. 6).
  * Un crowbar disparado no llega al MSP430: el SCR se queda conduciendo la
    corriente de pliegue del convertidor (los fusibles de `+-12 V` son de
    `3 A` y el THN 30 pliega a `1,875 A`) (#476). Si el convertidor lo suelta
    y cuanto se calienta el SCR se mide en el bring-up: `check_bringup.py`,
    paso 8, puntos `crowbar_*`, con la cota de `subida_max_scr_k()`.
"""
from __future__ import annotations

import csv
import importlib.util
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(DIR, "absmax.csv")
if DIR not in sys.path:
    sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "..", "..", "tools"))

from bom_valores import filas, valor  # noqa: E402
from canario import borde_rojo  # noqa: E402

_MODULOS: dict = {}


def _modulo(nombre: str):
    """Un guion de la v5, cargado al usarlo y no al importar: la v4 carga este
    modulo para el modelo RK4, y con su propio directorio en sys.path el
    margen_budget de la v5 acababa importando el rizado_budget equivocado. Por
    ruta y con nombre propio, por la misma razon; y si otro guion ya lo cargo
    (check_bringup, ladrillo_budget), se usa ese: volver a cargarlo con el
    rizado_budget de la v5 ya en sys.modules no funciona."""
    if nombre not in _MODULOS:
        ruta = os.path.normcase(os.path.abspath(os.path.join(DIR, f"{nombre}.py")))
        ya = next((m for m in list(sys.modules.values())
                   if os.path.normcase(os.path.abspath(getattr(m, "__file__", None) or "")) == ruta), None)
        if ya is None:
            spec = importlib.util.spec_from_file_location(f"_v5_{nombre}", ruta)
            assert spec and spec.loader
            ya = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = ya     # un @dataclass busca su modulo aqui
            spec.loader.exec_module(ya)
        _MODULOS[nombre] = ya
    return _MODULOS[nombre]


def _margen():
    return _modulo("margen_budget")


def v_sano_max_u1_v() -> float:
    return _margen().v_entrada_maxima_sana_v()

# EL MODELO SIMULA LAS PIEZAS DE LA PLACA. L, C, Cd, Rd y el divisor del OVP
# se leen de bom.csv (#474: el modelo llevaba un LC y la BOM otro, y con el de
# la BOM U1 veia 21,0 V; ningun numero de este fichero lo habria delatado).

# --- Limites de U1 (LT1963A) y parametros del tope M3 (#334) ----------------
V_ABSMAX_U1_V = 20.0                   # lt1963a-rev-g-2021-02.pdf p. 2
V_ABSMAX_U2_V = 33.0                   # lt3015-rev-b.pdf p. 2
# THN 20-2413WI: OVP entre el 112 % y el 164 % de 15 V (traco_thn20wi.pdf p. 2)
V_OVP_MAX_THN20_V = 1.64 * 15.0
# URB2405YMD-20WR3: OVP entre el 110 % y el 160 % de 5 V (mornsun_urb_ymd20wr3.pdf p. 2)
V_OVP_MAX_URB_V = 1.60 * 5.0
V_OVPR_NOM_V = 1.200                   # tps2663.pdf p. 6: V(OVPR) 1,176..1,224 V
V_DISPARO_NOM_U1_V = V_OVPR_NOM_V * (1.0 + valor("R35") / valor("R36"))
TOL_OVPR_TPS26631_FRAC = 0.020         # tps2663.pdf p. 6: 1,176..1,224 V (+-2,0 %)
TOL_DIVISOR_01PCT_FRAC = 0.002         # dos resistencias de 0,1 %
V_DISPARO_MIN_U1_V = V_DISPARO_NOM_U1_V * (1.0 - TOL_OVPR_TPS26631_FRAC - TOL_DIVISOR_01PCT_FRAC)
V_DISPARO_MAX_U1_V = V_DISPARO_NOM_U1_V * (1.0 + TOL_OVPR_TPS26631_FRAC + TOL_DIVISOR_01PCT_FRAC)
T_CORTE_OVP_MAX_S = 14.0e-6            # tps2663.pdf p. 8: 8,5 us typ, 14 us max
# Disparo rapido del TPS26631: 3 x I(OL) (p. 7), con I(OL) de R34 y su +-10 %
# (recuperacion_budget.py); respuesta 2,2..4,5 us en corto blando y 1 us por
# encima de I(SCP) (p. 9).
FACTOR_FASTTRIP_TPS26631 = 3.0
T_FASTTRIP_MAX_S = 4.5e-6
I_SCP_TPS2663_A = 45.0
T_SCP_MAX_S = 1.0e-6


def i_fasttrip_max_u19_a() -> float:
    rec = _modulo("recuperacion_budget")
    return FACTOR_FASTTRIP_TPS26631 * rec.corriente_limite_tps26631_a("R34", rec.TOL_ILIM_U19_FRAC)[2]


# L2 = SRP1265A-220M. Curva L-I de bourns_srp1265a.pdf p. 3, leida de la
# figura (22,4 / 22,0 / 20,9 / 19,9 / 18,5 / 16,8 uH) y bajada 0,5 uH; encima,
# el -20 % de la tolerancia de p. 1. Es la inductancia con polarizacion, y se
# usa como incremental, que es la que fija di/dt.
MPN_L2 = "SRP1265A-220M"
CURVA_L2_A_UH = ((0.0, 21.9), (2.4, 21.5), (4.8, 20.4), (7.2, 19.4), (9.6, 18.0), (12.0, 16.3))
TOL_L2_FRAC = 0.20
# C3 (47 uF) y C1 (220 uF): +-20 %, la tolerancia de serie del electrolitico de
# aluminio. Ninguna de las dos hojas esta en el arbol.
TOL_ELECTROLITICO_FRAC = 0.20


def l2_h(i_a: float, tol: bool = True) -> float:
    """Inductancia de L2 a `i_a`. Mas alla de la curva se sostiene su ultimo
    punto: eso solo lo usan los mutantes rojos, y ahi el modelo se queda corto,
    no largo. La guarda de U1 exige no salir de la curva."""
    i = abs(i_a)
    l_uh = CURVA_L2_A_UH[-1][1]
    for (a, la), (b, lb) in zip(CURVA_L2_A_UH, CURVA_L2_A_UH[1:]):
        if a <= i <= b:
            l_uh = la + (lb - la) * (i - a) / (b - a)
            break
    return l_uh * 1e-6 * ((1.0 - TOL_L2_FRAC) if tol else 1.0)


# Parametros del filtro LC amortiguado + TVS Bourns SMBJ16A (bourns_smbj.pdf p. 2)
# TPS2663x RON max (53m) + bobina (30m, por debajo de los 32,5 tipicos de la
# SRP1265A-220M: la DCR MAS BAJA amortigua menos, cota pesimista para el pico)
# + fuente/traza (50m).
R_SERIE_LC_OHM = 0.053 + 0.030 + 0.050
C_LC_F = valor("C3")
C_DAMP_F = valor("C1")
ESR_CD_OHM = 0.10                      # ESTIMADO: electrolitico de 220 uF (rizado_budget.py v4)
R_DAMP_OHM = valor("R37") + ESR_CD_OHM
# bourns_smbj.pdf p. 2: V_BR 17,8..19,7 V a 1 mA. Para el PICO manda el
# MAXIMO: con el minimo (que es lo que usaba #474) el TVS recorta antes y el
# modelo sale optimista.
V_BR_SMBJ16A_V = 19.70
R_DIN_SMBJ16A_OHM = 0.35               # pendiente dinamica del SMBJ16A en conduccion

# --- Parametros de D-F6 (NXP BT151-500R + TI TL431BI) -----------------------
I_MANTENIMIENTO_BT151_A = 0.040        # nxp-bt151-500r.pdf p. 2: I_H max 40 mA
I2T_BT151_A2S = 72.0                   # nxp-bt151-500r.pdf p. 2: I^2t = 72 A^2s
I_GT_MAX_BT151_A = 0.015               # nxp-bt151-500r.pdf p. 6
V_GT_MAX_BT151_V = 1.5                 # nxp-bt151-500r.pdf p. 6
R_GK_DVDT_OHM = 100.0                  # nxp-bt151-500r.pdf p. 6: 200 V/us con R_GK = 100 ohm
# MMBT3906 (onsemi_mmbt3906.pdf p. 2): h_FE >= 60 a 50 mA; V_CE(sat) <= 0,4 V
# y V_BE(sat) <= 0,95 V a 50 mA.
HFE_MIN_PNP = 60.0
V_CE_SAT_PNP_V = 0.40
V_BE_SAT_PNP_V = 0.95
# I^2t de fusion (tipico) de cada fusible de la BOM, por MPN:
# bourns_sf1206f.pdf p. 1 (a 10 x I_n) y littelfuse_0466.pdf p. 1.
I2T_FUSION_A2S = {"SF-1206F300-2": 0.501, "SF-1206F200-2": 0.181, "0466004.NRHF": 1.764}
# ESTIMADO: el despeje (fusion + arco) frente a la fusion tipica. Ninguna de
# las dos hojas da el I^2t de despeje.
FACTOR_DESPEJE_I2T = 10.0
# Un SCR enclavado (#476): Tj max 125 C (nxp-bt151-500r.pdf p. 3), Rth(j-mb)
# <= 1,3 K/W (p. 5), V_T <= 1,75 V a 23 A (p. 6). Los dos fusibles abren al
# 200 % (bourns_sf1206f.pdf p. 1, <= 60 s; littelfuse_0466.pdf p. 1, <= 5 s):
# lo que el SCR conduce sin que abra es menos del doble del nominal.
TJ_MAX_BT151_C = 125.0
RTH_JMB_BT151_K_W = 1.3
V_T_MAX_BT151_V = 1.75
I_NOMINAL_FUSIBLE_A = {"SF-1206F300-2": 3.0, "SF-1206F200-2": 2.0, "0466004.NRHF": 4.0}

# El disparo se calcula de los divisores de la placa: con el TL431 -> PNP ->
# puerta el umbral es 2,495 V * (1 + R_alta/R_baja), sin V_GT (en #474 el anodo
# del TL431 iba a la puerta y el umbral se corria V_GT*(1+R1/R2), de 3 a 8 V).
V_REF_TL431_V = 2.495                  # tl431.pdf p. 5
# TL431BI (tl431.pdf p. 13): V_ref 2483..2507 mV a 25 C; V_I(dev) <= 34 mV en
# todo el rango de temperatura; I_ref <= 4 uA e I_I(dev) <= 2,5 uA;
# dV_ref/dV_KA hasta -2,7 mV/V (V_KA de V_ref a 10 V) y -2 mV/V (de 10 a 36 V).
V_REF_MIN_TL431BI_V = 2.483 - 0.034
V_REF_MAX_TL431BI_V = 2.507 + 0.034
I_REF_MAX_TL431BI_A = 4.0e-6 + 2.5e-6
DVREF_DVKA_TL431BI = (-2.7e-3, -2.0e-3)
TOL_DIVISOR = 0.001                    # resistencias de 0,1 % (bom.csv)


def _disparo(r_alta: str, r_baja: str) -> float:
    return V_REF_TL431_V * (1.0 + valor(r_alta) / valor(r_baja))


def banda_disparo_v(r_alta: str, r_baja: str) -> tuple[float, float]:
    """Disparo mas bajo y mas alto garantizados: V = V_ref * (1 + Ra/Rb) + I_ref * Ra.

    Abajo: V_ref en su minimo con la deriva, el divisor torcido hacia abajo,
    I_ref = 0 y la caida de V_ref con V_KA, acotada con V_KA = disparo (el
    catodo no pasa del riel). Arriba: V_ref en su maximo, el divisor torcido
    hacia arriba e I_ref en su maximo con su deriva."""
    ra, rb = valor(r_alta), valor(r_baja)

    def ganancia(t: float) -> float:
        return 1.0 + ra * (1.0 + t) / (rb * (1.0 - t))

    v_ka = _disparo(r_alta, r_baja)
    dv = (DVREF_DVKA_TL431BI[0] * (min(v_ka, 10.0) - V_REF_TL431_V)
          + DVREF_DVKA_TL431BI[1] * max(0.0, v_ka - 10.0))
    bajo = (V_REF_MIN_TL431BI_V + dv) * ganancia(-TOL_DIVISOR)
    alto = (V_REF_MAX_TL431BI_V * ganancia(TOL_DIVISOR)
            + I_REF_MAX_TL431BI_A * ra * (1.0 + TOL_DIVISOR))
    return bajo, alto


# (V nominal, fracciones de hoja que suben la salida, tempco por K, rizado Vpp,
# desviacion transitoria ante un escalon de carga; None si la hoja no la da)
SANO_HOJA = {
    # traco_thn30wi.pdf p. 2 (modelo doble): exactitud 1 %, linea 0,5 %, carga
    # 1 %, regulacion cruzada 5 % con carga asimetrica, 0,02 %/K; rizado 60 mVpp
    # TIPICO (la hoja no da maximo). Del transitorio solo da el tiempo de
    # respuesta (250 us tipico): la desviacion se pidio a TRACO.
    "rack+12": (12.0, (0.01, 0.005, 0.01, 0.05), 0.0002, 0.060, None),
    "rack-12": (12.0, (0.01, 0.005, 0.01, 0.05), 0.0002, 0.060, None),
    # mornsun_k78_t1000r3.pdf p. 1-2: exactitud 3 %, linea 0,4 %, carga 0,6 %,
    # 0,03 %/C; rizado 75 mVpp max, 150 mVpp por debajo del 20 % de carga
    # (nota 2), que es el riel sin invitados; desviacion transitoria 150 mV max
    # ante un escalon del 25 % (p. 2).
    "rack+5": (5.0, (0.03, 0.004, 0.006), 0.0003, 0.150, 0.150),
}


def sano_max_v(riel: str) -> float:
    """Lo mas alto que el riel llega a valer funcionando bien: exactitud,
    regulaciones y deriva de hoja sumadas al maximo (con el salto de
    temperatura de margen_budget.py), mas medio rizado y la desviacion
    transitoria que declara la hoja."""
    v_nom, fracs, tempco_k, rizado, transitorio = SANO_HOJA[riel]
    return (v_nom * (1.0 + sum(fracs) + tempco_k * _margen().DELTA_T_K_V5)
            + rizado / 2.0 + (transitorio or 0.0))

# (r_alta, r_baja, R_B, R_BE, R_C, R_GK, fusible) de cada crowbar, como los
# coloca build_schematic.py (_crowbar y rack()).
PIEZAS_CROWBAR = {
    "rack+12": ("R45", "R47", "R70", "R74", "R78", "R53", "F2"),
    "rack-12": ("R46", "R48", "R71", "R75", "R79", "R54", "F3"),
    "rack+5": ("R49", "R50", "R72", "R76", "R80", "R55", "F4"),
}

RACK_RIELES = {
    "rack+12": {"ovp_max_v": 16.56, "victima_max_v": 16.00,
                "disparo_v": _disparo("R45", "R47"), "banda_v": banda_disparo_v("R45", "R47"),
                "i_pliegue_min_a": 1.875},
    "rack-12": {"ovp_max_v": 16.56, "victima_max_v": 16.00,
                "disparo_v": _disparo("R46", "R48"), "banda_v": banda_disparo_v("R46", "R48"),
                "i_pliegue_min_a": 1.875},
    "rack+5":  {"ovp_max_v": 6.75, "victima_max_v": 6.30,
                "disparo_v": _disparo("R49", "R50"), "banda_v": banda_disparo_v("R49", "R50"),
                "i_pliegue_min_a": 2.500},
}


def corriente_puerta_a(riel: str, i_gt_a: float = I_GT_MAX_BT151_A) -> dict[str, float]:
    """Lo que pide la puerta y lo que da el PNP en el disparo MAS BAJO del riel.

    Pide: I_GT max + lo que se lleva R_GK a V_GT max. Da: el PNP saturado (si
    h_FE * I_B alcanza) a traves de R_C. La base la tira el catodo del TL431,
    que no baja de V_ref, a traves de R_B, menos lo que se lleva R_BE."""
    _ra, _rb, r_b, r_be, r_c, r_gk, _f = PIEZAS_CROWBAR[riel]
    v = RACK_RIELES[riel]["banda_v"][0]
    pide = i_gt_a + V_GT_MAX_BT151_V / valor(r_gk)
    i_base = (v - V_BE_SAT_PNP_V - V_REF_TL431_V) / valor(r_b) - V_BE_SAT_PNP_V / valor(r_be)
    da = min(HFE_MIN_PNP * i_base, (v - V_CE_SAT_PNP_V - V_GT_MAX_BT151_V) / valor(r_c))
    return {"pide_a": pide, "da_a": da, "r_gk_ohm": valor(r_gk)}


def subida_max_scr_k(riel: str, t_aire_c: float) -> float:
    """Lo que puede subir la base del SCR de `riel` sobre el aire, enclavado, sin
    que la union pase de TJ_MAX con el aire a `t_aire_c`. La caida base-union
    va con la corriente mas alta que el fusible deja pasar sin abrir."""
    i_cota = 2.0 * I_NOMINAL_FUSIBLE_A[filas()[PIEZAS_CROWBAR[riel][-1]]["mpn"]]
    return TJ_MAX_BT151_C - t_aire_c - V_T_MAX_BT151_V * i_cota * RTH_JMB_BT151_K_W


# --- U18 (TPS709) detras de R64 + D2 ----------------------------------------
V_C_SMBJ26CA_V = 42.1                  # bourns_smbj.pdf p. 2: V_C a I_PP = 14,3 A
V_BR_MAX_SMBJ26CA_V = 31.9             # bourns_smbj.pdf p. 2: por debajo, D1 casi no conduce
V_IN_MAX_U18_V = 30.0                  # tps709.pdf p. 4: maximo de operacion
V_ABSMAX_U18_V = 32.0                  # tps709.pdf p. 4
# diodes_bzt52.pdf p. 2: (V_Z max, I_ZT, Z_ZT max) por valor; P_D 370 mW a 25 C.
ZENER_BZT52 = {"BZT52C18": (19.1, 5e-3, 45.0), "BZT52C20": (21.2, 5e-3, 55.0),
               "BZT52C22": (23.3, 5e-3, 55.0), "BZT52C24": (25.6, 5e-3, 70.0),
               "BZT52C27": (28.9, 2e-3, 80.0), "BZT52C30": (32.0, 2e-3, 80.0)}
P_D_BZT52_W = 0.370


def u18_peor(v_entrada_v: float, r64_ohm: float | None = None) -> dict[str, float]:
    """TPS709 IN sin carga (toda la corriente por el zener) con el zener en
    su V_Z maximo y la pendiente Z_ZT por encima de I_ZT."""
    r = valor("R64") if r64_ohm is None else r64_ohm
    vz, izt, zzt = ZENER_BZT52[filas()["D2"]["value"]]
    if v_entrada_v <= vz:
        return {"v_in_v": v_entrada_v, "i_z_a": 0.0, "p_z_w": 0.0}
    v = (vz - zzt * izt + zzt * v_entrada_v / r) / (1.0 + zzt / r)
    if (v_entrada_v - v) / r < izt:
        v = vz
    i_z = (v_entrada_v - v) / r
    return {"v_in_v": v, "i_z_a": i_z, "p_z_w": v * i_z}


def escalon_lc(*, v_fallo_v: float = 36.0,
               v_disparo_v: float = V_DISPARO_MAX_U1_V,
               t_corte_s: float = T_CORTE_OVP_MAX_S,
               sensa_antes_del_lc: bool = True,
               con_efuse: bool = True,
               con_tvs: bool = True,
               con_disparo_rapido: bool = True,
               t_disparo_rapido_s: float = T_FASTTRIP_MAX_S,
               i_disparo_rapido_a: float | None = None,
               peor_caso: bool = True) -> dict[str, float]:
    """Integracion RK4 del escalon de fallo sobre el LC amortiguado de U1 (#334).

    U19 abre por lo primero que llegue: el OVP (`t_corte_s` desde que ve el
    disparo), el disparo rapido (`t_disparo_rapido_s` desde que i_L pasa de
    3 x I(OL)) o el corto franco (1 us desde I(SCP)).

    `peor_caso`: arranca en el maximo sano en vacio y sin carga, con L2, C3 y
    C1 en el borde bajo de su tolerancia. Sin el, el banco: 15,50 V, la rama
    cargada y las piezas en su valor central.

    Estado:
      i_L: corriente en L2 (A)
      v_1: tension en el condensador principal C3 = entrada de U1 (V)
      v_d: tension en el condensador de amortiguacion C1 (V)
    """
    if peor_caso:
        v0, i_l, i_carga = v_sano_max_u1_v(), 0.0, 0.0
        c_lc, c_damp = (C_LC_F * (1.0 - TOL_ELECTROLITICO_FRAC),
                        C_DAMP_F * (1.0 - TOL_ELECTROLITICO_FRAC))
    else:
        v0 = 15.50
        i_l = i_carga = _margen().corriente_rama_a("U1")   # D-F1 + Iq de U1 (#343)
        c_lc, c_damp = C_LC_F, C_DAMP_F
    i_rapido = i_fasttrip_max_u19_a() if i_disparo_rapido_a is None else i_disparo_rapido_a
    v_1 = v0 - i_l * R_SERIE_LC_OHM
    v_d = v_1

    dt = 0.05e-6
    t_fin = 250.0e-6
    n_pasos = int(t_fin / dt)

    # Instante en que U19 abre: el minimo de los tres disparos que hayan saltado.
    t_abre = float("inf")
    if con_efuse and sensa_antes_del_lc and v_fallo_v >= v_disparo_v:
        t_abre = t_corte_s
    ovp_visto = rapido_visto = scp_visto = False
    v_pico = v_1
    i_max = i_l
    e_tvs_j = 0.0

    i_corte = None

    def derivadas(il: float, v1: float, vd: float, cortado: bool) -> tuple[float, float, float, float]:
        l_h = l2_h(il, tol=peor_caso)
        if cortado:
            # El eFuse abrio: si i_L > 0, el Schottky D19 de OUT a GNDA descarga
            # la bobina contra v1; si i_L <= 0, la bobina queda en 0 A. Con
            # V_F = 0 la bobina se descarga MAS DESPACIO que con el diodo real
            # y mete mas carga en C3: cota pesimista para el pico.
            if il <= 0.0:
                dil = 0.0
            else:
                dil = (-v1 - il * R_SERIE_LC_OHM) / l_h
        else:
            dil = (v_fallo_v - v1 - il * R_SERIE_LC_OHM) / l_h

        i_damp = (v1 - vd) / R_DAMP_OHM
        i_tvs = 0.0
        if con_tvs and v1 > V_BR_SMBJ16A_V:
            i_tvs = (v1 - V_BR_SMBJ16A_V) / R_DIN_SMBJ16A_OHM

        dv1 = (il - i_carga - i_damp - i_tvs) / c_lc
        dvd = i_damp / c_damp
        p_tvs = v1 * i_tvs
        return dil, dv1, dvd, p_tvs

    for paso in range(n_pasos):
        t = paso * dt
        if con_efuse:
            if not sensa_antes_del_lc and not ovp_visto and v_1 >= v_disparo_v:
                ovp_visto, t_abre = True, min(t_abre, t + t_corte_s)
            if con_disparo_rapido and not rapido_visto and i_l >= i_rapido:
                rapido_visto, t_abre = True, min(t_abre, t + t_disparo_rapido_s)
            if con_disparo_rapido and not scp_visto and i_l >= I_SCP_TPS2663_A:
                scp_visto, t_abre = True, min(t_abre, t + T_SCP_MAX_S)
        cortado = t >= t_abre
        if cortado and i_corte is None:
            i_corte = i_l
        if cortado and i_l < 0.0:
            i_l = 0.0

        k1_i, k1_v1, k1_vd, p_tvs = derivadas(i_l, v_1, v_d, cortado)
        k2_i, k2_v1, k2_vd, _ = derivadas(
            max(0.0, i_l + 0.5 * dt * k1_i) if cortado else i_l + 0.5 * dt * k1_i,
            v_1 + 0.5 * dt * k1_v1, v_d + 0.5 * dt * k1_vd, cortado)
        k3_i, k3_v1, k3_vd, _ = derivadas(
            max(0.0, i_l + 0.5 * dt * k2_i) if cortado else i_l + 0.5 * dt * k2_i,
            v_1 + 0.5 * dt * k2_v1, v_d + 0.5 * dt * k2_vd, cortado)
        k4_i, k4_v1, k4_vd, _ = derivadas(
            max(0.0, i_l + dt * k3_i) if cortado else i_l + dt * k3_i,
            v_1 + dt * k3_v1, v_d + dt * k3_vd, cortado)

        i_l += (dt / 6.0) * (k1_i + 2.0 * k2_i + 2.0 * k3_i + k4_i)
        if cortado and i_l < 0.0:
            i_l = 0.0
        v_1 += (dt / 6.0) * (k1_v1 + 2.0 * k2_v1 + 2.0 * k3_v1 + k4_v1)
        v_d += (dt / 6.0) * (k1_vd + 2.0 * k2_vd + 2.0 * k3_vd + k4_vd)

        if v_1 > v_pico:
            v_pico = v_1
        i_max = max(i_max, i_l)
        e_tvs_j += p_tvs * dt

    return {"v_pico_v": v_pico, "energia_tvs_mj": e_tvs_j * 1e3,
            "i_rueda_libre_a": max(0.0, i_corte or 0.0), "i_max_a": i_max,
            "t_abre_us": t_abre * 1e6}


I_FSM_SS34_A = 80.0                    # mdd_ss34.pdf p. 1 (8,3 ms; el pulso de L2 dura us)

P_BASE: dict[str, float] = {
    "t_corte_us": T_CORTE_OVP_MAX_S * 1e6,
    "t_disparo_rapido_us": T_FASTTRIP_MAX_S * 1e6,
    "i_disparo_rapido_a": None,             # None: el de R34 (i_fasttrip_max_u19_a)
    "v_disparo_u1_v": V_DISPARO_MAX_U1_V,
    "i_mantenimiento_scr_a": I_MANTENIMIENTO_BT151_A,
    "r64_ohm": valor("R64"),
    "i_gt_max_a": I_GT_MAX_BT151_A,
    "factor_despeje_i2t": FACTOR_DESPEJE_I2T,
}


def _guarda_u18(p: dict[str, float]) -> None:
    r = u18_peor(V_C_SMBJ26CA_V, p["r64_ohm"])
    assert r["v_in_v"] <= V_IN_MAX_U18_V, (
        f"U18 IN sube a {r['v_in_v']:.2f} V > {V_IN_MAX_U18_V:.0f} V con D1 en {V_C_SMBJ26CA_V} V")
    c = u18_peor(V_BR_MAX_SMBJ26CA_V, p["r64_ohm"])
    assert c["p_z_w"] <= P_D_BZT52_W, (
        f"D2 disipa {c['p_z_w'] * 1e3:.0f} mW continuos > {P_D_BZT52_W * 1e3:.0f} mW "
        f"con la entrada en {V_BR_MAX_SMBJ26CA_V} V")


def _guarda_puerta_scr(p: dict[str, float]) -> None:
    for riel in RACK_RIELES:
        c = corriente_puerta_a(riel, p["i_gt_max_a"])
        assert c["r_gk_ohm"] <= R_GK_DVDT_OHM, (
            f"{riel}: R_GK = {c['r_gk_ohm']:.0f} ohm; el dV/dt de 200 V/us pide <= 100")
        assert c["da_a"] >= c["pide_a"], (
            f"puerta corta en {riel}: el PNP da {c['da_a'] * 1e3:.1f} mA y la puerta "
            f"pide {c['pide_a'] * 1e3:.1f} mA")


def _guarda_i2t(p: dict[str, float]) -> None:
    for riel, piezas in PIEZAS_CROWBAR.items():
        i2t = I2T_FUSION_A2S[filas()[piezas[-1]]["mpn"]] * p["factor_despeje_i2t"]
        assert i2t < I2T_BT151_A2S, (
            f"el fusible {piezas[-1]} de {riel} deja pasar {i2t:.1f} A2s >= "
            f"{I2T_BT151_A2S:.0f} A2s del SCR")


def _guarda_u1_rk4(p: dict[str, float]) -> None:
    assert V_DISPARO_MIN_U1_V > v_sano_max_u1_v(), (
        f"disparo bajo {V_DISPARO_MIN_U1_V:.2f} V <= sano max {v_sano_max_u1_v():.2f} V")
    res = escalon_lc(
        v_fallo_v=36.0,
        v_disparo_v=p["v_disparo_u1_v"],
        t_corte_s=p["t_corte_us"] * 1e-6,
        sensa_antes_del_lc=True,
        con_efuse=True,
        con_tvs=True,
        t_disparo_rapido_s=p["t_disparo_rapido_us"] * 1e-6,
        i_disparo_rapido_a=p["i_disparo_rapido_a"],
    )
    assert res["v_pico_v"] <= V_ABSMAX_U1_V, (
        f"#334: U1 supera absmax: pico {res['v_pico_v']:.2f} V > {V_ABSMAX_U1_V:.1f} V")
    assert res["i_max_a"] <= CURVA_L2_A_UH[-1][0], (
        f"#334: L2 llega a {res['i_max_a']:.1f} A, fuera de la curva L-I publicada "
        f"(hasta {CURVA_L2_A_UH[-1][0]:.0f} A): el pico no vale")


def _guarda_enganche_scr(p: dict[str, float]) -> None:
    peor_pliegue = min(d["i_pliegue_min_a"] for d in RACK_RIELES.values())
    assert p["i_mantenimiento_scr_a"] < peor_pliegue, (
        f"el crowbar se suelta: I_H={p['i_mantenimiento_scr_a']:.2f} A >= "
        f"pliegue={peor_pliegue:.2f} A")


def leer_csv() -> list[dict[str, str]]:
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def demo() -> int:
    print("check_absmax v5: modelo RK4 de #334 (TPS26631 + SMBJ16A) y crowbars D-F6\n")
    tabla = leer_csv()
    filas_bom = filas()

    assert filas_bom["L2"]["mpn"] == MPN_L2, (
        f"L2 es {filas_bom['L2']['mpn']} y la curva L-I del modelo es de la {MPN_L2}")
    assert abs(CURVA_L2_A_UH[0][1] * 1e-6 - valor("L2")) <= 0.05 * valor("L2"), (
        "la curva de L2 no arranca en el valor de la BOM")
    con_tope = escalon_lc(v_fallo_v=36.0)
    banco = escalon_lc(v_fallo_v=36.0, peor_caso=False)
    sin_tope = escalon_lc(v_fallo_v=36.0, con_efuse=False, con_tvs=False)
    sin_rapido = escalon_lc(v_fallo_v=36.0, con_tvs=False, con_disparo_rapido=False)
    post_lc = escalon_lc(v_fallo_v=36.0, sensa_antes_del_lc=False, con_tvs=False,
                         con_disparo_rapido=False)

    print("  1. Simulacion RK4 de #334 (escalon de 36 V sobre el filtro LC de U1):")
    print(f"    maximo sano en vacio:             {v_sano_max_u1_v():.3f} V")
    print(f"    banda de disparo TPS26631 (0,1%): {V_DISPARO_MIN_U1_V:.2f} .. {V_DISPARO_MAX_U1_V:.2f} V "
          f"(nom {V_DISPARO_NOM_U1_V:.2f} V)")
    print(f"    disparo rapido de U19:            {i_fasttrip_max_u19_a():.2f} A max (3 x I(OL) de R34), "
          f"<= {T_FASTTRIP_MAX_S * 1e6:.1f} us")
    print(f"    [verde] peor caso (sano max, sin carga, L2/C3/C1 -20 %): pico = "
          f"{con_tope['v_pico_v']:.2f} V <= {V_ABSMAX_U1_V:.1f} V; L2 llega a "
          f"{con_tope['i_max_a']:.1f} A (curva hasta {CURVA_L2_A_UH[-1][0]:.0f} A); U19 abre a "
          f"{con_tope['t_abre_us']:.1f} us (energia TVS {con_tope['energia_tvs_mj']:.2f} mJ)")
    print(f"    banco (15,50 V, rama cargada, piezas centrales): pico = {banco['v_pico_v']:.2f} V")
    # Un mutante es rojo si U1 pasa de 20 V o si L2 sale de su curva: fuera de
    # ella el modelo sostiene la inductancia de 12 A y su pico se queda corto.
    i_curva = CURVA_L2_A_UH[-1][0]
    for nombre, r in (("SIN eFuse (puente 36 V)                      ", sin_tope),
                      ("MUTANTE sin disparo rapido (OVP antes del LC)  ", sin_rapido),
                      ("MUTANTE sin disparo rapido y OVP DESPUES del LC", post_lc)):
        assert r["v_pico_v"] > V_ABSMAX_U1_V or r["i_max_a"] > i_curva, (
            f"{nombre.strip()} sale verde: el tope no depende de lo que el mutante quita")
        print(f"    [rojo ] {nombre}: pico = {r['v_pico_v']:5.2f} V, L2 a {r['i_max_a']:5.1f} A "
              f"(rojo con > {V_ABSMAX_U1_V:.1f} V o > {i_curva:.0f} A)")
    print()

    _guarda_u1_rk4(dict(P_BASE))

    print("  2. Ventanas de disparo en rack (D-F6: BT151-500R + TL431BI):")
    for riel, d in RACK_RIELES.items():
        bajo, alto = d["banda_v"]
        sano = sano_max_v(riel)
        holgura_baja = bajo - sano
        holgura_alta = d["victima_max_v"] - alto
        assert holgura_baja > 0.0, f"{riel}: disparo bajo {bajo} <= sano {sano}"
        assert holgura_alta >= 0.0, f"{riel}: disparo alto {alto} > victima {d['victima_max_v']}"
        print(f"    {riel:<10} sano<={sano:.2f}V | "
              f"disparo {bajo:.2f}..{alto:.2f}V | "
              f"victima<={d['victima_max_v']:.2f}V | "
              f"I_pliegue={d['i_pliegue_min_a']:.2f}A >> I_H={I_MANTENIMIENTO_BT151_A*1000:.0f}mA")

    print("\n  3. U19 abre: la corriente de L2 vuelve por D19 (SS34):")
    assert "D19" in filas_bom, "el modelo descarga L2 por D19 y D19 no esta en bom.csv"
    i_rueda = con_tope["i_rueda_libre_a"]
    assert i_rueda < I_FSM_SS34_A, f"D19 lleva {i_rueda:.1f} A >= I_FSM {I_FSM_SS34_A:.0f} A"
    print(f"    [verde] pico en D19 al cortar: {i_rueda:.1f} A < I_FSM {I_FSM_SS34_A:.0f} A")

    print("\n  4. U18 (TPS709) tras R64 + D2:")
    _guarda_u18(dict(P_BASE))
    pico_u18 = u18_peor(V_C_SMBJ26CA_V)
    cont_u18 = u18_peor(V_BR_MAX_SMBJ26CA_V)
    print(f"    [verde] con D1 en {V_C_SMBJ26CA_V} V: U18 IN = {pico_u18['v_in_v']:.2f} V "
          f"<= {V_IN_MAX_U18_V:.0f} V (D2 {filas_bom['D2']['value']}, R64 {valor('R64'):.0f} ohm)")
    print(f"    [verde] a {V_BR_MAX_SMBJ26CA_V} V sostenidos: D2 disipa "
          f"{cont_u18['p_z_w'] * 1e3:.0f} mW <= {P_D_BZT52_W * 1e3:.0f} mW")

    print("\n  5. D-F6 por dentro (puerta y fusible):")
    _guarda_puerta_scr(dict(P_BASE))
    _guarda_i2t(dict(P_BASE))
    for riel, piezas in PIEZAS_CROWBAR.items():
        c = corriente_puerta_a(riel)
        i2t = I2T_FUSION_A2S[filas_bom[piezas[-1]]["mpn"]] * FACTOR_DESPEJE_I2T
        print(f"    [verde] {riel:<10} PNP da {c['da_a'] * 1e3:5.1f} mA >= puerta "
              f"{c['pide_a'] * 1e3:4.1f} mA (R_GK {c['r_gk_ohm']:.0f} ohm) | "
              f"{piezas[-1]} <= {i2t:.1f} A2s < {I2T_BT151_A2S:.0f} A2s")

    print("\n  6. Matriz completa de absmax.csv (cada fila contra su modelo):")
    v_max_u2 = 1.220 * (1 + (valor("R7") + valor("RV3")) / valor("R8"))   # lt3015-rev-b.pdf p. 1
    esperados = {
        "U1 ": con_tope["v_pico_v"],
        "U2 ": V_OVP_MAX_THN20_V,
        "U4,U5 ": con_tope["v_pico_v"],
        "U6,U7 ": v_max_u2,
        "U18 ": pico_u18["v_in_v"],
        "Cerebro digital +5V": V_OVP_MAX_URB_V,
    }
    for victima, riel in {"Invitados rack +12V": "rack+12", "Invitados rack -12V": "rack-12",
                          "Invitados rack +5V": "rack+5"}.items():
        esperados[victima] = RACK_RIELES[riel]["banda_v"][1]
    for f in tabla:
        clave = next((k for k in esperados if f["victima"].startswith(k)), None)
        assert clave is not None, f"absmax.csv: '{f['victima']}' no tiene modelo que la calcule"
        if clave == "U1 ":
            assert abs(float(f["v_pico_sin_tope_v"]) - sin_tope["v_pico_v"]) <= 0.05, (
                f"absmax.csv dice {f['v_pico_sin_tope_v']} V sin tope en U1 y el modelo "
                f"da {sin_tope['v_pico_v']:.2f} V: actualiza la fila")
        assert abs(float(f["v_pico_con_tope_v"]) - esperados[clave]) <= 0.05, (
            f"absmax.csv dice {f['v_pico_con_tope_v']} V en {f['victima']} y el modelo "
            f"da {esperados[clave]:.2f} V: actualiza la fila")
        v_con = float(f["v_pico_con_tope_v"])
        v_max = float(f["v_absmax_v"])
        assert v_con <= v_max, f"{f['victima']} supera absmax: {v_con} > {v_max}"
        print(f"    [verde] {f['victima']:<24} ve {v_con:>5.2f} V <= {v_max:>5.2f} V "
              f"(margen +{v_max - v_con:.2f} V)")

    _guarda_u1_rk4(dict(P_BASE))
    _guarda_enganche_scr(dict(P_BASE))
    # Canarios de #334 sobre el disparo rapido, que es el que corta: su retardo
    # y su umbral (subir R34 de corriente lo sube). El OVP ya no tiene canario:
    # con el disparo rapido llegando antes, su retardo no mueve el pico.
    t_rapido_us = borde_rojo(_guarda_u1_rk4, dict(P_BASE), "t_disparo_rapido_us",
                             T_FASTTRIP_MAX_S * 1e6, 100.0, "#334:")
    i_rapido_a = borde_rojo(_guarda_u1_rk4, dict(P_BASE), "i_disparo_rapido_a",
                            i_fasttrip_max_u19_a(), 40.0, "#334:")
    ih_max = borde_rojo(_guarda_enganche_scr, dict(P_BASE), "i_mantenimiento_scr_a",
                        0.040, 5.0, "el crowbar se suelta")
    r64_v = borde_rojo(_guarda_u18, dict(P_BASE), "r64_ohm", valor("R64"), 1.0, "U18 IN")
    r64_p = borde_rojo(_guarda_u18, dict(P_BASE), "r64_ohm", valor("R64"), 250.0, "D2 disipa")
    igt = borde_rojo(_guarda_puerta_scr, dict(P_BASE), "i_gt_max_a", I_GT_MAX_BT151_A, 1.0,
                     "puerta corta")
    despeje = borde_rojo(_guarda_i2t, dict(P_BASE), "factor_despeje_i2t", FACTOR_DESPEJE_I2T,
                         1000.0, "deja pasar")
    print(f"\n  canario #334: si el disparo rapido de U19 tarda > {t_rapido_us:.1f} us "
          f"(la hoja garantiza <= {T_FASTTRIP_MAX_S * 1e6:.1f}), o salta por encima de "
          f"{i_rapido_a:.1f} A (hoy {i_fasttrip_max_u19_a():.2f}), U1 o L2 salen de su limite")
    print(f"  canario D-F6: con I_H > {ih_max:.2f} A el crowbar se soltaria "
          f"(el BT151-500R pide <= 0,04 A)")
    print(f"  canario U18: R64 < {r64_v:.0f} ohm lleva U18 IN por encima de 30 V, y "
          f"R64 < {r64_p:.0f} ohm quema D2")
    print(f"  canario D-F6: con I_GT > {igt * 1e3:.0f} mA algun PNP no llega a la puerta")
    print(f"  canario D-F6: un despeje > {despeje:.0f} x la fusion pasaria el I2t del SCR")

    print("\n  FUERA DE CONTRATO (fallo simple, #475):")
    print(f"    - fallo doble THN- en OVP + U2 en corto: U6/U7 verian {V_OVP_MAX_THN20_V:.1f} V "
          f"contra 22 V; se acepta sin TVS ni tope")
    print(f"    - fallo doble THN+ en OVP + U1 en corto: {con_tope['v_pico_v']:.2f} V en la cascada, "
          f"cubierto por M3 (fila U4,U5), no por requisito")

    print("\n  REQUISITO al modulo 2 (T19, junta de piezas v5 sec. 4.5): el +5 V digital no lleva "
          f"crowbar, y su entrada de 5 V aguanta {V_OVP_MAX_URB_V:.2f} V, el OVP maximo del URB")

    print("\n  LO QUE NO CUBRE:")
    print("    - la curva L-I de L2 es tipica (bourns_srp1265a.pdf p. 3): leida, bajada 0,5 uH y "
          "con el -20 % encima; mas alla de 12 A no hay curva")
    print("    - OUT de U19 a -V_F de D19 (<= 0,55 V a 3 A) durante el corte; la hoja da "
          "-0,3 V en DC y pide el Schottky")
    print("    - pendiente del riel de rack en enchufe en caliente (el SCR aguanta 200 V/us)")
    sin_transitorio = [r for r, h in SANO_HOJA.items() if h[4] is None]
    print(f"    - la desviacion transitoria de {', '.join(sin_transitorio)}: la hoja del "
          "THN 30-2422WI no la da (pregunta a TRACO); el maximo sano no la cuenta")
    print("    - un crowbar disparado no llega al MSP430: el SCR sigue conduciendo el pliegue; "
          "se mide en el bring-up (paso 8, crowbar_*, #476)")

    print("\nOK: check_absmax.py v5 (#334, #340 y T18..T21 en verde)")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
