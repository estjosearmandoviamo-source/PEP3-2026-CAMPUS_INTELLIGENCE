# Explicación matemática · Dashboard VisionCampus

> Borrador para Elkin. Léelo, cámbialo con tus propias palabras y pruébate respondiendo cada punto en voz alta, porque el docente va a preguntar.

## 1. Qué datos usa el dashboard

El dashboard lee dos tablas. `ocupacion_historico` guarda una medición por minuto con la cantidad de personas y el porcentaje de ocupación (personas ÷ capacidad × 100). `eventos` guarda cada entrada y salida. Los datos del dashboard son **simulados** (AULA-SIM) y se muestran rotulados como tales. Nunca se mezclan con datos medidos.

## 2. Medidas de resumen

Para la ocupación de un aula, cada registro es un valor $x_i$ (un porcentaje). Con $n$ registros:

- **Media** ($\bar{x}$): el promedio. Dice la ocupación típica del periodo.

$$\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$$

- **Desviación estándar** ($s$): cuánto se alejan los valores de la media. Si $s$ es grande, el aula pasa de vacía a llena con frecuencia. Si es pequeña, la ocupación es parecida todos los días.

$$s = \sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2}$$

- **Máximo** y **mínimo**: los valores extremos del periodo.

En la tarjeta del dashboard, el resumen se calcula sobre **todos** los registros del periodo, no solo del día.

## 3. Distribución e histograma

El histograma cuenta cuántos registros caen en cada intervalo de 10 %: 0–10, 10–20, …, 90–100. Muestra en qué rangos se concentra la ocupación. Si las barras están a la derecha, el aula suele estar llena; si están a la izquierda, suele estar vacía.

## 4. Intervalo de confianza del 95 % para la media

La media de una muestra no es exactamente la media "verdadera". El intervalo de confianza dice en qué rango cae la media real, con un 95 % de confianza:

$$IC_{95\%} = \bar{x} \pm 1{,}96 \cdot \frac{s}{\sqrt{n}}$$

- **1,96** es el valor de la normal estándar que deja 95 % de la probabilidad en el centro. Por eso el 95 %.
- **$s/\sqrt{n}$** se llama error estándar. Mide cuánto variaría la media si repitiéramos la medición.
- **Por qué se estrecha cuando $n$ crece:** al dividir entre $\sqrt{n}$, cada registro adicional reduce el error. Para reducir el intervalo a la mitad hay que tener cuatro veces más datos.

**Ejemplo con la tarjeta del diseño:** $\bar{x} = 68\,\%$, $s = 12{,}4\,\%$, $n = 1800$:

$$1{,}96 \cdot \frac{12{,}4}{\sqrt{1800}} \approx 0{,}57 \quad\Rightarrow\quad IC_{95\%} \approx 67{,}4\,\% – 68{,}6\,\%$$

**Punto de atención:** según la tarea, 5 días × 600 minutos dan $n = 3000$, no 1800. Con $n = 3000$ el intervalo sería más estrecho: aproximadamente 67,6 % – 68,4 %. Conviene que el dashboard use el número real de registros que devuelve la consulta, que es lo que hace `app.py`.

## 5. Datos simulados frente a datos medidos

Los datos simulados se generan con un patrón (poca gente temprano, pico de 14:00 a 16:00) más una variación aleatoria. Sirven para practicar y probar el dashboard, pero **no describen una universidad real**. Las estadísticas de AULA-SIM no demuestran nada sobre las aulas reales. Por eso el dashboard se rotula siempre y no mezcla los dos tipos de datos.

## 6. Cómo el sistema reconoce a una persona

1. **Detectar:** YOLO11n recorre cada imagen del video y dibuja un recuadro donde hay una persona. Todavía no sabe quién es, solo que hay alguien.
2. **Huella del cuerpo:** PersonReID convierte cada recuadro en una lista de números llamada **embedding**. Dos imágenes de la misma persona dan listas parecidas. Así el sistema sigue a la persona aunque salga y vuelva a entrar.
3. **Comparar:** el parecido entre dos embeddings se mide con la **similitud coseno**:

$$\text{similitud}(A, B) = \frac{A \cdot B}{\lVert A \rVert \, \lVert B \rVert}$$

Va de –1 a 1. Cuanto más cerca de 1, más parecidas son las dos listas. En el reconocimiento de personas del aula, el sistema usa un **umbral de 0,75**: si la similitud supera ese valor, se considera la misma persona.

4. **Rostros (módulo aparte, solo voluntarios):** InsightFace convierte un rostro en 512 números. Si la similitud supera el umbral de **0,50**, muestra el nombre; si no, "no conocido".

## 7. Dónde entra la probabilidad

- **La similitud no es una probabilidad.** Un valor de 0,65 no significa 65 % de probabilidad de que sea la misma persona. Es una medida de parecido. Para convertirla en probabilidad habría que calibrarla con datos.
- **La similitud es una variable aleatoria.** Cambia en cada imagen según la luz, el ángulo y la distancia. Por eso tiene media y desviación estándar, igual que la ocupación.
- **El umbral puede fallar de dos formas:**
  - **Falso positivo:** acepta a una persona que no es la correcta. Es análogo al error tipo I.
  - **Falso negativo:** rechaza a la persona correcta. Es análogo al error tipo II.
  Un umbral bajo produce más falsos positivos; uno alto produce más falsos negativos.
- **Se mide, no se afirma:** se comparan pares de la misma persona y de personas distintas, y se calculan las tasas de error con su intervalo de confianza. Con pocos voluntarios, el intervalo es ancho.
- **A futuro (v3.0):** con el teorema de Bayes se podría estimar la probabilidad de que dos imágenes sean de la misma persona, a partir de las distribuciones de similitud.

## 8. Preguntas para practicar

1. ¿Cómo sabe el sistema que hay una persona y cómo la distingue de otra?
2. ¿Qué es un embedding y qué mide la similitud coseno?
3. ¿La similitud de 0,65 significa 65 % de probabilidad? ¿Por qué no?
4. ¿Qué pasa si el umbral es muy bajo? ¿Y si es muy alto?
5. ¿Qué diferencia hay entre un falso positivo y un falso negativo?
6. ¿Qué significa el intervalo de confianza del 95 % que muestra el dashboard?
7. ¿Por qué se usaron datos simulados y cómo se evita que se mezclen con los reales?
8. ¿Qué decisión podría tomar la universidad con estos gráficos?
