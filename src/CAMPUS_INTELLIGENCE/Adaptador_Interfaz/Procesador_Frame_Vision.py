
import cv2
import time
import torch

from datetime import datetime
from pathlib import Path

from ultralytics import YOLO

from CAMPUS_INTELLIGENCE.Logica.Aulas import AULAS
from CAMPUS_INTELLIGENCE.Logica.Person_Reid import PersonReID
from CAMPUS_INTELLIGENCE.Base_Datos.Conexion_DB import conectar

from CAMPUS_INTELLIGENCE.Reconocimiento_Facial.detector import DetectorFacial
from CAMPUS_INTELLIGENCE.Reconocimiento_Facial.Comparar_Rostros import ComparadorRostros
from CAMPUS_INTELLIGENCE.Reconocimiento_Facial.Capturar_Rostro import CapturarRostro
from CAMPUS_INTELLIGENCE.Reconocimiento_Facial.registro_rostroBD import RostrosDB 
from scipy.spatial import Delaunay


class VisionCampusCore:

    # ============================================================
    # 1. INICIALIZACIÓN
    # ============================================================

    def __init__(self):

        # MODELO YOLO
        ruta_modelo = Path(__file__).resolve().parent.parent / "Modelos" / "yolo11n.pt"
        self.modelo = YOLO(str(ruta_modelo))

        # CLASE DE LAS AULAS
        self.aula1 = AULAS("AULA-P6", 30)

        # CLASE REIDENTIFICADOR
        self.reid = PersonReID()

        # CLASES PARA RECONOCIMIENTO FACIAL
        self.detector_facial = DetectorFacial()
        self.comparador_rostros = ComparadorRostros()

        self.RegistroBD = RostrosDB()
        self.comparador_rostros.cargar_desde_base( self.RegistroBD)

        self.capturador_rostros = CapturarRostro(
            self.detector_facial,
            self.comparador_rostros,  self.RegistroBD
        )

        # BASE DE DATOS
        self.CONEXION = conectar()
        self.CURSOR = self.CONEXION.cursor()

        # HISTORIAL DE OCUPACIÓN
        self.historial = []
        self.ultimo_registro = time.time()

        # HISTORIAL DE PERSONAS: MEMORIA DEL SISTEMA
        self.tracks = {}
        self.provisionales = {}

        # TIEMPOS DE PÉRDIDA
        self.tiempo_maximo_perdido = 60
        self.tiempo_eliminacion_tracks = 540
        self.tiempo_eliminacion_provisonal = 5

        self.siguiente_id_identidad = 1
        self.tiempo_cambio_huellas = 1.0

        self.segundos_para_confirmar_entidad_nueva = 3.0

        # CONTADOR DE EMBEDDINGS
        self.contador_embeddings = 0
        self.inicio_conteo = time.time()

        # ÚLTIMA IMAGEN RECIBIDA
        self.ultimo_frame = None

        # RECONOCIMIENTO FACIAL SOBRE EL VIDEO
        self.reconocimiento_activo = True
                # Interruptor para dibujar la malla y los puntos del rostro
        self.dibujar_puntos = False

    # ============================================================
    # 2. REGISTRAR EVENTOS
    # ============================================================

    def Registrar_Evento(self, tipo, id_persona, hora, permanencia):

        horadb = datetime.fromtimestamp(hora)

        if tipo == "ENTRADA":

            print(
                f"========== EVENTO ==========\n"
                f"EVENTO     : ENTRADA\n"
                f"IDENTIDAD  : {id_persona}\n"
                f"HORA       : {datetime.fromtimestamp(hora).strftime('%H:%M:%S')}\n"
                f"============================"
            )

        elif tipo == "SALIDA":

            print(
                f"========== EVENTO ==========\n"
                f"EVENTO     : SALIDA\n"
                f"IDENTIDAD  : {id_persona}\n"
                f"HORA       : {datetime.fromtimestamp(hora).strftime('%H:%M:%S')}\n"
                f"PERMANENCIA: {permanencia:.1f} segundos\n"
                f"============================"
            )

        try:

            self.CURSOR.execute(
                """
                INSERT INTO EVENTOS
                (ID_PERSONA, TIPO, HORA, PERMANECIA, AULA_ID)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (id_persona, tipo, horadb, permanencia, 1)
            )

            self.CONEXION.commit()

        except Exception as e:

            print(
                "ERROR AL GUARDAR EL EVENTO EN LA BASE DE DATOS:\n",
                e
            )

            self.CONEXION.rollback()

    # ============================================================
    # 3. REGISTRAR OCUPACIÓN
    # ============================================================

    def Registrar_Ocupacion(
        self,
        aula_id,
        hora,
        cantidad_perso,
        porcentaje_ocupacion,
        estado
    ):

        try:

            self.CURSOR.execute(
                """
                INSERT INTO OCUPACION_HISTORICO
                (
                    AULA_ID,
                    HORA,
                    CANTIDAD_PERSONAS,
                    PORCETAJE_OCUPACION,
                    ESTADO
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    aula_id,
                    hora,
                    cantidad_perso,
                    porcentaje_ocupacion,
                    estado
                )
            )

            self.CONEXION.commit()

        except Exception as e:

            print(
                "ERROR AL GUARDAR LA OCUPACIÓN EN LA BASE DE DATOS:\n",
                e
            )

            self.CONEXION.rollback()

    # ============================================================
    # 4. PORCENTAJE DE SOLAPAMIENTO
    # ============================================================

    def porcentaje_solapamiento(self, caja_a, caja_b):

        a_x1, a_y1, a_x2, a_y2 = caja_a
        b_x1, b_y1, b_x2, b_y2 = caja_b

        borde_izquierdo = max(a_x1, b_x1)
        borde_derecho = min(a_x2, b_x2)

        borde_arriba = max(a_y1, b_y1)
        borde_abajo = min(a_y2, b_y2)

        ancho_tapadoooo = borde_derecho - borde_izquierdo
        alto_tapadoo = borde_abajo - borde_arriba

        if ancho_tapadoooo <= 0 or alto_tapadoo <= 0:
            return 0

        area_tapadaa = ancho_tapadoooo * alto_tapadoo

        area_de_a = (a_x2 - a_x1) * (a_y2 - a_y1)

        return area_tapadaa / area_de_a


    
    def dibujar_malla_y_puntos(self, imagen, rostro):
        puntos = rostro.landmark_2d_106      # 106 puntos (x, y)

        # Malla de triángulos sobre una capa semitransparente
        triangulos = Delaunay(puntos)
        capa = imagen.copy()

        for a, b, c in triangulos.simplices:
            pa = (int(puntos[a][0]), int(puntos[a][1]))
            pb = (int(puntos[b][0]), int(puntos[b][1]))
            pc = (int(puntos[c][0]), int(puntos[c][1]))

            cv2.line(capa, pa, pb, (0, 255, 255), 1)
            cv2.line(capa, pb, pc, (0, 255, 255), 1)
            cv2.line(capa, pc, pa, (0, 255, 255), 1)

        cv2.addWeighted(capa, 0.4, imagen, 0.6, 0, imagen)

        # 5 puntos clave (rojos)
        for x, y in rostro.kps:
            cv2.circle(imagen, (int(x), int(y)), 3, (0, 0, 255), -1)

        # 106 puntos (verdes)
        for x, y in puntos:
            cv2.circle(imagen, (int(x), int(y)), 1, (0, 255, 0), -1)
    # ============================================================
    # 5. PROCESAR UN FOTOGRAMA
    # ============================================================

    def procesar_frame(self, frame):

        # Guardamos el último fotograma para el registro facial.
        self.ultimo_frame = frame.copy()

        # Ejecutar YOLO.
        resultados = self.modelo.track(
            frame,
            classes=[0],
            conf=0.5,
            persist=True,
            verbose=False,
            device=0
        )

        resultado = resultados[0]

        # Dibujar detecciones sobre la imagen.
        frame_resultados = resultado.plot(labels=False)

        # ========================================================
        # ACTUALIZAR OCUPACIÓN DEL AULA
        # ========================================================

        cantidad_personas = len(resultado.boxes)

        self.aula1.ACTUALIZAR_DATOS(cantidad_personas)

        

        cv2.putText(
            frame_resultados,
            f"ESTADO: {self.aula1.estado}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            1
        )

        # ========================================================
        # GUARDAR LOS IDS TEMPORALES DE YOLO
        # ========================================================

        ids_actuales = []

        # GUARDAR IDENTIDADES ACTUALES.
        identidades_actuales = []

        if resultado.boxes.id is not None:

            ids = resultado.boxes.id

            for caja, id_persona in zip(resultado.boxes, ids):

                id_persona = int(id_persona)

                ids_actuales.append(id_persona)

                ahora = time.time()

                # OBTENER LAS COORDENADAS DE LA CAJA.
                x1, y1, x2, y2 = caja.xyxy[0]

                # =================================================
                # COMPROBAR SI YA CONOCEMOS A ESTA PERSONA
                # =================================================

                identidad_reciente = None

                for id_guardado, datos in self.tracks.items():

                    if (
                        datos.get("id_yolo") == id_persona
                        and datos.get("estado") in (
                            "activo",
                            "perdido_temporalmente"
                        )
                        and ahora - datos["ultimo_visto"] <= 1.0
                    ):

                        identidad_reciente = id_guardado
                        break

                # =================================================
                # REUTILIZAR LA IDENTIDAD SI LA ENCONTRAMOS
                # =================================================

                if identidad_reciente is not None:

                    self.tracks[identidad_reciente]["ultimo_visto"] = ahora

                    self.tracks[identidad_reciente]["estado"] = "activo"

                    # ¿ALGUIEN ME ESTÁ TAPANDO?

                    caja_principal = caja.xyxy[0].tolist()

                    mayor_solapamiento = 0

                    for otra_caja, otro_id in zip(
                        resultado.boxes,
                        ids
                    ):

                        if id_persona == int(otro_id):
                            continue

                        caja_de_la_otra = otra_caja.xyxy[0].tolist()

                        solapamiento = self.porcentaje_solapamiento(
                            caja_principal,
                            caja_de_la_otra
                        )

                        if solapamiento > mayor_solapamiento:
                            mayor_solapamiento = solapamiento

                    segundos_desde_ultima_huella = (
                        ahora
                        - self.tracks[identidad_reciente]["ultima_huella"]
                    )

                    if (
                        mayor_solapamiento <= 0.30
                        and segundos_desde_ultima_huella >= self.tiempo_cambio_huellas
                    ):

                        recorte_actual = frame[
                            int(y1):int(y2),
                            int(x1):int(x2)
                        ]

                        if recorte_actual.size > 0:

                            embedding_nuevo = self.reid.obtener_embedding(
                                recorte_actual
                            )

                            embedding_viejo = self.tracks[
                                identidad_reciente
                            ]["embedding"]

                            self.tracks[identidad_reciente]["embedding"] = (
                                0.90 * embedding_viejo
                                + 0.10 * embedding_nuevo
                            )

                            self.tracks[identidad_reciente]["ultima_huella"] = ahora

                    identidades_actuales.append(identidad_reciente)

                    id_mostrar = identidad_reciente

                    cv2.putText(
                        frame_resultados,
                        f"ID: {id_mostrar}",
                        (int(x1) + 42, int(y1) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        1
                    )

                    continue

                # =================================================
                # CALCULAR EMBEDDING DE LA PERSONA
                # =================================================

                recorte = frame[
                    int(y1):int(y2),
                    int(x1):int(x2)
                ]

                if recorte.size == 0:
                    continue

                embedding = self.reid.obtener_embedding(recorte)

                self.contador_embeddings += 1

                # BUSCAR LA PERSONA MÁS PARECIDA.

                mejor_id = None

                mejor_similitud = 0

                id_encontrado = False

                for id_guardado, datos in self.tracks.items():

                    if datos["estado"] == "activo":
                        continue

                    embedding_guardado = datos["embedding"]

                    similitud = self.reid.COMPARAR_EMBEDDING(
                        embedding_guardado,
                        embedding
                    )


                    if similitud > mejor_similitud:

                        mejor_similitud = similitud

                        mejor_id = id_guardado

                # =================================================
                # DECIDIR SI ES UNA PERSONA CONOCIDA
                # =================================================

                persona_conocida = False

                id_mostrar = None

                if not id_encontrado:

                    if mejor_similitud >= self.reid.Umbral:
                        persona_conocida = True

                # =================================================
                # RECUPERAR PERSONA CONOCIDA
                # =================================================

                if persona_conocida:

                    id_identificado = mejor_id

                    if id_persona in self.provisionales:
                        del self.provisionales[id_persona]

                    id_mostrar = id_identificado

                    identidades_actuales.append(id_identificado)

                    # SI ESTABA PERDIDA, COMENZAMOS UNA NUEVA SESIÓN.

                    if self.tracks[id_identificado]["estado"] == "perdido":

                        self.tracks[id_identificado]["entrada"] = ahora

                        self.tracks[id_identificado]["salida"] = None

                        self.Registrar_Evento(
                            "ENTRADA",
                            id_identificado,
                            ahora,
                            0
                        )

                    self.tracks[id_identificado]["ultimo_visto"] = ahora

                    self.tracks[id_identificado]["estado"] = "activo"

                    self.tracks[id_identificado]["id_yolo"] = id_persona

                    print(
                        f"IDENTIDAD RECUPERADA | "
                        f"ID: {id_identificado} || "
                        f"YOLO ID: {id_persona} || "
                        f"MEJOR SIMILITUD: {mejor_similitud:.2f}"
                    )

                # =================================================
                # PERSONA NUEVA
                # =================================================

                elif not id_encontrado:

                    if id_persona in self.provisionales:

                        self.provisionales[id_persona]["ultimo_visto"] = ahora

                        if (
                            ahora - self.provisionales[id_persona]["primera_vez"]
                            >= self.segundos_para_confirmar_entidad_nueva
                        ):

                            identidad_nueva = self.siguiente_id_identidad

                            self.siguiente_id_identidad += 1

                            self.tracks[identidad_nueva] = {

                                "entrada": ahora,
                                "ultimo_visto": ahora,
                                "ultima_huella": ahora,

                                "salida": None,
                                "tiempo_perdido": None,

                                "estado": "activo",

                                "embedding": embedding,

                                "id_identidad": identidad_nueva,
                                "id_yolo": id_persona
                            }

                            identidades_actuales.append(identidad_nueva)

                            del self.provisionales[id_persona]

                            id_mostrar = identidad_nueva

                            print(f"ID {identidad_nueva} NUEVO CONFIRMADO")

                            self.Registrar_Evento(
                                "ENTRADA",
                                identidad_nueva,
                                ahora,
                                0
                            )

                    else:

                        mejor_similitud_provisional = 0

                        mejor_id_provisional = None

                        for id_provisional, datos in self.provisionales.items():

                            embedding_provisional_guardado = datos["embedding"]

                            similitud_provisional = self.reid.COMPARAR_EMBEDDING(
                                embedding_provisional_guardado,
                                embedding
                            )

                            if similitud_provisional > mejor_similitud_provisional:

                                mejor_similitud_provisional = similitud_provisional

                                mejor_id_provisional = id_provisional

                        if mejor_similitud_provisional >= self.reid.Umbral:

                            self.provisionales[
                                mejor_id_provisional
                            ]["ultimo_visto"] = ahora

                            if (
                                ahora
                                - self.provisionales[
                                    mejor_id_provisional
                                ]["primera_vez"]
                                >= self.segundos_para_confirmar_entidad_nueva
                            ):

                                identidad_nueva = self.siguiente_id_identidad

                                self.siguiente_id_identidad += 1

                                self.tracks[identidad_nueva] = {

                                    "entrada": ahora,
                                    "ultimo_visto": ahora,
                                    "ultima_huella": ahora,

                                    "salida": None,
                                    "tiempo_perdido": None,

                                    "estado": "activo",

                                    "embedding": embedding,

                                    "id_identidad": identidad_nueva,
                                    "id_yolo": id_persona
                                }

                                identidades_actuales.append(identidad_nueva)

                                del self.provisionales[mejor_id_provisional]

                                id_mostrar = identidad_nueva

                                print(
                                    f"ID {identidad_nueva} NUEVO CONFIRMADO"
                                )

                                self.Registrar_Evento(
                                    "ENTRADA",
                                    identidad_nueva,
                                    ahora,
                                    0
                                )

                        else:

                            self.provisionales[id_persona] = {

                                "embedding": embedding,
                                "ultimo_visto": ahora,
                                "primera_vez": ahora
                            }

                # =================================================
                # MOSTRAR ID EN LA IMAGEN
                # =================================================

                if id_mostrar is not None:

                    cv2.putText(
                        frame_resultados,
                        f"ID: {id_mostrar}",
                        (int(x1) + 42, int(y1) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        1
                    )

        # ========================================================
        # REVISAR TRACKS PERDIDOS
        # ========================================================

        ahora = time.time()

        ids_a_eliminar = []

        for id_persona, datos in self.tracks.items():

            if id_persona not in identidades_actuales:

                tiempo_perdido = ahora - datos["ultimo_visto"]

                # TRACK PERDIDO DEFINITIVAMENTE.

                if tiempo_perdido > self.tiempo_maximo_perdido:

                    if datos["estado"] != "perdido":

                        datos["estado"] = "perdido"

                        datos["tiempo_perdido"] = ahora

                        datos["salida"] = datos["ultimo_visto"]

                        permanencia = datos["salida"] - datos["entrada"]

                        print(f"ID {id_persona} PERDIDO")

                        self.Registrar_Evento(
                            "SALIDA",
                            id_persona,
                            datos["salida"],
                            permanencia
                        )

                    else:

                        tiempo_desde_perdido = (
                            ahora - datos["tiempo_perdido"]
                        )

                        if (
                            tiempo_desde_perdido
                            > self.tiempo_eliminacion_tracks
                        ):

                            ids_a_eliminar.append(id_persona)

                # PÉRDIDA TEMPORAL.

                else:

                    if datos["estado"] != "perdido_temporalmente":

                        datos["estado"] = "perdido_temporalmente"

                        print(
                            f"ID {id_persona} perdido temporalmente "
                            f"({tiempo_perdido:.1f}s)"
                        )

            else:

                datos["estado"] = "activo"

        # LIMPIEZA DE TRACKS.

        for id_pers in ids_a_eliminar:
            del self.tracks[id_pers]

        # LIMPIEZA DE PROVISIONALES.

        ids_provisionales_eliminar = []

        for id_perso, datos in self.provisionales.items():

            tiempo_sin_ver = ahora - datos["ultimo_visto"]

            if tiempo_sin_ver > self.tiempo_eliminacion_provisonal:

                ids_provisionales_eliminar.append(id_perso)

        for id_persona in ids_provisionales_eliminar:
            del self.provisionales[id_persona]

        # ========================================================
        # GUARDAR HISTORIAL DE OCUPACIÓN
        # ========================================================

        ahora = time.time()

        if ahora - self.ultimo_registro >= 5:

            hora_actual = datetime.now()

            self.historial.append(
                (
                    hora_actual,
                    self.aula1.personas
                )
            )

            self.ultimo_registro = ahora

            print(
                f"HORA {hora_actual.strftime('%H:%M:%S')} || "
                f"{self.aula1.nombre} || "
                f"PERSONAS {self.aula1.personas}"
            )

            self.Registrar_Ocupacion(
                1,
                hora_actual,
                self.aula1.personas,
                self.aula1.ocupacion,
                self.aula1.estado
            )

        # ========================================================
        # CONTADOR DE EMBEDDINGS
        # ========================================================

        if time.time() - self.inicio_conteo >= 5:

            print(
                f"EMBEDDINGS calculados en 5 s: "
                f"{self.contador_embeddings}"
            )

            self.contador_embeddings = 0

            self.inicio_conteo = time.time()

       
        # ========================================================
# RECONOCIMIENTO FACIAL
# ========================================================

        personas_reconocidas = 0

        if self.reconocimiento_activo:

           rostros = self.detector_facial.detectar(frame)          # buscar caras

           for rostro in rostros:

            nombre, similitud = self.comparador_rostros.comparar(rostro.embedding)

            if nombre is None:
               nombre = "no conocido"
            else:
               personas_reconocidas += 1                       # contamos a los reconocidos

            izq, arriba, der, abajo = rostro.bbox               # esquinas del cuadro

            cv2.rectangle(
            frame_resultados,
            (int(izq), int(arriba)),
            (int(der), int(abajo)),
            (255, 0, 0),
            2
        )

            cv2.putText(
            frame_resultados,
            f"{nombre} {similitud:.2f}",
            (int(izq), int(arriba) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            1
        )
            if self.dibujar_puntos:
                self.dibujar_malla_y_puntos(frame_resultados, rostro)
         # ========================================================
                # DEVOLVER IMAGEN Y ESTADÍSTICAS A LA INTERFAZ
                # ========================================================
        
        estadisticas = {
                    "personas": self.aula1.personas,
                    "ocupacion": self.aula1.ocupacion,
                    "estado": self.aula1.estado,"reconocidas": personas_reconocidas
                }
        
        return frame_resultados, estadisticas

    # ============================================================
    # 6. REGISTRO FACIAL: ANTES SE ACTIVABA CON LA TECLA R
    # ============================================================

    
    def registrar_rostro(self, nombre, frame):
        if self.ultimo_frame is None:
           return False, "No hay una imagen disponible para registrar."

        return self.capturador_rostros.registrar_Rostro(
        nombre,frame    )
    # ============================================================
    # 7. CERRAR CONEXIÓN CON POSTGRESQL
    # ============================================================

    def cerrar(self):

        print("CERRANDO CONEXIÓN CON POSTGRESQL...")

        if self.CURSOR is not None:

            self.CURSOR.close()
            self.CURSOR = None

        if self.CONEXION is not None:

            self.CONEXION.close()
            self.CONEXION = None

        print("VISIONCAMPUS FINALIZADO.")

        # MOSTRAR HISTORIAL AL TERMINAR.

        print("\nHISTORIAL DE PERSONAS\n")

        for registro in self.historial:

            hora = registro[0]
            personas = registro[1]

            print(
                f"HORA: {hora.strftime('%H:%M:%S')} || "
                f"PERSONAS: {personas}"
            )
