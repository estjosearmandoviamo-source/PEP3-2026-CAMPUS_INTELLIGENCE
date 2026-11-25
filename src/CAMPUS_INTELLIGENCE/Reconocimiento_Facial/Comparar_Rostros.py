import numpy as np
import torch

class ComparadorRostros:
    def __init__(self):
        self.rostros_en_memoria = {}
        self.umbral = 0.50   # similitud mínima para decir "es esta persona" (se cambia desde Configuración)
    def agregar_rostro(self, id_rostro, nombre , embedding, autorizado ):
        self.rostros_en_memoria[id_rostro] = {
            "nombre": nombre,
            "embedding": embedding, "autorizado":autorizado

        }

    def eliminar_rostro(self, id_rostro):
        self.rostros_en_memoria.pop(id_rostro, None)  
        #pop devuelve lo que borra y del no. 
    def cambiar_autorizacion(self, id_rostro, autorizado):
        # Si la persona está en la memoria, le cambiamos el permiso.
        if id_rostro in self.rostros_en_memoria:
            self.rostros_en_memoria[id_rostro]["autorizado"] = autorizado
    def cargar_desde_base(self, rostros_db):
            filas = rostros_db.mostrar_Registro()       
            for id_rostro, nombre, huella, autorizado in filas:                       
               embedding = np.array(huella, dtype=np.float32)   # lista -> arreglo
               self.agregar_rostro(id_rostro, nombre, embedding,autorizado)           # a la lista en memoria
            print(f"Rostros cargados desde la base: {len(filas)}")
    def comparar(self, embedding_nuevo):

        mejor_similitud = 0 
        mejor_nombre = None
        tiene_autorizacion = None
        for rostro in self.rostros_en_memoria.values():
            embedding_registardo  = rostro["embedding"]
            nombre_persona = rostro["nombre"]
            similitud = torch.nn.functional.cosine_similarity(
    torch.as_tensor(embedding_nuevo).unsqueeze(0),
    torch.as_tensor(embedding_registardo).unsqueeze(0)#usamos  unsqueeze ya que cosine.... trabaja por defecto com una sola dimesion
)
            similitud = similitud.item()
 
            if similitud > mejor_similitud:
                mejor_nombre = rostro["nombre"]
                mejor_similitud = similitud
                tiene_autorizacion = rostro["autorizado"]

           
        if mejor_similitud >= self.umbral:
            return mejor_nombre,  mejor_similitud, tiene_autorizacion
        else:
            return None, mejor_similitud, None
            
