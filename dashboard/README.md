# Dashboard de estadísticas (Streamlit)

**Responsable:** Elkin · **Versión objetivo:** v1.5 · **Estado:** diseño aprobado, en desarrollo

Página web local, a pantalla completa, que lee la base de datos PostgreSQL y muestra estadísticas de ocupación de las aulas. La aplicación de escritorio solo abre esta página en el navegador con el botón *Abrir estadísticas*.

## Contenido aprobado

- Filtros de aula y rango de fechas, y botón Actualizar.
- Cuatro tarjetas: ocupación actual, estado del aula, personas ahora y promedio del día.
- Gráfico de ocupación en el tiempo con una línea de capacidad al 100 %.
- Barras por hora con las horas pico resaltadas.
- Resumen estadístico: media, desviación estándar, máximo y mínimo.
- Tabla de entradas y salidas recientes.
- Paneles "Próximamente": anomalías, predicción con intervalo de confianza, validación y ocupación real contra programada.
- Opcional: histograma de la ocupación e intervalo de confianza de la media.

## Reglas

- Se desarrolla con un aula simulada (`AULA-SIM`). Los datos simulados van siempre rotulados y **no se mezclan** con los reales al presentar resultados.
- Las credenciales de la base se leen del archivo `.env` (ver `src/CAMPUS_INTELLIGENCE/.env.example`); nunca se escriben en el código.
- Se trabaja en la rama `elkin/dashboard` y se une a `main` solo cuando está probado.
