
from pathlib import Path
import sys

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QStackedWidget,QCheckBox,
    QTableWidget,QWidget,QHBoxLayout,QTableWidgetItem
)

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtGui import QImage, QPixmap


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

# Carpeta donde se encuentran los archivos de la interfaz.
CARPETA = Path(__file__).resolve().parent

RUTA_SRC = CARPETA.parent.parent

sys.path.insert(0, str(RUTA_SRC)) # carpeta src
from CAMPUS_INTELLIGENCE.Adaptador_Interfaz.Capturador_De_Frames import ProcesadorCamara
from CAMPUS_INTELLIGENCE.Base_Datos.Conexion_DB import conectar
from PySide6.QtWidgets import QTableWidgetItem
# ============================================================
# 2. CARGAR LA INTERFAZ GRÁFICA
# ============================================================

def cargar_ventana() -> QMainWindow:
    """Carga visioncampus.ui y aplica los estilos."""

    ruta_ui = CARPETA / "visioncampus.ui"
    formulario = QFile(str(ruta_ui))

    if not formulario.open(QIODevice.OpenModeFlag.ReadOnly):
        raise FileNotFoundError(f"No se pudo abrir el formulario: {ruta_ui}")

    cargador = QUiLoader()
    ventana = cargador.load(formulario)
    formulario.close()

    if ventana is None:
        raise RuntimeError(cargador.errorString())

    ventana.setWindowTitle("VisionCampus | Inteligencia Visual")

    tema = CARPETA / "visioncampus.qss"
    if tema.exists():
        ventana.setStyleSheet(tema.read_text(encoding="utf-8"))

    return ventana
# ============================================================
# 3. NAVEGACIÓN ENTRE PANTALLAS
# ============================================================

def conectar_pantallas(ventana: QMainWindow) -> None:
    """Conecta los botones que permiten cambiar de página."""

    paginas = ventana.findChild(QStackedWidget, "paginas")

    nombres_botones = (
        "btnMonitoreo",
        "btnRegistroFacial",
        "btnPersonas",
        "btnConfiguracion"
    )

    # Cambia la página y actualiza el botón seleccionado.
    def mostrar_pagina(indice: int) -> None:
        if paginas is None:
            return

        paginas.setCurrentIndex(indice)
        # Los puntos del rostro solo se dibujan en Registro Facial (índice 1)
        if ventana.procesador is not None and ventana.procesador.core is not None:
            ventana.procesador.core.dibujar_puntos = (indice == 1)

        for posicion, nombre in enumerate(nombres_botones):
            boton = ventana.findChild(QPushButton, nombre)

            if boton is not None:
                boton.setChecked(posicion == indice)

    # Conectamos cada botón con su página correspondiente.
    for indice, nombre in enumerate(nombres_botones):
        boton = ventana.findChild(QPushButton, nombre)

        if boton is not None:
            boton.clicked.connect(
                lambda _estado=False, pagina=indice: mostrar_pagina(pagina)
            )

    # El botón de estadísticas abre la página Personas.
    boton_estadisticas = ventana.findChild(
        QPushButton, "btnIrEstadisticas"
    )

    if boton_estadisticas is not None:
        boton_estadisticas.clicked.connect(lambda: mostrar_pagina(2))

    # Cancelar el registro devuelve a la página de monitoreo.
    cancelar = ventana.findChild(QPushButton, "btnCancelarRegistro")

    if cancelar is not None:
        cancelar.clicked.connect(lambda: mostrar_pagina(0))


# ============================================================
# 4. CONFIGURAR TABLA, UMBRAL Y BÚSQUEDA
# ============================================================

    # Ajustamos la tabla para aprovechar el espacio disponible.
    tabla = ventana.findChild(QTableWidget, "tablaPersonas")

    if tabla is not None:
        tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        tabla.horizontalHeader().setMinimumSectionSize(125)
        tabla.verticalHeader().setVisible(False)
        tabla.setShowGrid(False)

    # Mostramos el valor del umbral con dos decimales.
    deslizador = ventana.findChild(QSlider, "controlUmbral")
    texto_umbral = ventana.findChild(QLabel, "valorUmbral")

    if deslizador is not None and texto_umbral is not None:
        deslizador.valueChanged.connect(
            lambda valor: texto_umbral.setText(f"{valor / 100:.2f}")
        )

    # Cada vez que se escribe, filtramos los registros de la tabla.
    busqueda = ventana.findChild(QLineEdit, "campoBuscarPersona")

    if busqueda is not None:
        busqueda.textChanged.connect(
            lambda texto: filtrar_tabla_personas(tabla, texto)
        )


