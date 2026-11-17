
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
    QStackedWidget,
    QTableWidget,
)
from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtGui import QImage, QPixmap


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

# Carpeta donde se encuentran los archivos de la interfaz.
CARPETA = Path(__file__).resolve().parent

# Accedemos a la carpeta principal del proyecto.
sys.path.insert(0, str(CARPETA.parent))

from CAMPUS_INTELLIGENCE.Adaptador_Interfaz.Capturador_De_Frames import ProcesadorCamara


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

    if personas is not None:
        personas.setText(str(datos["personas"]))

    if ocupacion is not None:
        ocupacion.setText(f'{datos["ocupacion"]:.1f}%')



def iniciar_camara(ventana: QMainWindow) -> None:
    ventana.procesador = None
    if ventana.procesador is not None:
        return

    procesador = ProcesadorCamara()
    ventana.procesador = procesador#agreganos un atributo a nuestra venata que haga referencai a un nuestro objeto
    #concepto nuevo de POO

    vista = ventana.findChild(QLabel, "textoVistaVacia")#para lueo poner una imagen encima dese label
    estado = ventana.findChild(QLabel, "estadoCamara")

    def mostrar_imagen(frame):

        alto, ancho, canales = frame.shape#bgr o canales de color yvcahpe es forma
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
        vista.setPixmap(
            pixmap.scaled(
                vista.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        # vista.setScaledContents(True)
        # vista.setPixmap(pixmap)
        #scaled permite cambiar el tamano de nuestra imagebn
  
    def mostrar_error(mensaje):
        estado.setText("● Cámara desconectada")
        QMessageBox.warning(ventana, "Error de cámara", mensaje)

    # Liberamos la referencia cuando el trabajador termina.
    def limpiar_procesador():
        if ventana.procesador is procesador:
            ventana.procesador = None#eliminamos la refenrecia

    procesador.nueva_imagen.connect(mostrar_imagen)

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
    """Captura un rostro para el registro de una persona."""

    pendiente(
        ventana,
        "Capturar rostro",
        "Conecta aquí tu clase CapturarRostro."
    )


def guardar_registro(ventana: QMainWindow) -> None:
    """
    Guarda los datos de una persona y su rostro.

    Aquí conectarás los campos del formulario y PostgreSQL.
    También validarás el consentimiento antes de guardar.
    """

    pendiente(
        ventana,
        "Guardar registro",
        "Conecta aquí el guardado de persona y rostro en la base de datos."
    )


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
    """Relaciona cada botón con la función que debe ejecutar."""

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
    """Crea la aplicación, configura la ventana y la muestra."""

    aplicacion = QApplication(sys.argv)

    ventana = cargar_ventana()

    conectar_pantallas(ventana)
    conectar_logica(ventana)

    ventana.show()

    return aplicacion.exec()

if __name__ == "__main__":
    raise SystemExit(main())
