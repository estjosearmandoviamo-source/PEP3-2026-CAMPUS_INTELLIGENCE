# =====================================================================
# VISIONCAMPUS
# Cuenta y reidentifica personas en un aula usando YOLO + ReID
#
# ORGANIZACION DEL ARCHIVO
#   1. Importaciones
#   2. Configuracion (todos los numeros ajustables)
#   3. Preparacion (camara, modelos, base de datos, memoria)
#   4. Funciones auxiliares
#   5. Bucle principal (un ciclo = un frame)
#   6. Cierre del programa
# =====================================================================


# ---------------------------------------------------------------------
# 1. IMPORTACIONES
# ---------------------------------------------------------------------
import time
from datetime import datetime

import cv2
from ultralytics import YOLO

from aula import AULAS
from person_id import PersonReID
from Conexion_DB import conectar


# ---------------------------------------------------------------------
# 2. CONFIGURACION
# ---------------------------------------------------------------------
# --- Tiempos de las identidades (en segundos) ---
tiempo_maximo_perdido = 5            # sin verla este tiempo -> pasa a "perdido"
tiempo_eliminacion_tracks = 20       # ya perdido este tiempo -> se borra el track
tiempo_eliminacion_provisonal = 5    # provisional sin verse -> se borra
segundos_misma_ficha_yolo = 1.0      # cuanto vale la ficha de YOLO para reconocer rapido

# --- Confirmacion de personas nuevas ---
observaciones_para_confirmar = 3     # veces que se ve un provisional antes de ser identidad

# --- Actualizacion de la huella (embedding) ---
segundos_entre_huellas = 1.0         # cada cuanto se recalcula la huella de una persona
limite_solapamiento = 0.30           # si la tapan mas de esto, no se actualiza la huella
peso_huella_vieja = 0.90             # cuanto pesa lo ya guardado
peso_huella_nueva = 0.10             # cuanto pesa lo que se acaba de ver

# --- Base de datos ---
segundos_entre_registros_bd = 5      # cada cuanto se guarda la ocupacion


# ---------------------------------------------------------------------
# 3. PREPARACION
# ---------------------------------------------------------------------
camara = cv2.VideoCapture(0)
# cv2.namedWindow("VisionCampus", cv2.WINDOW_NORMAL)
# cv2.setWindowProperty("VisionCampus", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

modelo = YOLO("yolo11n.pt")          # otras opciones: s, m
reid = PersonReID()
aula1 = AULAS("AULA-P6", 30)

CONEXION = conectar()
CURSOR = CONEXION.cursor()

# --- Memoria del sistema ---
tracks = {}                  # personas confirmadas: clave = identidad propia (1, 2, 3...)
provisionales = {}           # candidatas aun sin confirmar: clave = ficha de YOLO
siguiente_id_identidad = 1   # contador propio de identidades
historial = []
ultimo_registro = time.time()


# ---------------------------------------------------------------------
# 4. FUNCIONES AUXILIARES
# ---------------------------------------------------------------------

# ----- 4.1 Base de datos -----

# Registrar_Evento esta desactivado para pruebas:
# def Registrar_Evento(tipo, id_persona, hora, permanencia):
#     horadb = datetime.fromtimestamp(hora)
#     try:
#         CURSOR.execute("""INSERT INTO EVENTOS (ID_PERSONA, TIPO, HORA, PERMANECIA, AULA_ID)
#                           VALUES (%s, %s, %s, %s, %s)""",
#                        (id_persona, tipo, horadb, permanencia, 1))
#         CONEXION.commit()
#     except Exception as e:
#         print("ERROR AL GUARDAR EL EVENTO EN LA BASE DE DATOS:\n", e)
#         CONEXION.rollback()


def Registrar_Ocupacion(aula_id, hora, cantidad_perso, porcentaje_ocupacion, estado):
    try:
        CURSOR.execute(
            """INSERT INTO OCUPACION_HISTORICO
               (AULA_ID, HORA, CANTIDAD_PERSONAS, PORCETAJE_OCUPACION, ESTADO)
               VALUES (%s, %s, %s, %s, %s)""",
            (aula_id, hora, cantidad_perso, porcentaje_ocupacion, estado),
        )
        CONEXION.commit()
    except Exception as e:
        print("ERROR AL GUARDAR LA OCUPACION EN LA BASE DE DATOS:\n", e)
        CONEXION.rollback()


# ----- 4.2 Geometria de cajas -----

