#![no_std]
#![no_main]

//! **Un tic tardio provocado** (papel v3, §5.2 j; issue #445).
//!
//! Una interrupcion por encima del tic (`acapara` a P0, lo que R-H1 prohibe en el instrumento)
//! espera a la actualizacion de `TIM7` y retiene la CPU `δ` microsegundos: el tic entra `δ` tarde.
//! Con `δ` de mas de un periodo, la entrada funde actualizaciones. En cada fase se comprueba que:
//!
//! - `tics_tardios` (mas de 10 µs) cuenta todas las provocadas, y `tics_fuera_de_presupuesto`
//!   (mas de 60 µs, §2.8 y R-H2), exactamente las que pasan de 60;
//! - `retraso_entrada_max_us` llega a `δ`, y no mas de 2 µs por encima;
//! - `periodos_saltados` cuenta los periodos fundidos: `δ / periodo` por provocacion;
//! - el reloj del tic (K2, §2.7) no se aparta de la pared (`embassy-time`, que corre en TIM12)
//!   mas de dos periodos, tampoco con un tic de cada dos a 80 µs, que es donde la formula
//!   anterior a K2 corria x1,5;
//! - `reloj_anomalo` se queda en 0.
//!
//! La primera fase no provoca nada y deja dormir al nucleo entre tics (`Timer`); las demas
//! provocan desde el hilo, que gira mirando `tics`. Una ranura, el maestro del banco sin esclavo,
//! como `tic_cota`. Los plazos vencidos y las recuperaciones de cada fase salen como dato, sin
//! veredicto: §2.8 da por simulacion que una trama de 25 B a 6,25 MHz vence con 87 a 93 µs.
//!
//! ```bash
//! cargo run --release --features inyeccion,reloj-hub --bin tic_tardio
//! ```

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt::Priority;
use embassy_time::{Instant, Timer};
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
use sam17_nucleo_fw::j2_banco::{bajada_del_banco, juez_del_banco, maestro_del_banco};
use sam17_nucleo_fw::j2_ejecutor::cuentas;
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::j2_tic::{self, acapara, Testigos};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Las fases que provocan: (retraso en µs, un tic tardio cada tantos, cuantas veces), con el
/// retraso creciente hasta la ultima para poder leer el maximo de cada una.
const FASES: [(u32, u32, u32); 6] = [
    (40, 16, 200),
    (70, 16, 200),
    (110, 16, 200),
    (150, 16, 200),
    (300, 16, 200),
    (80, 2, 4_000),
];
/// Lo que se aparta el reloj del tic de la pared sin que sea un fallo: la foto lee `tics` y la
/// pared una tras otra, y entre las dos puede caer un tic. ESTIMADO.
const TOLERANCIA_PERIODOS: i64 = 2;
const PERIODO: u64 = PERIODO_GIRO_US as u64;

struct Foto {
    t: Testigos,
    us: u64,
    plazos: u32,
}

fn foto() -> Foto {
    Foto {
        t: j2_tic::testigos(),
        us: Instant::now().as_micros(),
        plazos: cuentas(0).plazos_vencidos,
    }
}

#[derive(Clone, Copy, Default)]
struct Fila {
    us: u32,
    veces: u32,
    tardios: u32,
    fuera: u32,
    saltados: u32,
    anomalos: u32,
    retraso_max: u32,
    /// Periodos que conto el tic menos los de la pared.
    error: i64,
    plazos: u32,
    recuperaciones: u32,
}

fn fila(us: u32, veces: u32, a: &Foto, b: &Foto) -> Fila {
    let pared = (b.us - a.us + PERIODO / 2) / PERIODO;
    Fila {
        us,
        veces,
        tardios: b.t.tics_tardios - a.t.tics_tardios,
        fuera: b.t.tics_fuera_de_presupuesto - a.t.tics_fuera_de_presupuesto,
        saltados: b.t.periodos_saltados - a.t.periodos_saltados,
        anomalos: b.t.reloj_anomalo - a.t.reloj_anomalo,
        retraso_max: b.t.retraso_entrada_max_us,
        error: i64::from(b.t.tics.wrapping_sub(a.t.tics)) - pared as i64,
        plazos: b.plazos - a.plazos,
        recuperaciones: b.t.recuperaciones - a.t.recuperaciones,
    }
}

