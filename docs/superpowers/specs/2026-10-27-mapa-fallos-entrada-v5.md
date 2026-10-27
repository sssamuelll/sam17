# Mapa de fallos de la entrada v5: del ladrillo a los DC-DC

**Fecha**: 2026-10-27 · **Estado**: mapa de papel de `H-V5-CORTO`
([v5](2026-09-05-fuente-v5-ladrillo-design.md) §9.2); no firma nada, no elige
piezas y no da por contestado ningún HUECO de fabricante ·
**Aplica** las decisiones de Samuel del 2026-10-27: el ladrillo es el
`TE90A2449F01` certificado (variante A, la salida sin unir a la tierra de red;
62368-1); un corto en su cordón cautivo, aguas arriba de nuestro receptáculo,
es responsabilidad del ladrillo certificado; y el chasis va al retorno de
continua (M2, firmada el 2026-09-08), así que un corto contra el chasis es un
corto contra el retorno ·
**Lee**: v5 §3, §9, §9.2 y §9.3; [pliego](2026-09-08-pliego-ladrillo.md) §4.1,
§5 y L15; [R5](2026-09-08-huecos-dv5-resolucion.md) `H-V5-CORTO`;
[junta de piezas v5](2026-10-25-junta-fuente-v5-piezas.md); y en
`hardware/01-power-supply/v5/`: `bom.csv`, `bom-chasis.csv`, la netlist
`kicad/sam17-power-v5.net`, `check_absmax.py`, `check_arnes.py`,
`ladrillo_budget.py`, `recuperacion_budget.py` y `medidas.csv` ·
**Va con**: la fila `H-V5-CORTO` de v5 §9.2 y la banda de `U16` con el 1 %
de `R11` en `recuperacion_budget.py` (§4.2) · **No toca**: la placa ni el
valor de ninguna pieza

---

## 1. En cristiano

1. **Detrás de `U16` todo corto franco tiene quien lo corte.** De la salida de
   `U16` a la entrada de cada convertidor, `U16` limita a 4,14–4,86 A durante
   202 ms como mucho y se enclava; el MSP430 lo reintenta tres veces y
   abandona. El ladrillo no se entera si su disparo real queda por encima de
   esa banda.
2. **Delante de `U16` no corta nada nuestro.** El cordón, la clavija, el
   receptáculo del panel, los 0,3 m de arnés, `J1` y el cobre hasta la
   entrada de `U16` solo los limita el ladrillo. Contra un corto franco, su
   hiccup, del que la hoja no da ni una cifra. Contra un corto parcial, nada
   hasta el 130–180 % de 3,75 A: **de 117 a 162 W** sostenidos dentro de la
   falta, sin un tiempo límite publicado.
3. **La decisión de hoy se lleva el cordón, no el resto.** El cordón cautivo y
   su clavija son del ladrillo certificado. El receptáculo, el arnés y el
   tramo de `J1` a `U16` siguen siendo nuestros, y en ellos nada nuestro para
   un corto parcial. Ahí queda viva la parte de `H-PL-ABANDONO-FUENTE` que M5
   no cubre: contra un corto franco en ese tramo, el ladrillo reintenta sin
   fin.
4. **El arnés aguanta, probablemente, y no está demostrado.** 16 AWG a 6,75 A
   son 0,60 W/m, y la única tabla de ampacidad citada en el repo da 7,9 A a
   45 °C para un cable más fino. Pero el cable no tiene referencia ni clase de
   aislamiento, y el aire del cajón son 62,6 °C. Contra un corto franco
   depende del pico del hiccup, que no se conoce.
5. **Un + contra el chasis delante de `U16` vuelve por `J5`, `NT1` y `Q7`.**
   Ni `J5`, ni su hilo al chasis, ni `NT1` tienen una cifra de corriente en
   el repo, y el hilo no está en ninguna BOM. En un corto franco, `Q7` pierde
   la puerta y la corriente pasa por su diodo.
6. **Dos cifras de los papeles no son lo que parecían.** Los 2,4 W no
   son la media del hiccup: son la I²R de un cordón de 16 AWG y 2 m llevando
   6,75 A continuos (§4.1). Y la banda de `U16` no cuenta el 1 % de `R11`: con
   él, el techo son 4,866 A, a 9 mA del disparo típico del ladrillo y no a
   60 (§4.2).

