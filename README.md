# VisionCampus · Campus Intelligence

**Equipo VISION CAMPUS — Unifranz, Cochabamba**
Materia: Probabilidad y Estadística I · Proyecto PEP3 2026

> **En una frase:** VisionCampus convierte una cámara común en un instrumento que **mide cuántas personas usan realmente cada aula**, y transforma esos datos en **estadísticas** para que la universidad decida con datos y no con suposiciones.

---

## 1. El problema

La universidad sabe qué aula está **programada** ("el aula P6 se usa de 8 a 10"), pero no sabe cómo se **usa realmente**:

- ¿Había 3 personas o 30?
- ¿Estuvo vacía con la luz encendida?
- ¿Estuvo llena o saturada?

Hoy esas decisiones (asignar aulas, horarios, energía, mantenimiento) se toman **con suposiciones**.

## 2. La solución

El sistema:

1. **Detecta y sigue personas** en el video de una cámara usando inteligencia artificial.
2. **Cuenta** cuántas hay en el aula y registra cada **entrada** y **salida**.
3. **Guarda** todo en una base de datos (PostgreSQL).
4. **Convierte los datos en estadísticas y gráficos**: ocupación en el tiempo, horas pico, promedio, desviación estándar, etc.

**Contar personas es solo el medio; el fin es decidir mejor con datos reales.**

## 3. ¿Dónde está la estadística?

| Parte del sistema | Concepto estadístico |
|---|---|
| Ocupación del aula a lo largo del día | Media, desviación estándar, máximo y mínimo |
| Horas pico | Distribución de frecuencias e histograma |
| Probabilidades de uso | Frecuencia observada (k/n) de que el aula tenga personas o supere el 50 % y el 80 %, con intervalo de confianza de Wilson |
| Llegadas de personas | Modelo de Poisson: probabilidad de que entre alguien en una hora |
| Distribución de la ocupación | Percentiles (mediana, P90, P95) y mapa de calor por día y hora |
| Reconocimiento facial | La similitud entre rostros se comporta como una **variable aleatoria**. El umbral de decisión produce **falsos positivos y falsos negativos**, análogos a los errores **tipo I y tipo II** |
| Fase futura | Validación contra conteo manual, detección de anomalías y predicción con intervalos de confianza |

**No se afirma, se mide:** todo se calcula con datos guardados en la base. Los datos simulados se rotulan siempre como tales y **nunca se mezclan con los reales**. Las fórmulas están explicadas en [`dashboard/EXPLICACION_MATEMATICA.md`](dashboard/EXPLICACION_MATEMATICA.md).

## 4. Privacidad

- El sistema de aulas es **anónimo por defecto**: cuenta personas, no las identifica.
- El **reconocimiento facial** es un **módulo experimental aparte**, solo con **voluntarios que autorizan** su registro, y sus datos se pueden eliminar.
- En este repositorio **no se suben** contraseñas (`.env`), fotos, rostros ni entornos virtuales.
- El modelo facial (`buffalo_l` de InsightFace) es de uso no comercial: el proyecto es **académico**.

## 5. Cómo funciona (resumen técnico)

```
Cámara ──► YOLO11n (detecta personas) ──► PersonReID (identidad de cada persona)
                                              │
                                              ▼
                         Clase AULAS: cuenta y calcula el estado del aula
                         (VACÍA · DISPONIBLE · MEDIA · ALTA · LLENA · SATURACIÓN)
                                              │
                                              ▼
                     PostgreSQL: eventos (ENTRADA/SALIDA) y ocupación cada 5 s
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
       App de escritorio (PySide6)                          Dashboard web (Streamlit)
       monitoreo en vivo y registro facial                  estadísticas y gráficos
```

## 6. Funcionalidades implementadas

**Visión y datos**
- Detección y seguimiento de personas en video en vivo (YOLO11n) con identidad estable (PersonReID).
- Conteo de personas, estado del aula (VACÍA, DISPONIBLE, OCUPACIÓN MEDIA, ALTA, LLENA, SATURACIÓN) y registro de cada ENTRADA y SALIDA.
- Guardado en PostgreSQL: tablas `aulas`, `eventos`, `ocupacion_historico` y `rostros_registrados`.

