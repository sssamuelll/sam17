# Junta de las piezas de la fuente v5, antes de la firma

**Fecha**: 2026-10-25 · **Estado**: **junta, no firma**. Este papel no elige ni
descarta ninguna pieza: dictamina sobre lo que
[`2026-10-22-fuente-v5-piezas-propuesta.md`](2026-10-22-fuente-v5-piezas-propuesta.md)
pone a firmar ·
**Revisa**: las siete piezas de la propuesta, P1 a P7, contra lo firmado
([v5](2026-09-05-fuente-v5-ladrillo-design.md) §8, §9, §9.2 y §9.3; las D-F
vigentes de la [v4](2026-09-03-fuente-v4-liston-design.md); el
[pliego](2026-09-08-pliego-ladrillo.md); el
[censo](2026-09-08-censo-dv4-resolucion.md)) y contra la placa v5-B de `main`
(`bom.csv`, `bom-chasis.csv` y la netlist `kicad/sam17-power-v5.net`) ·
**Panel**: tres lentes disjuntas (contradicciones con lo firmado · modos de
fallo en marcha · complejidad accidental). Cada hallazgo se comprobó contra la
hoja o el guion que cita antes de entrar aquí ·
**No toca**: ninguna pieza se firma ni se tumba aquí; la placa, la BOM y los
guiones no cambian; ningún HUECO de §9.2 se cierra

> **El orden es brief → papel → junta → firma.** La propuesta quedó lista para
> esta junta el mismo día: sus dos preguntas previas (el piso de 80 W y los
> crudos a 450 mA) están contestadas en su §8.

**Veredicto: ninguna firmable tal cual · P1, P2, P3, P4 y P6 firmables con
condición · P5 se parte: el TE90 firmable con condición y el respaldo Mean Well
no firmable aún · P7 no firmable aún · ninguna a tumbar.**

---

## 1. En cristiano

Pieza por pieza, lo escogido aguanta: cada convertidor lleva su carga, el TE90
tiene 17 W de holgura y la cadena de protección hace lo que firman M3 y M5. Lo
que falla es cómo se juntan, y casi siempre en un papel o una cuenta, no en la
pieza:

1. **El cable del enchufe pone en corto el ladrillo.** La nota de
   `bom-chasis.csv` une los pines 1 y 2 al +24 V, y en los dos ladrillos
   candidatos el pin 1 es + y el 2 es −. No rompe nada, porque el ladrillo
   entra en hiccup, pero el instrumento no enciende. El arreglo es barato: un
   pin por polo, el 1 y el 2, que AE y Mean Well cablean igual.
2. **La placa no es la que firman los papeles, en dos sitios.** No tiene los
   interruptores de carga del ±12 V de rack que D-F4 conserva, y tiene un
   cuarto tiristor en el +5 V digital que ningún papel firmó (uno dice
   expresamente que no se firma). Ese tiristor, además, se dispara con un
   alivio de carga normal del URB: entre lo sano y el disparo hay 30 mV.
3. **Tres cuentas que sostienen la protección miden otra cosa.**
   `recuperacion_budget.py` usa un temporizador de `U16` que solo existe con
   PGOOD alto, y en la placa PGOOD no sube nunca; con el que vale, su propio
   aserto sale rojo. `curvas.py` cita una frase de derating que las hojas de
   TRACO no tienen. Y `check_absmax.py` modela el +5 V de rack con el OVP de
   una IRM que ya no está, cuando el K78 es un buck no aislado y la telemetría
   cuelga de él por fuera de su crowbar.
4. **La entrada está mal coordinada con el ladrillo.** El TVS `D1` empieza a
   conducir antes que la protección de sobretensión del TE90. Y el respaldo
   Mean Well se enclava por sobretensión desde el 105 %, a 0,48 V de su propia
   tolerancia: cada corte de `U16` a plena carga puede dejarlo enclavado hasta
   que alguien lo desenchufe.

Nada de esto tumba una pieza. Casi todo se arregla en papel, en valores de BOM
o con preguntas gratis a los fabricantes. Lo que pide placa es D-F4 en rack, si
se restituye, y el tiristor digital, si se queda.

---

## 2. Las siete fichas

### P1 — ±12 V de rack: TRACO THN 30-2422WI (`PS1`)

| | |
|---|---|
| **Qué hace** | Los dos rieles de rack con un módulo doble de 30 W: 18,6 W declarados (`ladrillo_budget.py`) |
| **Lo que aguanta** | Su carga declarada y la ventana de entrada: 4:1, arranque a 8,8 V máx. (`traco_thn30wi.pdf` p. 2) |
| **Lo que falla** | (a) **D-F4 en rack no está en la placa** (§3.3). (b) **La regulación cruzada solo está garantizada entre el 25 y el 100 % de carga asimétrica** («Cross Regulation (25% / 100% asym. load) dual output models: 5% max.», p. 2), y `check_absmax.py` la aplica siempre. Con la fila B vacía el −12 V va al 0 % y el +12 V al 44 % (la pantalla): fuera de hoja, contra un crowbar que dispara desde 13,50 V. (c) **La carcasa queda a 3–8 K de su protección térmica.** Con la pérdida del guion (2,46 W) o la del 89 % típico (2,30 W), a 15,0 K/W (p. 4), sube 34,5–36,9 K; con el aire del cajón a 62,6–65 °C llega a 97–102 °C, contra un corte desde 105 °C (p. 3). Si corta, vuelve sola hacia los 100 °C, y el MCU no lo ve |
| **Con la nota `thn30wi-cc`** | `traco_thn30wi_characteristic_curves.pdf` p. 11, en lecturas de figura. A 24 V de entrada pierde 2,35 W con el 62 % de potencia total (18,6 de 30 W). A 15,0 K/W típ. la carcasa queda en 97,9–100,3 °C con el aire a 62,6–65 °C. El borde de su derating es esa misma cuenta con la carcasa a 105 °C, el corte mínimo: la cuenta lo pone a 69,8 °C de aire con el 62 % y a 60,6 °C con el 84 %, y la curva a 70,6 y 61,0 °C. La cuenta rehecha no cumple los 100 °C en todo el intervalo de aire: de la condición de carcasa queda la medida. Cómo se lee la curva con las salidas desiguales es §4.7 |
| **Veredicto** | **FIRMABLE CON CONDICIÓN**: D-F4 en rack resuelta (§4.4); la regulación cruzada por debajo del 25 % contestada por TRACO y medida en banco (el −12 V al 0 y al 24 %, con el +12 V al 44–84 %, contra 13,50 V); y la carcasa medida a carga declarada con aire de 62,6–65 °C, con criterio de 100 °C, o la nota de derating de TRACO versionada y la cuenta rehecha (§3.6) |