## 2. El recorrido y quién corta en él

De la netlist (`kicad/sam17-power-v5.net`), del ladrillo hacia dentro:

```text
TE90 ── cordón cautivo ── clavija KPPX-4P ║ receptáculo KPJX-PM-4S (X1, en el panel)
     ── arnés 16 AWG, 0,3 m ── J1.1 = +24V_RAW : D1, C10, U15, R85, TP1, fuente de Q2
                               J1.2 = RET24_RAW: D1, drenador de Q7
     ── Q2 ── +24V_PROT: R12, R64 → U18 (MSP430), IN de U16
     ── U16 ── +24V_SW : C14, PS1..PS5 (ningún fusible de entrada por módulo)
retorno: PS*.−Vin, C14, C10 … ── GND24 ── fuente de Q7
         GND24 ── NT1 ── GNDA ── J5 ── chasis (M2)
```

| Elemento | Qué hace ante un corto | Cifra | Fuente |
|---|---|---|---|
| TE90, sobrecarga | hiccup desde el 130–180 % de 3,75 A | **4,875–6,75 A, típicos a 25 °C** («All specifications are typical at nominal input, full load, at 25°C ambient unless noted») | `ae-TE90-datasheet.pdf` p. 2; 3,75 A en p. 5 |
| TE90, cortocircuito | «Hiccup mode, auto-recovery» | ni pico, ni encendido, ni apagado | p. 2 |
| TE90, temperatura | «Will shutdown upon an overtemperature condition, auto-recovery» | ni umbral ni tiempo | p. 2 |
| `U16` (TPS26631), límite | 1 × I_OL: el 2 × solo existe con PGOOD alto, y `PGTH` va a `GND24` (netlist; junta §3.7) | 4,185–4,815 A con 4,02 kΩ exactos; **4,146–4,866 A** con `R11` al ±1 % (§4.2) | `tps2663.pdf` p. 7 y p. 23 |
| `U16`, disparo rápido | abre y vuelve a entrar limitando | 3 × I_OL = 12,4–14,6 A, abre en 2,2–4,5 µs; por encima de 45 A, en 1 µs | p. 7 y p. 9 |
| `U16`, duración | limita hasta `tCL_PLIM` y se enclava (`MODE` al aire); la TSD, a 165 °C, puede cortar antes | 129–202 ms | p. 9, p. 8, p. 22–23 y Tabla 8-1 en p. 28 |
| M5 (`U17`, MSP430) | un intento y tres reintentos con 1 s de espera, y abandono; solo `SW1` (≥ 2 s) rearma | 4 pulsos | `recuperacion_budget.py:158–163`; `medidas.csv` paso 2c |
| `Q2`, `Q7` | bloquean la inversión; no limitan corriente | — | junta P7 (d); `lm74502.pdf` p. 1 |
| `R64` | alimenta el MSP430 desde `+24V_PROT` | 1,2 kΩ: 20–21 mA con su rama en corto | `bom.csv` |

**Lo que devuelve la caja a un corto delante de `Q2`.** `U16` no bloquea la
corriente inversa sin un FET externo: `B_GATE` y `DRV` van al aire (netlist;
`tps2663.pdf` p. 1 y p. 21). El `LM74502` «does not have reverse current
blocking» (`lm74502.pdf` p. 1). Lo que corta la devolución es que `Q2` se
apaga cuando `+24V_RAW`, que es su `EN/UVLO`, cae por debajo de 1,027–1,235 V
(p. 5), con la puerta abajo en 2 µs (p. 6); después bloquea su diodo. `Q7`
hace lo mismo en el retorno, porque su puerta cuelga de `+24V_RAW` por `R85`.
Así que un corto franco delante de `Q2` recibe de la caja, como mucho, la
energía de `C14` (½ × 100 µF × 25,2² = **31,8 mJ**) más la capacidad interna
de los convertidores, que no se publica («Input Filter: Internal Pi-Type»,
`traco_thn30wi.pdf` y `traco_thn20wi.pdf` p. 2). En un corto parcial
`+24V_RAW` no cae y no hay devolución.

## 3. El mapa

