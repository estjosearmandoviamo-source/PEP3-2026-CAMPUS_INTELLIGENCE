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

| Archivo | Qué hace |
|---|---|
| `conexion.py` | Conexión a PostgreSQL usando `.env` |
| `generar_datos_simulados.py` | Llena AULA-SIM con 5 días de datos por minuto (repetible) |
| `app.py` | Dashboard: tarjetas, gráficos, resumen estadístico, histograma e IC 95 % |
| `requirements.txt` | Mismas versiones que el proyecto |
| `EXPLICACION_MATEMATICA.md` | Explicación de la parte estadística y del reconocimiento |

Los datos de `generar_datos_simulados.py` se generan con una semilla fija, así que siempre salen iguales.