### P2 — +5 V digital aislado: Mornsun URB2405YMD-20WR3 (`PS2`)

| | |
|---|---|
| **Qué hace** | La barrera de M1 en el digital: 14,47 W de 20 W (72 %), con el 88 % mín. que publica (p. 1) |
| **Lo que aguanta** | M1: 1500 VDC (p. 1). OVP del 110–160 %, sobrecorriente del 110–190 % e hiccup en corto (p. 2). Su «Hot Plug: Unavailable» (p. 2; la propuesta cita la p. 1) no le llega: el módulo solo ve la rampa de `U16`, 19,0 ms hasta 32,7 V (`recuperacion_budget.py`) |
| **Lo que falla** | (a) **El tiristor que lo vigila no está firmado, y se dispara solo** (§3.4). (b) **Es una segunda marca** para 0,18 W de rendimiento garantizado, y en LCSC «solo hay clones de otras marcas con el mismo nombre: no valen» (`bom.csv`, fila `PS2`). La alternativa, el THN 20-2411WI, cabe en la huella de `PS1`/`PS4`/`PS5`, pero solo da un 89 % típico: con ella, H-CENSO-ETA-DIGITAL vuelve a quedar abierto |
| **Veredicto** | **FIRMABLE CON CONDICIÓN**: T19 decidida con nombre propio (§4.5), y la compra por distribuidor autorizado con la marca comprobada |

### P3 — crudos ±15,5 V: 2 × TRACO THN 20-2413WI (`PS4`, `PS5`)

| | |
|---|---|
| **Qué hace** | Los crudos de la cascada, uno cableado invertido, recortados a 15,5 V (D-V3) |
| **Lo que aguanta** | Con la cascada a 450 mA, cada rama lleva 0,620 A: 9,85 W, el 49 % (`ladrillo_budget.py`). Sus 1,74 W a 17,6 K/W (p. 4) son 30,6 K: con el aire del cajón, la carcasa queda por debajo de sus 105 °C (p. 3). Es lo mínimo que deja D-V3, porque el recorte es «(single output models only)» (p. 2) |
| **Lo que falla** | (a) **La constante del recorte no tiene hoja.** `R32`/`R33` = 45,3 kΩ salen de «R = 10000\*2.5/(15.5-2.5-12.5) - 5110 = 44.9k (nota TRACO)» (`bom.csv:69`). La hoja remite a una nota de la web (p. 2) que no está versionada, y la propuesta (§9.1) dice que la fórmula es de la serie sin WI. (b) **El borde bajo del OVP de `U19` queda 0,18 V por encima del máximo sano del crudo** (16,19 contra 16,012 V, `check_absmax.py`), y el THN 20 no declara cuánto se desvía ante un escalón, solo «Response Time 250 µs typ. (25% Load Step)» (p. 2). Un alivio de carga en la rama de `U1` puede abrir `U19` y gastar un intento. (c) `curvas.py` le atribuye una frase de derating que su hoja no tiene (§3.6) |
| **Con las notas de TRACO** | (a) se cierra. La nota de ajuste (`traco_thn15wi_thn20wi_thn30wi_voltage_adjustment.pdf` p. 1) cubre la serie WI y da para los xx13WI G = 10000, H = 5110, K = 12,5 y L = 2,5, las constantes de `bom.csv:69`. La resistencia de subida va de Trim a −Vout, como `R32` (`PS4` 4–5) y `R33` (`PS5` 4–5) en la netlist, y 45,3 kΩ dan 15,50 V. Con la resistencia en corto, la misma fórmula da 19,89 V, la cifra que la propuesta sacaba de la nota sin WI. (b) sigue, ya con número: la captura típica de un escalón del 25 % (`traco_thn20wi_characteristic_curves.pdf` p. 8, 100 mV/div) sube unos 0,19 V contra 0,18 V de ventana, y el OVP de `U19` corta en 8,5–14 µs (`tps2663.pdf` p. 8), así que un sobreimpulso de ~100 µs le da tiempo. La pérdida al 49 % es 1,29 W (p. 7), no 1,74 W: la carcasa sube 22,7 K. El derating sin disipador (potencia plena hasta 63 °C, −2,85 %/°C) deja el 49 % hasta unos 81 °C de aire |
| **Veredicto** | **FIRMABLE CON CONDICIÓN**: la nota de recorte de la serie WI versionada, o la constante por escrito de TRACO; y las 3 muestras de §9.4 de la propuesta midiendo, con `R32`/`R33` montadas, el valor estático y el pico de un alivio de carga contra 16,19 V |