Columnas: qué limita, corriente y duración en el peor caso, energía o
potencia, qué tiene que aguantarlo y si su hoja lo cubre, y dueño. **Nada
nuestro** marca los tramos donde ninguna pieza nuestra para un corto
parcial. La potencia en la falta es V × I: 24 V nominales y, entre
paréntesis, 25,2 V, el +5 % de `ladrillo_budget.py:141`.

### 3.1 Delante de `U16`: solo el ladrillo

| Fallo | Qué lo limita | Corriente y duración | Energía o potencia | Qué lo aguanta, y si su hoja lo cubre | Dueño |
|---|---|---|---|---|---|
| **A1** Cordón cautivo, franco + a − | cortocircuito del TE90, hiccup | pico, encendido y apagado sin publicar (p. 2); sin fin mientras dure | HUECO. Los 2,4 W no son esta cifra (§4.1) | el cordón y la clavija, bajo la certificación del ladrillo (DEMKO D-08123, EN IEC 62368-1:2020, `ae-TE90-DEMKO-EN62368.pdf` p. 1) | **ladrillo**; cifras: `H-MF-HICCUP` (AE) |
| **A2** Cordón, parcial | nada hasta la sobrecarga del TE90 | hasta 4,875–6,75 A típicos; la OTP no publica umbral ni tiempo | **117–162 W** en la falta (123–170 W) | ladrillo | **ladrillo**; cifras: `H-MF-SOSTENIDA` y `H-MF-PS` (AE) |
| **A3** Cordón contra chasis | — | el cordón no toca nuestro chasis: el blindaje de la clavija («Inner Shield: Copper Alloy», `kycon_KPPX-4P.pdf` p. 1) da con el contacto de masa del receptáculo, que va sin conectar (`bom-chasis.csv`, `X1`; `medidas.csv` paso 0). Si el conductor + toca una pieza metálica unida a `J5`, es la fila C3 | — | — | ladrillo; qué metal es chasis: `H-MF-CHASIS` |
| **B1** Clavija–receptáculo, franco entre polos | cortocircuito del TE90 | como A1 | HUECO | 7,5 A por pin a 48 V DC y 30 mΩ máx. por contacto (`kycon_KPJX-PM-4S.pdf` y `kycon_KPPX-4P.pdf` p. 1): es un régimen continuo, y el pico del hiccup no tiene contra qué compararse | clavija: ladrillo; receptáculo: **nuestro**; `H-MF-HICCUP` |
| **B2** Clavija–receptáculo, parcial entre polos (pin doblado, suciedad, contacto carbonizado) | **nada nuestro**; la sobrecarga del TE90 | 4,875–6,75 A típicos, sin tiempo | **117–162 W** dentro del cuerpo (123–170 W) | el receptáculo es de PBT UL94 V-0; la clavija, de ABS UL94 HB con inserto de nailon UL94 V-2 (p. 1 de cada hoja). Ninguna hoja da una potencia admisible dentro del cuerpo: no hay un aguante que acreditar, hay un fuego que evitar | receptáculo: **nuestro**; clavija: ladrillo |
| **B3** Clavija–receptáculo contra chasis | el contacto de masa va sin conectar; un pin + contra una pieza unida a `J5` es C3 | — | — | — | nuestro |
| **C1** Arnés `X1`→`J1` o `J1`, franco | cortocircuito del TE90 | pulsos del hiccup sin cifras; sin fin | HUECO | el cable no tiene referencia («Cable 16 AWG rojo y negro», sin fabricante, `bom-chasis.csv`) ni hay en el repo un I²t de 16 AWG; `J1` (MaiXu MX126-5.0-02P) no tiene hoja en el repo | **nuestro**; `H-MF-HICCUP` y `H-MF-ARNES` |
| **C2** Arnés o `J1`, parcial | **nada nuestro**; la sobrecarga del TE90 | 4,875–6,75 A típicos, sin tiempo | **117–162 W** en la falta (123–170 W); el cobre del arnés, 0,60 W/m a 6,75 A | §5 | **nuestro**; `H-MF-ARNES` |
| **C3** + contra chasis: el arnés o `J1` contra una pieza unida a `J5` | el TE90. Vuelve por chasis → `J5` → `GNDA` → `NT1` → `GND24` → `Q7` → `J1.2` (netlist) | franco: pulsos del hiccup por el **diodo** de `Q7`, que se queda sin puerta al caer `+24V_RAW`; parcial: hasta 6,75 A por su canal, sin tiempo | franco: ≤ 1 V × I_pico en `Q7` (V_SD máx. 1 V a 14 A, `csd18534q5a.pdf` p. 3); parcial: 6,75² × 15 mΩ = 0,68 W en `Q7` (`ladrillo_budget.py:168`) | `Q7`: 3,1 W y 229 A pulsados (p. 1) cubren el parcial; el franco espera al pico. `J5` (Vogt 3866A.68, `check_huellas.py`), su hilo al chasis, que no está en `bom-chasis.csv`, y `NT1` (NetTie de pads de 2,0 mm, `sam17-power-v5.kicad_pcb`): sin cifra de corriente | **nuestro**; `H-MF-CHASIS` |
| **C4** − contra chasis | no hay sobrecorriente | la vuelta se reparte entre `Q7` y chasis → `J5` → `NT1` | — | nada se calienta, pero puentea `Q7`: mientras dure, una fuente ajena a tierra conectada al revés vuelve a poner el chasis a +24 V sobre PE (junta P7 (d)), y nada lo detecta | nuestro; `H-V5-PE` |
| **D1** Franco + a − entre `J1` y la entrada de `U16`: el cobre, `D1` en corto (el modo de fallo de un TVS), `C10` en corto, `U15` de `VS` a `GND` o `U16` de `IN` a `GND` | cortocircuito del TE90 | pulsos del hiccup, sin fin; la caja devuelve ≤ 31,8 mJ más la capacidad interna (§2) | HUECO | el cobre de `+24V_RAW` y `+24V_PROT`; `Q2`/`Q7` solo ven la devolución, 2 µs | **nuestro**; `H-MF-HICCUP` |
| **D2** Parcial entre `J1` y `U16`: `C10` fisurado (MLCC 0805 entre `+24V_RAW` y `GND24`, que cierra por `Q7`), cobre carbonizado, `D1` con fuga | **nada nuestro**; la sobrecarga del TE90 | 4,875–6,75 A típicos, sin tiempo | **117–162 W** en la falta (123–170 W) | — | **nuestro** |
| **D3** + contra chasis entre `J1` y `U16` | como C3 | | | | **nuestro**; `H-MF-CHASIS` |
| **D4** La rama del MSP430: `D2`, `C7` o la entrada de `U18` en corto | `R64` | 20–21 mA (24 y 25,2 V / 1,2 kΩ), sin fin | **0,48–0,53 W en `R64`** | `R64` es una 0805 de 1/8 W por su código (`0805W8F1201T5E`; ESTIMADO, sin hoja en el repo): cuatro veces su potencia, acaba abriendo. El MSP430 se apaga, `R83` baja `SHDN` y `U16` abre (`medidas.csv` paso 2c, `shdn_U16_con_MCU_en_reset_v`): la caja queda apagada | nuestro; `H-MF-PIEZAS` |

