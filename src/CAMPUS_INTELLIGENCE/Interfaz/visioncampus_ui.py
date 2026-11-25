# ############################################################
#   VISIONCAMPUS - visioncampus_ui.py
#
#   visioncampus.ui   -> ESTRUCTURA (qué hay y dónde, como el HTML)
#   visioncampus.qss  -> COLORES y estilo (como el CSS)
#   este archivo      -> LÓGICA, en dos partes:
#       PARTE 1: TU LÓGICA  (secciones 1 a 7)  <- aquí programas tú
#       PARTE 2: INTERFAZ / DISEÑO (no hace falta estudiarla)
#       8. INICIAR APLICACIÓN (main)
# ############################################################


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


# ############################################################
#   PARTE 1: TU LÓGICA  (cámara, registro, personas, botones)
# ############################################################

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

    # [EXPLICACIÓN] ¿QUÉ HACE ESTA FUNCIÓN?
    # [EXPLICACIÓN] Hace que, al pulsar un botón del menú (Monitoreo, Registro Facial...),
    # [EXPLICACIÓN] cambie la pantalla que se ve.
    # [EXPLICACIÓN]
    # [EXPLICACIÓN] "paginas" es el QStackedWidget: como un mazo de cartas donde solo se ve una.
    # [EXPLICACIÓN]     índice 0 = Monitoreo, 1 = Registro Facial, 2 = Personas, 3 = Configuración
    paginas = ventana.findChild(QStackedWidget, "paginas")

    # [EXPLICACIÓN] El ORDEN importa: el botón de la posición 0 abre la página 0, el 1 la página 1...
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

        # [EXPLICACIÓN] Paso 1: mostrar la página pedida (como voltear a esa carta del mazo).
        paginas.setCurrentIndex(indice)
        # Los puntos del rostro solo se dibujan en Registro Facial (índice 1)
        if ventana.procesador is not None and ventana.procesador.core is not None:
            ventana.procesador.core.dibujar_puntos = (indice == 1)

        # [EXPLICACIÓN] Paso 3: dejar marcado SOLO el botón de la página actual.
        # [EXPLICACIÓN] enumerate da la posición (0,1,2,3) y el nombre de cada botón.
        # [EXPLICACIÓN] "posicion == indice" es True solo para uno, por eso solo uno se ve resaltado.
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
    # [EXPLICACIÓN] El slider da números enteros (por ejemplo 50) y aquí se muestran como 0.50.

    deslizador = ventana.findChild(QSlider, "controlUmbral")
    texto_umbral = ventana.findChild(QLabel, "valorUmbral")

    if deslizador is not None and texto_umbral is not None:
        deslizador.valueChanged.connect(
            lambda valor: texto_umbral.setText(f"{valor / 100:.2f}")
        )

    # Cada vez que se escribe, filtramos los registros de la tabla.
    busqueda = ventana.findChild(QLineEdit, "campoBuscarPersona")

    # [EXPLICACIÓN] textChanged se dispara con cada letra que escribes y manda el texto actual
    # [EXPLICACIÓN] a filtrar_tabla_personas (la sección 5, justo abajo).
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

    #casefold() pasa a minúsculas

    busqueda = texto.strip().casefold()

    for fila in range(tabla.rowCount()):

       
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
            boton_autorizar = QPushButton()
            boton_autorizar.setObjectName("botonAutorizar")

            boton_autorizar.clicked.connect(
                lambda estado=False, id=id_rostro, actual=autorizado:
                    cambiar_autorizacion(ventana, id, actual)
            )

            disposicion.addWidget(boton_autorizar)
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
# [TU LÓGICA] FASE A: aquí va la función cambiar_autorizacion(ventana, id_rostro, autorizado_actual)
# [TU LÓGICA]   - calcula el valor contrario: not autorizado_actual
# [TU LÓGICA]   - UPDATE rostros_registrados SET autorizado = %s WHERE id_rostro = %s
# [TU LÓGICA]   - commit() / rollback() igual que en eliminar_persona
# [TU LÓGICA]   - al final: cargar_personas(ventana) para refrescar la tabla

def cambiar_autorizacion(ventana: QMainWindow, id_rostro: int, autorizacion:bool) -> None:
    valor = not autorizacion
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor()
           
        cursor.execute(
                        "UPDATE rostros_registrados SET autorizado = %s WHERE id_rostro = %s",
                       (valor,id_rostro)
                   )
        conexion.commit()
           
    except Exception as error:
        if conexion is not None:
            conexion.rollback()
           
            QMessageBox.critical(ventana, "CAMBIAR AUTORIZACION", f"No se pudo CAMBIAR LA AUTORIZACION:\n{error}")
            return
           
    finally:
            if cursor is not None:
                cursor.close()
            if conexion is not None:
                conexion.close()

            if ventana.procesador is not None:
                ventana.procesador.autorizacion_pendiente = (id_rostro, valor)
           
              
            cargar_personas(ventana) 
        

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
            (id_rostro)
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
    activar_modo_anonimo(ventana)       


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