### P4 — +5 V de rack: Mornsun K7805T-1000R3 (`PS3`)

| | |
|---|---|
| **Qué hace** | El +5 V de la fila B y, por `R20`, el `+5V_AUX` de la telemetría, del detector de D-F4 y de `J6` (el módulo 2): 0,8 A y 4,0 W (`ladrillo_budget.py`), no los 0,5 A y 2,5 W de la tabla de la propuesta (§2) |
| **Lo que aguanta** | Su carga: el 80 % de 1 A, con un 96 % admitido a 62,6 °C (`derating_budget.py`) |
| **Lo que falla** | (a) **Es un buck no aislado** («Non-isolated», p. 1) **sin OVP ni umbral de sobrecorriente publicados**: solo «Short-circuit Protection: Continuous, self-recovery» (p. 2). `check_absmax.py` lo modela con el OVP de 6,75 V de la IRM-45-5 retirada. (b) **`+5V_AUX` cuelga antes de `F4`, y el crowbar del riel está después** (§3.5). (c) La ventana del crowbar son 0,21 V (sano ≤ 5,30 V, disparo desde 5,51 V), y el K78 declara hasta 150 mV de desviación ante un escalón del 25 % y 150 mVpp de rizado por debajo del 20 % de carga (p. 2, nota ②). El modelo usa 75 mVpp y ningún transitorio. (d) Es la única pieza SMD que JLC no monta: «No esta en LCSC: se suelda a mano o se consigna a JLC» (`bom.csv`, fila `PS3`) |
| **Veredicto** | **FIRMABLE CON CONDICIÓN**: su avería modelada como entrada puenteada a salida, igual que el #334 en los crudos, y `+5V_AUX` cubierta (§3.5); la ventana del crowbar con su transitorio y su rizado a carga ligera; y el umbral de sobrecorriente pedido a Mornsun. **La propuesta se equivoca con la alternativa:** la RECOM RPMB5.0-2.0 sí declara UVLO, sobrecorriente ≥ 120 % y temperatura («fully protected module (UVLO, SCP, OCP, OTP)», `recom_rpmb20.pdf` p. 1 y 4) |

### P5 — el ladrillo: AE/SL TE90 primero; Mean Well GST120A / GSM120A de respaldo

| | |
|---|---|
| **Qué hace** | Los 24 V de fuera: 65,36 W pedidos en el peor caso declarado (`ladrillo_budget.py`) |
| **Lo que aguanta** | La potencia: 82,5 W a 45 °C, +17,14 W. Sus cuatro protecciones se recuperan solas (`ae-TE90-datasheet.pdf` p. 2) |
| **Lo que falla** | (a) **La referencia pide otro enchufe** (§3.2). (b) **La selectividad con `U16` cuelga de una cifra típica.** El máximo de `ILIM` (4,818 A) queda un 1,2 % por debajo del 130 % de 3,75 A (4,875 A), el borde bajo de «Overload Protection 130% to 180% of rating, hiccup mode», y la hoja avisa: «All specifications are typical at nominal input, full load, at 25°C ambient unless noted» (p. 2). Si el TE90 entra en hiccup antes de que `U16` corte, el MSP430 se apaga con él (§3.7). La propuesta no le hace a AE la pregunta 12 del pliego (umbrales y tiempos de cada protección): solo se la hace a Mean Well (§6). (c) **`D1` conduce antes que su sobretensión** (§3.8). (d) **El respaldo Mean Well se enclava.** Su OVP actúa desde el 105 % (25,2 V) con «Shut down o/p voltage, re-power on to recover», y la tolerancia del modelo de 24 V es ±3,0 % (24,72 V) (`meanwell-GST120A-spec.pdf` y `meanwell-GSM120A-spec.pdf` p. 2): quedan 0,48 V. Cada vez que `U16` abre a plena carga, el ladrillo pierde de golpe de 2,7 a 4,8 A, y un sobreimpulso del 2 % lo deja enclavado. El pliego ya lo dice: «Si un evento que la política exige reintentar deja ese enclavamiento, la referencia no cumple por sí sola» (§4.1). (e) Los dos respaldos tienen relación opuesta con PE («-V connected to AC FG» en el GST, «-V not connected to AC FG» en el GSM, p. 3), y el GSM lleva el blindaje de la clavija a FG («Outer shell connected to AC FG», p. 3) |
| **Veredicto** | **El TE90: FIRMABLE CON CONDICIÓN**: la referencia con la opción 49 y la variante escogida (§3.2, §4.2); el umbral mínimo de sobrecarga a 45 °C y su retardo garantizados por escrito por AE (pregunta 12); y `D1` recoordinado (§3.8). **El respaldo Mean Well: NO FIRMABLE AÚN**: sale de la propuesta, o entra solo si 50 cortes de `U16` a plena carga y a 45 °C no lo enclavan ninguna vez |

### P6 — el enchufe nativo: Kycon KPJX-PM-4S en el panel, cableado a `J1`

