class AULAS:
    def __init__(self, nombre, capacidad):
        self.nombre = nombre
        self.capacidad = capacidad
        self.personas = 0
        self.ocupacion = 0
        self.estado= "VACIA"

    def ACTUALIZAR_DATOS(self, personas):
        self.personas = personas 
        self.ocupacion = (personas / self.capacidad) * 100

        if self.ocupacion == 0:
           self.estado = "VACIA"
        elif self.ocupacion < 50:
           self.estado = "DISPONIBLE"
        elif self.ocupacion < 80:
            self.estado = "OCUPACION MEDIA"
        elif self.ocupacion < 100:
            self.estado = "ALTA OCUPACION"
        elif self.ocupacion == 100:
            self.estado = "LLENA"
        else:
            self.estado = "SATURACION"