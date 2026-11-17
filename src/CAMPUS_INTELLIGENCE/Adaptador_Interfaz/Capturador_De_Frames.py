
from PySide6.QtCore import QThread, Signal
import cv2
from CAMPUS_INTELLIGENCE.Adaptador_Interfaz.Procesador_Frame_Vision import VisionCampusCore
#ProcesadorCamara: Se encarga de capturar las imágenes de la cámara, pasarlas a nuestra lógica (VisionCampusCore) para procesarlas y ejecutarse en segundo plano mediante QThread, evitando bloquear la interfaz gráfica.
class ProcesadorCamara(QThread):#nos permite ejcev=cutar el trabajo de esta clase en segundo palno sin afectaer la interfaz
    #bueno para que la ventana no se quede esperando a que yloo termine de trabajra 

   #claswe ue nos permite enviar avisso e informaon
    nueva_imagen = Signal(object)

    estadisticas = Signal(object)

    error = Signal(str)

    def __init__(self):
        super().__init__()#en python se inicialia asi la clase padre que en C# es BASE

        self.ejecutando = False
        self.camara = None
        self.core = None

    def run(self):
        self.ejecutando = True

        try:
           
            self.camara = cv2.VideoCapture(0)

            if not self.camara.isOpened():#isOpened comprueba si se abrrio
                self.error.emit("No se pudo abrir la cámara.")
                return

            self.core = VisionCampusCore()

            while self.ejecutando:

                ret, frame = self.camara.read()

                if not ret:
                    self.error.emit("No se pudo obtener la imagen.")
                    break

            
                frame_procesado, datos = self.core.procesar_frame(frame)

                #coonnect registramos que funcion se ejecur=tara cuando lllegue un abviso y entreagle la informacion recibida
                self.nueva_imagen.emit(frame_procesado)##tocamos el timbre y enviames el mensaje
                self.estadisticas.emit(datos)

        except Exception as e:
            self.error.emit(f"Error en VisionCampus: {e}")

        finally:
          #loas liberamos
            if self.camara is not None:
                self.camara.release()
                self.camara = None

            #Cerrar la conexin con la base de datos
            if self.core is not None:
                try:
                    self.core.cerrar()
                except Exception as e:
                    self.error.emit(f"Error al cerrar VisionCampus: {e}")

                self.core = None

            self.ejecutando = False

    def detener(self):
        self.ejecutando = False
