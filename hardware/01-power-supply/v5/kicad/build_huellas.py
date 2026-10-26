"""Genera las huellas propias de la fuente v5: el modulo Mornsun y la bobina L2.

    python build_huellas.py

Las que habia (#474) eran una sola huella generica de 6 pines repetida para el
URB y los dos TRACO -- que no se parecen entre si. Aqui las cotas salen
del plano de cada hoja, escritas en una tabla con su pagina; check_huellas.py
las vuelve a leer del .kicad_mod y las compara con la misma hoja.

Los TRACO THN 20WI/30WI no estan aqui: son el 1x1 pulgada estandar de TRACO y
KiCad ya trae esa huella (Converter_DCDC_TRACO_THL30-xxxxWI_THT, mismos seis
pines en las mismas cotas que la p. 4/5 de sus hojas).

La Bourns SRP1265A de L2 tampoco la trae KiCad (tiene la SRP1245A, otra talla).
"""
from __future__ import annotations

import os
import uuid

DIR = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.join(DIR, "sam17.pretty")
DS = "docs/reference/datasheets"

# Mornsun URB_YMD-20WR3, encapsulado horizontal sin disipador.
# mornsun_urb_ymd20wr3.pdf p. 6, "Top View (PCB Layout)": rejilla de 2.54 mm,
# taladro recomendado 1.50 mm, patilla de 1.00 mm. Origen en el pin 1.
URB = {
    "nombre": "Converter_DCDC_Mornsun_URB_YMD-20WR3_Horizontal_THT",
    "hoja": f"{DS}/mornsun_urb_ymd20wr3.pdf p. 6",
    "taladro": 1.5, "pad": 2.6,
    "pines": {"1": (0.0, 0.0), "2": (0.0, 7.62), "3": (0.0, 12.70),
              "6": (20.32, 0.0), "5": (20.32, 10.16), "4": (20.32, 20.32)},
    # Caja de 25.40 x 25.40 con los pines a 2.54 del borde.
    "cuerpo": (-2.54, -2.54, 22.86, 22.86),
}

# Bourns SRP1265A, bobina de L2 (#334). bourns_srp1265a.pdf p. 1,
# "Recommended Layout": 14.2 mm entre los bordes exteriores de los pads, 8.0
# entre los interiores, 5.0 de alto -> pads de 3.1 x 5.0 con los centros a
# 11.1 mm. "Product Dimensions": cuerpo de 13.5 x 12.5 mm, con los terminales
# en los lados de 13.5. Origen en el centro.
SRP = {
    "nombre": "L_Bourns_SRP1265A",
    "hoja": f"{DS}/bourns_srp1265a.pdf p. 1",
    "pad_smd": (3.1, 5.0),
    "pines": {"1": (-5.55, 0.0), "2": (5.55, 0.0)},
    "cuerpo": (-6.75, -6.25, 6.75, 6.25),
}


_SEMILLA = {"nombre": "", "n": 0}


def _u() -> str:
    """UUID estable: regenerar la huella sin cambiarla no deja diff."""
    _SEMILLA["n"] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"sam17/{_SEMILLA['nombre']}/{_SEMILLA['n']}"))


def _rect(x0: float, y0: float, x1: float, y1: float, capa: str, ancho: float) -> str:
    return (f'  (fp_rect (start {x0:g} {y0:g}) (end {x1:g} {y1:g}) '
            f'(stroke (width {ancho:g}) (type default)) (fill none) '
            f'(layer "{capa}") (uuid "{_u()}"))')


def _linea(xa: float, ya: float, xb: float, yb: float, capa: str, ancho: float) -> str:
    return (f'  (fp_line (start {xa:g} {ya:g}) (end {xb:g} {yb:g}) '
            f'(stroke (width {ancho:g}) (type default)) (layer "{capa}") (uuid "{_u()}"))')


def _cabecera(nombre: str, descr: str, tags: str, ref_y: float, val_y: float) -> list[str]:
    _SEMILLA.update(nombre=nombre, n=0)
    return [f'(footprint "{nombre}"', "  (version 20241229)",
            '  (generator "sam17-build_huellas")', '  (generator_version "10.0")',
            '  (layer "F.Cu")', f'  (descr "{descr}")', f'  (tags "{tags}")',
            f'  (property "Reference" "REF**" (at 0 {ref_y:g} 0) (layer "F.SilkS") '
            f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))',
            f'  (property "Value" "{nombre}" (at 0 {val_y:g} 0) (layer "F.Fab") '
            f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))']


def urb() -> str:
    d = URB
    x0, y0, x1, y1 = d["cuerpo"]
    out = _cabecera(d["nombre"],
                    f"Mornsun URB_YMD-20WR3 horizontal, 1x1 pulgada, {d['hoja']}",
                    "DC-DC Mornsun URB isolated THT", y0 - 1.5, y1 + 1.5)
    out.append('  (attr through_hole)')
    out.append(_rect(x0, y0, x1, y1, "F.Fab", 0.1))
    out.append(_rect(x0 - 0.12, y0 - 0.12, x1 + 0.12, y1 + 0.12, "F.SilkS", 0.12))
    out.append(_rect(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5, "F.CrtYd", 0.05))
    for num, (x, y) in d["pines"].items():
        forma = "rect" if num == "1" else "circle"
        out.append(f'  (pad "{num}" thru_hole {forma} (at {x:g} {y:g}) '
                   f'(size {d["pad"]:g} {d["pad"]:g}) (drill {d["taladro"]:g}) '
                   f'(layers "*.Cu" "*.Mask") (uuid "{_u()}"))')
    out.append(")")
    return "\n".join(out) + "\n"


def srp() -> str:
    d = SRP
    x0, y0, x1, y1 = d["cuerpo"]
    w, h = d["pad_smd"]
    out = _cabecera(d["nombre"],
                    f"Bourns SRP1265A, bobina apantallada 13.5 x 12.5 mm, {d['hoja']}",
                    "inductor Bourns SRP1265A SMD", y0 - 1.5, y1 + 1.5)
    out.append('  (attr smd)')
    out.append(_rect(x0, y0, x1, y1, "F.Fab", 0.1))
    # Los pads asoman 0.35 mm por los lados de 13.5: la serigrafia va solo
    # arriba y abajo, que no los toca.
    for y in (y0 - 0.12, y1 + 0.12):
        out.append(_linea(x0 - 0.12, y, x1 + 0.12, y, "F.SilkS", 0.12))
    xc = max(x1, max(abs(x) for x, _ in d["pines"].values()) + w / 2) + 0.25
    out.append(_rect(-xc, y0 - 0.25, xc, y1 + 0.25, "F.CrtYd", 0.05))
    for num, (x, y) in d["pines"].items():
        out.append(f'  (pad "{num}" smd rect (at {x:g} {y:g}) (size {w:g} {h:g}) '
                   f'(layers "F.Cu" "F.Paste" "F.Mask") (uuid "{_u()}"))')
    out.append(")")
    return "\n".join(out) + "\n"


def main() -> int:
    for d, texto in ((URB, urb()), (SRP, srp())):
        ruta = os.path.join(PRETTY, d["nombre"] + ".kicad_mod")
        with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)
        print(f"escrita {os.path.basename(ruta)} ({len(d['pines'])} pads)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