def porcentaje_solapamiento(caja_a, caja_b):
    """Que fraccion de caja_a esta tapada por caja_b (0 a 1)."""
    a_x1, a_y1, a_x2, a_y2 = caja_a
    b_x1, b_y1, b_x2, b_y2 = caja_b

    borde_izquierdo = max(a_x1, b_x1)
    borde_derecho = min(a_x2, b_x2)
    borde_arriba = max(a_y1, b_y1)
    borde_abajo = min(a_y2, b_y2)

    ancho_tapado = borde_derecho - borde_izquierdo
    alto_tapado = borde_abajo - borde_arriba

    if ancho_tapado <= 0 or alto_tapado <= 0:
        return 0

    area_tapada = ancho_tapado * alto_tapado
    area_de_a = (a_x2 - a_x1) * (a_y2 - a_y1)
    return area_tapada / area_de_a


def mayor_solapamiento_con_otras(caja_principal, id_persona, resultado, ids):
    """El mayor solapamiento de esta caja con cualquier otra caja del frame."""
    mayor_solapamiento = 0

    for otra_caja, otro_id in zip(resultado.boxes, ids):
        if id_persona == int(otro_id):
            continue  # saltamos la propia caja

        caja_de_la_otra = otra_caja.xyxy[0].tolist()
        solapamiento = porcentaje_solapamiento(caja_principal, caja_de_la_otra)

        if solapamiento > mayor_solapamiento:
            mayor_solapamiento = solapamiento

    return mayor_solapamiento


def recortar_persona(frame, x1, y1, x2, y2):
    """Recorta la persona del frame sin salirse de los bordes. None si queda vacio."""
    alto, ancho = frame.shape[:2]
    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(ancho, int(x2))
    y2 = min(alto, int(y2))

    recorte = frame[y1:y2, x1:x2]
    if recorte.size == 0:
        return None
    return recorte


# ----- 4.3 Busqueda de identidades -----

def buscar_identidad_reciente(id_persona, ahora):
    """Camino rapido: ya tenemos un track con esta ficha de YOLO, visto hace poco?"""
    for identidad, datos in tracks.items():
        if (
            datos.get("id_yolo") == id_persona
            and datos.get("estado") in ("activo", "perdido_temporalmente")
            and ahora - datos["ultimo_visto"] <= segundos_misma_ficha_yolo
        ):
            return identidad
    return None


def buscar_mas_parecida_entre_perdidos(embedding):
    """Camino lento: compara solo contra personas que NO estan visibles ahora."""
    mejor_id = None
    mejor_similitud = 0

    for identidad, datos in tracks.items():
        if datos["estado"] == "activo":
            continue

        similitud = reid.COMPARAR_EMBEDDING(datos["embedding"], embedding)
        if similitud > mejor_similitud:
            mejor_similitud = similitud
            mejor_id = identidad

    return mejor_id, mejor_similitud


def buscar_mas_parecida_entre_provisionales(embedding):
    mejor_id = None
    mejor_similitud = 0

    for id_provisional, datos in provisionales.items():
        similitud = reid.COMPARAR_EMBEDDING(datos["embedding"], embedding)
        if similitud > mejor_similitud:
            mejor_similitud = similitud
            mejor_id = id_provisional

    return mejor_id, mejor_similitud


# ----- 4.4 Creacion de tracks -----

def crear_track(identidad, embedding, id_persona, ahora):
    return {
        "entrada": ahora,
        "ultimo_visto": ahora,
        "ultima_huella": ahora,
        "salida": None,
        "tiempo_perdido": None,
        "estado": "activo",
        "embedding": embedding,
        "id_identidad": identidad,
        "id_yolo": id_persona,
    }


# ----- 4.5 Revision y limpieza -----

def revisar_tracks_perdidos(identidades_actuales, ahora):
    """Actualiza estados (activo / perdido_temporalmente / perdido).
    Devuelve la lista de identidades que hay que eliminar."""
    ids_a_eliminar = []

    for identidad, datos in tracks.items():

        # Visible en este frame
        if identidad in identidades_actuales:
            datos["estado"] = "activo"
            continue

        tiempo_perdido = ahora - datos["ultimo_visto"]

        # Perdido definitivamente
        if tiempo_perdido > tiempo_maximo_perdido:
            if datos["estado"] != "perdido":
                datos["estado"] = "perdido"
                datos["tiempo_perdido"] = ahora
                datos["salida"] = datos["ultimo_visto"]
                permanencia = datos["salida"] - datos["entrada"]
                print(f"ID {identidad} PERDIDO")
                # Registrar_Evento("SALIDA", identidad, datos["salida"], permanencia)
            else:
                tiempo_desde_perdido = ahora - datos["tiempo_perdido"]
                if tiempo_desde_perdido > tiempo_eliminacion_tracks:
                    ids_a_eliminar.append(identidad)

        # Perdida temporal
        else:
            if datos["estado"] != "perdido_temporalmente":
                datos["estado"] = "perdido_temporalmente"
                print(f"ID {identidad} perdido temporalmente ({tiempo_perdido:.1f}s)")

    return ids_a_eliminar