**Al quitar el corto.** El TE90 se recupera solo (p. 2), `U16` arranca al
subir su UVLO y el MSP430, con lo que diga su FRAM. Ningún corto de esta
tabla pasa por M5: **el abandono de §9.3 no existe delante de `U16`**, y
contra un franco ahí el ladrillo reintenta sin fin. Lo único que M5 cuenta es
el apagón, si pilla un intento en prueba (junta §3.7).

### 3.2 Detrás de `U16`: corta `U16`, y M5 abandona

| Fallo | Qué lo limita | Corriente y duración | Energía o potencia | Qué lo aguanta, y si su hoja lo cubre | Dueño |
|---|---|---|---|---|---|
| **E1** `+24V_SW`, franco + a −: el cobre, `C14` en corto, la entrada de cualquier convertidor | `U16`: disparo rápido, después 1 × I_OL hasta `tCL_PLIM`, y se enclava. M5: 4 pulsos con 1 s, y abandona | pico: decenas de amperios durante microsegundos (por encima de 45 A abre en 1 µs; entre 12,4–14,6 A y 45 A, en ≤ 4,5 µs); después 4,146–4,866 A durante ≤ 202 ms; cuatro veces | en `U16`, ≤ 25,2 V × 4,866 A × 0,202 s = **24,8 J** por pulso, ≤ 99 J los cuatro; en la falta, casi nada más `C14`: 31,8 mJ | `U16`: su TSD lo saca antes de los 202 ms si se calienta (p. 22–23). `Q2`/`Q7`: 45 A durante 1 µs contra 229 A pulsados (p. 1) y ≤ 4,866² × 15 mΩ = 0,35 W en canal. Receptáculo: 4,866 A < 7,5 A por pin. Arnés: 4,866² × 0,202 = 4,8 A²s por pulso. El TE90 no dispara si su umbral real a 45 °C pasa de 4,866 A (`H-MF-SELECTIVIDAD`); si dispara, el pulso se acorta y M5 cuenta igual el colapso («corto con colapso de V_in: 4 pulsos exactos y ABANDONADO persistente», autoprueba de `recuperacion_budget.py`) | nuestro, **cubierto** |
| **E2** `+24V_SW`, parcial | **nada** mientras la falta más la carga no pase del límite de `U16`; por encima, como E1 | hasta 4,146 A sin disparar en cualquier pieza, y hasta 4,866 A en una de banda alta; sin tiempo | hasta **99–117 W** en la falta (24 V × 4,146–4,866 A) con la carga en cero, menos lo que se lleve la carga | — | **nuestro**: el umbral es nuestro, y `U16` no distingue una falta de una carga |
| **E3** + de `+24V_SW` contra chasis | `U16`, como E1; vuelve por `J5` → `NT1` → `Q7` | ≤ 4,866 A ≤ 202 ms, 4 pulsos | — | `J5`, su hilo y `NT1` siguen sin cifra (`H-MF-CHASIS`), pero aquí la cota es la de `U16` | nuestro |
| **E4** Un convertidor que falla en corto a su entrada | como E1 si es franco y como E2 si es parcial | | | TRACO recomienda un fusible lento por módulo, 6 A en el THN 30 y 4 A en el THN 20, «The need of an external fuse has to be assessed in the final application» (`traco_thn30wi.pdf` y `traco_thn20wi.pdf` p. 2). La placa no lleva ninguno y `U16` hace ese trabajo contra el franco. Contra un parcial por debajo de 4 A tampoco abriría ese fusible | nuestro |