def activar_modo_anonimo(ventana):
    
    casilla = ventana.findChild(QCheckBox, "checkModoAnonimo")

    if casilla is None:
        return

    if ventana.procesador is not None:
        if  ventana.procesador.core is not None:
            ventana.procesador.core.modo_anonimo = casilla.isChecked()
         
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
    casilla_anonimo = ventana.findChild(QCheckBox, "checkModoAnonimo")   # <- PIEZA 4
    if casilla_anonimo is not None:
        casilla_anonimo.toggled.connect(lambda _marcado: activar_modo_anonimo(ventana))

# ############################################################
# ############################################################
#
#   PARTE 2: INTERFAZ / DISEÑO  (NO HACE FALTA ESTUDIARLO)
#
#   Todo lo de aquí abajo es decoración y datos en vivo:
#   animaciones, brillos, logo, iconos, reloj, FPS, barra de
#   ocupación y "Actividad reciente".
#
#   NO cambia tu lógica de arriba. Se engancha desde afuera:
#   main() llama UNA vez a aplicar_diseno(ventana), y cuando
#   pulsas "Iniciar cámara" primero corre TU iniciar_camara y
#   después cuando_inicia_camara (de aquí abajo).
#
#   Si borras la línea  aplicar_diseno(ventana)  en main(),
#   la app funciona igual, pero sin el diseño extra.
#
#   Los colores NO están aquí: están en visioncampus.qss.
#
# ############################################################
# ############################################################

from datetime import datetime
from PySide6.QtCore import (
    QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation, QRect, QRectF,
    QSize, QTimer
)
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QListWidget,
    QListWidgetItem, QProgressBar, QStyle, QStyledItemDelegate,
    QStyleOptionViewItem
)

# Carpeta con el fondo, el logo y los iconos (imágenes .png)
RECURSOS = CARPETA / "recursos"


# ============================================================
# A. DISEÑO PURO: ANIMACIONES, BRILLO, LOGO E ICONOS
# ============================================================

def poner_brillo(ventana: QMainWindow) -> None:
    """Da un brillo de color (efecto neón) a botones y tarjetas.

    Qt no tiene 'box-shadow' en el .qss, así que se hace con
    QGraphicsDropShadowEffect: una sombra sin desplazamiento y con color.
    Se evita el video para no bajar los FPS.
    """
    # nombre del widget -> color del brillo (R, G, B)
    brillos = {
        "btnIniciarCamara": (23, 214, 140),
        "btnGuardarRegistro": (23, 214, 140),
        "btnGuardarConfiguracion": (23, 214, 140),
        "btnCapturarRostro": (15, 166, 245),
        "btnIrEstadisticas": (15, 166, 245),
        "tarjetaDetectadas": (43, 196, 255),
        "tarjetaReconocidas": (62, 232, 165),
        "tarjetaOcupacion": (122, 155, 255),
        "tarjetaDesconocidos": (255, 169, 77),
        "tarjetaNoAutorizadas": (255, 77, 94),
    }

    for nombre, (r, g, b) in brillos.items():
        widget = ventana.findChild(QWidget, nombre)
        if widget is None:
            continue

        efecto = QGraphicsDropShadowEffect(widget)
        efecto.setBlurRadius(28)          # qué tan difuso es el brillo
        efecto.setOffset(0, 0)            # sin desplazamiento: brilla alrededor
        efecto.setColor(QColor(r, g, b, 120))
        widget.setGraphicsEffect(efecto)

        # Solo los botones reaccionan al mouse (las tarjetas no)
        if isinstance(widget, QPushButton):
            widget.installEventFilter(ventana.filtro_brillo)


