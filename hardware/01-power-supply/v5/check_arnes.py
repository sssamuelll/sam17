"""Puerta: el arnes del conector de panel X1 da la polaridad buena a J1.

    python check_arnes.py        # 0 verde, 1 rojo, 2 falta un archivo

`bom-chasis.csv` cableaba 1+2 -> J1.1 y 3+4 -> J1.2, y en la clavija del TE90
los pines 1 y 2 son de polo contrario: el arnes ponia en corto el ladrillo
delante de toda la cadena de entrada, y ninguna puerta leia esa BOM (#487,
junta de piezas v5 sec. 3.1).

Cruza tres fuentes, sin copiar ninguna:
  - el mapa X1 -> J1, de las notas de X1 en `bom-chasis.csv` («1+3 -> J1.1»);
  - la polaridad de cada pin de la clavija, de la hoja del ladrillo declarado;
  - la red de J1.1 y J1.2, de la netlist (`kicad/sam17-power-v5.net`).

Y exige que los pines por polo del mapa sean los que `ladrillo_budget.py`
cuenta para el conector (`N_PINES_PARALELO`), de donde salen su caida y el
techo de corriente de `recuperacion_budget.py`.

`_canario()` le pasa los mapas que tienen que fallar (el de antes de #487, uno
invertido y uno de un pin por polo) y comprueba que fallan.
"""
from __future__ import annotations

import csv
import importlib.util
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BOM_CHASIS = os.path.join(DIR, "bom-chasis.csv")
sys.path.insert(0, os.path.join(DIR, "kicad"))

from check_netlist import NET, leer, red_de  # noqa: E402

# AE/SL Power TE90, opcion de conector 49 (ae-TE90-datasheet.pdf p. 6):
# "4-pin Snap n Lock, Kycon Kpp - 4P or equivalent (Pins 1,3 = (+); pins 2,4 = (-))".
LADRILLO = "TE90 opcion 49"
POLO_PIN = {1: "+", 3: "+", 2: "-", 4: "-"}
POLO_RED = {"+24V_RAW": "+", "GND24": "-"}


def _ladrillo_budget():
    # Por ruta: importar un budget de la v5 arrastra la v4 al sys.path.
    spec = importlib.util.spec_from_file_location("ladrillo_budget",
                                                  os.path.join(DIR, "ladrillo_budget.py"))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("ladrillo_budget", mod)
    spec.loader.exec_module(mod)
    return mod


def mapa_de_bom() -> dict[int, list[int]]:
    """{pin de J1: [pines de X1]} leido de las notas de X1."""
    with open(BOM_CHASIS, encoding="utf-8", newline="") as fh:
        notas = next(r["notes"] for r in csv.DictReader(fh) if r["refs"] == "X1")
    return {int(j): [int(p) for p in pines.split("+")]
            for pines, j in re.findall(r"(\d(?:\+\d)*) -> J1\.(\d)", notas)}


def fallos(mapa: dict[int, list[int]], red_j1: dict[int, str | None],
           pines_por_polo: int) -> list[str]:
    out: list[str] = []
    usados = [p for pines in mapa.values() for p in pines]
    if len(usados) != len(set(usados)):
        out.append(f"un pin de X1 va a dos sitios: {sorted(usados)}")
    if desconocidos := set(usados) - set(POLO_PIN):
        out.append(f"pines de X1 que la clavija no tiene: {sorted(desconocidos)}")
    for j in (1, 2):
        red = red_j1.get(j)
        if red not in POLO_RED:
            out.append(f"J1.{j} esta en {red!r}, que no es +24V_RAW ni GND24")
            continue
        pines = mapa.get(j, [])
        if not pines:
            out.append(f"J1.{j} ({red}) no tiene ningun pin de X1")
        for p in pines:
            if POLO_PIN.get(p) != POLO_RED[red]:
                out.append(f"X1.{p} es ({POLO_PIN.get(p)}) en el {LADRILLO} "
                           f"y va a J1.{j}, que es {red}")
        if pines and len(pines) != pines_por_polo:
            out.append(f"J1.{j} lleva {len(pines)} pines de X1 y ladrillo_budget.py "
                       f"cuenta {pines_por_polo} por polo")
    return out


def _canario(red_j1: dict[int, str | None], n: int) -> None:
    otro_n = {1: [1, 3], 2: [2, 4]} if n == 1 else {1: [1], 2: [2]}
    for nombre, mapa in (("el de antes de #487", {1: [1, 2], 2: [3, 4]}),
                         ("invertido", {1: [2, 4], 2: [1, 3]}),
                         (f"con otro numero de pines que los {n} por polo", otro_n)):
        assert fallos(mapa, red_j1, n), f"canario: el mapa {nombre} pasa la puerta"


def main() -> int:
    for ruta in (BOM_CHASIS, NET):
        if not os.path.exists(ruta):
            print(f"HUECO: falta {os.path.relpath(ruta, DIR)}")
            return 2
    nets = leer()
    red_j1 = {j: red_de(nets, f"J1.{j}") for j in (1, 2)}
    n = _ladrillo_budget().N_PINES_PARALELO
    _canario(red_j1, n)

    mapa = mapa_de_bom()
    print(f"check_arnes.py -- X1 -> J1 contra la clavija del {LADRILLO}")
    for j, pines in sorted(mapa.items()):
        print(f"  X1.{'+'.join(map(str, pines)):<5} -> J1.{j} ({red_j1.get(j)})")
    if malos := fallos(mapa, red_j1, n):
        for f in malos:
            print(f"  FALLO: {f}")
        return 1
    print(f"  OK: cada polo con sus {n} pines, y los canarios fallan como deben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