**Al quitar el corto.** `U16` sigue enclavado (Tabla 8-1, p. 28); tras los
cuatro pulsos M5 lo deja abandonado, y solo `SW1` lo rearma
(`recuperacion_budget.py:163`).

### 3.3 Cortos de pieza que no son un corto de potencia

| Fallo | Qué pasa | Cifra | Dueño |
|---|---|---|---|
| Puerta de `Q2` o de `Q7` en corto, incluido `D20` | no hay corriente de falta, pero la carga pasa por el diodo del MOSFET | ≤ 1 V × 2,889 A = 2,9 W (V_SD máx. a 14 A, `csd18534q5a.pdf` p. 3; la corriente del cordón en su peor caso, `ladrillo_budget.py`); a 50 °C/W (p. 3) son 145 K sobre el aire, por encima de los 150 °C de unión (p. 1) con cualquier aire del cajón | nuestro; `H-MF-PIEZAS`. Nada lo ve en servicio: solo el banco, una vez (`medidas.csv` paso 1, caída de `Q7` ≤ 60 mV) |

## 4. Las cifras de los papeles, revisadas

### 4.1 Los 2,4 W del corto franco

Salen de la propuesta (`2026-10-22-fuente-v5-piezas-propuesta.md` l. 179):
«≤ 2,4 W con un corto franco (6,75 A × 52,6 mΩ de bucle)». La cuenta da:
6,75² × 0,0526 = 2,40 W, y con los 52,8 mΩ de R5 (`H-V5-CALIBRE`), 2,41 W.
No vale como cota, por tres razones:

- **No es una media.** Es la I²R de una corriente constante.
- **No es la corriente del hiccup.** 6,75 A es el techo de la *sobrecarga*;
  con un corto franco actúa la protección de *cortocircuito*, cuyo pico no
  publica la p. 2. Nada dice que el pulso se quede por debajo de 6,75 A.