class BrilloAlPasar(QObject):
    """Filtro de eventos: cuando el mouse entra a un botón su brillo crece,
    y cuando sale vuelve a la normalidad (parecido a :hover, pero animado)."""

    def eventFilter(self, objeto, evento):
        efecto = objeto.graphicsEffect()
        if isinstance(efecto, QGraphicsDropShadowEffect):
            if evento.type() == QEvent.Type.Enter:
                self.animar(objeto, efecto, 50)
            elif evento.type() == QEvent.Type.Leave:
                self.animar(objeto, efecto, 28)
        return False   # False = el botón sigue recibiendo el evento normalmente

    def animar(self, objeto, efecto, destino):
        anterior = getattr(objeto, "animacion_brillo", None)
        if anterior is not None:
            anterior.stop()

        animacion = QPropertyAnimation(efecto, b"blurRadius", efecto)
        animacion.setDuration(220)
        animacion.setEndValue(destino)
        animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
        objeto.animacion_brillo = animacion   # guardamos la referencia
        animacion.start()


def animar_entrada(pagina: QWidget) -> None:
    """La página nueva entra deslizándose un poco desde la derecha."""
    if pagina is None:
        return
    animacion = QPropertyAnimation(pagina, b"pos", pagina)
    animacion.setDuration(300)
    animacion.setStartValue(QPoint(45, 0))
    animacion.setEndValue(QPoint(0, 0))
    animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
    animacion.start()


def iniciar_pulso(etiqueta: QLabel) -> None:
    """Hace 'respirar' la etiqueta EN VIVO cambiando su opacidad."""
    if getattr(etiqueta, "pulso", None) is not None:
        return   # ya está pulsando

    efecto = QGraphicsOpacityEffect(etiqueta)
    etiqueta.setGraphicsEffect(efecto)

    pulso = QPropertyAnimation(efecto, b"opacity", efecto)
    pulso.setDuration(1400)
    pulso.setKeyValueAt(0.0, 1.0)
    pulso.setKeyValueAt(0.5, 0.4)
    pulso.setKeyValueAt(1.0, 1.0)
    pulso.setLoopCount(-1)          # -1 = se repite para siempre
    etiqueta.pulso = pulso
    pulso.start()


def detener_pulso(etiqueta: QLabel) -> None:
    pulso = getattr(etiqueta, "pulso", None)
    if pulso is not None:
        pulso.stop()
        etiqueta.pulso = None
    etiqueta.setGraphicsEffect(None)   # quita el efecto (y la animación con él)


