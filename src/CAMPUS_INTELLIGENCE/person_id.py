import torch
import torchreid


class PersonReID:

    def __init__(self):

        #DECIRLE PYTORCH QUE DISPCITIVO USAR
        if torch.cuda.is_available():
            self.dispositivo = torch.device("cuda")
        else :
            self.dispositivo = torch.device("cpu")

        self.Umbral = 0.75
        #PASO 2 Crear modelo OSNet
        self.modelo = torchreid.models.build_model(
            name="osnet_x1_0",
            num_classes=1,
            pretrained=True
        )
       
        
        # #PASO 3 DECIRLE QUE USE EL DIPOSITIVOQUESELECCIONAMOSYA QUE POR DEFECTO VIENE EN CPU 
        # self.modelo = self.modelo.to(self.dispositivo)
        # # Modo evaluación = MODELO YA ENTRENADO Y NO EN MODO DE ENTRENAR
        # self.modelo.eval()
        # print("Dispositivo ReID:", next(self.modelo.parameters()).device)
        # Mover el modelo al dispositivo seleccionado
        self.modelo = self.modelo.to(self.dispositivo)

# Modo evaluación
        self.modelo.eval()

# Comprobar dónde está funcionando realmente OSNet
        print("Dispositivo ReID:", next(self.modelo.parameters()).device)




    #ADAPTACION DEL IMAGEN YA QUE EL FRAME QUE NOS DA OPENCV ES DIFERENTE
    #AL MODO QUE TRABAJA OSNET
    def obtener_embedding(self, imagen):

        # Comprobar que recibimos una imagen

        if imagen is None:
            return None

        # Convertir frame(BGR) a RGB por que osnet trabajja con eso y opencv nos entrega en bgr
        imagen = imagen[:, :, ::-1]

        # Convertir la imagen a Tensor
        imagen = torch.from_numpy(imagen.copy())

        # H x W x C → C x H x W adaptamos la estructura 
        imagen = imagen.permute(2, 0, 1)

        # Convertir a float porque osnet trabaja con numeros flotantes para hacer sus operaciones y convertimos los tensores en flotantes
        imagen = imagen.float()

        # Normalizar 0-255 → 0-1 porque osnet trabaja con los pixeles normalizados
        imagen = imagen / 255.0

        # Agregar dimensión del batch
        imagen = imagen.unsqueeze(0)

        # Mover imagen a GPU/CPU
        imagen = imagen.to(self.dispositivo)

        # "Durante la ejecución de self.modelo(imagen), trabaja sin calcular/guardar gradientes."
        with torch.no_grad():
            embedding = self.modelo(imagen)

        return embedding

    def COMPARAR_EMBEDDING(self, embedding1, embedding2):
        similitud = torch.nn.functional.cosine_similarity(embedding1,embedding2)#nos devuelve un tensor
        similitud = similitud.item()

        return similitud

if __name__ == "__main__":
    reid = PersonReID()