- **No es el cordón del TE90.** 52,6 mΩ es el cordón de escenario del guion,
  16 AWG y 2 m (`ladrillo_budget.py:175–176`). Kycon recomienda 18 AWG para
  la clavija (`kycon_KPPX-4P.pdf` p. 1, «18 AWG. for Power Wire»), y el
  calibre y el largo del cordón de la opción 49 son la pregunta 19 del pliego.

La cifra real es la resistencia del cordón por la media de i² en un periodo
del hiccup: P = R_cordón × (1/T) ∫ i² dt. Pide la forma del pulso, que es
`H-MF-HICCUP`. Este mapa no usa los 2,4 W.

### 4.2 La banda de `U16`

4,185–4,815 A es la fila de `tps2663.pdf` p. 7 para R_ILIM = 4,02 kΩ exactos.
`R11` es E96 al 1 % (`0805W8F4021T5E` en `bom.csv`), e I_OL va como
1/R_ILIM (ec. 5, p. 22):

```text
18,1 / 4,02 = 4,5025 A nominal (la fila de la p. 7 lo redondea a 4,5)
× 0,93 / 1,01 = 4,146 A         × 1,07 / 0,99 = 4,866 A
margen al disparo típico del TE90:  4,875 − 4,815 = 60 mA (1,2 %)  sin R11
                                    4,875 − 4,866 =  9 mA (0,2 %)  con R11
```

Y eso antes del coeficiente térmico de `R11`, que no tiene hoja en el repo.
`recuperacion_budget.py` (`corriente_limite_tps26631_a`) usaba la banda sin
`R11`, y la junta §3.7 también («4,82 A en lo alto de su banda»). La función
ya la cuenta (`TOL_R_ILIM_FRAC`, también para `R34` en `U19`); su aserto de
selectividad sigue en verde, y con un 1,2 % de tolerancia sale rojo. El
pico de `U1` en el #334 no cambia (17,40 V). El mapa no cambia de veredicto,
porque la selectividad ya colgaba de que AE confirme su umbral a 45 °C
(pregunta 12 del pliego; preguntas 1 y 3 del correo del caso P-258801). El suelo sigue holgado: 4,146 / 2,889 = 1,435 veces la
corriente del cordón en su peor caso, contra el 1,3 que pide el guion.

### 4.3 Las demás

| Cifra | Comprobación |
|---|---|
| `tCL_PLIM` 202 ms máx., y enclava | p. 9; `MODE` al aire = «Latch» (p. 8) y «There after Latches OFF» (Tabla 8-1, p. 28). Correcta |
| 4,875 A de disparo mínimo | 1,30 × 3,75 A (`ae-TE90-datasheet.pdf` p. 2 y p. 5). Correcta, y **típica a 25 °C** (nota de la p. 2) |
| 117 W en un parcial que no dispara | 24 V × 4,875 A = 117 W. Correcta, pero es el **suelo** de la banda: un ladrillo que dispara al 180 % sostiene 6,75 A, **162 W** (170 W a 25,2 V). Hasta que AE diga la mayor corriente que sostiene sin disparar, el mapa usa la banda entera |

## 5. El arnés contra el peor caso del ladrillo

**Lo que hay.** «Cable 16 AWG rojo y negro», 0,3 m, de `X1` a `J1`
(`bom-chasis.csv`), sin fabricante, referencia, clase de aislamiento ni
temperatura. Con los 0,0132 Ω/m del guion (`ladrillo_budget.py:175`, cobre a
20 °C) y ρ_Cu = 0,01724 Ω·mm²/m, la sección es 0,01724 / 0,0132 = 1,31 mm².

| Caso | Corriente y tiempo | Lo que le pasa al arnés | Veredicto |
|---|---|---|---|
| Servicio | 2,889 A continuos (`ladrillo_budget.py`, peor caso del cordón) | 0,11 W/m por conductor | sobra |
| Corto detrás de `U16` (E1) | ≤ 4,866 A durante ≤ 202 ms, 4 pulsos | 4,8 A²s por pulso | sobra |
| Corto parcial delante de `U16`, que no dispara el TE90 | hasta 6,75 A típicos, sin tiempo | 6,75² × 0,0132 = **0,60 W/m** por conductor; 0,36 W en los 0,6 m de cobre | **aguanta, ESTIMADO** (abajo) |
| Corto franco delante de `U16` | pulsos del hiccup | sin pico ni ciclo de trabajo no hay I²t ni media | **HUECO** (`H-MF-HICCUP`) |