def poner_imagenes(ventana: QMainWindow) -> None:
    """Pone el logo y los iconos del menú desde la carpeta recursos."""
    logo = ventana.findChild(QLabel, "logoIcon")
    ruta_logo = RECURSOS / "logo.png"
    if logo is not None and ruta_logo.exists():
        imagen = QPixmap(str(ruta_logo)).scaled(
            76, 76,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logo.setPixmap(imagen)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # botón -> nombre del icono (icono_X.png normal, icono_X_activo.png seleccionado)
    iconos = {
        "btnMonitoreo": "monitoreo",
        "btnRegistroFacial": "registro",
        "btnPersonas": "personas",
        "btnConfiguracion": "config",
    }
    for nombre, archivo in iconos.items():
        boton = ventana.findChild(QPushButton, nombre)
        normal = RECURSOS / f"icono_{archivo}.png"
        activo = RECURSOS / f"icono_{archivo}_activo.png"
        if boton is None or not normal.exists() or not activo.exists():
            continue

        icono = QIcon()
        icono.addPixmap(QPixmap(str(normal)), QIcon.Mode.Normal, QIcon.State.Off)
        icono.addPixmap(QPixmap(str(activo)), QIcon.Mode.Normal, QIcon.State.On)  # On = seleccionado
        boton.setIcon(icono)
        boton.setIconSize(QSize(22, 22))
        boton.setText("   " + boton.text().strip())   # espacio entre icono y texto


def aparecer_ventana(ventana: QMainWindow) -> None:
    """Al abrir, la ventana aparece con un fundido suave."""
    ventana.setWindowOpacity(0.0)
    animacion = QPropertyAnimation(ventana, b"windowOpacity", ventana)
    animacion.setDuration(450)
    animacion.setStartValue(0.0)
    animacion.setEndValue(1.0)
    animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
    animacion.start()


def poner_en_vivo(ventana: QMainWindow, activo: bool) -> None:
    """Cambia la etiqueta de arriba a la derecha: EN VIVO o CÁMARA APAGADA."""
    etiqueta = ventana.findChild(QLabel, "etiquetaEnVivo")
    if etiqueta is None:
        return

    etiqueta.setText("●  EN VIVO" if activo else "●  CÁMARA APAGADA")

    if activo:
        iniciar_pulso(etiqueta)    # parpadeo suave mientras hay video
    else:
        detener_pulso(etiqueta)

    # El .qss pinta de rojo cuando activa="true" (propiedad dinámica de Qt)
    etiqueta.setProperty("activa", activo)

    # Qt no repinta solo al cambiar una propiedad: lo forzamos
    etiqueta.style().unpolish(etiqueta)
    etiqueta.style().polish(etiqueta)

    ventana.en_vivo = activo  # recordamos el estado para no repintar en cada frame


# ============================================================
# B. DATOS EN VIVO: BARRA, ACTIVIDAD, RELOJ Y FPS
# ============================================================

def actualizar_barra_ocupacion(ventana: QMainWindow, datos: dict) -> None:
    """Llena la barra de ocupación y le cambia el color según el nivel."""
    barra = ventana.findChild(QProgressBar, "barraOcupacion")
    texto = ventana.findChild(QLabel, "estadoOcupacion")
    ocupacion = datos["ocupacion"]

    if ocupacion < 50:
        nivel = "bajo"        # verde
    elif ocupacion < 80:
        nivel = "medio"       # amarillo
    else:
        nivel = "alto"        # rojo

    if barra is not None:
        barra.setValue(int(min(ocupacion, 100)))
        # Solo repintamos el estilo cuando el nivel cambia (no en cada frame)
        if barra.property("nivel") != nivel:
            barra.setProperty("nivel", nivel)
            barra.style().unpolish(barra)
            barra.style().polish(barra)

    if texto is not None:
        capacidad = datos.get("capacidad", "?")
        texto.setText(f'{datos["estado"].capitalize()}  ·  {datos["personas"]}/{capacidad}')


def agregar_eventos(ventana: QMainWindow, eventos: list) -> None:
    """Pone arriba de la lista las entradas y salidas nuevas."""
    lista = ventana.findChild(QListWidget, "listaActividad")
    if lista is None or not eventos:
        return

    # Si todavía está el mensaje "Sin actividad", lo quitamos
    if lista.count() == 1 and lista.item(0).data(Qt.ItemDataRole.UserRole) == "vacio":
        lista.clear()

    for tipo, id_persona, hora, permanencia in eventos:
        reloj = datetime.fromtimestamp(hora).strftime("%H:%M:%S")

        if tipo == "ENTRADA":
            texto = f"{reloj}   ➜  Entró persona #{id_persona}"
            color = QColor(85, 238, 174)      # verde
        else:
            minutos, segundos = divmod(int(permanencia or 0), 60)
            texto = f"{reloj}   ⬅  Salió persona #{id_persona}  ({minutos} min {segundos} s)"
            color = QColor(255, 179, 102)     # naranja

        item = QListWidgetItem(texto)
        item.setForeground(color)
        lista.insertItem(0, item)             # lo más nuevo arriba

    # Guardamos solo los últimos 30 para no llenar la memoria
    while lista.count() > 30:
        lista.takeItem(lista.count() - 1)


def mostrar_sin_actividad(ventana: QMainWindow) -> None:
    lista = ventana.findChild(QListWidget, "listaActividad")
    if lista is None:
        return
    lista.clear()
    item = QListWidgetItem("Sin actividad todavía. Enciende la cámara.")
    item.setData(Qt.ItemDataRole.UserRole, "vacio")   # marca para saber que es el mensaje
    item.setForeground(QColor(138, 163, 191))
    lista.addItem(item)


def iniciar_reloj(ventana: QMainWindow) -> None:
    """Cada segundo actualiza la hora, y el FPS y tiempo activo si hay cámara."""
    reloj = ventana.findChild(QLabel, "relojMonitoreo")
    texto_fps = ventana.findChild(QLabel, "textoFps")

    def tic():
        ahora = datetime.now()
        if reloj is not None:
            reloj.setText(ahora.strftime("%H:%M:%S   %d/%m/%Y"))

        if texto_fps is None:
            return

        if getattr(ventana, "en_vivo", False):
            fps = ventana.contador_frames          # frames que llegaron en este segundo
            ventana.contador_frames = 0
            activo = int((ahora - ventana.inicio_camara).total_seconds())
            horas, resto = divmod(activo, 3600)
            minutos, segundos = divmod(resto, 60)
            texto_fps.setText(f"FPS: {fps}    ⏱ {horas:02d}:{minutos:02d}:{segundos:02d}")
        else:
            texto_fps.setText("FPS: —")

    ventana.temporizador_reloj = QTimer(ventana)   # guardamos la referencia
    ventana.temporizador_reloj.timeout.connect(tic)
    ventana.temporizador_reloj.start(1000)          # cada 1000 ms = 1 segundo
    tic()


def mostrar_datos_vivos(ventana: QMainWindow, datos: dict) -> None:
    """Recibe las estadísticas del procesador (el mismo diccionario que ya
    usa tu actualizar_estadisticas) y actualiza SOLO lo nuevo."""

    # Sin identificar = detectadas por el cuerpo pero sin rostro reconocido
    desconocidos = ventana.findChild(QLabel, "valorDesconocidos")
    if desconocidos is not None:
        desconocidos.setText(str(max(datos["personas"] - datos["reconocidas"], 0)))

    # No autorizadas = rostros registrados con permiso quitado (clave "no_autorizados")
    no_autorizadas = ventana.findChild(QLabel, "valorNoAutorizadas")
    if no_autorizadas is not None:
        no_autorizadas.setText(str(datos.get("no_autorizados", 0)))

    actualizar_barra_ocupacion(ventana, datos)
    agregar_eventos(ventana, datos.get("eventos", []))


def contar_frame(ventana: QMainWindow, frame) -> None:
    """Se ejecuta cada vez que llega una imagen de la cámara."""
    # Con el primer fotograma, la etiqueta pasa a EN VIVO y empieza el cronómetro
    if not getattr(ventana, "en_vivo", False):
        poner_en_vivo(ventana, True)
        ventana.inicio_camara = datetime.now()
        ventana.contador_frames = 0

    ventana.contador_frames += 1   # el reloj lo convierte en FPS cada segundo


def camara_apagada(ventana: QMainWindow) -> None:
    """Se ejecuta cuando el hilo de la cámara termina."""
    poner_en_vivo(ventana, False)
    estado = ventana.findChild(QLabel, "estadoCamara")
    if estado is not None:
        estado.setText("● Esperando cámara")


def cambiar_umbral(ventana: QMainWindow, umbral: float) -> None:
    """El slider de Configuración: guarda el umbral facial y se lo pasa
    al hilo de la cámara (si está corriendo). El texto 0.50 lo sigue
    cambiando TU lambda de conectar_pantallas."""
    ventana.umbral_facial = umbral
    if ventana.procesador is not None:
        ventana.procesador.umbral_facial = umbral


# ============================================================
# D. PERSONAS: INICIALES, ESTADO, BASURERO Y RESUMEN (v1.0)
#    Todo es DISEÑO: solo dibuja y LEE la tabla. No cambia cómo se llena
#    (cargar_personas) ni cómo se elimina (eliminar_persona).
# ============================================================

class DelegadoNombre(QStyledItemDelegate):
    """Dibuja un círculo con las iniciales a la izquierda del nombre."""

    COLORES = ["#2bc4ff", "#3ee8a5", "#7a9bff", "#ffa94d", "#ff7ab6", "#b48cff"]

    def paint(self, painter, option, index):
        opcion = QStyleOptionViewItem(option)
        self.initStyleOption(opcion, index)
        nombre = opcion.text
        opcion.text = ""   # el fondo y la selección los dibuja Qt; el texto lo dibujamos nosotros
        estilo = opcion.widget.style() if opcion.widget else QApplication.style()
        estilo.drawControl(QStyle.ControlElement.CE_ItemViewItem, opcion, painter, opcion.widget)

        palabras = nombre.split()
        iniciales = "".join(p[0] for p in palabras[:2]).upper() or "?"
        color = QColor(self.COLORES[sum(ord(letra) for letra in nombre) % len(self.COLORES)])
        diametro = 34
        zona = option.rect
        circulo = QRectF(zona.left() + 18, zona.center().y() - diametro / 2, diametro, diametro)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        relleno = QColor(color)
        relleno.setAlpha(55)
        painter.setBrush(relleno)
        painter.setPen(QPen(color, 1.5))
        painter.drawEllipse(circulo)

        letra = painter.font()
        letra.setBold(True)
        letra.setPointSize(9)
        painter.setFont(letra)
        painter.setPen(color.lighter(130))
        painter.drawText(circulo, Qt.AlignmentFlag.AlignCenter, iniciales)
        painter.restore()

        painter.save()
        painter.setPen(QColor("#e6f0fb"))
        texto = QRect(int(circulo.right()) + 12, zona.top(), zona.width() - 70, zona.height())
        painter.drawText(texto, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, nombre)
        painter.restore()


class DelegadoEstado(QStyledItemDelegate):
    """Dibuja el estado como una pastilla: verde si está autorizado, roja si no."""

    def paint(self, painter, option, index):
        opcion = QStyleOptionViewItem(option)
        self.initStyleOption(opcion, index)
        texto = opcion.text
        opcion.text = ""
        estilo = opcion.widget.style() if opcion.widget else QApplication.style()
        estilo.drawControl(QStyle.ControlElement.CE_ItemViewItem, opcion, painter, opcion.widget)

        autorizado = (texto == "Autorizado")
        borde = QColor("#3ee8a5") if autorizado else QColor("#ff6b76")
        letra = QColor("#55eeae") if autorizado else QColor("#ff8a94")
        relleno = QColor(borde)
        relleno.setAlpha(40)

        ancho = painter.fontMetrics().horizontalAdvance(texto) + 30
        alto = 28
        zona = option.rect
        pastilla = QRectF(
            zona.center().x() - ancho / 2, zona.center().y() - alto / 2, ancho, alto
        )

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(relleno)
        painter.setPen(QPen(borde, 1.2))
        painter.drawRoundedRect(pastilla, alto / 2, alto / 2)
        painter.setPen(letra)
        painter.drawText(pastilla, Qt.AlignmentFlag.AlignCenter, texto)
        painter.restore()


def poner_texto_tarjeta(ventana: QMainWindow, nombre: str, texto: str) -> None:
    etiqueta = ventana.findChild(QLabel, nombre)
    if etiqueta is not None and etiqueta.text() != texto:
        etiqueta.setText(texto)


def decorar_personas(ventana: QMainWindow) -> None:
    """Pone el basurero en cada fila y calcula las tarjetas de resumen.
    Solo LEE la tabla; no la modifica (salvo el aspecto del botón)."""

    tabla = ventana.findChild(QTableWidget, "tablaPersonas")
    if tabla is None:
        return

    autorizadas = 0
    no_autorizadas = 0
    ultima = None

    for fila in range(tabla.rowCount()):

        # Basurero en lugar de "⋮" (cargar_personas crea los botones nuevos cada vez)
        contenedor = tabla.cellWidget(fila, 3)
        if contenedor is not None:
            boton = contenedor.findChild(QPushButton, "botonAccion")
            if boton is not None and not boton.toolTip():
                boton.setText("")
                boton.setIcon(QIcon(str(RECURSOS / "icono_basurero.png")))
                boton.setIconSize(QSize(20, 20))
                boton.setToolTip("Eliminar persona")

        # Conteo de autorizadas
        item_estado = tabla.item(fila, 2)
        autorizado_ahora = item_estado is not None and item_estado.text() == "Autorizado"
        if item_estado is not None:
            if autorizado_ahora:
                autorizadas += 1
            else:
                no_autorizadas += 1

        # Botón de autorización (lo crea TU cargar_personas; aquí solo se le pone ícono)
        if contenedor is not None:
            boton_aut = contenedor.findChild(QPushButton, "botonAutorizar")
            if boton_aut is not None:
                ayuda = "Quitar autorización" if autorizado_ahora else "Autorizar"
                if boton_aut.toolTip() != ayuda:
                    icono = "icono_candado.png" if autorizado_ahora else "icono_autorizar.png"
                    boton_aut.setText("")
                    boton_aut.setIcon(QIcon(str(RECURSOS / icono)))
                    boton_aut.setIconSize(QSize(20, 20))
                    boton_aut.setToolTip(ayuda)

        # Fecha más reciente
        item_fecha = tabla.item(fila, 1)
        if item_fecha is not None:
            try:
                fecha = datetime.strptime(item_fecha.text(), "%d/%m/%Y %H:%M")
            except ValueError:
                fecha = None
            if fecha is not None and (ultima is None or fecha > ultima):
                ultima = fecha

    poner_texto_tarjeta(ventana, "valorPersonasAutorizadas", str(autorizadas))
    poner_texto_tarjeta(ventana, "valorPersonasNoAutorizadas", str(no_autorizadas))
    poner_texto_tarjeta(
        ventana, "valorPersonasUltima",
        ultima.strftime("%d/%m/%Y %H:%M") if ultima is not None else "—"
    )


def iniciar_decoracion_personas(ventana: QMainWindow) -> None:
    """Se llama UNA vez. Mientras se ve la pantalla Personas, repite decorar_personas."""

    tabla = ventana.findChild(QTableWidget, "tablaPersonas")
    if tabla is not None:
        tabla.setItemDelegateForColumn(0, DelegadoNombre(tabla))
        tabla.setItemDelegateForColumn(2, DelegadoEstado(tabla))

    paginas = ventana.findChild(QStackedWidget, "paginas")
    if paginas is None:
        return

    def si_se_ve_personas():
        if paginas.currentIndex() == 2:
            decorar_personas(ventana)

    paginas.currentChanged.connect(lambda indice: si_se_ve_personas())

    temporizador = QTimer(ventana)
    temporizador.setInterval(300)
    temporizador.timeout.connect(si_se_ve_personas)
    temporizador.start()
    ventana.temporizador_personas = temporizador   # lo guardamos para que no se borre


# ============================================================
# E. REGISTRO FACIAL: ÓVALO GUÍA Y COLOR DEL ESTADO (v1.0)
#    Todo es DISEÑO. No cambia capturar_rostro ni guardar_registro:
#    solo LEE el texto que escribe tu lógica en "estadoCaptura".
# ============================================================

class GuiaOvalo(QWidget):
    """Capa transparente sobre la vista de cámara: dibuja un óvalo punteado
    y una frase para indicar dónde poner la cara. No recibe clics.
    Se centra sobre la IMAGEN real de la cámara (no sobre todo el cuadro negro)."""

    def __init__(self, padre, etiqueta_imagen):
        super().__init__(padre)
        self.etiqueta = etiqueta_imagen   # el QLabel donde tu lógica pone la imagen
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def zona_imagen(self) -> QRectF:
        """Rectángulo que ocupa la imagen de la cámara (o todo el cuadro si aún no hay)."""
        zona = QRectF(0, 0, self.width(), self.height())
        if self.etiqueta is None:
            return zona
        imagen = self.etiqueta.pixmap()
        if imagen is None or imagen.isNull():
            return zona
        caja = self.etiqueta.geometry()   # posición del QLabel dentro del cuadro
        ancho = min(imagen.width(), caja.width())
        alto = min(imagen.height(), caja.height())
        izquierda = caja.x() + (caja.width() - ancho) / 2
        arriba = caja.y() + (caja.height() - alto) / 2
        return QRectF(izquierda, arriba, ancho, alto)

    def paintEvent(self, evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)

        zona = self.zona_imagen()
        ovalo_alto = zona.height() * 0.68
        ovalo_ancho = ovalo_alto * 0.74            # proporción de un rostro
        ovalo = QRectF(
            zona.center().x() - ovalo_ancho / 2,
            zona.top() + zona.height() * 0.08,
            ovalo_ancho,
            ovalo_alto,
        )

        lapiz = QPen(QColor(43, 196, 255, 170))
        lapiz.setWidth(2)
        lapiz.setStyle(Qt.PenStyle.DashLine)
        pintor.setPen(lapiz)
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawEllipse(ovalo)

        # Frase sobre una pastilla oscura para que se lea sobre cualquier fondo
        fuente = QFont(pintor.font())
        fuente.setPointSize(10)
        pintor.setFont(fuente)
        texto = "Coloca tu rostro dentro del óvalo"
        medida = pintor.fontMetrics().horizontalAdvance(texto) + 28
        pastilla = QRectF(zona.center().x() - medida / 2, zona.bottom() - 40, medida, 28)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QColor(3, 8, 15, 190))
        pintor.drawRoundedRect(pastilla, 14, 14)
        pintor.setPen(QColor(207, 227, 247, 240))
        pintor.drawText(pastilla, Qt.AlignmentFlag.AlignCenter, texto)


