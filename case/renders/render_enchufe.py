"""La entrada de red de 24 V vista de cerca (#130): las tres ventanas que Samuel
elige mirando, y la escuadra que las sostiene por dentro.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b --factory-startup -P render_enchufe.py
    ... -P render_enchufe.py -- A,C,escuadra     (solo esas vistas)

    PERSIANA_MOTOR=eevee   para encuadrar: Eevee a 800 x 600 (como render_persiana.py)
    PERSIANA_MUESTRAS      muestras de Cycles (128)
    ENCHUFE_SALIDA         carpeta de los PNG (por defecto build/enchufe/, que no se versiona)

Samuel eligio la B (2026-10-26), y es la que lleva params.scad; A y C se pasan
con -D al exportar, y los STL de cada una viven en build/enchufe/<variante>/.

  A  los 48 x 27.5 de la IEC vieja, con los dos M2.5 de cabeza alomada a la vista
  B  30 x 18 con las esquinas a R3 (iec_radio_esq), con los M2.5 a la vista
  C  un circulo de Ø16 (iec_radio_esq = 8 con los dos lados iguales). Las cabezas
     quedan DETRAS de la trasera -- la ventana mide menos que la separacion de
     los dos tornillos mas su cabeza --, y una cabeza alomada de 1.8 no cabe
     entre la placa y el acrilico de un lote grueso (escuadra_aire_trasera = 2.0
     menos los 1.2 de tolerancia): se dibuja con los M2.5 AVELLANADOS y a ras de
     la placa (enchufe_avellanado = 1).
  escuadra  la escuadra sola, con el talon, vista por DENTRO (desde el lado de la
     caja) para ver las dos lenguetas y el alivio de la placa sobre la pestana.

En B y C se corre iec_margen_der para que el CENTRO de la ventana sea el de A
(au - margen - ancho/2 = 506.32 en la trasera): la placa y el enchufe no se mueven.

Como render_persiana.py, reusa de render.py el mundo, las luces, mat() y medir();
de render.py NO se importan sus cuatro ensamblados enteros (minutos de CGAL para
un case que aqui no se ve): se cargan vacios. Los colores son de mirar, no cotas;
la escuadra de la vista de dentro va en aluminio claro para que se lea su forma,
aunque la pieza es anodizado negro.
"""
import math
import os
import re
import subprocess
import sys

import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SALIDA = os.environ.get("ENCHUFE_SALIDA", os.path.join(AQUI, "build", "enchufe"))
os.makedirs(SALIDA, exist_ok=True)

# --- 1. la escena de render.py: mundo, luces, camara, mat(), medir() ----------
ruta = os.path.join(AQUI, "render.py")
src = open(ruta, encoding="utf-8").read()


