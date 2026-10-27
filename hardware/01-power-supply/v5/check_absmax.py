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
         * contra un alivio de carga del THN, HUECO (`_guarda_ovp_sobreimpulso`): el
           sobreimpulso tipico (`~0,19 V`, `traco_thn20wi_characteristic_curves.pdf`
           p. 8) cabe con lo que la hoja garantiza y no en la envolvente de `2,5 %` de
           `margen_budget.py`; TRACO no da maximo;
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
       El TVS **SMBJ16A** (`D10`, `bourns_smbj.pdf` p. 2: `V_WM = 16,0 V`,
       `V_BR = 17,8..19,7 V`) en `U1 IN` va SIN MONTAR (junta de piezas v5
       sec. 4.6): con el tope el pico es de `17,40 V` y no llega a su `V_BR`
       minimo, asi que no conduce en ningun caso modelado. El modelo lee de
       `bom.csv` si esta montado (`montada("D10")`), y `_guarda_d10_sobra()` es
       la que respalda que sobra.

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
       minimo) y `+5 V` (`THN 20-2411WI`, `traco_thn20wi.pdf` p. 2: `125..190 %`
       de `4 A`, `5 A` el minimo), la corriente de pliegue supera en mas de 35
       veces los `40 mA` de mantenimiento del `BT151-500R`.

  4. **Supervivencia del `+5 V` digital aislado (T19, `H-CENSO-DIGITAL`):**
     - El `Mornsun URB2405YMD-20WR3` (`mornsun_urb_ymd20wr3.pdf` p. 2) declara
       OVP entre `110 %` y `160 %` (`5,50..8,00 V`). El digital no lleva
       crowbar (junta de piezas v5 sec. 4.5): `SCR4` y su disparo quedan sin
       montar, y la entrada de 5 V del modulo 2 aguanta `8,00 V` como
       REQUISITO, igual que en la v4. Con el URB declarando `+-8 %` de
       desviacion ante un escalon de carga del 25 % (p. 2), el disparo de
       `5,66 V` nominal saltaba dentro del transitorio sano.

  5. **`U18` (`TPS709`, el LDO del supervisor M5):** `R64` y el zener `D2`
     sujetan su entrada cuando `D1` (`SMBJ33CA`) recorta un transitorio a
     `53,3 V`.

  6. **D-F6 por dentro:** la corriente de puerta que el PNP puede dar con
     `R_GK` en el disparo mas bajo, y el `I^2t` de los fusibles contra el del SCR.

  7. **El `+5 V` de rack y `+5V_AUX` (#491):**
     - `PS3` es un `THN 20-2411WI`, flyback aislado (`traco_thn20wi.pdf` p. 3).
       El buck no aislado que montaba (`K7805T-1000R3`) con la entrada puenteada
       a la salida ponia el riel en `6,15..7,23 V` (segun una bobina que su hoja
       no publica) o en `21,8 V` (sin ella) antes del disparo, contra los `6,0 V`
       de los INA226 y del ISO1541. En el flyback la entrada y la salida solo se
       tocan por la barrera de `1600 VDC`: ese corto es el camino menos probable
       de la propuesta de piezas sec. 9.1, fuera del contrato. La guarda exige
       que `PS3` sea un modulo aislado (`AISLADOS`).
     - Lo que si entra en el contrato es su FUGA: con el lazo roto el THN empuja
       hasta su limite (`190 %` de `4 A`, p. 2) y el riel sube a `I / C`. Con
       `C16` sola eran `0,35 V/us`, y los `2 us` tipicos de `t_gt`
       (`nxp-bt151-500r.pdf` p. 6, sin maximo) llevaban `+5V_AUX` a `6,55 V`.
       `C39` (`1000 uF` en su `-20 %`) lo deja en `0,0095 V/us`. El pico sale en
       demo() desde el borde alto de la banda de `SCR3`, y el canario dice
       cuanto retardo aguanta.
     - Disparado `SCR3`, el THN da su limite (`>= 5 A`) y `F4` (`2 A`) abre.
       `+5V_AUX` cuelga de `+5V_FUSED_RACK`, despues de `F4` (`check_netlist.py`):
       se apaga con el en vez de quedarse con el OVP del THN (`112..164 %`, hasta
       `8,20 V`, p. 2). Con ella se apagan la telemetria, el `+5 V` auxiliar del
       modulo 2 (`J6`) y el pull-up de `SHDN_CASCADE`, que para la cascada.

  8. **`D1` (`SMBJ33CA`) y todo lo que cuelga de `+24V_RAW` (junta de piezas v5
     sec. 3.8, #494; retorno por `Q7`, P7 (d)):**
     - `V_BR` minimo `36,7 V` contra el OVP del TE90 (`130..150 %` de 24 V =
       `36,0 V`, `ae-TE90-datasheet.pdf` p. 2) y el de `U16` (`32,7 V` nominal,
       de `R12`, `R13` y `R14`): `D1` no conduce con el ladrillo en su OVP ni
       antes de que `U16` corte.
     - Con `V_C = 53,3 V` a `I_PP = 11,3 A` (`bourns_smbj.pdf` p. 2), todo lo
       que esta entre `+24V_RAW` y `GND24` lo aguanta: `C10` (su tension sale
       de `bom.csv`), `VS` del `LM74502` (`65 V`, `lm74502.pdf` p. 4), `IN` de
       `U16` (`67 V`, `tps2663.pdf` p. 5) y el `VDS` de `Q2` y `Q7` (`60 V`,
       `csd18534q5a.pdf` p. 1 y `BVDSS` de p. 3).
     - La puerta de `Q7`: el zener `D20` (`BZT52C15`) fija `VGS` en su `V_Z`
       maximo (`15,6 V`, `diodes_bzt52.pdf` p. 2) contra los `+-20 V` de
       `csd18534q5a.pdf` p. 1.
     - La hoja de `D1` que se cita es la de Bourns (valores JEDEC); la de
       Littelfuse (la pieza que se compra, C83325) no esta en el arbol, y LCSC
       lista las mismas cifras.

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
  * La fuga de `PS3` como fuente de corriente a su limite maximo es una cota:
    la hoja no dice como se desboca. Y `t_gt` solo tiene tipico (`2 us`): el
    canario imprime cuanto retardo aguanta `+5V_AUX`.
  * La descarga de `C39` por `SCR3` al disparar: la hoja del BT151 pide
    `dI_T/dt <= 50 A/us` (p. 3), y la pendiente la pone la inductancia del lazo
    `C39 - F4 - R30 - SCR3`, que no esta medida.
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

from bom_valores import filas, montada, tension_v, valor  # noqa: E402
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


def v_sano_max_hoja_u1_v() -> float:
    """Maximo sano con SOLO lo que la hoja garantiza (exactitud, linea, carga y
    0,02 %/K): la cota OPTIMISTA, sin la tolerancia del recorte por Trim que la
    hoja no da y que la envolvente de 2,5 % de margen_budget.py estima. Sin rizado:
    el del pin de U19 es el del modulo sin LC (75 mVpp tipico, p. 2) y no se sabe
    si el comparador lo sigue."""
    mb = _margen()
    return mb.V_NOM_V5 * (1.0 + TOL_HOJA_THN20_FRAC + mb.TEMPCO_PPM_K_V5 * 1e-6 * mb.DELTA_T_K_V5)

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
# THN 20-2411WI (PS3, +5 V de rack): OVP 112..164 % de 5 V y limitacion de
# corriente 125..190 % de 4 A (traco_thn20wi.pdf p. 2).
V_OVP_MAX_PS3_V = 1.64 * 5.0
I_LIMITE_MIN_PS3_A = 1.25 * 4.0
I_LIMITE_MAX_PS3_A = 1.90 * 4.0
# Los convertidores aislados de la v5 (hojas p. 1). PS3 tiene que ser uno (#491).
AISLADOS = {"THN 20-2411WI", "THN 20-2413WI", "THN 30-2422WI", "URB2405YMD-20WR3"}
# +5V_AUX: VS del INA226 (ina226.pdf p. 4) y VCC1 del ISO1541 (iso1541.pdf p. 6).
V_ABSMAX_AUX_V = 6.0
V_OVPR_NOM_V = 1.200                   # tps2663.pdf p. 6: V(OVPR) 1,176..1,224 V
V_DISPARO_NOM_U1_V = V_OVPR_NOM_V * (1.0 + valor("R35") / valor("R36"))
TOL_OVPR_TPS26631_FRAC = 0.020         # tps2663.pdf p. 6: 1,176..1,224 V (+-2,0 %)
TOL_DIVISOR_01PCT_FRAC = 0.002         # dos resistencias de 0,1 %
V_DISPARO_MIN_U1_V = V_DISPARO_NOM_U1_V * (1.0 - TOL_OVPR_TPS26631_FRAC - TOL_DIVISOR_01PCT_FRAC)
V_DISPARO_MAX_U1_V = V_DISPARO_NOM_U1_V * (1.0 + TOL_OVPR_TPS26631_FRAC + TOL_DIVISOR_01PCT_FRAC)
T_CORTE_OVP_MAX_S = 14.0e-6            # tps2663.pdf p. 8: 8,5 us min, 11 us nom, 14 us max
# Sobreimpulso del THN 20-2413WI al soltar carga: lectura de la figura "Transient
# Response to Dynamic Load Change (25%)" (100 mV/div, 100 us/div,
# traco_thn20wi_characteristic_curves.pdf p. 8): la traza oscura sube 0,19 V
# sobre el techo del rizado en reposo (el sombreado de persistencia, 0,22 V).
# ESTIMADO: lectura de figura (+-0,02 V), a 15,0 V de salida y con el condensador
# de salida de la hoja (1 uF || 10 uF, traco_thn20wi.pdf p. 2); +15V5_RAW no lleva
# ninguno. HUECO: la hoja (p. 2: solo "Response Time 250 us typ.") y las curvas no
# dan un maximo; se le pidio a TRACO.
V_SOBREIMPULSO_TIP_THN20_V = 0.19
V_SOBREIMPULSO_MAX_THN20_V: float | None = None
# Lo que la hoja SI garantiza de la salida simple de 15 V (traco_thn20wi.pdf p. 2):
# exactitud +-1 %, regulacion de linea 0,2 % y de carga 0,2 %, maximas.
TOL_HOJA_THN20_FRAC = 0.010 + 0.002 + 0.002
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
V_BR_MIN_SMBJ16A_V = 17.80             # bourns_smbj.pdf p. 2: V_BR minimo, con el que D10 conduce primero
R_DIN_SMBJ16A_OHM = 0.35               # pendiente dinamica del SMBJ16A en conduccion
# D10 (SMBJ16A) va SIN MONTAR (junta de piezas v5 sec. 4.6): el modelo lo lee
# de bom.csv y no lo supone.
D10_MONTADO = montada("D10")

# --- Parametros de D-F6 (NXP BT151-500R + TI TL431BI) -----------------------
I_MANTENIMIENTO_BT151_A = 0.040        # nxp-bt151-500r.pdf p. 2: I_H max 40 mA
I2T_BT151_A2S = 72.0                   # nxp-bt151-500r.pdf p. 2: I^2t = 72 A^2s
I_GT_MAX_BT151_A = 0.015               # nxp-bt151-500r.pdf p. 6
V_GT_MAX_BT151_V = 1.5                 # nxp-bt151-500r.pdf p. 6
T_GT_TIP_BT151_S = 2.0e-6              # nxp-bt151-500r.pdf p. 6: t_gt 2 us tipico, sin maximo
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
    # traco_thn20wi.pdf p. 2 (THN 20-2411WI, salida simple): exactitud 1 %,
    # linea 0,2 %, carga 0,2 %, 0,02 %/K; rizado 75 mVpp TIPICO. Del transitorio
    # solo da el tiempo de respuesta, como el THN 30.
    "rack+5": (5.0, (0.01, 0.002, 0.002), 0.0002, 0.075, None),
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
    # La victima mas baja del +5 V de rack es +5V_AUX (6,0 V), no los invitados.
    "rack+5":  {"ovp_max_v": V_OVP_MAX_PS3_V, "victima_max_v": V_ABSMAX_AUX_V,
                "disparo_v": _disparo("R49", "R50"), "banda_v": banda_disparo_v("R49", "R50"),
                "i_pliegue_min_a": I_LIMITE_MIN_PS3_A},
}


def fuga_ps3(c_f: float | None = None, t_s: float = T_GT_TIP_BT151_S) -> float:
    """Pico del +5 V de rack, y de +5V_AUX que cuelga detras, si PS3 se
    desboca: desde el borde alto de la banda de SCR3, el limite maximo del THN
    cargando C39 en su -20 % durante el retardo del disparo. C16 y los
    invitados no se cuentan, y las caidas en F4, R30 y R20 tampoco: cota
    pesimista."""
    c = valor("C39") * (1.0 - TOL_ELECTROLITICO_FRAC) if c_f is None else c_f
    return RACK_RIELES["rack+5"]["banda_v"][1] + I_LIMITE_MAX_PS3_A * t_s / c


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
# D1 = SMBJ33CA (Littelfuse C83325). Las cifras son de la hoja de BOURNS, la
# unica en el arbol (bourns_smbj.pdf p. 2, JEDEC, bidireccional "SMBJ33CA"); LCSC
# lista las mismas para la Littelfuse. Si la de Littelfuse difiriera, mandaria ella.
MPN_D1 = "SMBJ33CA"
V_RWM_SMBJ33CA_V = 33.0                # bourns_smbj.pdf p. 2: V_RWM
V_BR_MIN_SMBJ33CA_V = 36.7             # bourns_smbj.pdf p. 2: V_BR a 1 mA, minimo
V_BR_MAX_SMBJ33CA_V = 40.6             # bourns_smbj.pdf p. 2: V_BR a 1 mA, maximo: por debajo D1 casi no conduce
V_C_SMBJ33CA_V = 53.3                  # bourns_smbj.pdf p. 2: V_C a I_PP = 11,3 A (10/1000 us)
V_IN_MAX_U18_V = 30.0                  # tps709.pdf p. 4: maximo de operacion
V_ABSMAX_U18_V = 32.0                  # tps709.pdf p. 4
# diodes_bzt52.pdf p. 2: (V_Z max, I_ZT, Z_ZT max) por valor; P_D 370 mW a 25 C.
ZENER_BZT52 = {"BZT52C15": (15.6, 5e-3, 30.0), "BZT52C18": (19.1, 5e-3, 45.0), "BZT52C20": (21.2, 5e-3, 55.0),
               "BZT52C22": (23.3, 5e-3, 55.0), "BZT52C24": (25.6, 5e-3, 70.0),
               "BZT52C27": (28.9, 2e-3, 80.0), "BZT52C30": (32.0, 2e-3, 80.0)}
P_D_BZT52_W = 0.370

# --- lo que cuelga de +24V_RAW con D1 en V_C (D1, Q7 y su puerta) ------------
V_OVP_MAX_TE90_V = 1.50 * 24.0         # ae-TE90-datasheet.pdf p. 2: OVP 130..150 % de la salida
V_LADRILLO_MAX_V = 24.0 * 1.05         # salida nominal +5 % (ladrillo_budget.TOL_LADRILLO): lo mas alto en servicio
V_ABSMAX_VS_LM74502_V = 65.0           # lm74502.pdf p. 4: VS to GND -65..65 V
V_ABSMAX_IN_TPS2663_V = 67.0           # tps2663.pdf p. 5: IN, OUT... -0,3..67 V
MPN_Q2_Q7 = "CSD18534Q5A"
V_DS_MAX_CSD18534_V = 60.0             # csd18534q5a.pdf p. 1: VDS 60 V (BVDSS 60 V min, p. 3)
V_GS_MAX_CSD18534_V = 20.0             # csd18534q5a.pdf p. 1: VGS +-20 V


def v_ovp_u16_v(con_tolerancia: bool = True) -> float:
    """OVP de U16 desde el divisor de la placa: V(OVPR) * (R12 + R13 + R14) / R14.
    Con `con_tolerancia`, el borde ALTO de la banda (+-2 % de V(OVPR), tps2663.pdf
    p. 6, y las dos resistencias al 0,1 %): el que importa para D1, que tiene que
    quedar por encima."""
    v = V_OVPR_NOM_V * (valor("R12") + valor("R13") + valor("R14")) / valor("R14")
    return v * (1.0 + TOL_OVPR_TPS26631_FRAC + TOL_DIVISOR_01PCT_FRAC) if con_tolerancia else v


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
               con_tvs: bool | None = None,
               v_br_tvs_v: float = V_BR_SMBJ16A_V,
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

    `con_tvs=None`: el TVS D10 esta si bom.csv lo monta (hoy no).

    Estado:
      i_L: corriente en L2 (A)
      v_1: tension en el condensador principal C3 = entrada de U1 (V)
      v_d: tension en el condensador de amortiguacion C1 (V)
    """
    if con_tvs is None:
        con_tvs = D10_MONTADO
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
        if con_tvs and v1 > v_br_tvs_v:
            i_tvs = (v1 - v_br_tvs_v) / R_DIN_SMBJ16A_OHM

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
    "v_disparo_min_u1_v": V_DISPARO_MIN_U1_V,
    "v_sobreimpulso_tip_v": V_SOBREIMPULSO_TIP_THN20_V,
    "v_sobreimpulso_max_v": V_SOBREIMPULSO_MAX_THN20_V,   # None: HUECO, TRACO no lo da
    "i_mantenimiento_scr_a": I_MANTENIMIENTO_BT151_A,
    "r64_ohm": valor("R64"),
    "v_rwm_d1_v": V_RWM_SMBJ33CA_V,
    "v_ladrillo_max_v": V_LADRILLO_MAX_V,
    "v_br_min_d1_v": V_BR_MIN_SMBJ33CA_V,
    "v_c_d1_v": V_C_SMBJ33CA_V,
    "v_ovp_te90_max_v": V_OVP_MAX_TE90_V,
    "v_ovp_u16_max_v": v_ovp_u16_v(),
    "c10_v": tension_v("C10"),
    "vs_u15_v": V_ABSMAX_VS_LM74502_V,
    "in_u16_v": V_ABSMAX_IN_TPS2663_V,
    "vds_q2_v": V_DS_MAX_CSD18534_V,
    "vds_q7_v": V_DS_MAX_CSD18534_V,
    "vz_max_d20_v": ZENER_BZT52[filas()["D20"]["value"]][0],
    "vgs_max_q7_v": V_GS_MAX_CSD18534_V,
    "v_br_min_d10_v": V_BR_MIN_SMBJ16A_V,
    "i_gt_max_a": I_GT_MAX_BT151_A,
    "factor_despeje_i2t": FACTOR_DESPEJE_I2T,
    "c39_uf": valor("C39") * (1.0 - TOL_ELECTROLITICO_FRAC) * 1e6,
    "t_disparo_scr_us": T_GT_TIP_BT151_S * 1e6,
}


def _guarda_u18(p: dict[str, float]) -> None:
    r = u18_peor(V_C_SMBJ33CA_V, p["r64_ohm"])
    assert r["v_in_v"] <= V_IN_MAX_U18_V, (
        f"U18 IN sube a {r['v_in_v']:.2f} V > {V_IN_MAX_U18_V:.0f} V con D1 en {V_C_SMBJ33CA_V} V")
    c = u18_peor(V_BR_MAX_SMBJ33CA_V, p["r64_ohm"])
    assert c["p_z_w"] <= P_D_BZT52_W, (
        f"D2 disipa {c['p_z_w'] * 1e3:.0f} mW continuos > {P_D_BZT52_W * 1e3:.0f} mW "
        f"con la entrada en {V_BR_MAX_SMBJ33CA_V} V")


def _guarda_d1(p: dict[str, float]) -> None:
    """D1 no conduce con el ladrillo en OVP, y todo lo que cuelga de +24V_RAW
    aguanta lo que D1 deja pasar."""
    assert p["v_rwm_d1_v"] > p["v_ladrillo_max_v"], (
        f"D1 conduce en servicio: V_RWM {p['v_rwm_d1_v']:.1f} V <= {p['v_ladrillo_max_v']:.1f} V del "
        f"ladrillo en su borde alto")
    assert p["v_br_min_d1_v"] > p["v_ovp_te90_max_v"], (
        f"D1 conduce con el TE90 en OVP: V_BR minimo {p['v_br_min_d1_v']:.1f} V <= "
        f"OVP maximo del ladrillo {p['v_ovp_te90_max_v']:.1f} V (ae-TE90-datasheet.pdf p. 2)")
    assert p["v_br_min_d1_v"] > p["v_ovp_u16_max_v"], (
        f"D1 conduce antes de que U16 corte: V_BR minimo {p['v_br_min_d1_v']:.1f} V <= "
        f"OVP maximo de U16 {p['v_ovp_u16_max_v']:.2f} V")
    for nombre, limite in (("C10", p["c10_v"]), ("VS de U15", p["vs_u15_v"]), ("IN de U16", p["in_u16_v"]),
                           ("VDS de Q2", p["vds_q2_v"]), ("VDS de Q7", p["vds_q7_v"])):
        assert p["v_c_d1_v"] <= limite, (
            f"{nombre} aguanta {limite:.0f} V y D1 deja pasar {p['v_c_d1_v']:.1f} V (V_C)")
    assert p["vz_max_d20_v"] < p["vgs_max_q7_v"], (
        f"VGS de Q7: D20 sube a {p['vz_max_d20_v']:.1f} V y la puerta aguanta {p['vgs_max_q7_v']:.0f} V")


def _guarda_d10_sobra(p: dict[str, float]) -> None:
    """D10 no conduce en ningun caso modelado: el pico de U1 sin el queda por
    debajo de su V_BR MINIMO. Es lo que permite dejarlo sin montar."""
    r = escalon_lc(v_fallo_v=36.0, con_tvs=False)
    assert r["v_pico_v"] < p["v_br_min_d10_v"], (
        f"D10 conduciria: U1 llega a {r['v_pico_v']:.2f} V sin el y su V_BR minimo es "
        f"{p['v_br_min_d10_v']:.1f} V")


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
        t_disparo_rapido_s=p["t_disparo_rapido_us"] * 1e-6,
        i_disparo_rapido_a=p["i_disparo_rapido_a"],
    )
    assert res["v_pico_v"] <= V_ABSMAX_U1_V, (
        f"#334: U1 supera absmax: pico {res['v_pico_v']:.2f} V > {V_ABSMAX_U1_V:.1f} V")
    assert res["i_max_a"] <= CURVA_L2_A_UH[-1][0], (
        f"#334: L2 llega a {res['i_max_a']:.1f} A, fuera de la curva L-I publicada "
        f"(hasta {CURVA_L2_A_UH[-1][0]:.0f} A): el pico no vale")


def _guarda_ovp_sobreimpulso(p: dict[str, float]) -> str:
    """El borde bajo del OVP de U19 contra un alivio de carga del THN: OK, HUECO
    o FALLO (el assert). Sin un maximo garantizado por TRACO nunca es OK: la
    cota es la de la hoja sola (optimista) contra el sobreimpulso TIPICO, y lo
    que sale es HUECO, con el margen que queda en la envolvente del repo. Con un
    maximo garantizado cuenta ese, contra la envolvente del repo, y puede ser OK."""
    tip, mx = p["v_sobreimpulso_tip_v"], p["v_sobreimpulso_max_v"]
    m_repo = p["v_disparo_min_u1_v"] - v_sano_max_u1_v()
    m_hoja = p["v_disparo_min_u1_v"] - v_sano_max_hoja_u1_v()
    margen, exigido = (m_hoja, tip) if mx is None else (m_repo, mx)
    assert margen >= exigido, (
        f"OVP de U19: un alivio de carga sube la salida del THN {exigido:.2f} V "
        f"({'tipico' if mx is None else 'maximo'}) y el borde bajo del OVP "
        f"({p['v_disparo_min_u1_v']:.2f} V) solo deja {margen:.3f} V sobre el maximo sano")
    if mx is not None:
        return f"OK: maximo garantizado {mx:.2f} V <= margen {m_repo:.3f} V"
    cabe = "cabe" if m_repo >= tip else f"NO cabe ({m_repo - tip:+.3f} V)"
    return (f"HUECO: TRACO no da un maximo del sobreimpulso; el tipico {tip:.2f} V {cabe} en el "
            f"margen de {m_repo:.3f} V de la envolvente del repo, y cabe en los {m_hoja:.3f} V "
            f"de la hoja sola")


def _guarda_ovp_techo(p: dict[str, float]) -> None:
    """Con el THN atascado arriba sin pasar del OVP (lazo roto, o R32 en corto:
    19,89 V, traco_thn20wi.pdf nota de la p. 1), U19 no abre y U1 ve el borde
    alto del OVP en continua. El disparo rapido no lo ve: no hay sobrecorriente."""
    assert p["v_disparo_u1_v"] < V_ABSMAX_U1_V, (
        f"techo del OVP de U19: deja pasar hasta {p['v_disparo_u1_v']:.2f} V a U1, "
        f"por encima de su absmax ({V_ABSMAX_U1_V:.1f} V)")


def _guarda_fuga_ps3(p: dict[str, float]) -> None:
    mpn = filas()["PS3"]["mpn"]
    assert mpn in AISLADOS, (
        f"#491: PS3 es {mpn}; el +5 V de rack pide un modulo aislado: un buck con la "
        "entrada puenteada a la salida pone 24 V en +5V_AUX antes que SCR3")
    v = fuga_ps3(p["c39_uf"] * 1e-6, p["t_disparo_scr_us"] * 1e-6)
    assert v <= V_ABSMAX_AUX_V, (
        f"#491: PS3 desbocado lleva +5V_AUX a {v:.2f} V > {V_ABSMAX_AUX_V:.1f} V")


def _guarda_enganche_scr(p: dict[str, float]) -> None:
    peor_pliegue = min(d["i_pliegue_min_a"] for d in RACK_RIELES.values())
    assert p["i_mantenimiento_scr_a"] < peor_pliegue, (
        f"el crowbar se suelta: I_H={p['i_mantenimiento_scr_a']:.2f} A >= "
        f"pliegue={peor_pliegue:.2f} A")


def leer_csv() -> list[dict[str, str]]:
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def demo() -> int:
    print("check_absmax v5: modelo RK4 de #334 (TPS26631; D10 SMBJ16A sin montar), D1 SMBJ33CA y crowbars D-F6\n")
    tabla = leer_csv()
    filas_bom = filas()

    assert filas_bom["L2"]["mpn"] == MPN_L2, (
        f"L2 es {filas_bom['L2']['mpn']} y la curva L-I del modelo es de la {MPN_L2}")
    assert abs(CURVA_L2_A_UH[0][1] * 1e-6 - valor("L2")) <= 0.05 * valor("L2"), (
        "la curva de L2 no arranca en el valor de la BOM")
    assert filas_bom["D1"]["mpn"] == MPN_D1, (
        f"D1 es {filas_bom['D1']['mpn']} y las cifras del modelo son de la {MPN_D1}")
    assert filas_bom["Q2"]["mpn"] == filas_bom["Q7"]["mpn"] == MPN_Q2_Q7, (
        f"Q2 es {filas_bom['Q2']['mpn']} y Q7 {filas_bom['Q7']['mpn']}; los limites del modelo son del {MPN_Q2_Q7}")
    con_tope = escalon_lc(v_fallo_v=36.0)
    banco = escalon_lc(v_fallo_v=36.0, peor_caso=False)
    sin_tope = escalon_lc(v_fallo_v=36.0, con_efuse=False, con_tvs=False)
    con_d10 = escalon_lc(v_fallo_v=36.0, con_tvs=True, v_br_tvs_v=V_BR_MIN_SMBJ16A_V)
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
          f"{con_tope['t_abre_us']:.1f} us (D10 {'montado' if D10_MONTADO else 'SIN MONTAR'}: "
          f"energia TVS {con_tope['energia_tvs_mj']:.2f} mJ)")
    _guarda_d10_sobra(dict(P_BASE))
    assert abs(con_d10["v_pico_v"] - con_tope["v_pico_v"]) <= 0.005, (
        "montar D10 mueve el pico de U1: el modelo ya no dice que sobra")
    print(f"    [verde] D10 sobra: pico {con_tope['v_pico_v']:.2f} V < V_BR minimo del SMBJ16A "
          f"{V_BR_MIN_SMBJ16A_V:.1f} V (con D10 montado y su V_BR minimo el pico es el mismo, "
          f"{con_d10['v_pico_v']:.2f} V y {con_d10['energia_tvs_mj']:.2f} mJ)")
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
    print(f"    maximo sano con solo la hoja:     {v_sano_max_hoja_u1_v():.3f} V "
          f"(exactitud 1 % + linea 0,2 % + carga 0,2 % + 0,02 %/K, traco_thn20wi.pdf p. 2)")
    print(f"    {_guarda_ovp_sobreimpulso(dict(P_BASE))}")
    # Con un maximo garantizado el aserto pasa a medir la envolvente del repo: OK por debajo
    # del margen, FALLO por encima.
    m_repo = V_DISPARO_MIN_U1_V - v_sano_max_u1_v()
    assert _guarda_ovp_sobreimpulso(dict(P_BASE, v_sobreimpulso_max_v=m_repo - 0.001)).startswith("OK")
    try:
        _guarda_ovp_sobreimpulso(dict(P_BASE, v_sobreimpulso_max_v=m_repo + 0.001))
    except AssertionError as e:
        assert "OVP de U19:" in str(e), str(e)
    else:
        raise AssertionError("un maximo garantizado mayor que el margen sale verde: el aserto no lo mira")
    print(f"    con un maximo garantizado, OK solo si es <= {m_repo:.3f} V (el tipico, "
          f"{V_SOBREIMPULSO_TIP_THN20_V:.2f} V, {'daria FALLO' if V_SOBREIMPULSO_TIP_THN20_V > m_repo else 'cabria'})\n")

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

    _guarda_fuga_ps3(dict(P_BASE))
    c39 = P_BASE["c39_uf"] * 1e-6
    print(f"    [verde] PS3 ({filas_bom['PS3']['mpn']}) aislado; desbocado a "
          f"{I_LIMITE_MAX_PS3_A:.1f} A sobre C39 ({c39 * 1e6:.0f} uF en su -20 %): "
          f"{I_LIMITE_MAX_PS3_A / c39 * 1e-6:.4f} V/us, pico {fuga_ps3():.2f} V con "
          f"t_gt {T_GT_TIP_BT151_S * 1e6:.0f} us <= {V_ABSMAX_AUX_V:.1f} V de +5V_AUX")
    sin_c39 = fuga_ps3(valor("C16") * (1.0 - TOL_ELECTROLITICO_FRAC))
    assert sin_c39 > V_ABSMAX_AUX_V, "sin C39 la fuga de PS3 sale verde: el modelo no mira C39"
    print(f"    [rojo ] MUTANTE sin C39 (C16 sola, -20 %): pico {sin_c39:.2f} V "
          f"> {V_ABSMAX_AUX_V:.1f} V")

    print("\n  3. U19 abre: la corriente de L2 vuelve por D19 (SS34):")
    assert "D19" in filas_bom, "el modelo descarga L2 por D19 y D19 no esta en bom.csv"
    i_rueda = con_tope["i_rueda_libre_a"]
    assert i_rueda < I_FSM_SS34_A, f"D19 lleva {i_rueda:.1f} A >= I_FSM {I_FSM_SS34_A:.0f} A"
    print(f"    [verde] pico en D19 al cortar: {i_rueda:.1f} A < I_FSM {I_FSM_SS34_A:.0f} A")

    print("\n  4. U18 (TPS709) tras R64 + D2:")
    _guarda_u18(dict(P_BASE))
    pico_u18 = u18_peor(V_C_SMBJ33CA_V)
    cont_u18 = u18_peor(V_BR_MAX_SMBJ33CA_V)
    print(f"    [verde] con D1 en {V_C_SMBJ33CA_V} V: U18 IN = {pico_u18['v_in_v']:.2f} V "
          f"<= {V_IN_MAX_U18_V:.0f} V (D2 {filas_bom['D2']['value']}, R64 {valor('R64'):.0f} ohm)")
    print(f"    [verde] a {V_BR_MAX_SMBJ33CA_V} V sostenidos: D2 disipa "
          f"{cont_u18['p_z_w'] * 1e3:.0f} mW <= {P_D_BZT52_W * 1e3:.0f} mW")

    print("\n  4b. D1 (SMBJ33CA) y lo que cuelga de +24V_RAW:")
    _guarda_d1(dict(P_BASE))
    ovp_u16 = v_ovp_u16_v()
    print(f"    [verde] V_RWM de D1 {V_RWM_SMBJ33CA_V:.1f} V > {V_LADRILLO_MAX_V:.1f} V del ladrillo en servicio; "
          f"V_BR minimo {V_BR_MIN_SMBJ33CA_V:.1f} V > OVP maximo del TE90 "
          f"{V_OVP_MAX_TE90_V:.1f} V (margen +{V_BR_MIN_SMBJ33CA_V - V_OVP_MAX_TE90_V:.1f} V) y > OVP de U16 "
          f"{v_ovp_u16_v(False):.2f} V nominal, {ovp_u16:.2f} V en el borde alto "
          f"(margen +{V_BR_MIN_SMBJ33CA_V - ovp_u16:.2f} V)")
    for nombre, limite in (("C10 (bom.csv)", tension_v("C10")), ("VS del LM74502 (U15)", V_ABSMAX_VS_LM74502_V),
                           ("IN del TPS26631 (U16)", V_ABSMAX_IN_TPS2663_V),
                           ("VDS de Q2", V_DS_MAX_CSD18534_V), ("VDS de Q7", V_DS_MAX_CSD18534_V)):
        print(f"    [verde] {nombre:<22} aguanta {limite:>5.1f} V >= V_C de D1 {V_C_SMBJ33CA_V:.1f} V "
              f"(margen +{limite - V_C_SMBJ33CA_V:.1f} V)")
    vz_d20 = ZENER_BZT52[filas_bom["D20"]["value"]][0]
    print(f"    [verde] VGS de Q7: D20 ({filas_bom['D20']['value']}) fija V_Z max {vz_d20:.1f} V < "
          f"{V_GS_MAX_CSD18534_V:.0f} V de VGS max (margen +{V_GS_MAX_CSD18534_V - vz_d20:.1f} V)")

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
    for victima, riel in {"Invitados rack +12V": "rack+12", "Invitados rack -12V": "rack-12"}.items():
        esperados[victima] = RACK_RIELES[riel]["banda_v"][1]
    esperados["Invitados rack +5V"] = fuga_ps3()
    esperados["+5V_AUX"] = fuga_ps3()
    for f in tabla:
        clave = next((k for k in esperados if f["victima"].startswith(k)), None)
        assert clave is not None, f"absmax.csv: '{f['victima']}' no tiene modelo que la calcule"
        if clave == "U1 ":
            assert abs(float(f["v_pico_sin_tope_v"]) - sin_tope["v_pico_v"]) <= 0.05, (
                f"absmax.csv dice {f['v_pico_sin_tope_v']} V sin tope en U1 y el modelo "
                f"da {sin_tope['v_pico_v']:.2f} V: actualiza la fila")
        if clave == "U18 ":
            assert abs(float(f["v_pico_sin_tope_v"]) - V_C_SMBJ33CA_V) <= 0.05, (
                f"absmax.csv dice {f['v_pico_sin_tope_v']} V sin R64 + D2 en U18 y D1 deja pasar "
                f"{V_C_SMBJ33CA_V} V: actualiza la fila")
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
    ovp_tip = borde_rojo(_guarda_ovp_sobreimpulso, dict(P_BASE), "v_sobreimpulso_tip_v",
                         V_SOBREIMPULSO_TIP_THN20_V, 20.0, "OVP de U19:")
    ovp_min = borde_rojo(_guarda_ovp_sobreimpulso, dict(P_BASE), "v_disparo_min_u1_v",
                         V_DISPARO_MIN_U1_V, 15.0, "OVP de U19:")
    ih_max = borde_rojo(_guarda_enganche_scr, dict(P_BASE), "i_mantenimiento_scr_a",
                        0.040, 5.0, "el crowbar se suelta")
    r64_v = borde_rojo(_guarda_u18, dict(P_BASE), "r64_ohm", valor("R64"), 1.0, "U18 IN")
    # 700: por debajo de ~340 ohm salta antes "U18 IN" (D1 deja pasar 53,3 V) y el
    # canario de D2 no veria su propio aserto.
    r64_p = borde_rojo(_guarda_u18, dict(P_BASE), "r64_ohm", valor("R64"), 700.0, "D2 disipa")
    # D1: cada aserto de _guarda_d1 tiene su canario, que baja (o sube) el
    # parametro suyo hasta que salta POR SU texto y dice donde.
    d1_rwm = borde_rojo(_guarda_d1, dict(P_BASE), "v_rwm_d1_v", V_RWM_SMBJ33CA_V, 10.0,
                        "D1 conduce en servicio")
    d1_te90 = borde_rojo(_guarda_d1, dict(P_BASE), "v_br_min_d1_v", V_BR_MIN_SMBJ33CA_V, 20.0,
                         "D1 conduce con el TE90 en OVP")
    d1_u16 = borde_rojo(_guarda_d1, dict(P_BASE), "v_ovp_u16_max_v", v_ovp_u16_v(), 60.0,
                        "D1 conduce antes de que U16 corte")
    lim_d1 = {n: borde_rojo(_guarda_d1, dict(P_BASE), clave, P_BASE[clave], 10.0, texto)
              for n, clave, texto in (("C10", "c10_v", "C10 aguanta"),
                                       ("VS de U15", "vs_u15_v", "VS de U15 aguanta"),
                                       ("IN de U16", "in_u16_v", "IN de U16 aguanta"),
                                       ("VDS de Q2", "vds_q2_v", "VDS de Q2 aguanta"),
                                       ("VDS de Q7", "vds_q7_v", "VDS de Q7 aguanta"))}
    vgs_q7 = borde_rojo(_guarda_d1, dict(P_BASE), "vz_max_d20_v", P_BASE["vz_max_d20_v"], 40.0,
                        "VGS de Q7")
    d10_vbr = borde_rojo(_guarda_d10_sobra, dict(P_BASE), "v_br_min_d10_v", V_BR_MIN_SMBJ16A_V, 10.0,
                         "D10 conduciria")
    igt = borde_rojo(_guarda_puerta_scr, dict(P_BASE), "i_gt_max_a", I_GT_MAX_BT151_A, 1.0,
                     "puerta corta")
    despeje = borde_rojo(_guarda_i2t, dict(P_BASE), "factor_despeje_i2t", FACTOR_DESPEJE_I2T,
                         1000.0, "deja pasar")
    t_fuga = borde_rojo(_guarda_fuga_ps3, dict(P_BASE), "t_disparo_scr_us",
                        P_BASE["t_disparo_scr_us"], 1000.0, "PS3 desbocado")
    c_fuga = borde_rojo(_guarda_fuga_ps3, dict(P_BASE), "c39_uf", P_BASE["c39_uf"], 1.0,
                        "PS3 desbocado")
    print(f"\n  canario #334: si el disparo rapido de U19 tarda > {t_rapido_us:.1f} us "
          f"(la hoja garantiza <= {T_FASTTRIP_MAX_S * 1e6:.1f}), o salta por encima de "
          f"{i_rapido_a:.1f} A (hoy {i_fasttrip_max_u19_a():.2f}), U1 o L2 salen de su limite")
    # El borde exacto (la biseccion devuelve un punto ya dentro del rojo) y el R36 que lo da:
    # V_OVPR * (1 + R35/R36) * (1 - tolerancias) = borde bajo.
    borde_min = v_sano_max_hoja_u1_v() + V_SOBREIMPULSO_TIP_THN20_V
    assert abs(ovp_min - borde_min) < 0.05 and abs(ovp_tip - (V_DISPARO_MIN_U1_V - v_sano_max_hoja_u1_v())) < 0.05, (
        "los canarios de OVP de U19 no coinciden con el borde calculado a mano")
    r36_rojo = valor("R35") / (borde_min / (V_OVPR_NOM_V * (1.0 - TOL_OVPR_TPS26631_FRAC
                                                            - TOL_DIVISOR_01PCT_FRAC)) - 1.0)
    print(f"  canario OVP de U19: con un sobreimpulso tipico > {V_DISPARO_MIN_U1_V - v_sano_max_hoja_u1_v():.2f} V, "
          f"o un borde bajo < {borde_min:.2f} V (R36 > {r36_rojo / 1e3:.2f} kohm, hoy {valor('R36') / 1e3:.2f}), "
          f"ni la hoja sola deja pasar un alivio de carga sin abrir U19")
    _guarda_ovp_techo(dict(P_BASE))
    ovp_techo = borde_rojo(_guarda_ovp_techo, dict(P_BASE), "v_disparo_u1_v",
                           V_DISPARO_MAX_U1_V, 30.0, "techo del OVP de U19")
    r36_techo = valor("R35") / (V_ABSMAX_U1_V / (V_OVPR_NOM_V * (1.0 + TOL_OVPR_TPS26631_FRAC
                                                                + TOL_DIVISOR_01PCT_FRAC)) - 1.0)
    print(f"  canario techo del OVP de U19: con el borde alto en {ovp_techo:.2f} V "
          f"(R36 < {r36_techo / 1e3:.2f} kohm, hoy {valor('R36') / 1e3:.2f}) un THN atascado "
          f"arriba llega a U1 por encima de {V_ABSMAX_U1_V:.1f} V sin abrir U19")
    print(f"  canario D-F6: con I_H > {ih_max:.2f} A el crowbar se soltaria "
          f"(el BT151-500R pide <= 0,04 A)")
    print(f"  canario U18: R64 < {r64_v:.0f} ohm lleva U18 IN por encima de 30 V, y "
          f"R64 < {r64_p:.0f} ohm quema D2")
    print(f"  canario D1: con un V_RWM <= {d1_rwm:.1f} V conduciria con el ladrillo en su borde alto, con un "
          f"V_BR minimo <= {d1_te90:.1f} V conduce con el TE90 en OVP, y con el OVP "
          f"de U16 por encima de {d1_u16:.1f} V conduce antes de que U16 corte")
    print("  canario D1: lo que aguanta cada pieza de +24V_RAW antes de que V_C de D1 la pase: "
          + ", ".join(f"{n} {v:.1f} V" for n, v in lim_d1.items()))
    print(f"  canario Q7: con un D20 de V_Z max >= {vgs_q7:.1f} V la puerta pasa de VGS max")
    print(f"  canario D10: con un V_BR minimo de D10 <= {d10_vbr:.2f} V conduciria con el pico de U1 "
          f"({con_tope['v_pico_v']:.2f} V), y habria que montarlo")
    print(f"  canario D-F6: con I_GT > {igt * 1e3:.0f} mA algun PNP no llega a la puerta")
    print(f"  canario D-F6: un despeje > {despeje:.0f} x la fusion pasaria el I2t del SCR")
    print(f"  canario #491: +5V_AUX aguanta la fuga de PS3 hasta {t_fuga:.1f} us de retardo "
          f"del disparo (la hoja da {T_GT_TIP_BT151_S * 1e6:.0f} us tipico, sin maximo), y "
          f"pide C39 >= {c_fuga:.0f} uF")

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
    print(f"    - la desviacion transitoria de {', '.join(sin_transitorio)}: las hojas del "
          "THN 30-2422WI y del THN 20-2411WI no la dan (pregunta a TRACO); el maximo sano "
          "no la cuenta")
    print(f"    - el sobreimpulso MAXIMO del THN 20-2413WI al soltar carga: la hoja y sus curvas solo dan "
          f"el tipico (~{V_SOBREIMPULSO_TIP_THN20_V:.2f} V a 15,0 V, lectura de figura, p. 8) y el "
          f"comparador de U19 tarda 8,5..14 us (tps2663.pdf p. 8); sin condensador de salida en +15V5_RAW")
    print("    - la fuga de PS3 a su limite maximo es una cota: la hoja no dice como se desboca")
    print("    - la descarga de C39 por SCR3: el BT151 pide dI_T/dt <= 50 A/us (p. 3) y la "
          "inductancia del lazo C39-F4-R30-SCR3 no esta medida")
    print("    - un crowbar disparado no llega al MSP430: el SCR sigue conduciendo el pliegue; "
          "se mide en el bring-up (paso 8, crowbar_*, #476)")

    print("\nOK: check_absmax.py v5 (#334, #340 y T18..T21 en verde)")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