class AjustarGuia(QObject):
    """Filtro de eventos: cuando la vista de cámara cambia de tamaño,
    la capa del óvalo se estira para cubrirla."""

    def __init__(self, guia, vista):
        super().__init__(vista)
        self.guia = guia

    def eventFilter(self, objeto, evento):
        if evento.type() == QEvent.Type.Resize:
            self.guia.setGeometry(0, 0, objeto.width(), objeto.height())
        return False


def poner_estado_captura(ventana: QMainWindow) -> None:
    """Pinta el estado según el texto que dejó tu lógica:
    verde = foto lista, naranja = aviso, gris = sin foto."""
    estado = ventana.findChild(QLabel, "estadoCaptura")
    if estado is None:
        return

    texto = estado.text().strip().upper()
    if texto == "" or texto.startswith("SIN FOTO"):
        valor = "vacio"
    elif "CAPTURADA" in texto:
        valor = "ok"
    else:
        valor = "aviso"    # "enciende la cámara", "espera un momento", etc.

    if estado.property("estado") != valor:
        estado.setProperty("estado", valor)
        estado.style().unpolish(estado)   # obliga a Qt a releer el .qss
        estado.style().polish(estado)

    estado.setVisible(texto != "")        # sin texto, no se ve la cajita vacía

    guia = getattr(ventana, "guia_ovalo", None)
    if guia is not None:
        guia.update()                     # se reacomoda cuando llega la imagen de la cámara