**Aplicación de escritorio (PySide6)**
- **Monitoreo:** cámara en vivo, tarjetas de personas detectadas, reconocidas, no autorizadas y sin identificar, ocupación, actividad reciente y rendimiento (FPS).
- **Registro facial:** formulario en cuatro pasos con consentimiento, guía en óvalo y malla de puntos del rostro.
- **Personas registradas:** tabla conectada a la base de datos, autorizar o desautorizar a una persona (candado) y eliminarla.
- **Modo anónimo:** oculta nombres y rostros y conserva solo el conteo.
- **Reconocimiento facial** con voluntarios (InsightFace): cuadro, nombre y similitud sobre el video; caja roja "NO AUTORIZADO" para rostros sin permiso.

**Dashboard web (Streamlit)**
- Lee la base de datos con el mismo método de conexión de la aplicación.
- Tarjetas de ocupación actual, estado, hora pico y promedio del último día.
- Gráficos de ocupación en el tiempo, ocupación promedio por hora, histograma e intervalo de confianza del 95 %.
- Probabilidades observadas, mapa de calor por día y hora, percentiles, entradas por hora y permanencia.
- Datos reales (AULA-P6) y simulados (AULA-SIM) separados y rotulados.

## 7. Estado actual

| Componente | Estado |
|---|---|
| Detección y seguimiento (YOLO11n + PersonReID) | ✅ Funciona |
| Registro de entradas, salidas y ocupación en PostgreSQL | ✅ Funciona |
| Reconocimiento facial con voluntarios (InsightFace) | ✅ Funciona (falta calibrar el umbral) |
| Aplicación de escritorio (PySide6): Monitoreo, Registro facial y Personas | ✅ Funciona |
| Aplicación de escritorio: pantalla de Configuración | 🔧 Pendiente |
| Scripts de base de datos (`database/scripts/01_schema.sql`) | ✅ Listo |
| Dashboard de estadísticas (Streamlit) con datos reales y simulados | ✅ Funciona |
| Pruebas y evidencias con capturas (`docs/pruebas/`) | ✅ Listo |
| Anomalías, predicción y validación con conteo manual | ⏳ Pendiente (v3.0) |

Limitaciones conocidas: al cerrar el programa quedan ENTRADAS sin su SALIDA, los identificadores de persona reinician en 1 en cada sesión y el umbral del reconocimiento facial aún se está calibrando. Están detalladas en [`docs/pruebas/PRUEBAS.md`](docs/pruebas/PRUEBAS.md).

## 8. Equipo y responsabilidades

| Integrante | Responsabilidad |
|---|---|
| **José Armando Vía Montaño** | **Código y sistema:** visión por computadora (YOLO, PersonReID), reconocimiento facial, base de datos, aplicación de escritorio e integración. Explica el código en la defensa. |
| **Richard Hinojosa Poquechoque** | **Documentos y defensa:** informe final, Gantt con responsables, diagrama de arquitectura, privacidad, anexos y presentación. Explica el problema, la innovación y el uso de la IA. |
| **Elkin** | **Dashboard de estadísticas (Streamlit)** y **explicación de la parte matemática:** dónde entra la estadística, cómo se reconoce a una persona (embedding y similitud) y qué significan las tasas de error. |

Detalle de cada rol en la carpeta [`equipo/`](equipo/).

## 9. Organización del repositorio

| Carpeta | Contenido | Responsable |
|---|---|---|
| [`src/CAMPUS_INTELLIGENCE/`](src/CAMPUS_INTELLIGENCE/) | Código del sistema (visión, rostros, base de datos, interfaz) | José |
| [`dashboard/`](dashboard/) | Dashboard de estadísticas en Streamlit | Elkin |
| [`docs/`](docs/) | Informe, Gantt, diagramas, presentación y [pruebas con capturas](docs/pruebas/PRUEBAS.md) | Richard |
| [`database/`](database/) | Scripts de la base de datos (`scripts/01_schema.sql`) | José |
| [`equipo/`](equipo/) | Roles de cada integrante | Todos |
| [`resources/`](resources/) | Imágenes y videos de apoyo | Todos |
| [`tests/`](tests/) | Reservada; las evidencias de funcionamiento (capturas) están en `docs/pruebas/` | Todos |

