# Detectar dónde están los rostros.
# Identificar las coordenadas de cada rostro.
# Extraer el embedding facial de cada rostro detectado.
from insightface.app import FaceAnalysis
class DetectorFacial:

    def __init__(self):
        self.modelo = FaceAnalysis(
        name="buffalo_l",
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        
        self.modelo.prepare(ctx_id=0, det_size=(640, 640))

    def detectar(self, imagen):
        rostros = self.modelo.get(imagen)

        return rostros