| | |
|---|---|
| **Qué hace** | El camino 1, decidido el 2026-10-22: el cordón del ladrillo entra por un receptáculo de 4 polos, y un tramo interno lo lleva a `J1` |
| **Lo que aguanta** | 7,5 A por pin a 48 V y 30 mΩ máx. por contacto (`kycon_KPJX-PM-4S.pdf` p. 1), contra 2,87 A en el peor caso |
| **Lo que falla** | (a) **BLOQUEANTE: el arnés pone en corto el ladrillo** (§3.1). (b) La línea `X1P` (la clavija para un cordón a medida, `bom-chasis.csv:3`) sobra con el camino 1. (c) El receptáculo tiene un contacto de masa («Ground: Brass, Tin Plated», p. 1), y `bom-chasis.csv` no dice adónde va. Con un Mean Well el blindaje de la clavija está en FG (p. 3): si ese contacto toca el chasis, el cordón trae un PE que D-V5 excluye. (d) Los tornillos: `bom-chasis.csv:5` pide M2,5 × 8, la hoja pide 6,60 mm más el grueso del panel, y la trasera del case es una plancha de 8 mm (`case/clearance_budget.py`) |
| **Veredicto** | **FIRMABLE CON CONDICIÓN**: el arnés rehecho (§4.1), con una puerta que cruce su mapa con la hoja del ladrillo; el contacto de masa declarado en `bom-chasis.csv` y en el mapa de H-V5-PE; y la fijación medida contra la trasera |

### P7 — la cadena de protección (placa v5-B)

