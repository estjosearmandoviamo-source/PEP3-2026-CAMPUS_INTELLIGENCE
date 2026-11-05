import cv2
from ultralytics import YOLO
import time
from datetime import datetime
from aula import AULAS
from person_id import PersonReID
from Conexion_DB import conectar
import torch



camara = cv2.VideoCapture(0)
# #CREAR VENTANA
# cv2.namedWindow("VisionCampus", cv2.WINDOW_NORMAL)
# #PONER VENTANA EN PANTALLA COMPLETA
# cv2.setWindowProperty("VisionCampus", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
#MODELO
modelo = YOLO("yolo11n.pt")#s, m

#CLASE DE LAS AULAS
aula1 = AULAS("AULA-P6", 30)

#CLASE REIDENTIFICADOR
reid = PersonReID()

#BASE DEDATROS
CONEXION = conectar()
CURSOR = CONEXION.cursor()

# Historial de ocupación
historial = []
ultimo_registro = time.time()

# Historial de personas ids LA CLAVE MEMORIA DEL SISTENMA
tracks = {}
provisionales  ={}

# titempo máximo que una persona puede permanecer perdida
tiempo_maximo_perdido = 60         # 1 minuto
tiempo_eliminacion_tracks = 540    # 9 min más → ~10 min en total
tiempo_eliminacion_provisonal = 5


# def Registrar_Evento(tipo, id_persona, hora, permanencia):
#     horadb= datetime.fromtimestamp(hora)
#     if tipo == "ENTRADA":
#         print(
#                         f"========== EVENTO ==========\n"
#                         f"EVENTO     : ENTRADA\n"
#                         f"IDENTIDAD  : {id_persona}\n"
#                         f"HORA       : {datetime.fromtimestamp(hora).strftime('%H:%M:%S')}\n"
#                         f"============================"
#             )

#     elif tipo == "SALIDA":
#         print(
#                         f"========== EVENTO ==========\n"
#                         f"EVENTO     : SALIDA\n"
#                         f"IDENTIDAD  : {id_persona}\n"
#                         f"HORA       : {datetime.fromtimestamp(hora).strftime('%H:%M:%S')}\n"
#                         f"PERMANENCIA: {permanencia:.1f} segundos\n"
#                         f"============================")
#     try:
#         CURSOR.execute("""INSERT INTO EVENTOS (ID_PERSONA, TIPO, HORA, PERMANECIA, AULA_ID) VALUES (%s, %s, %s, %s, %s)""",
#                        (id_persona, tipo , horadb, permanencia, 1 ))
#         CONEXION.commit()
#     except Exception as e:
#         print("❌ ERROR AL GUARDAR EL EVENTO EN LA BASE DE DATOS: \n", e)
#         CONEXION.rollback()

def Registrar_Ocupacion(aula_id, hora, cantidad_perso, porcentaje_ocupacion, estado):
    try:
        CURSOR.execute("""INSERT INTO OCUPACION_HISTORICO (AULA_ID, HORA, CANTIDAD_PERSONAS, PORCETAJE_OCUPACION, ESTADO)
        VALUES (%s, %s, %s, %s,%s)""", (aula_id, hora, cantidad_perso, porcentaje_ocupacion, estado))
        CONEXION.commit()
    except Exception as e:
        print("❌ ERROR AL GUARDAR LA OCUPACION EN LA BASE DE DATOS: \n", e)
        CONEXION.rollback()
def porcentaje_solapamiento(caja_a, caja_b):
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

siguiente_id_identidad = 1
tiempo_cambio_huellas = 1.0

segundos_para_confirmar_entidad_nueva = 3.0

