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
| Precisión del conteo | Conteo manual contra el del sistema: tasa de error e intervalo de confianza |
| Reconocimiento facial | La similitud entre rostros se comporta como una **variable aleatoria**. El umbral de decisión produce **falsos positivos y falsos negativos**, análogos a los errores **tipo I y tipo II** |
| Fase futura | Detección de anomalías y predicción con intervalos de confianza |

**No se afirma, se mide:** cada resultado se valida comparándolo con un conteo manual.

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

## 6. Estado actual

| Componente | Estado |
|---|---|
| Detección y seguimiento (YOLO11n + PersonReID) | ✅ Funciona |
| Registro de entradas, salidas y ocupación en PostgreSQL | ✅ Funciona |
| Reconocimiento facial con voluntarios (InsightFace) | ✅ Funciona (falta calibrar el umbral) |
| Aplicación de escritorio (PySide6) | 🔧 En construcción |
| Dashboard de estadísticas (Streamlit) | 🎨 Diseño aprobado, en desarrollo |
| Análisis estadístico, anomalías y predicción | ⏳ Pendiente (v3.0) |

## 7. Equipo y responsabilidades

| Integrante | Responsabilidad |
|---|---|
| **José Armando Vía Montaño** | **Código y sistema:** visión por computadora (YOLO, PersonReID), reconocimiento facial, base de datos, aplicación de escritorio e integración. Explica el código en la defensa. |
| **Richard Hinojosa Poquechoque** | **Documentos y defensa:** informe final, Gantt con responsables, diagrama de arquitectura, privacidad, anexos y presentación. Explica el problema, la innovación y el uso de la IA. |
| **Elkin** | **Dashboard de estadísticas (Streamlit)** y **explicación de la parte matemática:** dónde entra la estadística, cómo se reconoce a una persona (embedding y similitud) y qué significan las tasas de error. |

Detalle de cada rol en la carpeta [`equipo/`](equipo/).

## 8. Organización del repositorio

| Carpeta | Contenido | Responsable |
|---|---|---|
| [`src/CAMPUS_INTELLIGENCE/`](src/CAMPUS_INTELLIGENCE/) | Código del sistema (visión, rostros, base de datos, interfaz) | José |
| [`dashboard/`](dashboard/) | Dashboard de estadísticas en Streamlit | Elkin |
| [`docs/`](docs/) | Informe, Gantt, diagramas, presentación y pruebas | Richard |
| [`database/`](database/) | Scripts y diagramas de la base de datos | José |
| [`equipo/`](equipo/) | Roles de cada integrante | Todos |
| [`resources/`](resources/) | Imágenes y videos de apoyo | Todos |
| [`tests/`](tests/) | Pruebas | Todos |

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

## 9. Versiones

| Versión | Contenido | Estado |
|---|---|---|
| `base-integracion` | Base de integración de los módulos | ✅ |
| `v0.9` | Reidentificación estable y registro de entradas y salidas | ✅ |
| `v0.95` | Reconocimiento facial, rostros en la base de datos e interfaz inicial | ✅ |
| `v1.0` | Visión y datos cerrados | 🔧 En curso |
| `v1.5` | Dashboard web en Streamlit | 🔧 En desarrollo |
| `v2.0` | Pruebas estadísticas del reconocimiento facial y unión cuerpo-rostro | ⏳ |
| `v3.0` | Estadística: media, desviación, anomalías y predicción con intervalos de confianza | ⏳ |
| `v4.0` | Pulido y cierre | ⏳ |

## 10. Cómo ejecutarlo

Requisitos: Windows 11, Python 3.12, PostgreSQL y una cámara web (se recomienda GPU NVIDIA).

```bash
cd src/CAMPUS_INTELLIGENCE
python -m venv .venv_campus
.venv_campus\Scripts\activate
pip install -r requirements_principal.txt
```

1. Copiar `.env.example` como `.env` y completar los datos de PostgreSQL.
2. Ejecutar la aplicación de escritorio: `python Interfaz/visioncampus_ui.py`

El reconocimiento facial usa además `requirements_rostros.txt`.

## 11. Documentación

- Informe actualizado del proyecto: [`docs/informe/`](docs/informe/)
- Diagrama de arquitectura: [`docs/diagramas/`](docs/diagramas/)
- Cronograma (Gantt): [`docs/gantt/`](docs/gantt/)