/// Un tic tardio de `us` cada `cada` tics, `veces` veces. El hilo gira: el golpe tiene que salir
/// despues del tic que lo dispara y antes de la actualizacion siguiente.
fn provoca(us: u32, cada: u32, veces: u32) {
    let mut siguiente = j2_tic::testigos().tics.wrapping_add(cada);
    for _ in 0..veces {
        while (j2_tic::testigos().tics.wrapping_sub(siguiente) as i32) < 0 {}
        acapara::tic_tardio(us);
        siguiente = siguiente.wrapping_add(cada);
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let _ = spawner;
    #[cfg(feature = "reloj-hub")]
    let config = usb::configuracion_hub();
    #[cfg(not(feature = "reloj-hub"))]
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = usb::iniciar(config);
    let ranura = maestro_del_banco(
        p.PE15,
        p.PG2,
        p.PG1,
        p.PA3,
        p.GPDMA1_CH0,
        p.GPDMA1_CH1,
        &p.RCC,
        Config {
            f_sck_hz: 10_000_000,
            f_cpu_hz: f_cpu,
            retardo_tsck_cuartos: 4,
        },
    );
    let mut ranuras = [const { None }; 6];
    ranuras[0] = Some(ranura);
    j2_tic::lanzar(
        ranuras,
        p.TIM7,
        PERIODO_GIRO_US,
        f_cpu,
        bajada_del_banco,
        juez_del_banco,
    );
    // SAFETY: nadie mas toca el SCB en este binario.
    unsafe {
        let mut cp = cortex_m::Peripherals::steal();
        cp.SCB.enable_icache();
        cp.SCB.enable_dcache(&mut cp.CPUID);
    }
    // Despues de `lanzar`: su puerta de R-H1 no arranca con una interrupcion por encima del tic.
    acapara::arranca(Priority::P0);
    Timer::after_millis(300).await;

    let mut filas = [Fila::default(); FASES.len() + 1];
    let a = foto();
    Timer::after_secs(2).await;
    let b = foto();
    filas[0] = fila(0, 0, &a, &b);
    for (k, &(us, cada, veces)) in FASES.iter().enumerate() {
        let a = foto();
        provoca(us, cada, veces);
        // La recuperacion del ultimo plazo, si lo hubo, y unos giros limpios.
        Timer::after_millis(20).await;
        let b = foto();
        filas[k + 1] = fila(us, veces, &a, &b);
    }

    info!(
        "tic_tardio: firmware {}, f_cpu {} Hz, periodo {} us",
        env!("SAM17_GIT"),
        f_cpu,
        PERIODO_GIRO_US
    );
    let mut fallos = 0;
    let mut max_visto = 0;
    for f in &filas {
        let saltados = f.veces * (f.us / PERIODO_GIRO_US);
        let tardios = if f.us > 10 { f.veces } else { 0 };
        let fuera = if f.us > 60 { f.veces } else { 0 };
        // El maximo es de toda la corrida: solo se lee en las fases que lo suben.
        let mira_max = f.us >= max_visto;
        max_visto = max_visto.max(f.us);
        let ok_max = !mira_max || (f.us..=f.us + 2).contains(&f.retraso_max);
        let ok = f.tardios == tardios
            && f.fuera == fuera
            && f.saltados == saltados
            && f.anomalos == 0
            && f.error.abs() <= TOLERANCIA_PERIODOS
            && ok_max;
        if !ok {
            fallos += 1;
        }
        info!(
            "tic_tardio,us={},veces={},tardios={}/{},fuera={}/{},saltados={}/{},anomalos={},retraso_max={}{=str},error_periodos={},plazos={},recuperaciones={},{=str}",
            f.us,
            f.veces,
            f.tardios,
            tardios,
            f.fuera,
            fuera,
            f.saltados,
            saltados,
            f.anomalos,
            f.retraso_max,
            if mira_max { "" } else { "(no se mira)" },
            f.error,
            f.plazos,
            f.recuperaciones,
            if ok { "ok" } else { "FALLA" }
        );
    }
    info!("tic_tardio,{}", j2_tic::testigos());
    info!(
        "tic_tardio: {} de {} fases en verde",
        filas.len() - fallos,
        filas.len()
    );
    info!("tic_tardio: fin");
    // Un `bkpt` para que `probe-rs run` termine solo y suelte la sonda.
    cortex_m::asm::bkpt();
    loop {
        Timer::after_secs(60).await;
    }
}