**Por qué ESTIMADO.** La única ampacidad del repo es la que cita la propuesta
(l. 87): la tabla de Lapp, DIN VDE 0298-4, que no está versionada, da 10 A
para 1,0 mm² a 30 °C, y con el factor 0,79 de 45 °C, unos 7,9 A. 16 AWG
tiene 1,31 mm², un 31 % más de cobre, así que 6,75 A caben a 45 °C. Pero no
está demostrado:

- el cable no tiene referencia, y sin clase de aislamiento no hay
  temperatura máxima contra la que medir;
- el aire del cajón son 62,6 °C (`derating_budget.py`, «sala de 45 C +
  chimenea pesimista»), y el factor de la tabla a esa temperatura no está en
  el repo;
- los 6,75 A son típicos, y el máximo real lo dice AE (`H-MF-SOSTENIDA`).

**Lo que va con él.** El receptáculo `KPJX-PM-4S` lleva la misma corriente
por dos pines por polo: 6,75 A caben en 7,5 A aunque un solo pin la lleve
entera. En sus cuatro contactos, 4 × 3,375² × 30 mΩ = 1,37 W, y el
receptáculo trabaja hasta 75 °C (`kycon_KPJX-PM-4S.pdf` p. 1): 12,4 K sobre
los 62,6 °C del cajón. Si esos 1,37 W caben en 12,4 K se mide
(`H-MF-RECEPTACULO`). `J1` (MaiXu MX126-5.0-02P, C5188434) no tiene hoja en el
repo (`H-MF-ARNES`).

**Veredicto.** Con todas las cifras del repo, el arnés sobrevive al peor caso
sostenido del ladrillo; queda en ESTIMADO hasta que el cable tenga
referencia con clase de aislamiento y su ampacidad con el aire del cajón, y
`J1` su hoja. Contra un corto franco no hay veredicto sin el pulso del hiccup.

## 6. Dónde nada nuestro para un corto parcial

| Tramo | Qué lo limita | Potencia en la falta, peor caso | Dueño tras la decisión del 2026-10-27 |
|---|---|---|---|
| Cordón cautivo y clavija (A2, B2) | la sobrecarga del TE90 | 117–162 W (123–170 W) | **ladrillo**, bajo su certificación |
| Receptáculo `X1` (B2) | la sobrecarga del TE90 | 117–162 W (123–170 W) | **nuestro** |
| Arnés y `J1` (C2) | la sobrecarga del TE90 | 117–162 W (123–170 W) | **nuestro** |
| De `J1` a la entrada de `U16` (D2) | la sobrecarga del TE90 | 117–162 W (123–170 W) | **nuestro** |
| + contra chasis delante de `U16`, por `J5`, `NT1` y `Q7` (C3, D3) | la sobrecarga del TE90 | 117–162 W (123–170 W) | **nuestro**, cruzado con `H-V5-PE` |
| Detrás de `U16`, por debajo de su límite (E2, E4) | el límite de `U16` | 99–117 W, menos la carga | **nuestro**: es nuestro umbral |

**Lo que deja la decisión de hoy.** El tramo nuestro delante de `U16` es
corto: el receptáculo, 0,3 m de arnés, `J1` y el cobre hasta `U16`. Pero queda
entero fuera de M5: contra un franco el ladrillo reintenta sin fin, y contra
un parcial por debajo de su umbral no dispara. Es el resto de
`H-PL-ABANDONO-FUENTE` (pliego §4.1 y §6; v5 §9, D-V4) que la decisión de
hoy no mueve, porque esas piezas son nuestras.

El árbol ya descarta una salida: **un fusible en `X1` no lo resuelve.**
Tendría que dejar pasar el límite de `U16`, hasta 4,866 A durante 202 ms y
cuatro veces (junta §3.8 lo dijo para el fusible delante de `D1`), y un
fusible que aguanta eso no abre con un parcial por debajo de su nominal: a
4,5 A son 108 W en la falta. La salida que casa con la decisión de hoy es
tratar ese tramo como el cordón, protegido por el ladrillo certificado, con
cada pieza dimensionada para la mayor corriente que AE diga que sostiene sin
disparar. Eso es una decisión de Samuel, no una consecuencia de este mapa.

