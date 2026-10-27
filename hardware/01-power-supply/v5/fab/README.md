# Ficheros de fabricación — Módulo 1, versión 5 (fuente ladrillo 24 V)

Todo lo de esta carpeta sale de `../kicad/sam17-power-v5.kicad_pcb` con
`../kicad/build_fab.py` (kicad-cli). `../check_fab.py` lo reexporta con las
mismas órdenes y lo compara fichero a fichero: si alguien rerutea y no
reexporta, la puerta se pone roja.

## Estado

```
DRC (kicad-cli, todas las severidades + paridad)  0 infracciones · 0 sin conectar · 0 de paridad
cobre            1464 pistas, 294 vías (72 térmicas de U1/U2, 108 de masa cosidas)
stackup          F.Cu señal+potencia | In1 masas GND24/GNDA/GNDD | In2 señal | B.Cu señal+masa
```

El informe completo es `../kicad/sam17-power-v5-drc.json`, atado al sha256
de la placa que comprobó: `../kicad/check_pcb.py` lo da por rojo si la placa
cambió después, y `../kicad/check_drc.py` repite el DRC en vivo.

La placa de #474 que había aquí antes no tenía ni una pista (161 huellas,
0 segmentos, 0 vías) y este README decía "ruteada y con DRC en cero".

## Especificación

| | |
|---|---|
| Dimensiones | 200 × 150 mm (Eurocard) |
| Capas | **4** |
| Cobre | 1 oz exterior: los caminos de 3 A están calculados con ese espesor |
| Espesor | 1.6 mm, FR-4 |
| Vías | 271 de 0.6 / 0.3 mm y 23 de 0.8 / 0.4 mm (redes de potencia); las huellas DFN traen sus vías térmicas de 0.2 mm |
| Pista mínima | 0.187 mm (la entrada a los pines de 0.45 mm de paso) |
| Holgura mínima | 0.15 mm |

## Cómo está hecha

- **Tres masas en In1**, un polígono por dominio, repetidas en F.Cu y B.Cu:
  GND24 (entrada del ladrillo y lado primario de los convertidores), GNDA
  (analógica, rack y telemetría) y GNDD (isla de M1). GNDD queda a ≥ 2 mm de
  las otras dos en las cuatro capas. GND24 y GNDA se unen **solo** en NT1,
  entre PS5 y PS3: con los cinco convertidores aislados no lleva corriente de
  carga (#491).
- **El retorno del ladrillo pasa por Q7** (CSD18534Q5A, canal N en el polo
  negativo): J1.2 es `RET24_RAW`, una isla de cobre fijo en F.Cu que lleva
  J1.2, D1.2 y el drenador de Q7, cortada de los vertidos de GND24. Las tres
  fuentes de Q7 van juntas a GND24 por cobre de 1,8 mm. D1 cuelga de J1 (no de
  GND24) para que un transitorio vuelva por J1 sin cruzar Q7.
- **Caminos de ~3 A en cobre fijo**, no en pista ruteada: J1 → Q2 → U16 → bus
  de 2,5 mm a las +Vin de los cinco convertidores (24 V, hasta 2,9 A) y PS2 →
  F5 → J9 (+5 V digital, hasta 2,9 A). `check_pcb.py` comprueba que cada pad
  de esos caminos se alcanza desde el origen por cobre de ≥ 1,4 mm (~3 A con
  10 °C de subida en 1 oz, IPC-2221), incluidos J1.2 → Q7 y D1.2 y las fuentes
  de Q7.
- **Disipación de U1 y U2** (1,75 / 1,82 W en DD-PAK con la cascada a
  450 mA/riel, `../tj_budget.py`: la unión de U1 queda en 120,5 °C y la de U2
  se acota midiendo su aleta en el bring-up, #478): la aleta de U1 es
  GNDA y baja al plano por 36 vías; la de U2 es −15V5_FILT y tiene su
  propio cobre en F.Cu, In2 y B.Cu con otras 36.
- **Ruteo**: Freerouting 2.4.1 (por línea de órdenes, sin tocar su
  configuración de usuario) más un rescate propio (`../kicad/rescate.py`)
  para las conexiones que Freerouting deja abiertas. El juez es el DRC de KiCad.

## Qué se sube a JLCPCB

| fichero | dónde va |
|---|---|
| los 10 gerbers + `sam17-power-v5.drl`, en un zip | "Add gerber file" (4 capas) |
| `sam17-power-v5-bom-jlc.csv` | "Add BOM File" |
| `sam17-power-v5-cpl-jlc.csv` | "Add CPL File" |

El zip no se versiona (cambia de bytes en cada exportación):

```bash
cd hardware/01-power-supply/v5/fab
zip -j sam17-power-v5-jlcpcb.zip sam17-power-v5-*.g* sam17-power-v5.drl
```

**Antes de pagar**, en el visor de colocación de JLC: el giro de algunas
huellas (SOT-23, electrolíticos, DFN) no coincide con el de su biblioteca y
`cpl_jlc.py` no lo "corrige" con una tabla de memoria. Se revisa allí.

## Lo que NO monta JLC

- **Módulos fuera de LCSC** (se compran en Farnell/Mouser y van a mano):
  PS1 (THN 30-2422WI), PS3 (THN 20-2411WI), PS4/PS5 (THN 20-2413WI) y PS2
  (URB2405YMD-20WR3).
- **THT con código LCSC** (se compran en LCSC y van a mano): conectores,
  SCR1–SCR3, RV2/RV3, SW1, puntos de prueba.
- **Sin montar** (`supplier` «SIN MONTAR» en `bom.csv`): SCR4 y su disparo
  (U25, Q6, R51, R52, R56, R73, R77, R81), D10 (SMBJ16A) y D12 (S1M). Las
  huellas quedan en la placa.
- `bom_jlc.py` lo decide por la placa: entra cada huella SMD del fichero de
  posiciones que se compra en LCSC; una SMD de la placa que no esté en
  `bom.csv` es un error.

Nueve referencias no caben en la serigrafía de las zonas densas y van solo
en F.Fab (el dibujo de montaje de `../pcb/sam17-power-v5.pdf`): R22, R41,
R48, R53, R67, R70, R75, R78 y FB1.

## Regenerar

Desde la raíz del repositorio, con el Python de KiCad (`pcbnew`) donde hace falta:

```bash
python hardware/01-power-supply/v5/kicad/build_schematic.py      # esquema, netlist, ERC
FREEROUTING_JAR=/ruta/freerouting-2.4.1-executable.jar JAVA=/ruta/java25 \
  python hardware/01-power-supply/v5/kicad/build_pcb.py          # placa + DRC (~1 h)
python hardware/01-power-supply/v5/kicad/build_fab.py            # esta carpeta y ../pcb/
python hardware/tools/gates.py                                   # todas las puertas
```

`build_pcb.py --desde-ruteo=RUTA` repite lo que va después de Freerouting
sobre la placa ruteada que guardó una corrida anterior.
