# Dashboard de estadísticas · VisionCampus (Elkin)

Dashboard web en Streamlit con **datos simulados** (AULA-SIM). Solo hace consultas `SELECT` y no usa la tabla de rostros.

## Cómo ejecutarlo

1. Crear y activar el entorno virtual dentro de `dashboard/`:
   ```bash
   cd dashboard
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Crear la base `VisionCampus` en PostgreSQL y ejecutar el script de tablas del documento de la tarea.
3. Copiar `src/CAMPUS_INTELLIGENCE/.env.example` a `dashboard/.env` y completar tus datos. **No subas `.env` a GitHub.**
4. Generar los datos simulados:
   ```bash
   python generar_datos_simulados.py
   ```
5. Abrir el dashboard:
   ```bash
   streamlit run app.py
   ```

## Archivos

Cada archivo hace una sola cosa:

| Archivo | Qué hace | ¿Estudiarlo? |
|---|---|---|
| `app.py` | La pantalla: qué componente va y en qué posición | Sí |
| `datos.py` | Consultas a PostgreSQL (usa el `conectar()` de `Conexion_DB.py`) | Sí, es la lógica de datos |
| `estadistica.py` | Todas las fórmulas: media, intervalo de confianza, probabilidades, percentiles | Sí |
| `diseno.py` | Decoración: HTML de las tarjetas, colores y estilo de los gráficos | No |
| `estilo.css` | Solo colores y bordes (como el `.qss` de la app de escritorio) | No |
| `generar_datos_simulados.py` | Llena AULA-SIM con 5 días de datos por minuto (repetible) | Opcional |
| `requirements.txt` | Versiones de las librerías | No |
| `EXPLICACION_MATEMATICA.md` | Explicación de la parte estadística y del reconocimiento | Sí |

Orden de lectura recomendado: `datos.py` (de dónde salen los datos), `estadistica.py` (qué se calcula) y `app.py` (cómo se junta todo).

Los datos de `generar_datos_simulados.py` se generan con una semilla fija, así que siempre salen iguales.