def decorar_registro(ventana: QMainWindow) -> None:
    """Se llama UNA vez: pone el óvalo guía y empieza a vigilar el estado."""
    vista = ventana.findChild(QFrame, "vistaRegistro")
    if vista is not None:
        guia = GuiaOvalo(vista, ventana.findChild(QLabel, "textoRostroVacio"))
        guia.setGeometry(0, 0, vista.width(), vista.height())
        guia.raise_()   # encima de la imagen de la cámara
        guia.show()
        ventana.guia_ovalo = guia
        ventana.ajustar_guia = AjustarGuia(guia, vista)
        vista.installEventFilter(ventana.ajustar_guia)

    temporizador = QTimer(ventana)
    temporizador.setInterval(300)
    temporizador.timeout.connect(lambda: poner_estado_captura(ventana))
    temporizador.start()
    ventana.temporizador_registro = temporizador   # lo guardamos para que no se borre
    poner_estado_captura(ventana)


# ============================================================
# C. CONEXIÓN: EL ÚNICO PUNTO DE ENTRADA
# ============================================================

def cuando_inicia_camara(ventana: QMainWindow) -> None:
    """Corre justo DESPUÉS de tu iniciar_camara (misma pulsación del botón).
    Aquí ya existe ventana.procesador y nos conectamos a sus señales."""
    procesador = ventana.procesador

    if procesador is None:
        return   # tu función no inició la cámara (por ejemplo, ya estaba encendida)

    if getattr(procesador, "diseno_conectado", False):
        return   # ya lo conectamos antes: evita duplicar conexiones
    procesador.diseno_conectado = True

    mostrar_sin_actividad(ventana)                       # cada encendido empieza limpio
    procesador.umbral_facial = ventana.umbral_facial     # arranca con el umbral elegido

    # Señales del procesador (las mismas que usas tú, ahora con un segundo oyente)
    procesador.estadisticas.connect(lambda datos: mostrar_datos_vivos(ventana, datos))
    procesador.nueva_imagen.connect(lambda frame: contar_frame(ventana, frame))
    procesador.error.connect(lambda mensaje: poner_en_vivo(ventana, False))
    procesador.finished.connect(lambda: camara_apagada(ventana))


