class CapturarRostro:
    def __init__(self, detector, comparador, registro_BD):
            self.detector = detector
            self.comparador = comparador
            self.Registro_rostro =registro_BD
   
    def registrar_Rostro(self, nombre, imagen):
        rostros= self.detector.detectar(imagen)

        if len(rostros) == 0:
            print(" no se dectecti ningun rostro")
            return
        if len(rostros) > 1:
             print("se registraron varios rostros , solo podemos registrar uno por uno")
             return
        embedding = rostros[0].embedding#lista de objeto y entramos al atributo
        
        Guardado = self.Registro_rostro.guardar(nombre, embedding, True)
        if Guardado:
             self.comparador.agregar_rostro(nombre, embedding)
             print(f"rostro de {nombre} registrado")#agregar a la lista memoria para hacer las comparaciones con lo que es ta registradi
        else:

             print("NO SE PUEDO CUARDAR EL ROSSTRO CORRECTAMENYE")