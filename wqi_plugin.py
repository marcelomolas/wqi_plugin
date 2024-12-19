# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WQIPlugin
                                 A QGIS plugin
 Complemento para calcular de forma automática el WQI
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-07-04
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Carin Martinez; Marcelo Molas
        email                : marcemolas@fpuna.edu.py
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtWidgets import QTableWidget, QWizardPage
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QRegExp, QLibraryInfo, QLocale, QTimer
from qgis._core import QgsMapLayer
from qgis.core import QgsProject, QgsMessageLog, QgsMapLayerType
from qgis.PyQt.QtGui import QIcon, QRegExpValidator
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem, QAbstractItemView, QHeaderView, QStyledItemDelegate, QLineEdit, QWizard, QComboBox
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import processing
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .wqi_plugin_wizard import WQIPluginWizard
import os.path


class WQIPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        QgsMessageLog.logMessage('WQIPlugin_{}.qm'.format(locale), "tag", 0)
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'WQIPlugin_{}.qm'.format(locale))

        QgsMessageLog.logMessage(os.path.exists(locale_path).__str__(), "tag", 0)
        QgsMessageLog.logMessage(locale_path.__str__(), "tag", 0)
        if os.path.exists(locale_path):
            QgsMessageLog.logMessage("Existe!", "tag", 0)
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&WQIPlugin')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.peso_total = 0
        self.columnas_validadas = [False, False, False]

        self.flag_mas_de_dos_rasters_seleccionados = True #Ponemos en true para que durante el primer uso no tire un error.
        self.flag_solo_rasters_seleccionados = False

        self.parametros_estandar = {
            1: {"Estandar": 7.5, "Ideal": 5, "Peso": 4},  # "pH"
            2: {"Estandar": 1000, "Ideal": 0, "Peso": 5},  # "Sólidos Totales Disueltos"
            3: {"Estandar": 250, "Ideal": 0, "Peso": 5},  # "Cloro"
            4: {"Estandar": 250, "Ideal": 0, "Peso": 5},  # "Sulfato"
            5: {"Estandar": 200, "Ideal": 0, "Peso": 4},  # "Sodio"
            6: {"Estandar": 12, "Ideal": 0, "Peso": 2},  # "Potasio"
            7: {"Estandar": 100, "Ideal": 0, "Peso": 3},  # "Calcio"
            8: {"Estandar": 50, "Ideal": 0, "Peso": 3},  # "Magnesio"
            9: {"Estandar": 400, "Ideal": 0, "Peso": 2},  # "Dureza"
            10: {"Estandar": 45, "Ideal": 0, "Peso": 5},  # "Nitratos"
        }

        self.indice_a_clave = {
            2: "Estandar",
            3: "Ideal",
            4: "Peso",
        }

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('WQIPlugin', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/wqi_plugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'WQI Plugin'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&WQIPlugin'),
                action)
            self.iface.removeToolBarIcon(action)

    def capa_ya_seleccionada(self, capa_seleccionada):
        if self.dlg.SelectedCapas.count() != 0:
            for fila in range(0,self.dlg.SelectedCapas.count()):
                capa = self.dlg.SelectedCapas.item(fila).text()
                if capa == capa_seleccionada:
                    return True
        return False

    def seleccionar_capas(self):
        """Transfiere las capas de la tabla de AllCapas a la tabla de Seleccionados"""
        capas_seleccionadas = self.dlg.AllCapas.selectedItems()
        indice = self.dlg.SelectedCapas.count()

        for capa in capas_seleccionadas:
            if not self.capa_ya_seleccionada(capa.text()):
                self.dlg.SelectedCapas.addItem(capa.text())
                self.dlg.DatosAdicionales.setRowCount(indice+1)
                item_nombre_capa = QTableWidgetItem(capa.text())
                item_nombre_capa.setFlags(item_nombre_capa.flags() ^ QtCore.Qt.ItemIsEditable )
                #agregar la capa seleccionada a la tabla
                self.dlg.DatosAdicionales.setItem(indice,0,item_nombre_capa)
                #agregar un combobox a la tabla
                combo_box_parametros = QComboBox()
                combo_box_parametros.addItems([self.tr("Personalizado"),self.tr("pH"), self.tr("Sólidos Totales Disueltos"), self.tr("Cloro"), self.tr("Sulfato"), self.tr("Sodio"), self.tr("Potasio"), self.tr("Calcio"), self.tr("Magnesio"), self.tr("Dureza"), self.tr("Nitratos")])
                combo_box_parametros.currentIndexChanged.connect(lambda state, row=indice : self.agregar_datos_preestablecidos_a_tabla(state, row))
                self.dlg.DatosAdicionales.setCellWidget(indice, 1, combo_box_parametros)

                """Hacer que la columna de peso relativo no sea modificable"""
                item_peso_relativo = QTableWidgetItem()
                item_peso_relativo.setFlags(item_peso_relativo.flags() ^ (QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled) )

                self.dlg.DatosAdicionales.setItem(indice, 5, item_peso_relativo)

                indice+=1

        self.flag_mas_de_dos_rasters_seleccionados = self.dlg.SelectedCapas.count() > 1
        self.verificar_mensaje_de_error()

        self.dlg.SeleccionarCapasPage.completeChanged.emit()

    def remover_capas(self):
        """Remueve las capas de la tabla de SelectedTablas """
        capas_seleccionadas = self.dlg.SelectedCapas.selectedItems()

        for capa in capas_seleccionadas:
            #para la lista de seleccionados
            num_fila = self.dlg.SelectedCapas.row(capa)
            self.dlg.SelectedCapas.takeItem(num_fila)
            self.dlg.DatosAdicionales.removeRow(num_fila)

        self.flag_mas_de_dos_rasters_seleccionados = self.dlg.SelectedCapas.count() > 1
        self.verificar_mensaje_de_error()

        self.dlg.SeleccionarCapasPage.completeChanged.emit()

    def actualizar_peso_relativo(self, item:QTableWidgetItem):
        tabla:QTableWidget = self.dlg.DatosAdicionales
        tabla.blockSignals(True)

        self.columnas_validadas = [True, True, True]

        if item.column() == 4:
            self.peso_total = 0
            for fila in range(0, tabla.rowCount()):
                peso=tabla.item(fila, 4)
                if peso is not None:
                    self.peso_total += float(tabla.item(fila, 4).text())

            self.dlg.peso_total_label.setText("{0:.0f}".format(self.peso_total))

            for fila in range(0, tabla.rowCount()):
                peso=tabla.item(fila, 4)
                if peso is not None:
                    peso_relativo = float(peso.text()) / self.peso_total
                    item_peso_relativo = QTableWidgetItem("{:.2f}".format(peso_relativo))
                    item_peso_relativo.setFlags(item_peso_relativo.flags() ^ (QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled))
                    tabla.setItem(fila, 5, item_peso_relativo)

        for columna in range(2, 5):
            for fila in range(0, tabla.rowCount()):
                item_tabla = tabla.item(fila, columna)
                if item_tabla is None:
                    self.columnas_validadas[columna-2] = False
                else:
                    text = item_tabla.text()
                    if text == "":
                        self.columnas_validadas[columna-2] = False

        self.dlg.DatosAdicionalesPage.completeChanged.emit()
        tabla.blockSignals(False)

    def calcular_wqi(self):

        layers_seleccionados = []
        peso_total = 0
        for fila in range(0,self.dlg.DatosAdicionales.rowCount()):
            peso_total += int(self.dlg.DatosAdicionales.item(fila,4).text())
            for layer in self.layers:
                if layer.name() == self.dlg.DatosAdicionales.item(fila,0).text():
                    layers_seleccionados.append(layer.layer())

        entries = []
        formula = ""

        for fila in range(0,len(layers_seleccionados)):
            entry = QgsRasterCalculatorEntry()
            entry.bandNumber = 1
            entry.raster = layers_seleccionados[fila]
            entry.ref = layers_seleccionados[fila].name() + "@1"
            entries.append(entry)


            concentracion = entry.ref
            estandar = self.dlg.DatosAdicionales.item(fila, 2).text()
            valor_ideal = self.dlg.DatosAdicionales.item(fila,3).text()
            peso_relativo = float(self.dlg.DatosAdicionales.item(fila, 4).text())/peso_total


            quality_rating = f"((({concentracion} - {valor_ideal}) / ({estandar} - {valor_ideal})) * {peso_relativo} * 100)"


            if fila == 0:
                formula += quality_rating
            else:
                formula += "+ " + quality_rating

        directorio = self.dlg.DirectorioWQI.filePath()
        raster_file = directorio + ".tif"

        calculadora = QgsRasterCalculator(formulaString=formula,outputFile=raster_file,outputFormat="GTiff",rasterEntries=entries, outputExtent=layers_seleccionados[0].extent(), nOutputColumns=layers_seleccionados[0].width(), nOutputRows=layers_seleccionados[0].height())
        calculadora.processCalculation()


        self.iface.addRasterLayer(raster_file, "WQI")
        QgsMessageLog.logMessage(formula, "tag", 0)

    def evaluar_seleccionar_capas_page(self):
        return self.dlg.SelectedCapas.count() > 1

    def evaluar_datos_adicionales_page(self):
        return self.columnas_validadas[0] & self.columnas_validadas[1] & self.columnas_validadas[2] & (self.dlg.DirectorioWQI.filePath() != "")

    def evaluar_resumen_page(self):
        return self.dlg.DirectorioWQI.filePath() != ""

    def se_selecciono_un_archivo(self):
        self.dlg.DatosAdicionalesPage.completeChanged.emit()

    def generar_resumen(self):
        if self.dlg.currentId() == 2:
            self.dlg.resumenTextEdit.clear()
            layers_seleccionados = []
            peso_total = 0
            for fila in range(0, self.dlg.DatosAdicionales.rowCount()):
                peso_total += int(self.dlg.DatosAdicionales.item(fila, 4).text())
                for layer in self.layers:
                    if layer.name() == self.dlg.DatosAdicionales.item(fila, 0).text():
                        layers_seleccionados.append(layer.layer())
            formula = ""

            for fila in range(0, len(layers_seleccionados)):
                concentracion = layers_seleccionados[fila].name() + "@1"
                estandar = self.dlg.DatosAdicionales.item(fila, 2).text()
                valor_ideal = self.dlg.DatosAdicionales.item(fila, 3).text()
                peso_relativo = float(self.dlg.DatosAdicionales.item(fila, 4).text()) / peso_total

                quality_rating = f"<span style='font-family: Latin Modern;font-weight: bold; font-size: 16px;'>(<span style='color: #cb4335;'>({concentracion}</span> - <span style='color: #1e8449 ;'>{valor_ideal}</span>) / (<span style='color: #2e86c1;'>{estandar}</span> - <span style='color: #1e8449 ;'>{valor_ideal}</span>)) * <span style='color: #d68910;'>{peso_relativo:.2f}</span> * 100</span>"

                if fila == 0:
                    formula += quality_rating
                else:
                    formula += " + " + quality_rating
            self.dlg.resumenTextEdit.insertHtml(formula)


    def obtener_lista_de_capas(self):
        self.layers = QgsProject.instance().layerTreeRoot().findLayers()
        self.dlg.AllCapas.clear()
        self.dlg.AllCapas.addItems(
            [layer.name() for layer in self.layers])

    def delay_actualizar_rasters(self, *args):
        # Usa un pequeño retraso para permitir que la capa se agregue completamente
        QTimer.singleShot(100, self.obtener_lista_de_capas)  # 100 ms debería ser suficiente

    def abrir_plugin_interpolacion(self):
        processing.execAlgorithmDialog('gdal:gridinversedistance',)

    def se_selecciono_un_elemento_de_la_lista(self):


        solo_capas_raster_seleccionadas = True
        for capa in (self.dlg.AllCapas.selectedItems()):
            for layer in self.layers:
                if layer.name() == capa.text() and layer.layer().type() == QgsMapLayer.VectorLayer:
                        solo_capas_raster_seleccionadas = False

        if solo_capas_raster_seleccionadas:
            self.dlg.AddCapas.setEnabled(True)
            self.dlg.RemoveCapas.setEnabled(True)
            self.dlg.InterpolarButton.setEnabled(False)
        else:
            self.dlg.AddCapas.setEnabled(False)
            self.dlg.RemoveCapas.setEnabled(False)
            self.dlg.InterpolarButton.setEnabled(True)

        self.flag_solo_rasters_seleccionados = solo_capas_raster_seleccionadas
        self.verificar_mensaje_de_error()

    def agregar_datos_preestablecidos_a_tabla(self, index, row):

        columnas_de_tabla_datos_adicionales = [2,3,4]
        if index != 0:
            for columna in columnas_de_tabla_datos_adicionales:
                item = self.dlg.DatosAdicionales.item(row, columna)
                if item is None:
                        item = QTableWidgetItem(str(self.parametros_estandar[index][self.indice_a_clave[columna]]))
                        self.dlg.DatosAdicionales.setItem(row, columna, item)
                else:
                        self.dlg.DatosAdicionales.item(row, columna).setText(str(self.parametros_estandar[index][self.indice_a_clave[columna]]))

    def verificar_mensaje_de_error(self):
        if self.flag_mas_de_dos_rasters_seleccionados & self.flag_solo_rasters_seleccionados:
            self.dlg.errorTextLabel1.setText("")
        elif not self.flag_solo_rasters_seleccionados:
            self.dlg.errorTextLabel1.setText(self.tr(f"Solo capas ráster pueden ser seleccionadas."))
        elif not self.flag_mas_de_dos_rasters_seleccionados:
            self.dlg.errorTextLabel1.setText(self.tr(f"Seleccionar como mínimo 2 capas ráster."))



    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started

        if self.first_start == True:
            self.first_start = False
            self.dlg = WQIPluginWizard()
            self.dlg.AllCapas.clear()

            self.dlg.AddCapas.setMinimumWidth(120)
            self.dlg.RemoveCapas.setMinimumWidth(120)
            self.dlg.AddCapas.setMinimumHeight(30)
            self.dlg.RemoveCapas.setMinimumHeight(30)
            self.dlg.InterpolarButton.setMinimumWidth(120)
            self.dlg.InterpolarButton.setMinimumHeight(30)
            self.dlg.InterpolarButton.setEnabled(False)

            self.dlg.errorTextLabel1.setStyleSheet("color: red;font-weight: bold")
            self.dlg.errorTextLabel2.setStyleSheet("color: red;font-weight: bold")

            self.dlg.AddCapas.clicked.connect(self.seleccionar_capas)
            self.dlg.RemoveCapas.clicked.connect(self.remover_capas)
            self.dlg.InterpolarButton.clicked.connect(self.abrir_plugin_interpolacion)

            self.dlg.AllCapas.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.dlg.SelectedCapas.setSelectionMode(QAbstractItemView.ExtendedSelection)


            self.dlg.DirectorioWQI.fileChanged.connect(self.se_selecciono_un_archivo)

            self.dlg.SeleccionarCapasPage.isComplete = self.evaluar_seleccionar_capas_page
            self.dlg.DatosAdicionalesPage.isComplete = self.evaluar_datos_adicionales_page
            #self.dlg.ResumenPage.isComplete = self.evaluar_resumen_page

            self.dlg.setButtonText(QWizard.FinishButton, self.tr("Calcular WQI"))
            self.dlg.button(QWizard.FinishButton).clicked.connect(self.calcular_wqi)
            #self.dlg.button(QWizard.NextButton).clicked.connect(self.generar_resumen)

            self.dlg.AllCapas.itemSelectionChanged.connect(self.se_selecciono_un_elemento_de_la_lista)

            self.dlg.DatosAdicionales.itemChanged.connect(self.actualizar_peso_relativo)
            header = self.dlg.DatosAdicionales.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            delegate = NumericDelegate(self.dlg.DatosAdicionales)
            self.dlg.DatosAdicionales.setItemDelegate(delegate)

            self.peso_total = 0
            self.obtener_lista_de_capas()
            QgsProject.instance().layerWasAdded.connect(self.delay_actualizar_rasters)
            QgsProject.instance().layerRemoved.connect(self.delay_actualizar_rasters)

        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()

        #QgsMessageLog.logMessage("hola", "tag", 0)
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.

            pass


class NumericDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super(NumericDelegate, self).createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            reg_ex = QRegExp("[0-9]+\.?[0-9]{,2}")

            validator = QRegExpValidator(reg_ex, editor)
            editor.setValidator(validator)
        return editor