| | |
|---|---|
| **Qué hace** | M5 y el tope de M3: `U16` (TPS26631) en latch, con `LM74502`/`Q2`, el `MSP430FR2111` con FRAM y `SW1`; `U19` con `L2` (SRP1265A-220M) y `D10` en la rama de `U1`; el Schottky del negativo; los tiristores de D-F6 |
| **Lo que aguanta** | El núcleo es el mínimo que firman M3 y M5, y sus guiones salen en verde: 17,40 V de pico en `U1` en el peor caso (`check_absmax.py`). Enchufar con la salida viva lo cubre `U16`, abierto durante su retardo de UVLO y su rampa |
| **Lo que falla** | (a) **El temporizador de `U16` del guion no es el de la placa** (§3.7). (b) **`D1` está mal coordinado con el ladrillo** (§3.8). (c) **Los crowbars no tienen filtro.** `REF_CB1` a `REF_CB4` solo tocan su divisor y su `TL431` (netlist), así que disparan en microsegundos con cualquier pico; en el digital eso ya cae dentro del transitorio del URB (§3.4). (d) **La inversión solo se bloquea en el positivo.** `Q2` está entre `+24V_RAW` y `+24V_PROT`, y `GND24` va de `J1.2` a `NT1` y de ahí al chasis por `J5` (netlist). Con una clavija ajena cableada al revés y de salida a tierra, `GND24`, `GNDA` y el chasis quedan a +24 V sobre PE, y cualquier equipo con tierra unido por audio o USB cierra el lazo, limitado solo por la sobrecarga de esa fuente (inferencia, no de una hoja). §9.3 pide bloquear la inversión y recuperar al corregir. (e) **Piezas sin trabajo demostrable.** `D12` (S1M de salida a entrada de `U1`) viene del LM2941, y el LT1963A dice «No Protection Diodes Needed» (`lt1963a-rev-g-2021-02.pdf` p. 1) y aguanta «reverse voltages from output to input» (p. 19). `D10` (SMBJ16A) no conduce en ningún caso modelado (V_BR 17,8–19,7 V contra 17,40 V, `bourns_smbj.pdf` p. 2), y frente a una fuente rígida tampoco sujetaría `U1` por debajo de 20 V (V_C 26,0 V). Ningún fusible de riel tiene apertura garantizada contra lo que lo alimenta (#476). (f) El texto de §9 publica cifras de antes del 25-10 (§3.9) |
| **Veredicto** | **NO FIRMABLE AÚN.** Falta: el temporizador de `U16` corregido en el guion y en el firmware, o `PGTH` cableado para que PGOOD suba (§3.7); `D1` con V_BR por encima del OVP del TE90 (§3.8); filtro en las referencias de los crowbars, o el digital retirado (§4.5); y la inversión con una fuente ajena a tierra resuelta: bloqueo del retorno, o escrita en §9.3 como fuera de contrato. `D10`, `D12` y los fusibles van a la firma como simplificaciones opcionales (§4.6) |

---

## 3. Defectos ejecutables

No son opiniones sobre la propuesta: son cosas que están mal en el árbol hoy.
Cada una lleva su issue.

### 3.1 BLOQUEANTE — el arnés de `X1` pone en corto el ladrillo (P6) · #487

`bom-chasis.csv:2`: «Pines 1 y 2 = +24 V, 3 y 4 = retorno … 1+2 -> J1.1
(+24V_RAW), 3+4 -> J1.2 (GND24)». La opción 49 del TE90 es «Pins 1,3 = (+);
pins 2,4 = (-)» (`ae-TE90-datasheet.pdf` p. 6), y el R7B de Mean Well es
1 = +Vo, 2 = −Vo, 3 = −Vo, 4 = +Vo (`meanwell-GSM120A-spec.pdf` p. 3). En los
dos ladrillos, los pines 1 y 2 son de polo contrario: el arnés une + y − en
`J1.1`, delante de `D1`, del `LM74502` y de `U16`. El ladrillo entra en hiccup
sin fin y nada de la cadena lo ve.

Ninguna puerta de la v5 lee `bom-chasis.csv`. La propuesta ya avisaba de que
«que un enchufe encaje no dice que la polaridad sea la buena» (§4), y el aviso
no llegó a la BOM del chasis.

**Cierra:** el arnés de §4.1; una puerta que cruce el mapa de `X1` con la hoja
del ladrillo declarado; y un paso de bring-up que compruebe la polaridad de
`X1` con cada ladrillo antes de conectar `J1`.

### 3.2 ALTA — la referencia del TE90 pide un barril (P5, P6) · #488

«The “03” in the standard model number is replaced by the applicable digits
below» (`ae-TE90-datasheet.pdf` p. 6). `TE90A2403F01` es el modelo estándar,
con un barril de 2,5 × 5,5 mm; el 4 polos del camino 1 es la opción 49. Para
la salida unida a la tierra de red, «insert a “B” in the part number where the
“A” is located» (nota 3, p. 5). La referencia es `TE90A2449F01` o
`TE90B2449F01`.

`TE90A2403F01` está en 15 líneas de 9 archivos: la propuesta,
`ladrillo_budget.py`, `curvas.py`, `recuperacion_budget.py`, `check_bringup.py`,
`test_curvas.py`, `medidas.csv`, `docs/references.md` y
`docs/modules/01-power-supply.md`.

**Cierra:** la referencia con el «49» y la variante de §4.2 en todos esos
sitios, y el acople KPP-4P ↔ KPJX-PM-4S confirmado por AE (pregunta 19 del
pliego).

### 3.3 ALTA — D-F4 en rack: la placa no tiene los interruptores que los papeles conservan (P1) · #489

v5 §7, fila D-F4 (l. 622): «`D-F4` gobierna los pines `SHDN` de `U1`/`U2` …
y los interruptores de carga del par de rack …, que **se quedan dentro**». El
censo, T23 (l. 132): «detector analógico con un hilo sobre los interruptores de
carga conservados». `secuencia_budget.py:9` lo repite.

En la placa, `+12V_RAW_RACK` va por `F2` y `R29` a `J3`, y `-12V_RAW_RACK` por
`F3` a `J3`, sin actuador. El `Remote` de `PS1` (pin 6) está al aire, y las dos
salidas de `U20` (LM393B) van a `SHDN_CASCADE` (netlist).

La razón de la v4 eran «dos fuentes independientes y un bus ajeno sin límite de
falta» (v4 l. 695–700). Con un solo módulo doble puede haber desaparecido, pero
la hoja del THN 30 no dice si sus dos salidas caen juntas. #339 corrigió el
sujeto en el papel; esta es la mitad que no llegó a la placa.

**Cierra:** §4.4.

### 3.4 ALTA — el cuarto tiristor: sin firma, y dentro del transitorio del URB (P2, P7) · #490

D-F6 es «**crowbar** en los rieles de rack, y solo ahí» (v4 l. 299), y la v4
resolvió el digital con un requisito: «el **+5 V digital no lleva crowbar**:
que lo que reciba `PS6` aguante 6,75 V pasa a ser requisito al módulo 2» (v4
l. 56–58). La firma de D-V4 lo repite: «Falta demostrar la supervivencia
digital; no se le firma un crowbar ni una protección adicional por inferencia
de M3» (v5 l. 799–800).

Aun así, la placa lleva `SCR4` entre `+5V_DIG` y `GNDD`, `check_absmax.py:57–61`
lo justifica por M3, y la BOM, `absmax.csv`, la propuesta y #476 lo cuentan
como D-F6. Entró con b5daa46 (2026-10-22) sin decisión citada.

Y se dispara solo. `check_absmax.py` da «digital+5 sano<=5.33V | disparo
5.36..5.96V»: 30 mV. El URB declara una desviación de ±5 % típica y ±8 %
máxima ante un escalón del 25 % (`mornsun_urb_ymd20wr3.pdf` p. 2). Con un
alivio de carga (los N657 bajando de cómputo, un USB que se suelta), la salida
llega a unos 5,6 V típicos y 5,7 V máximos, dentro de la banda de disparo, y
`REF_CB4` no tiene condensador. `SCR4` pone en corto el digital, los cuatro
N657 se reinician y el MSP430 no se entera. Si el URB, en vez de hacer hiccup,
limita en continuo (110–190 % de 4 A, p. 2), `F5` (4 A) puede abrir: visita al
taller.

**Cierra:** §4.5.

### 3.5 ALTA — el +5 V de rack, modelado como una IRM, y `+5V_AUX` fuera de su crowbar (P4, P7) · #491

`RACK_RIELES["rack+5"]` de `check_absmax.py` lleva `"ovp_max_v": 6.75`, el OVP
de la IRM-45-5 (v4 l. 53–55) que se fue con D-F7, y un pliegue de 2,50 A sin
fuente. El K78 es un buck no aislado («Non-isolated», p. 1) y no publica ni
OVP ni umbral de sobrecorriente (p. 2).

En la placa, `+5V_AUX` sale de `+5V_RAW_RACK` por `R20`, **antes** de `F4`, y
`SCR3` está **después** (netlist). `check_absmax.py` diseña `F4` para abrir tras
el disparo («F4 <= 1.8 A2s < 72 A2s»). Una avería del K78 que pase su entrada a
su salida (el interruptor alto en corto, la típica de un buck: inferencia, no
de su hoja) dispara `SCR3`, `F4` abre como está diseñado, y `+5V_AUX` se queda
en la salida del K78 sin nada que la sujete. Los INA226 (6 V máx. de
alimentación, `ina226.pdf` p. 4), el resto de la telemetría, `U20` y `J6`, que
alimenta al módulo 2, verían hasta 24 V.

Y aun sin avería: el disparo de `SCR3` llega a 6,11 V, por encima de los 6 V de
los INA226, y `absmax.csv` no los tiene como víctimas: su fila del riel es
«Invitados rack +5V ve 6.11 V <= 6.30 V» (`check_absmax.py`).

**Cierra:** el K78 modelado con la entrada puenteada a la salida, como el #334
en los crudos; `+5V_AUX` detrás de `F4` y `SCR3`, con su propio tope, o con `F4`
incapaz de abrir antes de que `U16` enclave; y las víctimas de `+5V_AUX` en
`absmax.csv`.

### 3.6 MEDIA — `curvas.py` cita una frase de derating que las hojas de TRACO no tienen (P1, P2, P3) · #492

`curvas.py:36–38` atribuye al THN 30-2422WI, en su p. 2, «Operating
temperature range -40C to +85C, derating above 65C without heatsink, max case
temperature +105C», y `curvas.py:45–47` lo mismo al THN 20 con 75 °C. La hoja
del THN 30 dice «Operating temp. range: –40°C to +80°C and up to 85°C with heat
sink» (p. 1) y, para el derating, «Depending on model — See application note:
www.tracopower.com/thn30wi-cc/» (p. 3). La del THN 20 dice «–40°C to +75°C,
–40°C to +85°C (with heatsink THN-HS1)» (p. 3).

Las curvas de los dos THN no salen de ninguna hoja versionada, y
`derating_budget.py` pone su rojo encima de ellas. La del URB acaba en el 50 %
a 85 °C, y su hoja da +95 °C de máximo para la salida de 5 V (p. 3), con la
curva en una figura. El paso 7 de `medidas.csv` pide «<= 85» °C de carcasa a
45 °C de ambiente para los THN, y esos 85 °C no son de carcasa: en sus hojas,
85 °C es el ambiente con disipador, y la carcasa admite 105 °C (p. 3).

Las notas bajan como PDF desde la ficha de cada serie y están versionadas:
`traco_thn30wi_characteristic_curves.pdf` (THN 30-2422WI en pp. 11–12) y
`traco_thn20wi_characteristic_curves.pdf` (THN 20-2413WI en pp. 7–8). En
convección natural y sin disipador, el THN 30-2422WI da potencia plena hasta
54 °C y cae 2,31 puntos por grado; el THN 20-2413WI, hasta 63 °C y 2,85 puntos
por grado. Los dos llegan a cero hacia los 100–102 °C (lecturas de figura, como
todas las de esta nota). Con ellas, `PS4` pasa de un rojo a 90,2 °C de aire a
uno hacia los 81 °C. `PS1` se sale: por la corriente del +12 V pide el 84 % y la
curva se lo da hasta 61 °C, con el aire a 62,6 °C. Por potencia total, que es
el eje de la figura, pide el 62 % y cabe hasta 70,6 °C. Las curvas entran en
`curvas.py` con esa lectura decidida (§4.7): con la de hoy,
`derating_budget.py` sale rojo.

**Cierra:** las notas de derating de TRACO versionadas, o su respuesta por
escrito, y las curvas rehechas; con ellas, la cuenta de la carcasa de `PS1`
(P1) y los criterios del paso 7.

### 3.7 MEDIA — `recuperacion_budget.py` usa un temporizador de `U16` que la placa no activa (P5, P7) · #493

`T_CB_MAX_S = 31e-3  # tps2663.pdf p. 8: tCB(dly) a 2 x I_OL`
(`recuperacion_budget.py:142`), y el aserto de la l. 487 pide que la
confirmación de sano (`T_CONFIRMA_SANO_S` = 200 ms) cubra «la rampa de U16 mas
su tCB». Pero «The 2 × I(OL) pulse current support is activated only after
PGOOD goes high» (`tps2663.pdf` p. 23), y en la placa `PGTH` de `U16` (pin 16)
va a `GND24` y `PGOOD` (pin 17) está al aire: PGOOD no sube nunca. Con `MODE`
al aire, el TPS26631 limita a 1 × «for a maximum duration of tCL_PLIM(dly)» y
después enclava (Tabla 8-1, p. 28): de 129 a 202 ms (p. 9).

La rampa de `U16` son 19,0 ms (el propio guion). 19,0 + 202 = 221 ms, más que
los 200 ms de la confirmación: con el temporizador que vale, el aserto sale
rojo.

Y se suma a la selectividad de P5. Si el TE90 entra en hiccup durante esos
hasta 202 ms, el MSP430, que vive de `+24V_PROT`, se apaga con él. Si eso pasa
después de confirmar, la FRAM dice «sano» y el intento no se cuenta, y la FSM
del guion solo modela el colapso antes de confirmar.

**Cierra:** el temporizador de la placa en el guion; la confirmación de sano
por encima de 221 ms en el firmware, o `PGTH` cableado para que PGOOD suba; la
FSM contando un colapso que llegue poco después de confirmar; y el umbral
mínimo del TE90 garantizado por AE (P5).

### 3.8 MEDIA — `D1` conduce antes que la sobretensión del TE90 (P5, P7) · #494

`D1` (SMBJ26CA) está entre `+24V_RAW` y `GND24`, en `J1`, delante de `Q2` y de
`U16` (netlist). Empieza a conducir entre 28,9 y 31,9 V (V_BR,
`bourns_smbj.pdf` p. 2; la BOM monta el de Littelfuse, cuya hoja no está
versionada). El TE90 corta por sobretensión entre el 130 y el 150 %, de 31,2 a
36,0 V, en hiccup (`ae-TE90-datasheet.pdf` p. 2).

Si el lazo del ladrillo falla hacia arriba, `D1` sujeta la entrada por debajo
de ese OVP, que no llega a disparar, y se come la sobrecarga del ladrillo
(130–180 % de 3,75 A, p. 2) a unos 30 V: del orden de 150 W, contra 5 W en
régimen permanente (`bourns_smbj.pdf`). Lo probable es que acabe en corto y
deje `J1` en corto aunque se cambie el ladrillo. El OVP de `U16` (32,7 V) está
detrás y no lo alivia.

**Cierra:** un TVS con V_BR mínima por encima de 36 V, comprobado contra `C10`
(100 nF de 50 V), `Q2`, `U16`, la cadena de `U18` y el pico de enchufar en
caliente; o un fusible delante de `D1`.

### 3.9 BAJA — la propuesta publica cifras y piezas viejas (todas) · #495

- §1 sigue con «cuatro módulos TRACO» y con LEMO o EN3 como conector: el URB y
  el camino 1 no llegaron.
- §2: el +5 V de rack a 0,5 A / 2,5 W (son 0,8 A / 4,0 W); la RPMB «sin UVLO
  declarado» (lo declara, p. 1 y 4); «Hot Plug: Unavailable» en la p. 1 (está
  en la 2).
- §4 y §5: las caídas, a 2,68 A (el guion da 2,867 A en el peor caso).
- §6: a AE no se le hace la pregunta 12.
- §9.1: «18,08 V < 20,0 V» (l. 149) y la nota de #475, con «18,11 V» y «el
  `SMBJ16A` recorta en `U1 IN`» (l. 145), son de antes del 25-10: hoy son
  17,40 V y el `SMBJ16A` no conduce. Los «40,8 mV de los +811 mV» (l. 141) son
  de la cascada a 650 mA.
- §9.2: la ventana de 20 / 18 / 30 V (l. 163) no es la de la placa (17,9 /
  16,8 / 32,7 V, la nota de la l. 165). «Gastan intento: … sobrecarga de un
  riel» (l. 167) solo vale para el riel de `U19`, el único cuyo `FLT` llega al
  MCU.
- §9.3: la lista de piezas (l. 184) no tiene `L2`.
- Páginas: el pinout del R7B y el cable de Mean Well están en la p. 3, no en la
  2 (l. 75, 83 y 97).

**Cierra:** la propuesta enmendada antes de la firma.

### 3.10 Fuera de la fuente: la ventana IEC del case

El case conserva el recorte IEC de 48 × 27,5 mm (`case/cad/params.scad`,
`iec_ancho` / `iec_alto`) y `case/clearance_budget.py` sigue razonando sobre
él, cuando D-V1 sacó la red de la caja (v5 l. 716–719). Con el camino 1, lo
que va en la trasera es el KPJX-PM-4S con sus dos M2,5. Va como comentario al
#130, que es donde vive ese recorte.

---

## 4. Lo que decide Samuel

### 4.1 El arnés de `X1`

| Opción | Qué es | Lo que cuesta |
|---|---|---|
| **Un pin por polo** | `X1.1` → `J1.1` (+24 V), `X1.2` → `J1.2` (retorno), 3 y 4 sin conectar | El bucle de contactos pasa de 30 a 60 mΩ: +86 mV y +0,25 W a 2,867 A, contra +13,37 V de holgura; 2,87 A por pin contra 7,5 A. `ladrillo_budget.py` cambia su constante del conector |
| **Dos pines por polo, para un solo ladrillo** | TE90 opción 49: 1+3 → `J1.1`, 2+4 → `J1.2` | Un arnés por fabricante: con el otro ladrillo, otra vez un corto |

**Lectura de la junta:** con un pin por polo, cualquier mini-DIN de 4 polos
da polaridad buena, inversión bloqueada o 0 V, y nunca un corto. Las tres
lentes encontraron el corto por separado; dos proponen esta salida, y la
tercera el arnés para un solo ladrillo, apoyada en el contrato exclusivo.

### 4.2 La variante del TE90: A o B

«A» deja la salida flotante; «B» une el común de salida a la tierra de red (nota
3, p. 5). Con M2, el chasis va al retorno de continua: con «A», el chasis no
toca PE más que por la fuga del ladrillo (<4 mA de salida a tierra, p. 2); con
«B», el retorno y el
chasis quedan atados a tierra desde el ladrillo, con el lazo que eso abre hacia
otros equipos con tierra por el audio. Es H-V5-PE, y lo decide su mapa. La
variante no cambia el caso de §2 P7 (d): ese viene de una fuente ajena.

### 4.3 El respaldo del ladrillo

Retirar el Mean Well, y quedarse sin respaldo calificado hasta que haya otro
que no se enclave; o mantenerlo con el ensayo de P5. Dos lentes lo condicionan
a ese ensayo o a un rearme acreditado, y la tercera pide quedarse con uno solo
de los dos, el que case con la variante del TE90.

### 4.4 D-F4 en el par de rack

| Opción | Qué pide |
|---|---|
| **Restituir** | Dos interruptores de carga en ±12 V, un segundo canal de detector y su punto 2b de bring-up. Placa: reruteo |
| **Firmar su retiro** | Que el sujeto se fue con los dos módulos: hoy es un solo THN 30 doble. Pide que TRACO confirme por escrito que una falta en una salida baja las dos, un punto de banco «los dos o ninguno», y enmendar v5 §7, el T23 del censo y `secuencia_budget.py` |

### 4.5 T19: el tiristor del +5 V digital

| Opción | Qué pide |
|---|---|
| **Retirarlo** | `SCR4` y su disparo sin montar, sin rerutear, y el requisito pasa al módulo 2, como en la v4: que su entrada de 5 V aguante el OVP máximo del URB, 8,0 V (p. 2). El módulo 2 es nuestro |
| **Adoptarlo con nombre propio** | Una decisión nueva, no D-F6; un filtro en `REF_CB4` más largo que la recuperación del URB (500 µs máx., p. 2) y comprobado contra la subida de su OVP, o una referencia más estrecha. Placa: componentes nuevos |

### 4.6 Simplificaciones que la firma puede tomar o dejar

- `D12` sin montar: el LT1963A no la necesita (§2, P7). `D13`, la de `U2`, se
  queda.
- `D10` sin montar, o con su trabajo escrito: no conduce en ningún caso
  modelado.
- `F2` a `F5` a 0 Ω en la misma huella, o con su trabajo escrito: ninguno tiene
  apertura garantizada contra su convertidor (#476). Con `F4` a 0 Ω, además,
  `+5V_AUX` no se queda sin tope tras el disparo: `SCR3` la sujeta hasta que
  `U16` enclava (§3.5).
- `PS2` y `PS3` a THN 20-2411WI: una familia, un proveedor y OVP publicado.
  Cuesta reruteo y el rendimiento garantizado del digital (P2).
- `L3` también SRP1265A-220M, y `R32`/`R33` con la misma referencia al 0,1 %
  que `R45`/`R46`: dos referencias menos. `L3` cambia de huella.

### 4.7 Cómo se lee el derating de `PS1`

La curva de TRACO está en potencia de salida, y `PS1` lleva sus dos salidas
desiguales: el +12 V al 84 % de su corriente, el −12 V al 40 % y el total al
62 %. `derating_budget.py` toma la mayor de las fracciones (§3.6).

| Opción | Qué pasa | Qué pide |
|---|---|---|
| **Por potencia total** | `PS1` cabe hasta 70,6 °C de aire: +8,0 K | La guarda deja de mirar la corriente de cada salida, y TRACO confirma por escrito que la curva vale con las salidas desiguales |
| **Por la mayor fracción, como hoy** | `PS1` se sale a 61 °C: 1,6 K por debajo del aire de diseño | Un cambio de placa o de carga. Con el disipador `THN-HS1` (13,8 K/W típ., p. 4) la curva da el 84 % hasta 64,2 °C: +1,6 K. O menos +12 V: la pantalla (#480) son 550 mA de los 1,05 A |

En las dos, la carcasa se mide con criterio de 100 °C (P1).

---

## 5. Qué falta para firmar

| | |
|---|---|
| **Papel** | El arnés (§3.1), la referencia del TE90 (§3.2), la cita de `curvas.py` (§3.6), el temporizador de `U16` en el guion (§3.7), el modelo del +5 V de rack y las víctimas de `+5V_AUX` (§3.5), y la propuesta enmendada (§3.9) |
| **Gratis: preguntas** | **TRACO:** la regulación cruzada por debajo del 25 %, la desviación transitoria máxima del THN 20 y del THN 30 (sus notas solo traen capturas típicas), si el THN 30 baja las dos salidas a la vez, y si su derating vale por potencia total con las salidas desiguales (§4.7). La constante de recorte y las curvas de derating ya están en sus notas (P3, §3.6). **AE:** la pregunta 12 (el umbral mínimo de sobrecarga a 45 °C y su retardo) y la 19 (el acople con el KPJX). **Mornsun:** el umbral de sobrecorriente del K78. **Mean Well**, solo si el respaldo sigue: el sobreimpulso al soltar el 100 % de carga |
| **BOM, sin rerutear** | `D1` con V_BR mínima por encima de 36 V (§3.8); y si se retira, `SCR4` sin montar (§4.5) |
| **Firmware** | La confirmación de sano por encima de 221 ms, o la que salga del temporizador corregido (§3.7) |
| **Placa** | D-F4 en rack, si se restituye (§4.4); el filtro de los crowbars, si el digital se queda (§4.5); el bloqueo del retorno, si se elige (P7); y la toma de `+5V_AUX`, si se mueve (§3.5) |
| **Banco** | El −12 V a carga ligera (P1); la carcasa de `PS1` (P1); las 3 muestras del THN 20 con el recorte y el alivio de carga (P3); el arranque con la carga declarada entera; y la polaridad de `X1` con cada ladrillo antes de conectar `J1` (§3.1) |

## 6. Lo que la junta no pudo comprobar

- La correspondencia física cara a cara entre KPJX-PM-4S y KPPX-4P: su dibujo
  no trae texto. §3.1 no depende de ella, porque en las dos hojas de ladrillo
  los pines 1 y 2 tienen polaridad opuesta.
- ~~Las notas de TRACO (derating `thn20wi-cc` y `thn30wi-cc`, recorte
  `thn20wi-adj`): la web pinta las curvas sin PDF descargable.~~ Sí bajan,
  desde el panel «Application Notes» de la ficha de cada serie, y están
  versionadas (P3, §3.6).
- La curva del TE90 a 45 °C y la del URB, que son imágenes.
- Cómo falla un K78: su hoja no lo dice, y §3.5 parte de cómo falla un buck.
- El firmware del MSP430: solo la FSM de `recuperacion_budget.py`.
- La hoja del SMBJ26CA de Littelfuse que monta la BOM: las cifras de §3.8 son
  de la de Bourns.
- Precios.
