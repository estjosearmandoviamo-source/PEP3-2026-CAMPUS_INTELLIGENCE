class CapturarRostro:
    def __init__(self, detector, comparador, registro_BD):
            self.detector = detector
            self.comparador = comparador
            self.Registro_rostro =registro_BD
   
    def registrar_Rostro(self, nombre, imagen):
         rostros = self.detector.detectar(imagen)

         if len(rostros) == 0:
            return False, "No se detectó ningún rostro."

         if len(rostros) > 1:
            return False, "Se detectaron varios rostros. Registra una persona a la vez."

         embedding = rostros[0].embedding
         id_rostro = self.Registro_rostro.guardar(nombre, embedding, True)

         if id_rostro is not None:
            self.comparador.agregar_rostro(id_rostro,nombre, embedding, True)#agregar a la memoeria 
            return True, f"Rostro de {nombre} registrado."

         return False, "No se pudo guardar el rostro."