# CONTADOR TEMPORAL (después lo borramos)
contador_embeddings = 0
inicio_conteo = time.time()
while True:

    ret, frame = camara.read()
   
    if not ret:
        print("No se pudo obtener imagen de la cámara.")
        break

   
    resultados = modelo.track(
    frame,
    classes=[0],
    conf=0.5,
    persist=True,
    verbose=False,
    device=0
)

    resultado = resultados[0]

    # Dibujar detecciones sobre la imagen
    frame_resultados = resultado.plot(labels=False)


    # 3. ACTUALIZAR OCUPACIÓN DEL AULA
    cantidad_personas = len(resultado.boxes)

    aula1.ACTUALIZAR_DATOS(cantidad_personas)


    # Mostrar información del aula

    cv2.putText(
        frame_resultados,
        f"PERSONAS: {aula1.personas}",
        (20, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        1
    )

    cv2.putText(
        frame_resultados,
        f"OCUPACION: {aula1.ocupacion:.1f}%",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        1
    )

    cv2.putText(
        frame_resultados,
        f"ESTADO: {aula1.estado}",
        (20, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        1
    )


    
    #GUARADAR LOS IDS TEMPORALES QUE YOLO NOS ENETEGRE
    ids_actuales = []
    #GUARADR
    identidades_actuales = []
    

    if resultado.boxes.id is not None:

        ids = resultado.boxes.id

        for caja, id_persona in zip(resultado.boxes, ids):

            id_persona = int(id_persona)
            ids_actuales.append(id_persona)

            ahora = time.time()
             
         # ------------------------------------------------
            #OBTENEMOS LAS CORDENADAS DE ÑLA CAJA
            x1, y1, x2, y2 = caja.xyxy[0]

            
            # Comprobar si ya conocemos a esta persona
            identidad_reciente = None

            for id_guardado, datos in tracks.items():
                if (
                    datos.get("id_yolo") == id_persona
                    and datos.get("estado") in ("activo", "perdido_temporalmente")
                    and ahora - datos["ultimo_visto"] <= 1.0 ):
                   identidad_reciente = id_guardado
                   break

            # BLOQUE 2: reutilizar la identidad si la encontramos 
            if identidad_reciente is not None:
                tracks[identidad_reciente]["ultimo_visto"] = ahora
                tracks[identidad_reciente]["estado"] = "activo"

                 # BLOQUE 3:alguien me está tapando?
                caja_principal = caja.xyxy[0].tolist()
                mayor_solapamiento = 0

                for otra_caja, otro_id in zip(resultado.boxes, ids):
                    if id_persona == int(otro_id):
                       continue

                    caja_de_la_otra = otra_caja.xyxy[0].tolist()
                    solapamiento = porcentaje_solapamiento(caja_principal, caja_de_la_otra)

                    if solapamiento > mayor_solapamiento:
                        mayor_solapamiento = solapamiento

                segundos_desde_ultima_huella = ahora - tracks[identidad_reciente]["ultima_huella"]
                if mayor_solapamiento <= 0.30 and segundos_desde_ultima_huella >= tiempo_cambio_huellas:
                    recorte_actual = frame[int(y1): int(y2), int(x1): int(x2)]
                    if recorte_actual.size > 0:
                        embedding_nuevo = reid.obtener_embedding(recorte_actual)     
                        embedding_viejo = tracks[identidad_reciente]["embedding"]
                        tracks[identidad_reciente]["embedding"] = 0.90 * embedding_viejo + 0.10 * embedding_nuevo
                        tracks[identidad_reciente]["ultima_huella"] = ahora

                identidades_actuales.append(identidad_reciente)
                id_mostrar = identidad_reciente

                cv2.putText(
                frame_resultados,
               f"ID: {id_mostrar}",
                (int(x1) + 42, int(y1) - 5),
               cv2.FONT_HERSHEY_SIMPLEX, 1,(0, 255, 0),1 )

                continue

            
            recorte = frame[int(y1): int(y2), int(x1): int(x2)]
            if recorte.size == 0:
                continue
            
            embedding = reid.obtener_embedding(recorte)     

            contador_embeddings += 1  # cuenta una vez por cada embedding calculado
                    
            #busacr la ,mas parecidsa
            mejor_id = None            
            mejor_similitud = 0
            id_encontrado = False

            for id_guardado, datos in tracks.items():#PRIMERO VUELTA ESTA VACIO LO CUALE ESTMTRA LA PERSONA NO ES CONOCMIDS
                if datos["estado"] ==  "activo":
                    continue#soolo para personas que esten perdidod y perdidos temporalmenete
                embedding_guardado = datos["embedding"]
                
                similitud = reid.COMPARAR_EMBEDDING(embedding_guardado, embedding)
                print(f"COMPARANDO con {id_guardado} | similitud: {similitud:.2f} | umbral:{reid.Umbral}")
                if similitud > mejor_similitud:
                    mejor_similitud = similitud
                    
                    mejor_id = id_guardado

            #decidir si es una persona conocida
            persona_conocida = False

            id_mostrar = id_persona#por defecto
            if not id_encontrado:
                if mejor_similitud >= reid.Umbral:
                   persona_conocida = True

            if persona_conocida:
                id_identificado = mejor_id
                if id_persona in provisionales:
                    del provisionales[id_persona]
                id_mostrar = id_identificado#si es c onocida mostarmos esto
                identidades_actuales.append(id_identificado)

                #SI ESTABA PERDIDOD COMENZAMOS UNA NIUEVA SESION DE ENTRADA Y SALIAD
                if tracks[id_identificado]["estado"] == "perdido":
                    tracks[id_identificado]["entrada"] = ahora
                    tracks[id_identificado]["salida"] = None


                tracks[id_identificado]["ultimo_visto"] = ahora
                tracks[id_identificado]["estado"] = "activo"
                tracks[id_identificado]["id_yolo"] = id_persona
                

                print(F"IDENTIDAD RECUPERADA | ID :{id_identificado} || YOLO ID : {id_persona} || MEJOR SIMILTUD : {mejor_similitud:.2f}")

            #Persona nueva
            elif not id_encontrado:
                if id_persona in provisionales:

                    provisionales[id_persona]["ultimo_visto"] = ahora
                    if ahora - provisionales[id_persona]["primera_vez"] >= segundos_para_confirmar_entidad_nueva:
                    
                        identidad_nueva = siguiente_id_identidad
                        siguiente_id_identidad += 1
                    
                        tracks[identidad_nueva] = {
                                                        "entrada": ahora,
                                                        "ultimo_visto": ahora,
                                                        "ultima_huella":ahora,
                                                        "salida": None,
                                                        "tiempo_perdido": None,
                                                        "estado": "activo",
                                                        "embedding": embedding,
                                                        "id_identidad": identidad_nueva,
                                                        "id_yolo":id_persona
                                                    }
                        identidades_actuales.append(identidad_nueva)
                        del provisionales[id_persona]
                        id_mostrar = identidad_nueva
                        print(f"ID {identidad_nueva} NUEVO CONFIRMADP")

                        # Registrar_Evento("ENTRADA", identidad_nueva, ahora , 0)

          
                else:
                    mejor_similitud_provisional = 0
                    mejor_id_provisional = None
                    for id_provisional, datos in provisionales.items():
                        embedding_provisional_guardado = datos["embedding"]

                        similitud_provisional = reid.COMPARAR_EMBEDDING(embedding_provisional_guardado, embedding)

                        if similitud_provisional > mejor_similitud_provisional:
                            mejor_similitud_provisional = similitud_provisional
                            mejor_id_provisional = id_provisional

                    if mejor_similitud_provisional >= reid.Umbral:
                        provisionales[mejor_id_provisional]["ultimo_visto"] = ahora

                        if ahora - provisionales[mejor_id_provisional]["primera_vez"] >= segundos_para_confirmar_entidad_nueva:
                            identidad_nueva = siguiente_id_identidad
                            siguiente_id_identidad += 1

                            tracks[identidad_nueva] = {
                                                                "entrada": ahora,
                                                                "ultimo_visto": ahora,
                                                                "ultima_huella": ahora,
                                                                "salida": None,
                                                                "tiempo_perdido": None,
                                                                "estado": "activo",
                                                                "embedding": embedding,
                                                                "id_identidad": identidad_nueva,
                                                                "id_yolo":id_persona
                                                            }
                            identidades_actuales.append(identidad_nueva)
                            del provisionales[mejor_id_provisional]
                            id_mostrar = identidad_nueva
                            print(f"ID {identidad_nueva} NUEVO CONFIRMADP")

                            # Registrar_Evento("ENTRADA", identidad_nueva, ahora, 0 )

                            

                    else:
                        
                          provisionales[id_persona] = {"embedding": embedding, "ultimo_visto": ahora, "primera_vez": ahora}
                        # provisionales[id_persona] = {"observacion": 1, "embedding": embedding, "ultimo_visto": ahora, "primera_vez": ahora}
                        # if provisionales[id_persona]["observacion"] >= 3:

                        #     identidad_nueva = siguiente_id_identidad
                        #     siguiente_id_identidad += 1
                        
                        #     tracks[identidad_nueva] = {
                        #                                     "entrada": ahora,
                        #                                     "ultimo_visto": ahora,
                        #                                     "ultima_huella":ahora,
                        #                                     "salida": None,
                        #                                     "tiempo_perdido": None,
                        #                                     "estado": "activo",
                        #                                     "embedding": embedding,
                        #                                     "id_identidad": identidad_nueva,
                        #                                     "id_yolo":id_persona
                        #                                 }
                        #     identidades_actuales.append(identidad_nueva)
                        #     del provisionales[id_persona]
                        #     id_mostrar = identidad_nueva
                        #     print(f"ID {identidad_nueva} NUEVO CONFIRMADP")

                        #     # Registrar_Evento("ENTRADA", identidad_nueva, ahora, 0 )


                
                 # MOSTRAR ID EN LA IMAGEN
           
            cv2.putText(
                        frame_resultados,
                        f"ID: {id_mostrar}",
                        (int(x1)+42, int(y1) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        1
                        )
            

    # 5. REVISAR TRACKS PERDIDOS
    ahora = time.time()
    ids_a_eliminar = []

    for id_persona, datos in tracks.items():

        if id_persona not in identidades_actuales:

            tiempo_perdido = ahora - datos["ultimo_visto"]

            # TRACK PERDIDO DEFINITIVAMENTE
          
            if tiempo_perdido > tiempo_maximo_perdido:

                if datos["estado"] != "perdido":

                    datos["estado"] = "perdido"
                    datos["tiempo_perdido"] = ahora
                    datos["salida"] = datos["ultimo_visto"]
                    permanencia = datos["salida"] - datos["entrada"]

                    print(
                        f"ID {id_persona} PERDIDO"
                    )

                    # Registrar_Evento("SALIDA", id_persona, datos["salida"], permanencia )
                
                  

                else:
                    #Cuanto tiempo lleva desde que la marcamos como perdido
                    tiempo_desde_perdido = ahora - datos["tiempo_perdido"]

                    if tiempo_desde_perdido > tiempo_eliminacion_tracks:
                        ids_a_eliminar.append(id_persona)


            # PÉRDIDA TEMPORAL

            else:
                if datos["estado"] != "perdido_temporalmente":
                    datos["estado"] = "perdido_temporalmente"
                    
                    print(
                        f"ID {id_persona} perdido temporalmente "
                        f"({tiempo_perdido:.1f}s)"
                                    )

        else :
            datos["estado"] = "activo"

    # LIMPIEZA DE TRACKS 
    # ELIMAR TRACKS QUE LLEVAN PEDIDOS MAS DELLIMITE
    #ya que nose puede elimra o modificar su tama;p en un diccionaroiio en mmedio de un recorirdo

    for id_pers in ids_a_eliminar:
        del tracks[id_pers]

    #LIMPIEZA DE PROVIDONALEDS
    ids_provionales_eliminar =[]
    for id_perso, datos in provisionales.items():
        tiempo_sin_ver = ahora - datos["ultimo_visto"]
        if tiempo_sin_ver > tiempo_eliminacion_provisonal:
            ids_provionales_eliminar.append(id_perso)

    for id in ids_provionales_eliminar:
        del provisionales[id]


    # 6. GUARDAR HISTORIAL DE OCUPACIÓN
    ahora = time.time()

    if ahora - ultimo_registro >= 5:

        hora_actual = datetime.now()

        historial.append(
            (
                hora_actual,
                aula1.personas
            )
        )

        ultimo_registro = ahora

        print(
            f"HORA {hora_actual.strftime('%H:%M:%S')} || "
            f"{aula1.nombre} || "
            f"PERSONAS {aula1.personas}"
        )
   
        Registrar_Ocupacion(1, hora_actual, aula1.personas, aula1.ocupacion, aula1.estado)

    # MSTRAR CÁMARA
    nuevo = cv2.resize(
        frame_resultados,
        (1000, 600)
    )

    if time.time() - inicio_conteo >= 5:
        print(f"EMBEDDINGS calculados en 5 s: {contador_embeddings}")
        contador_embeddings = 0
        inicio_conteo = time.time()
    cv2.imshow(
        "VisionCampus",
        nuevo
    )

    
    tecla = cv2.waitKey(1)
   
    if tecla == ord("q"):
        break


# FINAaaLIZAR PROGRAMA
camara.release()
cv2.destroyAllWindows()
#CERRaaAR CONEXION CON LA BASE
CURSOR.close()
CONEXION.close()

# mostraar historial al termiaanar
print("\nHISTORIAL DE PERSONAS\n")
for registro in historial :
    hora = registro[0]
    personas = registro[1]
    print(F"HORA : {hora.strftime('%H:%M:%S')} || PERSONAS: {personas}")