def _vacio():
    me = bpy.data.meshes.new("vacio")
    ob = bpy.data.objects.new("vacio", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


src, n_importes = re.subn(r'^(\w+) = importar\("assembly_\w+"\)$', r"\1 = _vacio()", src, flags=re.M)
assert n_importes == 4, f"render.py ya no importa cuatro ensamblados ({n_importes}): revisar este guion"
ns = {"__file__": ruta, "__name__": "render_enchufe", "_vacio": _vacio}
exec(compile(src, ruta, "exec"), ns)
for o in (ns["acr"], ns["alu"], ns["jun"], ns["pat"]):
    bpy.data.objects.remove(o, do_unlink=True)
esc = bpy.context.scene
mat = ns["mat"]

# --- 2. materiales (color de mirar, no cota) -----------------------------------
mat("anodizado_negro", **{"Base Color": (0.014, 0.014, 0.016, 1.0), "Metallic": 0.0, "Roughness": 0.45})
mat("plastico_negro", **{"Base Color": (0.008, 0.008, 0.009, 1.0), "Roughness": 0.35})
mat("tornillo", **{"Base Color": (0.62, 0.63, 0.66, 1.0), "Metallic": 1.0, "Roughness": 0.30})
mat("talon_gris", **{"Base Color": (0.10, 0.105, 0.115, 1.0), "Metallic": 0.9, "Roughness": 0.38})

# --- 3. las tres ventanas: los parametros que cambian respecto de params.scad ---
CENTRO_ZA = 506.32      # centro de la ventana de A en la trasera: au - 22 - 48/2
VARIANTES = {
    "A": [("iec_ancho", 48), ("iec_alto", 27.5), ("iec_radio_esq", 0),
          ("iec_margen_der", 22)],
    "B": [],
    "C": [("iec_ancho", 16), ("iec_alto", 16), ("iec_radio_esq", 8),
          ("iec_margen_der", 552.32 - CENTRO_ZA - 8), ("enchufe_avellanado", 1)],
}
OPENSCAD = ns["OPENSCAD"]
SCAD = os.path.join(AQUI, "..", "cad", "sam17_case.scad")


def exportar(parte, variante):
    """El STL de una parte de la escena, exportado con los -D de su variante si el
    .scad es mas nuevo (la misma regla de importar() en render.py)."""
    carpeta = os.path.join(AQUI, "build", "enchufe", variante)
    os.makedirs(carpeta, exist_ok=True)
    stl = os.path.join(carpeta, parte + ".stl")
    if not os.path.exists(stl) or os.path.getmtime(stl) < ns["_fuentes_mtime"]():
        print(f"exportando {parte} [{variante}]", flush=True)
        defs = [x for k, v in VARIANTES[variante] for x in ("-D", f"{k}={v}")]
        subprocess.run([OPENSCAD, "-o", stl, *defs, "-D", f'PART="{parte}"', SCAD],
                       check=True, capture_output=True)
    return stl


ESCENA = []        # lo que hay puesto ahora; se vacia al cambiar de vista


def poner(parte, variante, material):
    bpy.ops.wm.stl_import(filepath=exportar(parte, variante))
    ob = bpy.context.selected_objects[0]
    ob.name = f"{parte}_{variante}"
    ob.data.materials.append(bpy.data.materials[material])
    for p in ob.data.polygons:
        p.use_smooth = False
    ESCENA.append(ob)
    return ob


def vaciar():
    while ESCENA:
        bpy.data.objects.remove(ESCENA.pop(), do_unlink=True)


# --- 4. motor ------------------------------------------------------------------
if os.environ.get("PERSIANA_MOTOR", "").lower() == "eevee":
    esc.render.engine = "BLENDER_EEVEE"
    esc.eevee.taa_render_samples = 16
    esc.render.resolution_x, esc.render.resolution_y = 800, 600
else:
    esc.cycles.samples = int(os.environ.get("PERSIANA_MUESTRAS", "128"))
    esc.cycles.use_denoising = True


# --- 5. camaras ----------------------------------------------------------------
def base(az, el):
    """Igual que render_persiana.py: az en grados desde -X hacia +Z, el sobre la horizontal."""
    horizontal = Vector((-math.cos(az), 0.0, math.sin(az)))
    direccion = (horizontal * math.cos(el) + Vector((0.0, math.sin(el), 0.0))).normalized()
    adelante = -direccion
    derecha = adelante.cross(Vector((0.0, 1.0, 0.0))).normalized()
    arriba_cam = derecha.cross(adelante).normalized()
    return direccion, derecha, arriba_cam, adelante


def cerca(nombre, foco, az, el, semi, lente=70.0):
    """Un primer plano: camara en perspectiva a `semi` mm de medio ancho de cuadro
    alrededor de `foco`. No encuadra por el bbox del case -- el case no esta."""
    direccion, derecha, arriba_cam, adelante = base(math.radians(az), math.radians(el))
    cd = bpy.data.cameras.new("cam_" + nombre)
    cd.lens = lente
    cam = bpy.data.objects.new("cam_" + nombre, cd)
    esc.collection.objects.link(cam)
    esc.camera = cam
    dist = semi / math.tan(cd.angle_x / 2)
    cam.location = foco + direccion * dist
    cam.rotation_euler = Matrix((derecha, arriba_cam, -adelante)).transposed().to_euler()
    cd.clip_start, cd.clip_end = 1.0, dist * 4.0 + 500.0
    # las luces de render.py cuelgan de `centro` y `radio` (el bbox del case entero)
    ns["centro"], ns["radio"] = foco, semi * 1.2
    ns["poner_luces"](derecha, arriba_cam, adelante, max(dist, 400.0))
    salida = os.path.join(SALIDA, nombre + ".png")
    esc.render.filepath = salida
    bpy.ops.render.render(write_still=True)
    print("OUT", nombre, flush=True)
    return salida


# --- 6. las vistas ---------------------------------------------------------------
YC, ZC = 46.38, 514.47            # el centro de la ventana de A (y, z), el mismo en B y C


def ventana(variante):
    """La ventana desde atras, un poco de lado y de arriba para que se lea el fondo de 8."""
    vaciar()
    poner("assembly_acrilico", variante, "acrilico_naranja")
    poner("escuadra_enchufe", variante, "anodizado_negro")
    poner("render_enchufe", "A", "plastico_negro")
    poner("render_tornillos_enchufe", variante, "tornillo")
    return cerca(f"sam17-enchufe-{variante}", Vector((309.0, YC, ZC)), 160.0, 12.0, 38.0)


def escuadra():
    """La escuadra con el talon, vista desde dentro: del lado de la caja hacia la trasera."""
    vaciar()
    poner("render_talon", "A", "talon_gris")
    poner("escuadra_enchufe", "A", "aluminio")
    return cerca("sam17-enchufe-escuadra", Vector((298.0, 30.0, 516.0)), 24.0, 28.0, 62.0)


VISTAS = {"A": lambda: ventana("A"), "B": lambda: ventana("B"), "C": lambda: ventana("C"),
          "escuadra": escuadra}
COBERTURA_MINIMA = 0.05
rojos = 0
for v in (args[0].split(",") if args else VISTAS):
    png = VISTAS[v.strip()]()
    frac, brillo = ns["medir"](png)
    veredicto = "VERDE" if frac >= COBERTURA_MINIMA and brillo >= 0.05 else "ROJO"
    rojos += veredicto == "ROJO"
    print(f"{veredicto} [{os.path.basename(png)}]: cobertura {frac:.4f} (minimo "
          f"{COBERTURA_MINIMA}), brillo {brillo:.4f}", flush=True)
print("FIN", flush=True)
if rojos:
    sys.exit(1)
