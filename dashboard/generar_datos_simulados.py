"""
Genera datos simulados para AULA-SIM (aula_id = 2) en la base de práctica VisionCampus.

Uso (desde la carpeta dashboard/, con el entorno virtual activo):
    python generar_datos_simulados.py

Qué hace:
1. Borra SOLO los datos de AULA-SIM, para poder ejecutarlo varias veces sin duplicar.
2. Crea un registro de ocupación por minuto, de 08:00 a 17:59, del 10 al 14 de noviembre de 2026.
3. Crea ENTRADAS y SALIDAS coherentes con los cambios de cantidad de personas.
"""
import random
from datetime import date, datetime, time, timedelta

NOMBRE_AULA = "AULA-SIM"
CAPACIDAD = 30
FECHA_INICIO = date(2026, 11, 10)
DIAS = 5
MINUTOS_POR_DIA = 600  # 08:00 a 18:00, un registro por minuto
SEMILLA = 42           # misma semilla = mismos datos cada vez (repetible)
RUIDO = 1.2            # desviación del ruido aleatorio, en personas

# Perfil promedio de ocupación (fracción de la capacidad) por hora.
# Entre dos puntos se interpola en línea recta.
PERFIL = [
    (8, 0.15),   # poca gente al inicio
    (9, 0.35),
    (10, 0.50),
    (11, 0.60),  # subida a media mañana
    (12, 0.45),  # baja al mediodía
    (13, 0.50),
    (14, 0.80),  # pico entre 14:00 y 16:00
    (15, 0.90),
    (16, 0.85),
    (17, 0.65),
    (18, 0.50),
]


def estado_de_ocupacion(porcentaje):
    """Aplica las mismas reglas de estado que el sistema real."""
    if porcentaje == 0:
        return "VACIA"
    if porcentaje < 50:
        return "DISPONIBLE"
    if porcentaje < 80:
        return "OCUPACION MEDIA"
    if porcentaje < 100:
        return "ALTA OCUPACION"
    if porcentaje == 100:
        return "LLENA"
    return "SATURACION"


def fraccion_esperada(hora_decimal):
    """Fracción de ocupación esperada a una hora dada (14.5 significa 14:30)."""
    for (h1, f1), (h2, f2) in zip(PERFIL, PERFIL[1:]):
        if h1 <= hora_decimal <= h2:
            t = (hora_decimal - h1) / (h2 - h1)
            return f1 + t * (f2 - f1)
    return PERFIL[-1][1]


def generar_dia(rng, dia, siguiente_id):
    """
    Genera los registros de un día.
    Devuelve (ocupacion, eventos, siguiente_id):
      ocupacion: lista de dicts con las columnas de ocupacion_historico (sin aula_id)
      eventos:   lista de dicts con las columnas de eventos (sin aula_id)
    """
    ocupacion, eventos = [], []
    dentro = []  # (id_persona, hora_de_entrada) de quienes están en el aula
    inicio = datetime.combine(dia, time(8, 0))

    for minuto in range(MINUTOS_POR_DIA):
        ahora = inicio + timedelta(minutes=minuto)
        hora_decimal = 8 + minuto / 60

        # Patrón del día + variación aleatoria, limitado entre 0 y la capacidad
        esperadas = fraccion_esperada(hora_decimal) * CAPACIDAD
        cantidad = round(esperadas + rng.gauss(0, RUIDO))
        cantidad = max(0, min(CAPACIDAD, cantidad))

        porcentaje = round(cantidad / CAPACIDAD * 100, 2)
        ocupacion.append({
            "hora": ahora,
            "cantidad_personas": cantidad,
            "porcetaje_ocupacion": porcentaje,
            "estado": estado_de_ocupacion(porcentaje),
        })

        # Cambios respecto al minuto anterior generan eventos
        cambio = cantidad - len(dentro)
        if cambio > 0:
            for _ in range(cambio):
                eventos.append({"id_persona": siguiente_id, "tipo": "ENTRADA",
                                "hora": ahora, "permanecia": None})
                dentro.append((siguiente_id, ahora))
                siguiente_id += 1
        elif cambio < 0:
            for _ in range(-cambio):
                pid, entrada = dentro.pop(rng.randrange(len(dentro)))
                eventos.append({"id_persona": pid, "tipo": "SALIDA", "hora": ahora,
                                "permanecia": (ahora - entrada).total_seconds()})

    return ocupacion, eventos, siguiente_id


def main():
    from conexion import conectar  # importación aquí para que el resto del archivo se pueda probar sin base

    rng = random.Random(SEMILLA)
    conn = conectar()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM aulas WHERE aula = %s", (NOMBRE_AULA,))
            fila = cur.fetchone()
            if fila is None:
                raise SystemExit("No existe AULA-SIM en la tabla aulas. Ejecuta primero el script de tablas.")
            aula_id = fila[0]

            # Solo borra datos de AULA-SIM; los datos reales no se tocan
            cur.execute("DELETE FROM eventos WHERE aula_id = %s", (aula_id,))
            cur.execute("DELETE FROM ocupacion_historico WHERE aula_id = %s", (aula_id,))

            siguiente_id = 1
            total_ocup = total_ev = 0
            for d in range(DIAS):
                dia = FECHA_INICIO + timedelta(days=d)
                ocupacion, eventos, siguiente_id = generar_dia(rng, dia, siguiente_id)

                cur.executemany(
                    "INSERT INTO ocupacion_historico "
                    "(aula_id, hora, cantidad_personas, porcetaje_ocupacion, estado) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    [(aula_id, r["hora"], r["cantidad_personas"], r["porcetaje_ocupacion"], r["estado"])
                     for r in ocupacion],
                )
                cur.executemany(
                    "INSERT INTO eventos (id_persona, tipo, hora, permanecia, aula_id) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    [(e["id_persona"], e["tipo"], e["hora"], e["permanecia"], aula_id) for e in eventos],
                )
                total_ocup += len(ocupacion)
                total_ev += len(eventos)
                print(f"{dia}: {len(ocupacion)} registros de ocupación, {len(eventos)} eventos")

        print(f"Listo. AULA-SIM: {total_ocup} registros de ocupación y {total_ev} eventos.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
