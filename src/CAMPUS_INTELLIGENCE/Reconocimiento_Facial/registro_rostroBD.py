from CAMPUS_INTELLIGENCE.Base_Datos.Conexion_DB import conectar
class RostrosDB:
    def __init__(self):

        self.CONEXION = conectar()
        self.CURSOR = self.CONEXION.cursor()   
    def guardar(self, nombre, embedding, autorizado):
        huella = embedding.tolist()
        try:
            self.CURSOR.execute("""INSERT INTO rostros_registrados (nombre, huella_facial ,autorizado) VALUES (%s, %s, %s)""",
                               (nombre, huella , autorizado ))
            self.CONEXION.commit()

            return True#si se guardo
        except Exception as e:
            print("❌ ERROR AL GUARDAR EL ROSTRO EN LA BASE DE DATOS: \n", e)
            self.CONEXION.rollback()
            return False#nooooooooooooooooo
    def mostrar_Registro(self):
        try:
            self.CURSOR.execute("SELECT nombre, huella_facial FROM rostros_registrados ")
                                        
            filas = self.CURSOR.fetchall()#en c# es registro por registro aca es en una lista comppleatr con tupl
            return filas
        except Exception as e:
            print("❌ ERROR AL GUARDAR EL ROSTRO EN LA BASE DE DATOS: \n", e)
            self.CONEXION.rollback()
            return []