## 7. HUECOS y quién los contesta

| HUECO | Qué falta | Quién lo contesta | Qué filas mueve |
|---|---|---|---|
| `H-MF-HICCUP` | pico, tiempo encendido y tiempo apagado del hiccup con un corto franco en el extremo del cordón; resistencia del cordón de la opción 49 | **AE**, en el seguimiento del caso P-258801; pliego preguntas 15 y 19 | A1, B1, C1, C3 franco, D1; §4.1 |
| `H-MF-SOSTENIDA` | la mayor corriente que sostiene sin disparar, a 45 °C, y cuánto tiempo antes de que actúe su OTP | **AE**, en el seguimiento del caso P-258801 | A2, B2, C2, C3, D2; §5 |
| `H-MF-PS` | clase PS/LPS de la salida. Ni el informe CB (IEC 60950-1, `ae-TE90-CB-cert.pdf`) ni el certificado DEMKO (`ae-TE90-DEMKO-EN62368.pdf`) la dan | **AE**, en el seguimiento del caso P-258801 | de ella depende qué le exige 62368-1 al tramo nuestro delante de `U16` y a la caja; la norma no está en el repo |
| `H-MF-SELECTIVIDAD` | disparo mínimo garantizado de la sobrecarga a 45 °C, contra 4,866 A | **AE**: pregunta 12 del pliego, hecha como preguntas 1 y 3 del correo del caso P-258801 | E1 |
| `H-MF-ARNES` | referencia del cable de `X1` a `J1`, con clase de aislamiento y su ampacidad con el aire del cajón; su I²t; la hoja de `J1` | diseño | C1, C2; §5 |
| `H-MF-CHASIS` | corriente admisible de `J5`; el hilo de `J5` al chasis, que no está en `bom-chasis.csv`; el cobre de `NT1`; qué piezas metálicas son chasis (la escuadra del enchufe, la base) | diseño, junto con `H-V5-PE` | A3, B3, C3, C4, D3, E3 |
| `H-MF-R11` | ~~la banda de `U16` con la tolerancia de `R11`~~ **contada en `recuperacion_budget.py` (§4.2)**; falta su coeficiente térmico, sin hoja de UniOhm en el repo | diseño | E1; §4.2 |
| `H-MF-RECEPTACULO` | temperatura del `KPJX-PM-4S` a 6,75 A con el aire a 62,6 °C, contra sus 75 °C | medida | B2; §5 |
| `H-MF-PIEZAS` | la potencia de `R64` con la rama del MSP430 en corto (sin hoja); `Q2`/`Q7` conduciendo por el diodo sin que nada lo vea en servicio | diseño | D4; §3.3 |
| sin nombre, no bloquea | capacidad interna de entrada de los THN y del URB | TRACO, Mornsun | la devolución de §2 y la energía de E1 en la falta: por encima de 31,8 mJ, sin cambiar ningún veredicto |

## 8. Qué cierra este papel y qué no

**Cierra la parte de papel de `H-V5-CORTO`** tal como la pide R5 en su
criterio de aceptación: «Un mapa del conjunto debe asignar cada posición de
fallo a un elemento físico que cubra el recorrido, con hojas locales y
comparación de envolventes». Cada posición de §3 tiene su elemento, o dice
que no lo tiene y de quién es. Incluye el tramo de cable expuesto (A, B y C),
el corto contra el chasis con su lazo real (C3, D3, E3), el del retorno (C4)
y la descarga desde la caja (§2).

**No cierra** los números de AE, los HUECOS de diseño de §7, ni el ensayo que
pide R5: «En ensayo controlado se verifica cada recorrido, la limitación o
interrupción, el estado de los rieles y la recuperación declarada». El banco
ya tiene el corto franco detrás de `U16` (`medidas.csv` paso 2c,
`pulsos_reintento_ante_corto`). Le faltarían, sin tocar `medidas.csv` aquí:

- un + contra el chasis delante de `U16`, con una fuente de banco limitada a
  6,75 A, midiendo `Q7`, `J5` y `NT1`;
- el receptáculo y el arnés a 6,75 A sostenidos con el aire a 62,6 °C, y su
  estado después.

La fila `H-V5-CORTO` de v5 §9.2 se enmienda con la decisión de hoy y con este
mapa por separado.