# ============================================================
# 5. FILTRAR PERSONAS
# ============================================================

def filtrar_tabla_personas(
    tabla: QTableWidget | None,
    texto: str
) -> None:
    """Oculta las filas que no coinciden con la búsqueda."""

    if tabla is None:
        return

    busqueda = texto.strip().casefold()

    for fila in range(tabla.rowCount()):

        # Buscamos el texto en todas las columnas de la fila.
        coincide = any(
            tabla.item(fila, columna) is not None
            and busqueda in tabla.item(fila, columna).text().casefold()
            for columna in range(tabla.columnCount())
        )

        tabla.setRowHidden(fila, bool(busqueda) and not coincide)


# ============================================================
# 6. FUNCIONES DEL SISTEMA VISIONCAMPUS
# ============================================================

def actualizar_estadisticas(
    ventana: QMainWindow,
    datos: dict
) -> None:

    personas = ventana.findChild(QLabel, "valorDetectadas")
    ocupacion = ventana.findChild(QLabel, "valorOcupacion")
    reconocidas = ventana.findChild(QLabel, "valorReconocidas")

    if personas is not None:
        personas.setText(str(datos["personas"]))

    if ocupacion is not None:
        ocupacion.setText(f'{datos["ocupacion"]:.1f}%')
    if reconocidas is not None:
            reconocidas.setText(str(datos["reconocidas"]))