def limpiar_provisionales(ahora):
    ids_a_eliminar = []

    for id_provisional, datos in provisionales.items():
        if ahora - datos["ultimo_visto"] > tiempo_eliminacion_provisonal:
            ids_a_eliminar.append(id_provisional)

    for id_provisional in ids_a_eliminar:
        del provisionales[id_provisional]


# ----- 4.6 Dibujo en pantalla -----

def dibujar_info_aula(imagen, aula):
    letra = cv2.FONT_HERSHEY_SIMPLEX
    verde = (0, 255, 0)
    cv2.putText(imagen, f"PERSONAS: {aula.personas}", (20, 20), letra, 1, verde, 1)
    cv2.putText(imagen, f"OCUPACION: {aula.ocupacion:.1f}%", (20, 40), letra, 1, verde, 1)
    cv2.putText(imagen, f"ESTADO: {aula.estado}", (20, 65), letra, 1, verde, 1)


def dibujar_id(imagen, id_mostrar, x1, y1):
    cv2.putText(
        imagen,
        f"ID: {id_mostrar}",
        (int(x1) + 42, int(y1) - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        1,
    )


# ---------------------------------------------------------------------
# 5. BUCLE PRINCIPAL  (un ciclo = un frame)
# ---------------------------------------------------------------------
while True:

    # ===== PASO 1: capturar imagen =====
    ret, frame = camara.read()
    if not ret:
        print("No se pudo obtener imagen de la camara.")
        break

    # ===== PASO 2: detectar personas con YOLO =====
    resultados = modelo.track(
        frame,
        classes=[0],
        conf=0.5,
        persist=True,
        verbose=False,
        device=0,
    )
    resultado = resultados[0]
    frame_resultados = resultado.plot(labels=False)

    # ===== PASO 3: actualizar y mostrar ocupacion del aula =====
    aula1.ACTUALIZAR_DATOS(len(resultado.boxes))
    dibujar_info_aula(frame_resultados, aula1)

    # ===== PASO 4: identificar a cada persona del frame =====
    identidades_actuales = []   # identidades visibles en ESTE frame

    if resultado.boxes.id is not None:
        ids = resultado.boxes.id

        for caja, ficha_yolo in zip(resultado.boxes, ids):

            id_persona = int(ficha_yolo)   # ficha de YOLO (temporal)
            ahora = time.time()
            x1, y1, x2, y2 = caja.xyxy[0]

            # ---------------------------------------------------------
            # 4A. CAMINO RAPIDO: ya la conocemos por su ficha de YOLO
            # ---------------------------------------------------------
            identidad_reciente = buscar_identidad_reciente(id_persona, ahora)

            if identidad_reciente is not None:
                tracks[identidad_reciente]["ultimo_visto"] = ahora
                tracks[identidad_reciente]["estado"] = "activo"

                # Actualizar huella solo si: no la tapan Y ya toca por tiempo
                caja_principal = caja.xyxy[0].tolist()
                mayor_solapamiento = mayor_solapamiento_con_otras(
                    caja_principal, id_persona, resultado, ids
                )
                segundos_desde_ultima_huella = ahora - tracks[identidad_reciente]["ultima_huella"]

                if (
                    mayor_solapamiento <= limite_solapamiento
                    and segundos_desde_ultima_huella >= segundos_entre_huellas
                ):
                    recorte_actual = recortar_persona(frame, x1, y1, x2, y2)
                    if recorte_actual is not None:
                        embedding_nuevo = reid.obtener_embedding(recorte_actual)
                        embedding_viejo = tracks[identidad_reciente]["embedding"]
                        tracks[identidad_reciente]["embedding"] = (
                            peso_huella_vieja * embedding_viejo
                            + peso_huella_nueva * embedding_nuevo
                        )
                        tracks[identidad_reciente]["ultima_huella"] = ahora

                identidades_actuales.append(identidad_reciente)
                dibujar_id(frame_resultados, identidad_reciente, x1, y1)
                continue

            # ---------------------------------------------------------
            # 4B. CAMINO LENTO: no la conocemos, calculamos su huella
            # ---------------------------------------------------------
            recorte = recortar_persona(frame, x1, y1, x2, y2)
            if recorte is None:
                continue

            embedding = reid.obtener_embedding(recorte)
            id_mostrar = id_persona   # por defecto, hasta que se confirme

            # Buscar entre las personas que NO estan visibles ahora
            mejor_id, mejor_similitud = buscar_mas_parecida_entre_perdidos(embedding)

            # ---------------------------------------------------------
            # 4B-1. Persona CONOCIDA: recuperamos su identidad
            # ---------------------------------------------------------
            if mejor_similitud >= reid.Umbral:
                id_identificado = mejor_id

                if id_persona in provisionales:
                    del provisionales[id_persona]

                # Si estaba perdida, empieza una nueva sesion de entrada
                if tracks[id_identificado]["estado"] == "perdido":
                    tracks[id_identificado]["entrada"] = ahora
                    tracks[id_identificado]["salida"] = None

                tracks[id_identificado]["ultimo_visto"] = ahora
                tracks[id_identificado]["estado"] = "activo"
                tracks[id_identificado]["id_yolo"] = id_persona

                identidades_actuales.append(id_identificado)
                id_mostrar = id_identificado

                print(
                    f"IDENTIDAD RECUPERADA | ID: {id_identificado} "
                    f"|| YOLO ID: {id_persona} || MEJOR SIMILITUD: {mejor_similitud:.2f}"
                )

            # ---------------------------------------------------------
            # 4B-2. Persona NUEVA: pasa por "provisional" antes de confirmarse
            # ---------------------------------------------------------
            else:
                id_provisional = None   # clave del provisional que sumo una observacion

                if id_persona in provisionales:
                    # Ya la veniamos observando con esta misma ficha
                    id_provisional = id_persona
                else:
                    # Quiza es un provisional que cambio de ficha de YOLO
                    mejor_id_prov, mejor_similitud_prov = buscar_mas_parecida_entre_provisionales(embedding)
                    if mejor_similitud_prov >= reid.Umbral:
                        id_provisional = mejor_id_prov

                if id_provisional is None:
                    # Primera vez que la vemos: creamos su provisional
                    provisionales[id_persona] = {
                        "observacion": 1,
                        "embedding": embedding,
                        "ultimo_visto": ahora,
                    }
                else:
                    provisionales[id_provisional]["observacion"] += 1
                    provisionales[id_provisional]["ultimo_visto"] = ahora

                    # Suficientes observaciones: se confirma como identidad nueva
                    if provisionales[id_provisional]["observacion"] >= observaciones_para_confirmar:
                        identidad_nueva = siguiente_id_identidad
                        siguiente_id_identidad += 1

                        tracks[identidad_nueva] = crear_track(identidad_nueva, embedding, id_persona, ahora)
                        identidades_actuales.append(identidad_nueva)
                        del provisionales[id_provisional]
                        id_mostrar = identidad_nueva

                        print(f"ID {identidad_nueva} NUEVO CONFIRMADO")
                        # Registrar_Evento("ENTRADA", identidad_nueva, ahora, 0)

            dibujar_id(frame_resultados, id_mostrar, x1, y1)

    # ===== PASO 5: revisar quien se perdio y limpiar memoria =====
    ahora = time.time()

    ids_a_eliminar = revisar_tracks_perdidos(identidades_actuales, ahora)
    for identidad in ids_a_eliminar:   # se borra fuera del recorrido del diccionario
        del tracks[identidad]

    limpiar_provisionales(ahora)

    # ===== PASO 6: guardar ocupacion en la base de datos =====
    if ahora - ultimo_registro >= segundos_entre_registros_bd:
        hora_actual = datetime.now()
        historial.append((hora_actual, aula1.personas))
        ultimo_registro = ahora

        print(
            f"HORA {hora_actual.strftime('%H:%M:%S')} || "
            f"{aula1.nombre} || PERSONAS {aula1.personas}"
        )
        Registrar_Ocupacion(1, hora_actual, aula1.personas, aula1.ocupacion, aula1.estado)

    # ===== PASO 7: mostrar en pantalla =====
    imagen_final = cv2.resize(frame_resultados, (1000, 600))
    cv2.imshow("VisionCampus", imagen_final)

    if cv2.waitKey(1) == ord("q"):
        break


# ---------------------------------------------------------------------
# 6. CIERRE DEL PROGRAMA
# ---------------------------------------------------------------------
camara.release()
cv2.destroyAllWindows()

CURSOR.close()
CONEXION.close()

print("\nHISTORIAL DE PERSONAS\n")
for hora, personas in historial:
    print(f"HORA : {hora.strftime('%H:%M:%S')} || PERSONAS: {personas}")
