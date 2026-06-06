"""
Vista.py  (continuación — agregar al archivo ya existente)
Se muestra únicamente la clase VentanaDashboard ampliada.
Las otras clases (Bienvenida, Login, Cámara) permanecen intactas.
"""

# ── Importaciones adicionales que necesita el Dashboard ──────────────
import cv2
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox,
    QTableWidgetItem, QInputDialog
)
from PyQt5.uic import loadUi


class VentanaDashboard(QMainWindow):
    """
    Vista del panel médico principal.
    Su única responsabilidad: capturar eventos de la UI y delegarlos
    al coordinador. NUNCA hace cálculos aquí.
    """

    def __init__(self, coordinador=None):
        super().__init__()
        loadUi("views/ui/dashboard.ui", self)
        self.__coord = coordinador

        # Crear los canvas de matplotlib y embeberlos en los layouts del .ui
        self._inicializar_canvas_dicom()
        self._inicializar_canvas_senales()
        self._inicializar_canvas_tablas()

        # Conectar botones y widgets con el coordinador
        self._conectar_modulo_dicom()
        self._conectar_modulo_senales()
        self._conectar_modulo_tablas()

    # ===================================================================
    # SECCIÓN 1 — CANVAS MATPLOTLIB (se insertan en los layouts del .ui)
    # Los layouts en el .ui deben llamarse: layoutAxial, layoutSagital,
    # layoutCoronal, layoutSenalCanal, layoutSenalRuido,
    # layoutEstadisticas, layoutPlot, layoutScatter
    # ===================================================================
    def _inicializar_canvas_dicom(self):
        """Crea tres figuras para los cortes multiplanares."""
        self.fig_axial   = Figure(tight_layout=True)
        self.fig_sagital = Figure(tight_layout=True)
        self.fig_coronal = Figure(tight_layout=True)

        self.canvas_axial   = FigureCanvas(self.fig_axial)
        self.canvas_sagital = FigureCanvas(self.fig_sagital)
        self.canvas_coronal = FigureCanvas(self.fig_coronal)

        self.layoutAxial.addWidget(self.canvas_axial)
        self.layoutSagital.addWidget(self.canvas_sagital)
        self.layoutCoronal.addWidget(self.canvas_coronal)

        # Figura extra para zoom/recorte y segmentación
        self.fig_zoom = Figure(tight_layout=True)
        self.canvas_zoom = FigureCanvas(self.fig_zoom)
        self.layoutZoom.addWidget(self.canvas_zoom)

        self.fig_seg = Figure(tight_layout=True)
        self.canvas_seg = FigureCanvas(self.fig_seg)
        self.layoutSegmentacion.addWidget(self.canvas_seg)

    def _inicializar_canvas_senales(self):
        self.fig_canal = Figure(tight_layout=True)
        self.canvas_canal = FigureCanvas(self.fig_canal)
        self.layoutSenalCanal.addWidget(self.canvas_canal)

        self.fig_ruido = Figure(tight_layout=True)
        self.canvas_ruido = FigureCanvas(self.fig_ruido)
        self.layoutSenalRuido.addWidget(self.canvas_ruido)

        self.fig_stats = Figure(tight_layout=True)
        self.canvas_stats = FigureCanvas(self.fig_stats)
        self.layoutEstadisticas.addWidget(self.canvas_stats)

    def _inicializar_canvas_tablas(self):
        self.fig_plot   = Figure(tight_layout=True)
        self.canvas_plot = FigureCanvas(self.fig_plot)
        self.layoutPlot.addWidget(self.canvas_plot)

        self.fig_scatter = Figure(tight_layout=True)
        self.canvas_scatter = FigureCanvas(self.fig_scatter)
        self.layoutScatter.addWidget(self.canvas_scatter)

    # ===================================================================
    # SECCIÓN 2 — CONEXIONES MÓDULO DICOM
    # Widgets esperados en el .ui: btnCargarDicom, btnExportarCSV,
    # btnConvertirNifti, sliderAxial, sliderSagital, sliderCoronal,
    # btnAplicarZoom, btnGuardarRecorte, comboTipoUmbral, spinUmbral,
    # spinKernel, comboMorfologia, btnSegmentar
    # ===================================================================
    def _conectar_modulo_dicom(self):
        self.btnCargarDicom.clicked.connect(self._solicitar_carpeta_dicom)
        self.btnExportarCSV.clicked.connect(lambda: self.__coord.exportar_metadatos_csv())
        self.btnConvertirNifti.clicked.connect(lambda: self.__coord.convertir_a_nifti())

        self.sliderAxial.valueChanged.connect(
            lambda v: self.__coord.actualizar_corte("axial", v)
        )
        self.sliderSagital.valueChanged.connect(
            lambda v: self.__coord.actualizar_corte("sagital", v)
        )
        self.sliderCoronal.valueChanged.connect(
            lambda v: self.__coord.actualizar_corte("coronal", v)
        )

        self.btnAplicarZoom.clicked.connect(self._solicitar_parametros_recorte)
        self.btnGuardarRecorte.clicked.connect(self._solicitar_nombre_recorte)
        self.btnSegmentar.clicked.connect(self._solicitar_segmentacion)

    # ===================================================================
    # SECCIÓN 3 — CONEXIONES MÓDULO SEÑALES
    # Widgets esperados: btnCargarMat, spinCanalSenal, spinInicio, spinFin,
    # btnGraficarCanal, spinCanalRuido, spinDesviacion (o doubleSpinDesv),
    # btnAgregarRuido, radioEje0, radioEje1, radioEje2, btnCalcEstadisticas
    # ===================================================================
    def _conectar_modulo_senales(self):
        self.btnCargarMat.clicked.connect(self._solicitar_archivo_mat)
        self.btnGraficarCanal.clicked.connect(self._solicitar_graficado_canal)
        self.btnAgregarRuido.clicked.connect(self._solicitar_ruido)
        self.btnCalcEstadisticas.clicked.connect(self._solicitar_estadisticas_3d)

    # ===================================================================
    # SECCIÓN 4 — CONEXIONES MÓDULO TABLAS
    # Widgets esperados: btnCargarTabla, listColumnasPlt (QListWidget, multiselect),
    # btnGraficarColumnas, comboColX, comboColY, btnScatter,
    # tablaInfoDf, tablaDescribeDf
    # ===================================================================
    def _conectar_modulo_tablas(self):
        self.btnCargarTabla.clicked.connect(self._solicitar_archivo_tabla)
        self.btnGraficarColumnas.clicked.connect(self._solicitar_plot_columnas)
        self.btnScatter.clicked.connect(
            lambda: self.__coord.graficar_scatter(
                self.comboColX.currentText(),
                self.comboColY.currentText()
            )
        )

    # ===================================================================
    # MÉTODOS AUXILIARES DE VISTA — Solo abren diálogos y delegan al coord
    # ===================================================================
    def _solicitar_carpeta_dicom(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta DICOM")
        if carpeta:
            self.__coord.cargar_dicom(carpeta)

    def _solicitar_archivo_mat(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo .mat", "", "MAT Files (*.mat)")
        if ruta:
            self.__coord.cargar_señal(ruta)

    def _solicitar_archivo_tabla(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar datos médicos", "",
            "Archivos de datos (*.csv *.xlsx *.xls)"
        )
        if ruta:
            self.__coord.cargar_tabla(ruta)

    def _solicitar_graficado_canal(self):
        canal  = self.spinCanalSenal.value()
        inicio = self.spinInicio.value()
        fin    = self.spinFin.value()
        self.__coord.graficar_canal(canal, inicio, fin)

    def _solicitar_ruido(self):
        canal = self.spinCanalRuido.value()
        desv  = self.doubleSpinDesv.value()
        self.__coord.mostrar_canal_ruidoso(canal, desv)

    def _solicitar_estadisticas_3d(self):
        # Determinamos eje según el RadioButton activo
        if self.radioEje0.isChecked():
            eje = 0
        elif self.radioEje1.isChecked():
            eje = 1
        else:
            eje = 2
        self.__coord.calcular_estadisticas_3d(eje)

    def _solicitar_parametros_recorte(self):
        # En una implementación completa, el usuario definiría la ROI
        # interactivamente sobre el canvas. Por ahora usamos valores fijos
        # o podría abrirse un diálogo de entrada numérica.
        self.__coord.aplicar_zoom_y_recorte(
            plano=self.comboPlanoZoom.currentText().lower(),
            indice=self.sliderAxial.value(),
            x1=50, y1=50, x2=200, y2=200   # sustituir por selección interactiva
        )

    def _solicitar_nombre_recorte(self):
        nombre, ok = QInputDialog.getText(self, "Guardar recorte", "Nombre del archivo (.png):")
        if ok and nombre:
            self.__coord.guardar_recorte(nombre if nombre.endswith(".png") else nombre + ".png")

    def _solicitar_segmentacion(self):
        tipo   = self.comboTipoUmbral.currentIndex()   # mapeo en el controlador
        umbral = self.spinUmbral.value()
        kernel = self.spinKernel.value()
        morf   = self.comboMorfologia.currentIndex()   # mapeo en el controlador
        self.__coord.segmentar_imagen(tipo, umbral, kernel, morf)

    def _solicitar_plot_columnas(self):
        # Recolectamos ítems seleccionados del QListWidget de columnas
        seleccionados = [
            item.text()
            for item in self.listColumnasPlt.selectedItems()
        ]
        if len(seleccionados) < 2:
            QMessageBox.warning(self, "Selección insuficiente",
                                "Seleccione al menos 2 columnas para graficar.")
            return
        self.__coord.graficar_columnas(seleccionados)

    # ===================================================================
    # MÉTODOS PARA QUE EL COORDINADOR ACTUALICE LA UI
    # El coordinador llama a estos métodos con los datos ya procesados.
    # ===================================================================
    def mostrar_corte(self, plano, imagen_uint8):
        """Recibe un ndarray uint8 y lo dibuja en el canvas del plano indicado."""
        canvas_map = {
            "axial": (self.canvas_axial, self.fig_axial),
            "sagital": (self.canvas_sagital, self.fig_sagital),
            "coronal": (self.canvas_coronal, self.fig_coronal),
        }
        canvas, fig = canvas_map[plano]
        fig.clear()
        ax = fig.add_subplot(111)
        ax.imshow(imagen_uint8, cmap="gray", aspect="auto")
        ax.set_title(plano.capitalize(), fontsize=9)
        ax.axis("off")
        canvas.draw()

    def mostrar_zoom(self, img_marcada, img_recorte, texto_dims):
        """Muestra imagen original con ROI marcada y el recorte ampliado."""
        self.fig_zoom.clear()
        ax1 = self.fig_zoom.add_subplot(121)
        ax2 = self.fig_zoom.add_subplot(122)

        ax1.imshow(cv2.cvtColor(img_marcada, cv2.COLOR_BGR2RGB))
        ax1.set_title("Original con ROI", fontsize=8)
        ax1.axis("off")

        ax2.imshow(cv2.cvtColor(img_recorte, cv2.COLOR_BGR2RGB))
        ax2.set_title(f"Recorte\n{texto_dims}", fontsize=8)
        ax2.axis("off")
        self.canvas_zoom.draw()

    def mostrar_segmentacion(self, imagen_binaria, imagen_morfologica):
        self.fig_seg.clear()
        ax1 = self.fig_seg.add_subplot(121)
        ax2 = self.fig_seg.add_subplot(122)
        ax1.imshow(imagen_binaria, cmap="gray"); ax1.set_title("Binarización"); ax1.axis("off")
        ax2.imshow(imagen_morfologica, cmap="gray"); ax2.set_title("Morfología"); ax2.axis("off")
        self.canvas_seg.draw()

    def poblar_tabla_metadatos(self, datos_lista):
        """
        datos_lista: lista de tuplas [(campo, valor), ...]
        Puebla el QTableWidget 'tablaMetadatos'.
        """
        self.tablaMetadatos.setRowCount(len(datos_lista))
        self.tablaMetadatos.setColumnCount(2)
        self.tablaMetadatos.setHorizontalHeaderLabels(["Campo", "Valor"])
        for fila, (campo, valor) in enumerate(datos_lista):
            self.tablaMetadatos.setItem(fila, 0, QTableWidgetItem(str(campo)))
            self.tablaMetadatos.setItem(fila, 1, QTableWidgetItem(str(valor)))
        self.tablaMetadatos.resizeColumnsToContents()

    def actualizar_sliders_dicom(self, max_axial, max_coronal, max_sagital):
        """Ajusta los rangos de los sliders al tamaño real del volumen."""
        self.sliderAxial.setRange(0, max_axial)
        self.sliderAxial.setValue(max_axial // 2)
        self.sliderSagital.setRange(0, max_sagital)
        self.sliderSagital.setValue(max_sagital // 2)
        self.sliderCoronal.setRange(0, max_coronal)
        self.sliderCoronal.setValue(max_coronal // 2)

    def mostrar_canal_senal(self, tiempo, señal, titulo="Canal seleccionado"):
        self.fig_canal.clear()
        ax = self.fig_canal.add_subplot(111)
        ax.plot(tiempo, señal, linewidth=0.8, color="steelblue")
        ax.set_title(titulo, fontsize=9)
        ax.set_xlabel("Muestras"); ax.set_ylabel("Amplitud (μV)")
        ax.grid(True, alpha=0.3)
        self.canvas_canal.draw()

    def mostrar_señal_vs_ruidosa(self, señal_orig, señal_ruido):
        self.fig_ruido.clear()
        ax1 = self.fig_ruido.add_subplot(211)
        ax2 = self.fig_ruido.add_subplot(212)

        ax1.plot(señal_orig, linewidth=0.8, color="steelblue")
        ax1.set_title("Señal Original", fontsize=8); ax1.grid(True, alpha=0.3)

        ax2.plot(señal_ruido, linewidth=0.8, color="tomato")
        ax2.set_title("Señal con Ruido Gaussiano", fontsize=8); ax2.grid(True, alpha=0.3)

        self.fig_ruido.tight_layout()
        self.canvas_ruido.draw()

    def mostrar_estadisticas_stem(self, promedio, desviacion, nombre_eje, unidades):
        self.fig_stats.clear()
        ax1 = self.fig_stats.add_subplot(211)
        ax2 = self.fig_stats.add_subplot(212)

        x = range(len(promedio))
        ax1.stem(x, promedio, linefmt="steelblue", markerfmt="C0o", basefmt="k-")
        ax1.set_title(f"Promedio — {nombre_eje}", fontsize=8)
        ax1.set_ylabel(unidades)

        ax2.stem(x, desviacion, linefmt="tomato", markerfmt="C3o", basefmt="k-")
        ax2.set_title("Desviación Estándar", fontsize=8)
        ax2.set_ylabel(unidades)

        self.fig_stats.tight_layout()
        self.canvas_stats.draw()

    def mostrar_plot_columnas(self, datos_dict):
        """
        datos_dict: {nombre_columna: pd.Series, ...}
        Genera subplots individuales tipo 'plot'.
        """
        n = len(datos_dict)
        self.fig_plot.clear()
        for i, (nombre, serie) in enumerate(datos_dict.items(), 1):
            ax = self.fig_plot.add_subplot(n, 1, i)
            ax.plot(serie.values, linewidth=0.8)
            ax.set_title(nombre, fontsize=8)
            ax.grid(True, alpha=0.3)
        self.fig_plot.tight_layout()
        self.canvas_plot.draw()

    def mostrar_scatter(self, serie_x, serie_y, nombre_x, nombre_y):
        self.fig_scatter.clear()
        ax = self.fig_scatter.add_subplot(111)
        ax.scatter(serie_x, serie_y, alpha=0.6, edgecolors="steelblue", facecolors="none", s=20)
        ax.set_xlabel(nombre_x); ax.set_ylabel(nombre_y)
        ax.set_title(f"Dispersión: {nombre_x} vs {nombre_y}", fontsize=9)
        ax.grid(True, alpha=0.3)
        self.canvas_scatter.draw()

    def poblar_tabla_generica(self, tabla_widget, encabezados, filas):
        """Método reutilizable para poblar cualquier QTableWidget."""
        tabla_widget.setColumnCount(len(encabezados))
        tabla_widget.setRowCount(len(filas))
        tabla_widget.setHorizontalHeaderLabels(encabezados)
        for i, fila in enumerate(filas):
            for j, valor in enumerate(fila):
                tabla_widget.setItem(i, j, QTableWidgetItem(str(round(valor, 4) if isinstance(valor, float) else valor)))
        tabla_widget.resizeColumnsToContents()

    def poblar_combos_columnas(self, columnas):
        """Puebla los dos ComboBox de scatter y el ListWidget de plot."""
        self.comboColX.clear()
        self.comboColY.clear()
        self.listColumnasPlt.clear()
        for col in columnas:
            self.comboColX.addItem(col)
            self.comboColY.addItem(col)
            self.listColumnasPlt.addItem(col)