def cargar_personas(ventana):

    tabla = ventana.findChild(QTableWidget, "tablaPersonas")

    if tabla is None:
        return

    conexion = None
    cursor = None

    try:
        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id_rostro, nombre, fecha_registro, autorizado
            FROM rostros_registrados
        """)

        registros = cursor.fetchall()

        tabla.setRowCount(len(registros))
        etiqueta_total = ventana.findChild(QLabel, "totalPersonas")

        if etiqueta_total is not None:
           etiqueta_total.setText(f"Total de personas: {len(registros)}")
            
        for fila, registro in enumerate(registros):

            id_rostro, nombre, fecha, autorizado = registro

            item_nombre = QTableWidgetItem(str(nombre.upper()))
            item_nombre.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(fila, 0, item_nombre)

            item_fecha = QTableWidgetItem(fecha.strftime("%d/%m/%Y %H:%M"))
            item_fecha.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(fila, 1, item_fecha)

            texto_autorizacion = "Autorizado" if autorizado else "No autorizado"
            item_autorizacion = QTableWidgetItem(texto_autorizacion)
            item_autorizacion.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(fila, 2, item_autorizacion)

            boton = QPushButton("⋮")
            boton.setObjectName("botonAccion")
            boton.setProperty("id_rostro", id_rostro)

            

            boton.clicked.connect(lambda estado=False, id =id_rostro, nombreeEli = nombre: 
                                eliminar_persona(ventana, id, nombreeEli )   )

            contenedor = QWidget()
            disposicion = QHBoxLayout(contenedor)
            disposicion.setContentsMargins(0, 0, 0, 0)
            disposicion.setAlignment(Qt.AlignCenter)
            disposicion.addWidget(boton)

            tabla.setCellWidget(fila, 3, contenedor)

    except Exception as error:
        QMessageBox.critical(
            ventana,
            "Error al cargar personas",
            f"No se pudieron obtener los registros:\n{error}"
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None:
            conexion.close()
def eliminar_persona(ventana: QMainWindow, id_rostro: int, nombre: str) -> None:

    respuesta = QMessageBox.question(
        ventana,
        "Eliminar registro",
        f"¿QUIEERES Eliminar el registro facial de {nombre.upper()}?"
        
    )

    if respuesta != QMessageBox.StandardButton.Yes:
        return

    conexion = None
    cursor = None

    try:
        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute(
            "DELETE FROM rostros_registrados WHERE id_rostro = %s",
            (id_rostro,)
        )
        conexion.commit()

    except Exception as error:
        if conexion is not None:
            conexion.rollback()

        QMessageBox.critical(ventana, "Error al eliminar", f"No se pudo eliminar:\n{error}")
        return

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

        # Si la cámara está encendida, avisamos al hilo para que saque a la persona de la memoria
    if ventana.procesador is not None:
        ventana.procesador.eliminar_pendiente = id_rostro
    cargar_personas(ventana)  

def iniciar_camara(ventana: QMainWindow) -> None:
    if ventana.procesador is not None:
        return

    procesador = ProcesadorCamara()
    ventana.procesador = procesador#agreganos un atributo a nuestra venata que haga referencai a un nuestro objeto
    #concepto nuevo de POO

    vista_Monitoreo = ventana.findChild(QLabel, "textoVistaVacia")#para lueo poner una imagen encima dese label
    vista_registro_facial = ventana.findChild(QLabel, "textoRostroVacio")

    vistas = [vista_Monitoreo, vista_registro_facial]
    estado = ventana.findChild(QLabel, "estadoCamara")

    def mostrar_imagen(frame):

        alto, ancho, canales = frame.shape#bgr o canales de color y shape es forma
       #conversiones opncv formanto nmpy
        imagen = QImage(
            frame.data,
            ancho,
            alto,
            frame.strides[0],
            QImage.Format.Format_BGR888
        ).copy()

        pixmap = QPixmap.fromImage(imagen)#es uan hermanienta de qt para mostrar imagenes osea es que es como Qlabel
        #recibe un objeto de ese tippo 
        for vista in vistas:

            vista.setPixmap(
            pixmap.scaled(
                vista.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        #scaled permite cambiar el tamano de nuestra imagebn
  
    def mostrar_error(mensaje):
        estado.setText("● Cámara desconectada")
        QMessageBox.warning(ventana, "Error de cámara", mensaje)
    def mostrar_resultado_registroDeRostro(exito, mensaje):
        if exito:
            QMessageBox.information(ventana, "Registro FACIALL", mensaje)
            campo_nombre = ventana.findChild(QLineEdit, "campoNombre")
            chek_permiso = ventana.findChild(QCheckBox , "checkConsentimiento")
            estado = ventana.findChild(QLabel, "estadoCaptura")

            #LIMPIAMOS
            campo_nombre.clear()
            chek_permiso.setChecked(False)
            estado.setText("")
            ventana.frame_capturado = None

            cargar_personas(ventana)


        else:
            QMessageBox.warning(ventana, "Registro FACIALL", mensaje)


    # Liberamos la referencia cuando el trabajador termina.
    def limpiar_procesador():
        if ventana.procesador is procesador:
            ventana.procesador = None#eliminamos la refenrecia

    procesador.nueva_imagen.connect(mostrar_imagen)
    procesador.registro_terminado.connect(mostrar_resultado_registroDeRostro)
    procesador.estadisticas.connect(
    lambda datos: actualizar_estadisticas(ventana, datos)
)

    procesador.error.connect(mostrar_error)
    procesador.finished.connect(limpiar_procesador)#Es una señal que nos avisa cuando la ejecución en segundo plano ha terminado completamen
    estado.setText("● Cámara conectando...")

    # Iniciamos la captura en segundo plano.
    procesador.start()



def detener_camara(ventana: QMainWindow) -> None:
    procesador = ventana.procesador

    if procesador is None:
        return

    # Solicitamos detener el procesamiento.
    procesador.detener()

    # Actualizamos el estado de la interfaz.
    estado = ventana.findChild(QLabel, "estadoCamara")

    if estado is not None:
        estado.setText("● Deteniendo cámara...")


def capturar_rostro(ventana: QMainWindow) -> None:
   estado = ventana.findChild(QLabel, "estadoCaptura")

   if ventana.procesador is None :
        estado.setText("ENCUENDE LA CAMRA PRIMERO PORFAVOR")
        return
   core =ventana.procesador.core
   
    # Todavía no llegó ningún fotograma
   if core.ultimo_frame is None:
        estado.setText("ESPERA UN MOMENTO, LA CÁMARA ESTÁ CARGANDO")
        return
   ventana.frame_capturado = core.ultimo_frame#PORQUE YA TIERNE UNA COPIA 
   estado.setText("CAPTURADA CORRECTAMNETE")
    


def guardar_registro(ventana: QMainWindow) -> None:
    campo_nombre = ventana.findChild(QLineEdit, "campoNombre")
    chek_permiso = ventana.findChild(QCheckBox , "checkConsentimiento")

    nombre = campo_nombre.text().strip()

    if nombre == "":
        QMessageBox.warning(ventana, "REGISTRO FACIAL ","NO SE PERMITEN CAMPOS VACIOS ")
        return

    if not  chek_permiso.isChecked():
         QMessageBox.warning(ventana, "REGISTRO FACIAL ","FALTA LA AUTORIZACION DE L A[PERSONA] ")
         return

    if ventana.frame_capturado is None :
                QMessageBox.warning(ventana,"REGISTRO FACIAL ", "PRIMEWRO CAPTURA EL CAPTURA EL ROSTRO DE LA PERSPON ")
                return
    if ventana.procesador is None:
                 QMessageBox.warning(ventana, "REGISTRO FACIAL ","PRIMERO DEBVES PRENDE RLA CAMARA ")
                 return
    ventana.procesador.registro_pendiente = (nombre, ventana.frame_capturado)



def guardar_configuracion(ventana: QMainWindow) -> None:
    """
    Guarda las preferencias de VisionCampus.

    Aquí leerás la cámara, el aula, su capacidad y el umbral.
    """

    pendiente(
        ventana,
        "Guardar configuración",
        "Conecta aquí la validación y el guardado de preferencias."
    )


def restablecer_configuracion(ventana: QMainWindow) -> None:
    """Devuelve la configuración a sus valores iniciales."""

    pendiente(
        ventana,
        "Restablecer valores",
        "Define aquí los valores originales de tu configuración."
    )


def pendiente(
    ventana: QMainWindow,
    titulo: str,
    detalle: str
) -> None:
    """Muestra un aviso mientras la función todavía no está implementada."""

    QMessageBox.information(ventana, titulo, detalle)


# ============================================================
# 7. CONECTAR BOTONES CON SUS FUNCIONES
# ============================================================

def conectar_logica(ventana: QMainWindow) -> None:#types hints o anotacions de tipos sriven para comprender el codigo pero python no nos obliuga a cumplirla como c#
    ventana.frame_capturado = None
    acciones = {
        "btnIniciarCamara": iniciar_camara,
        "btnDetenerCamara": detener_camara,
        "btnCapturarRostro": capturar_rostro,
        "btnGuardarRegistro": guardar_registro,
        "btnGuardarConfiguracion": guardar_configuracion,
        "btnRestablecerConfiguracion": restablecer_configuracion,
    }

    for nombre_boton, funcion in acciones.items():

        boton = ventana.findChild(QPushButton, nombre_boton)

        if boton is not None:
            def ejecutar(estado=False, accion=funcion):
                accion(ventana)
            # # boton.clicked.connect(
            # #     lambda  accion=funcion: accion(ventana)
            # # )
            boton.clicked.connect(ejecutar)#si presiionas el boton es un false y lo interpreta como el primer parametro
            #le entrego la funcion para que uenda el evento ocuura la ejeciute 


# ============================================================
# 8. INICIAR APLICACIÓN
# ============================================================

def main() -> int:

    aplicacion = QApplication(sys.argv)

    ventana = cargar_ventana()
    ventana.procesador = None      # todavía no hay cámara corriendo

    conectar_pantallas(ventana)
    conectar_logica(ventana)
    cargar_personas(ventana)
    def cerrar_todo():
        if ventana.procesador is not None:
          ventana.procesador.detener()
          ventana.procesador.wait()    # esperamos a que termine su limpieza

    aplicacion.aboutToQuit.connect(cerrar_todo)
    ventana.show()

    return aplicacion.exec()

if __name__ == "__main__":
    raise SystemExit(main())