### Dentro de `src/CAMPUS_INTELLIGENCE/`

| Carpeta | Qué hace |
|---|---|
| `Logica/` | Clases principales: `AULAS` (ocupación y estados), `PersonReID` (identidad de cada persona) y `main.py` (versión de consola) |
| `Reconocimiento_Facial/` | Detectar, capturar, comparar y guardar rostros de voluntarios |
| `Base_Datos/` | Conexión a PostgreSQL (credenciales en `.env`, nunca en el código) |
| `Adaptador_Interfaz/` | Puente entre la visión y la ventana: hilo de cámara (`ProcesadorCamara`) y lógica (`VisionCampusCore`) |
| `Interfaz/` | Aplicación de escritorio PySide6 (`visioncampus_ui.py`, diseño `.ui` y estilos `.qss`) |
| `Modelos/` | Modelo YOLO11n |
| `deep-person-reid/` | Librería externa de terceros (torchreid), usada por PersonReID |

## 10. Versiones

| Versión | Contenido | Estado |
|---|---|---|
| `base-integracion` | Base de integración de los módulos | ✅ |
| `v0.9` | Reidentificación estable y registro de entradas y salidas | ✅ |
| `v0.95` | Reconocimiento facial, rostros en la base de datos e interfaz inicial | ✅ |
| `v0.97` | Registro facial completo, modo anónimo y permisos de autorización | ✅ |
| `v0.98` | Dashboard de estadísticas (Streamlit) con datos reales y simulados, scripts de base de datos y pruebas con capturas | ✅ |
| `v1.0` | Visión y datos cerrados | 🔧 En curso |
| `v1.5` | Dashboard pulido y validado con más datos reales | ⏳ |
| `v2.0` | Pruebas estadísticas del reconocimiento facial y unión cuerpo-rostro | ⏳ |
| `v3.0` | Estadística: media, desviación, anomalías y predicción con intervalos de confianza | ⏳ |
| `v4.0` | Pulido y cierre | ⏳ |

## 11. Cómo ejecutarlo

Requisitos: Windows 11, Python 3.12, PostgreSQL y una cámara web (se recomienda GPU NVIDIA).

**1. Crear la base de datos.** En PostgreSQL crea una base llamada `VisionCampus` y ejecuta el script
[`database/scripts/01_schema.sql`](database/scripts/01_schema.sql) (por ejemplo desde DBeaver). Crea las cuatro tablas y las aulas `AULA-P6` (real) y `AULA-SIM` (simulada).

**2. Configurar las credenciales.** En `src/CAMPUS_INTELLIGENCE/` copia `.env.example` como `.env` y completa `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`. El `.env` nunca se sube a GitHub.

**3. Aplicación de escritorio.**

```bash
cd src/CAMPUS_INTELLIGENCE
python -m venv .venv_campus
.venv_campus\Scripts\activate
pip install -r requirements_principal.txt
python Interfaz/visioncampus_ui.py
```

El reconocimiento facial usa además `requirements_rostros.txt`.

**4. Dashboard de estadísticas.** Desde la carpeta `dashboard/`:

```bash
cd dashboard
pip install -r requirements.txt
python generar_datos_simulados.py   # opcional: llena AULA-SIM con datos ficticios
streamlit run app.py                # se abre en http://localhost:8501
```

Más detalle en [`dashboard/README.md`](dashboard/README.md).

## 12. Documentación

- Pruebas y evidencias con capturas de pantalla: [`docs/pruebas/PRUEBAS.md`](docs/pruebas/PRUEBAS.md)
- Informe actualizado del proyecto: [`docs/informe/`](docs/informe/)
- Diagrama de arquitectura: [`docs/diagramas/`](docs/diagramas/)
- Cronograma (Gantt): [`docs/gantt/`](docs/gantt/)