def aplicar_diseno(ventana: QMainWindow) -> None:
    """Se llama UNA vez desde main(), antes de ventana.show()."""

    # 1. Imágenes del .qss: el .qss escribe {RECURSOS} y aquí ponemos la ruta real
    estilos = ventana.styleSheet().replace("{RECURSOS}", RECURSOS.as_posix())
    ventana.setStyleSheet(estilos)

    # 2. Valores iniciales que usa este archivo
    ventana.umbral_facial = 0.50    # igual al valor inicial del slider
    ventana.contador_frames = 0

    # 3. Slider de umbral (segunda conexión: la tuya sigue funcionando igual)
    deslizador = ventana.findChild(QSlider, "controlUmbral")
    if deslizador is not None:
        deslizador.valueChanged.connect(
            lambda valor: cambiar_umbral(ventana, valor / 100)
        )

    # 4. Animación al cambiar de página (sin tocar tu mostrar_pagina)
    paginas = ventana.findChild(QStackedWidget, "paginas")
    if paginas is not None:
        paginas.currentChanged.connect(
            lambda indice: animar_entrada(paginas.currentWidget())
        )

    # 5. Botón "Iniciar cámara": mi conexión se agrega DESPUÉS de la tuya,
    #    por eso corre después de tu iniciar_camara
    boton_iniciar = ventana.findChild(QPushButton, "btnIniciarCamara")
    if boton_iniciar is not None:
        boton_iniciar.clicked.connect(
            lambda estado=False: cuando_inicia_camara(ventana)
        )

    # 6. Efectos visuales
    ventana.filtro_brillo = BrilloAlPasar(ventana)   # debe existir antes de poner_brillo
    poner_brillo(ventana)
    poner_imagenes(ventana)

    # 7. Panel de monitoreo en vivo
    mostrar_sin_actividad(ventana)
    iniciar_reloj(ventana)

    # 8. Pantalla Personas: iniciales, estado, basurero y tarjetas de resumen
    iniciar_decoracion_personas(ventana)

    # 8b. Registro Facial: óvalo guía y color del estado de captura
    decorar_registro(ventana)

    # 9. Fundido al abrir
    aparecer_ventana(ventana)


# ############################################################
#   FIN DE LA PARTE 2 (DISEÑO)
# ############################################################


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
    aplicar_diseno(ventana)   # [DISEÑO] ver PARTE 2: animaciones, iconos y datos en vivo
    ventana.show()

    return aplicacion.exec()

if __name__ == "__main__":
    raise SystemExit(main())
