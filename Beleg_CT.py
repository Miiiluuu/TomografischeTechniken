"""
    Bildrekonstruktion: "Wir basteln uns einen CT".
    Aufgabe 1: Erzeugung eines Satzes von Projektionen aus echten und
    simulierten CT-Bildern, stellt Sinogramm grafisch dar. Dabei koennen
    bestimmte Parameter eingestellt werden und werden bei grafischen
    Darstellung beruecksichtigt.
    Aufgabe 2: Rekonstruktion von CT-Bildern aus den Sinogrammen von Aufgabe 1
"""

import sys

import numpy as np
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from scipy.ndimage import map_coordinates
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QPushButton, QGridLayout,
                             QVBoxLayout, QHBoxLayout, QRadioButton,
                             QGroupBox, QProgressBar, QLabel,
                             QSpinBox, QComboBox, QAction, QCheckBox)

import pyqtgraph


def drehmatrix(grad):
    """ Erzeugt eine Drehmatrix.

        Parameter:
        ----------
        grad: Angabe der Drehung(im positivem Drehsinne) in Grad.
    """
    # Umrechnung Winkel in Bogenmaß
    grad_rad = np.radians(grad)
    # Drehmatrix in homogenen Koordinaten
    dreh = np.array([[np.cos(grad_rad), np.sin(grad_rad), 0],
                     [-np.sin(grad_rad), np.cos(grad_rad), 0], [0, 0, 1]])
    # Matrizen invertieren, da Transformation im positiven Sinn
    dreh = np.linalg.inv(dreh)
    return dreh


def drehung_vorverarbeitung(image):
    """ Fuer eine anschließende Drehung muessen am Rande des Originalbild
        Nullen hinzugefuegt werden, um eine anschließende verlustlose Drehung
        des Bildes zu ermoeglichen (es sollen keine gefuellten Werte des
        Originalbildes abgeschnitten werden, nur Nullen).

        Parameter:
        ----------
        image: Array, Eingabewerte.

        Skizze zur Verdeutlichung:

                            c
          +--------------------------------------+
          |                                      |
          |                 a                    |
          |    +----------------------------+    |
          |    |                            |    +---------->  mit Nullen
          |    |                            |    |             gefuellter
          |    |                            |    |             Rand
          |    |                            |    |
          |    |                            |    |
        c |  a |                            | a  | c
          |    |                            |    |
          |    |                            |    |
          |    |                            |    |
          |    |                            |    |
          |    |                            +------------>   Originalbild
          |    |                            |    |
          |    |                            |    |
          |    +----------------------------+    |
          |                 a                    |
          |                                      |
          +--------------------------------------+
                            c
    """
    # Annahme: quadratische Eingangs-Matrix
    # Seitenlaenge der ursprünglichen Matrix abspeichern (a)
    laenge_original = len(image)
    # Wie groß muss vergrößertes Bild sein für anschließende verlustfreie
    # Drehung? (mit Satz des Pythagoras berechnet)
    # (auf)runden und Integer damit keine halben Pixel als Ergebnis erhalten
    # werden (c)
    c = np.int(np.ceil(np.sqrt(2) * laenge_original))
    # Prüfen, ob Originalbild überhaupt mittig reingelegt werden kann:
    b = c - laenge_original
    # ist b eine ungerade Zahl, dann vergroeßere c um Eins, damit b im
    # anschließenden gerade Zahl ist
    if b % 2 == 1:
        c += 1
        b = c - laenge_original
    # ansonsten ist b gerade und Originalbild kann mittig reingelegt werden
    # Anlegen eines (groeßeren) Arrays, indem Originalbild anschließend
    # (mittig!!) gespeichert wird
    image_groß = np.zeros((c, c))
    # nun wird Originalbild mittig ins vergroeßertes Bild gelegt
    image_groß[np.int(b / 2):laenge_original + np.int(b / 2), np.int(b / 2):laenge_original + np.int(b / 2)] = image
    return image_groß


def drehung(image, grad):
    """ Drehung eines Bildes im positiven Drehsinne.

        Parameter:
        ----------
        image: Array, Eingabewerte.

        grad: Angabe der Drehung(im positivem Drehsinne) in Grad.
    """
    # Erzeugen einer Drehmatrix mit gewaehltem Winkel
    transform = drehmatrix(grad)
    image_transform = np.zeros_like(image)
    # Rotation mit Drehmatrix bezieht sich auf Nullpunkt des Koordinatensystems
    # das heißt fuer eine Drehung um die Mitte des Bildes muss der Nullpunkt
    # des Koordinatensystems in die Mitte des Bildes gelegt werden
    # (ansonsten Drehung um obere linke Ecke des Bildes)
    # Pixel, bei dem Mitte des Koordinaensystems liegt:
    pixel_mitte = len(image) // 2
    if len(image_transform) % 2 == 0:
        x = np.arange(-pixel_mitte, pixel_mitte)
        y = np.arange(-pixel_mitte, pixel_mitte)
    else:
        x = np.arange(-pixel_mitte, pixel_mitte + 1)
        y = np.arange(-pixel_mitte, pixel_mitte + 1)
    x, y = np.meshgrid(x, y)
    koord_xy_transform = (np.array([x, y, np.ones_like(x)]).T @ transform).T
    x_transform = (koord_xy_transform[0])
    y_transform = (koord_xy_transform[1])
    bed1 = (-pixel_mitte <= x_transform) * (x_transform < pixel_mitte)
    bed2 = (-pixel_mitte <= y_transform) * (y_transform < pixel_mitte)
    bed = bed1 * bed2
    image_transform[bed] = \
        map_coordinates(image, np.array([(y_transform[bed] + pixel_mitte),
                                         (x_transform[bed] + pixel_mitte)]))
    return image_transform


def rescale(original, img_rueck):
    """
    Skaliert ein rückprojiziertes Bild auf den Wertebereich des Originalbildes.

    Parameters
    ----------
    original: Originalbild.

    img_rueck: rückprojiziertes Bild.

    Return
    ----------
    img_rueck: skaliertes rückprojiziertes Bild
    """
    # Wertebereich fuer Originalbild
    min_original = np.min(original)
    max_original = np.max(original)
    # Wertebereich des rueckprojiziertes Bildes
    min_rueck = np.min(img_rueck)
    max_rueck = np.max(img_rueck)
    diff = min_rueck - min_original
    img_rueck -= diff
    scal = max_original / max_rueck
    img_rueck *= scal
    return img_rueck


# Layouteinstellungen, grafische Oberflaeche gestalten
class MainGui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.tb = self.addToolBar("")
        self.grid = QGridLayout()
        self.central = Gui(self.grid, self.tb)
        self.central.setLayout(self.grid)
        self.setCentralWidget(self.central)


# Layouteinstellungen, grafische Oberflaeche gestalten
class Gui(QtWidgets.QWidget):
    def __init__(self, grid, toolbar):
        super().__init__()
        self.calculate_vor = None
        self.calculate_rueck = None
        self.data = None
        self.grid = grid
        # Tollbar erzeugen
        self.tb = toolbar
        self.grid.setSpacing(10)
        self.setWindowTitle("Wir basteln uns ein CT!")
        # TODO: nicht mehr zu sehen
        self.vbox_button_vor = QVBoxLayout()
        self.grid.addLayout(self.vbox_button_vor, 0, 0)
        self.vbox_button_rueck = QVBoxLayout()
        self.grid.addLayout(self.vbox_button_rueck, 1, 0)

        # Buttons in Toolbar
        # OpenButton hinzufügen
        self.load = QAction(QIcon('openIcon.bmp'), "Open", self)
        self.load.setToolTip('Öffnen (Ctrl+Q). \n'
                             'Öffnet ein vorhandenes Bild.')
        self.load.setShortcut('Ctrl+Q')
        self.tb.addAction(self.load)
        self.load.triggered.connect(self.loadButtonPress)
        # SaveButton Sinogramm hinzufuegen
        self.saveSino = QAction(QIcon('SaveSinoIcon.bmp'), "Save Sinogramm",
                                self)
        self.saveSino.setEnabled(False)
        self.saveSino.setToolTip('Speichere Sinogramm (Ctrl+S). \n'
                                 'Speichert aktuelles Sinogramm unter selbst'
                                 'gewählten Dateinamen ab.')
        self.saveSino.setShortcut('Ctrl+S')
        self.tb.addAction(self.saveSino)
        self.saveSino.triggered.connect(self.saveButtonPress)
        # Knopf zum Laden des Sinogramms
        self.loadSino = QAction(QIcon('openSinoIcon.bmp'), "Load Sinogramm",
                                self)
        self.loadSino.setToolTip('Lade Sinogramm (Ctrl+R). \n'
                                 'Lädt ein selbst gewähltes '
                                 'abgespeichertes Sinogramm.')
        self.saveSino.setShortcut('Ctrl+R')
        self.tb.addAction(self.loadSino)
        self.loadSino.triggered.connect(self.loadsinoButtonPress)
        # ClearButton hinzufuegen
        self.clear = QAction(QIcon('clearIcon.bmp'), "Clear", self)
        self.clear.setToolTip('Clear (Ctrl+C). \n'
                              'Entfernt alle vorherig geladenen Bilder.')
        self.clear.setShortcut('Ctrl+C')
        self.tb.addAction(self.clear)
        self.clear.triggered.connect(self.clearButtonPress)
        # AbbruchButton hinzufuegen
        self.breaking = QAction(QIcon('abbruchIcon.bmp'), "Close", self)
        self.breaking.setToolTip('Abbruch (Ctrl+B). \n'
                                 'Abbruch der aktuellen Berechnung.')
        self.breaking.setShortcut('Ctrl+B')
        self.breaking.setEnabled(False)
        self.tb.addAction(self.breaking)
        self.breaking.triggered.connect(self.breakingButtonPress)
        # SaveButton rückprojiziertes Bild hinzufuegen
        self.save_img = QAction(QIcon('SaveImgIcon.bmp'), "Save Reko-bild",
                                self)
        self.save_img.setEnabled(False)
        self.save_img.setToolTip('Speichere Bild (Ctrl+T). \n'
                                 'Speichert aktuelles rückprojiziertes Bild'
                                 ' unter selbst gewählten Dateinamen ab.')
        self.save_img.setShortcut('Ctrl+T')
        self.tb.addAction(self.save_img)
        self.save_img.triggered.connect(self.save_imgButtonPress)
        # Liste Buttons
        self.alle_buttons = [self.load, self.save_img, self.saveSino,
                             self.clear, self.loadSino]

        # Auswahlmoeglichkeiten fuer Vorwärtsprojektion
        # ist Uebersicht zur Auswahl Parameter fuer Vorwaertsprojektion
        self.hbox_v = QHBoxLayout()
        self.groupBox_vor = QGroupBox("Vorwärtsprojektion")
        self.vbox_v = QVBoxLayout()
        self.vbox_v.addLayout(self.hbox_v)
        self.vbox_v.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox_vor.setLayout(self.vbox_v)
        self.vbox_button_vor.addWidget(self.groupBox_vor)
        # erstellt RadioButton, zur Auswahl, ob Sinogramm im Vollkreis (360°)
        # oder Halbkreis (180°) berechnet werden soll
        self.groupBox_angle = QGroupBox("Projektion im Winkelraum:")
        self.radio180 = QRadioButton("180°")
        self.radio360 = QRadioButton("360°")
        self.radio180.setChecked(True)
        self.vbox_angle = QVBoxLayout()
        self.vbox_angle.addWidget(self.radio180)
        self.vbox_angle.addWidget(self.radio360)
        self.groupBox_angle.setLayout(self.vbox_angle)
        self.hbox_v.addWidget(self.groupBox_angle)
        # erstellt SpinBox zur Auswahl der Anzahl an Winkelschritten,
        # die fuer eine anschließende Vorwaertsprojektion verwendet werden
        self.groupBox_anglesteps = QGroupBox("Anzahl der Winkelschritte:")
        self.sb_anglesteps = QSpinBox()
        self.sb_anglesteps.setValue(60)
        self.sb_anglesteps.setMinimum(10)
        self.sb_anglesteps.setMaximum(500)
        self.sb_anglesteps.setSingleStep(10)
        self.vbox_anglesteps = QVBoxLayout()
        self.vbox_anglesteps.addWidget(self.sb_anglesteps)
        self.groupBox_anglesteps.setLayout(self.vbox_anglesteps)
        self.hbox_v.addWidget(self.groupBox_anglesteps)
        # erstellt Checkbox, zur Auswahl, ob während Berechnung Animation
        # dargestellt werden soll
        self.ani_v = QCheckBox("mit Animation?")
        self.ani_v.setChecked(True)
        self.vbox_v.addWidget(self.ani_v)
        # erstellt eine Progressbar, welche den Fortschritt in der
        # Vorwaertsprojektion (des Sinogramms) darstellt.
        self.progress_sino = QProgressBar()
        self.progress_sino.setStyleSheet("text-align: center;")
        # Hinzufuegen zum Layout (VBox)
        self.vbox_v.addWidget(self.progress_sino)
        # Knopf zum Erzeugen des Sinogramms
        self.sinoButton = QPushButton("Go")
        self.sinoButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                      QtWidgets.QSizePolicy.Fixed)
        self.sinoButton.resize(50, 50)
        self.sinoButton.clicked.connect(self.sinoButtonPress)
        self.vbox_v.addWidget(self.sinoButton, 0, QtCore.Qt.AlignCenter)
        self.groupBox_vor.setEnabled(False)

        # Auswahlmoeglichkeiten fuer Rückwärtsprojektion
        # ist Uebersicht zur Auswahl Parameter fuer Rückwaertsprojektion
        self.hbox_r = QHBoxLayout()
        self.groupBox_rueck = QGroupBox("Rückwärtsprojektion")
        self.vbox_r = QVBoxLayout()
        self.vbox_r.addLayout(self.hbox_r)
        self.vbox_r.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox_rueck.setLayout(self.vbox_r)
        self.vbox_button_rueck.addWidget(self.groupBox_rueck)
        # erstellt RadioButton, zur Auswahl, ob gefilterte oder ungefilterte
        # Rueckprojektion stattfinden soll
        self.groupBox_projection = QGroupBox("Projektion im Winkelraum:")
        self.radio_mit = QRadioButton("gefiltert")
        self.radio_ohne = QRadioButton("ungefiltert")
        self.radio_mit.setChecked(True)
        self.vbox_projection = QVBoxLayout()
        self.vbox_projection.addWidget(self.radio_mit)
        self.vbox_projection.addWidget(self.radio_ohne)
        self.groupBox_projection.setLayout(self.vbox_projection)
        self.hbox_r.addWidget(self.groupBox_projection)
        # erstellt ComboBox zur Auswahl der Filter für gefilterte 
        # Rueckprojektion
        self.groupBox_cb = QGroupBox("Filter fuer Rückprojektion:")
        self.cb_filter = QComboBox()
        self.cb_filter.addItem("Ramp")
        self.cb_filter.addItem("Hamming")
        self.vbox_cb = QVBoxLayout()
        self.vbox_cb.addWidget(self.cb_filter)
        self.groupBox_cb.setLayout(self.vbox_cb)
        self.hbox_r.addWidget(self.groupBox_cb)
        self.radio_mit.clicked.connect(self.activate_cb_filter)
        self.radio_ohne.clicked.connect(self.deactivate_cb_filter)
        # erstellt Checkbox, zur Auswahl, ob während Berechnung Animation
        # dargestellt werden soll
        self.ani_r = QCheckBox("mit Animation?")
        self.ani_r.setChecked(True)
        self.vbox_r.addWidget(self.ani_r)
        # erstellt eine Progressbar, welche den Fortschritt in der
        # Vorwaertsprojektion (des Sinogramms) darstellt.
        self.progress_img_r = QProgressBar()
        self.progress_img_r.setStyleSheet("text-align: center;")
        self.vbox_r.addWidget(self.progress_img_r)
        # Knopf fuer Start Rückprojektion
        self.rueckButton = QPushButton("Go")
        self.rueckButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                       QtWidgets.QSizePolicy.Fixed)
        self.rueckButton.resize(50, 50)
        self.rueckButton.clicked.connect(self.rueckButtonPress)
        self.vbox_r.addWidget(self.rueckButton, 0, QtCore.Qt.AlignCenter)
        self.groupBox_rueck.setEnabled(False)

        # Hinzufuegen grafischer Bilder zum Layout
        # Bild 1: Originalbild
        self.vbox_img1 = QVBoxLayout()
        label_img1 = QLabel("Originalbild")
        font = label_img1.font()
        font.setPointSize(10)
        label_img1.setFont(font)
        self.vbox_img1.addWidget(label_img1)
        self.graphic1 = pyqtgraph.GraphicsLayoutWidget()
        self.vbox_img1.addWidget(self.graphic1)
        self.view1 = self.graphic1.addViewBox()
        self.view1.setAspectLocked(True)
        # damit verhalten wie Mathplotlib
        self.view1.invertY(True)
        self.img1 = pyqtgraph.ImageItem()
        # damit verhalten wie Mathplotlib
        self.img1.setOpts(axisOrder='row-major')
        self.view1.addItem(self.img1)
        self.grid.addLayout(self.vbox_img1, 0, 1)

        # Bild 2: Sinogramm
        self.vbox_img2 = QVBoxLayout()
        label_img2 = QLabel("Sinogramm")
        label_img2.setFont(font)
        self.vbox_img2.addWidget(label_img2)
        self.graphic2 = pyqtgraph.GraphicsLayoutWidget()
        self.vbox_img2.addWidget(self.graphic2)
        self.view2 = self.graphic2.addViewBox()
        self.view2.setAspectLocked(True)
        # damit verhalten wie Mathplotlib
        self.view2.invertY(True)
        self.img2 = pyqtgraph.ImageItem()
        # damit verhalten wie Mathplotlib
        self.img2.setOpts(axisOrder='row-major')
        self.view2.addItem(self.img2)
        self.grid.addLayout(self.vbox_img2, 0, 2)
        
        # Bild 3: rückprojiziertes Bild
        self.vbox_img3 = QVBoxLayout()
        label_img3 = QLabel("rückprojiziertes Bild")
        label_img3.setFont(font)
        self.vbox_img3.addWidget(label_img3)
        self.graphic3 = pyqtgraph.GraphicsLayoutWidget()
        self.vbox_img3.addWidget(self.graphic3)
        self.view3 = self.graphic3.addViewBox()
        self.view3.setAspectLocked(True)
        # damit verhalten wie Mathplotlib
        self.view3.invertY(True)
        self.img3 = pyqtgraph.ImageItem()
        # damit verhalten wie Mathplotlib
        self.img3.setOpts(axisOrder='row-major')
        self.view3.addItem(self.img3)
        self.grid.addLayout(self.vbox_img3, 1, 1)

        # Bild 4: Differenzbild
        self.vbox_img4 = QVBoxLayout()
        label_img4 = QLabel("Differenzbild")
        label_img4.setFont(font)
        self.vbox_img4.addWidget(label_img4)
        self.graphic4 = pyqtgraph.GraphicsLayoutWidget()
        self.vbox_img4.addWidget(self.graphic4)
        self.view4 = self.graphic4.addViewBox()
        self.view4.setAspectLocked(True)
        # damit verhalten wie Mathplotlib
        self.view4.invertY(True)
        self.img4 = pyqtgraph.ImageItem()
        # damit verhalten wie Mathplotlib
        self.img4.setOpts(axisOrder='row-major')
        self.view4.addItem(self.img4)
        self.grid.addLayout(self.vbox_img4, 1, 2)

    def loadButtonPress(self):
        """
        Öffnet file dialog um eine Datei zu laden/grafisch darzustellen.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,
                                                  "Open file", "",
                                                  "CT Bilder (*.npy)",
                                                  options=options)
        if fileName:
            # nachdem neue Datei geladen wird sollen vorherige Grafiken
            # aus allen Bildern entfernt werden, Löschen vorherig
            # gespeicherter Daten
            self.clearButtonPress()
            # Einlesen der Daten
            self.data = np.load(fileName)
            self.img1.setImage(self.data)
            self.groupBox_vor.setEnabled(True)

    def sinoButtonPress(self):
        """ Erstellt Sinogramm und stellt es grafisch dar. """
        # Ausgangszustand herstellen
        self.img2.clear()
        self.img3.clear()
        self.img4.clear()
        self.progress_img_r.reset()
        self.progress_sino.reset()
        self.groupBox_rueck.setEnabled(False)
        self.img1.setImage(self.data)
        self.groupBox_vor.setEnabled(False)
        for i in self.alle_buttons:
            i.setEnabled(False)
        self.breaking.setEnabled(True)
        self.laenge_original = len(self.data)
        # Vorverarbeitung fuer Drehung
        self.data_gross = drehung_vorverarbeitung(self.data)
        # verschiedene (Rotations)winkel durchgehen
        # Auswahl Endpunkt je nachdem, was auf der graphischen Oberflaeche
        # ausgewaehlt wird
        # 180 Grad oder 360 Grad
        angle = self.radio180.isChecked()
        if angle:
            angle_value = 180
        else:
            angle_value = 360
        self.winkel_max = angle_value
        angle_steps = self.sb_anglesteps.value()
        self.sinogramm = np.zeros([angle_steps, len(self.data_gross)])
        # Animation CT Tisch
        self.data_gms = np.zeros_like(self.data_gross)
        self.cttisch = np.zeros_like(self.data)
        self.cttisch[-3:-1] = np.max(self.data)
        self.cttisch = drehung_vorverarbeitung(self.cttisch)
        self.cttisch = np.roll(self.cttisch, len(self.data)//10, axis=0)
        # auf grafischen Oberfläche Auswahl, ob Darstellung mit Animation
        # oder nicht
        animation_vor = self.ani_v.isChecked()
        # hier Thread wegen rechenaufwändigem Teil
        self.calculate_vor = Vorwaertsprojektion(self.data_gms, angle_value,
                                                 self.cttisch, self.data_gross,
                                                 angle_steps, self.sinogramm,
                                                 animation_vor)
        # mit Animation
        if animation_vor:
            self.calculate_vor.signal.connect(self.progress_vor)
            self.calculate_vor.signal.connect(self.animation)
            self.calculate_vor.signal_finish.connect(self.animation_finish)
            self.calculate_vor.signal.connect(self.animation_cttisch)
        else:
            # ohne Animation
            self.calculate_vor.signal.connect(self.progress_vor)
            self.calculate_vor.signal_finish.connect(self.animation_finish)
        # Progressbar zeigt Fortschritt während Berechnung
        self.progress_sino.setMaximum(angle_value)
        self.calculate_vor.start()

    def saveButtonPress(self):
        """
        In einem sich oeffnenden file dialog kann ein Sinogramm
        unter selbst gewaehlten Dateinamen abgespeichert werden.
        """
        self.sinogramm_plus_info = np.vstack((np.ones((1,
                                                    len(self.sinogramm[0]))),
                                                    self.sinogramm))
        self.sinogramm_plus_info[0, 0] = self.laenge_original
        # je nachdem was auf grafischen Oberfläche ausgewaehlt wurde,
        # 180 Grad oder 360 Grad abspeichern
        angle = self.radio180.isChecked()
        if angle:
            angle_value = 180
        else:
            angle_value = 360
        self.sinogramm_plus_info[0, 1] = angle_value
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save file",
                                                  "Sinogramm.milu",
                                                  "Sinogramme (*.milu)",
                                                  options=options)
        if fileName:
            # Speichern der Daten
            with open(fileName, "wb") as file:
                np.save(file, self.sinogramm_plus_info)

    def loadsinoButtonPress(self):
        """
        Ladet ein (bereits bestehendes) Sinogramm in einem sich oeffnenden
        file dialog.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open Sino", "",
                                                  "Sinogramme (*.milu)",
                                                  options=options)
        if fileName:
            self.clearButtonPress()
            # Einlesen der Daten
            self.sinogramm_plus_info = np.load(fileName)
            # nachdem neue Datei geladen wird sollen vorherige Grafiken
            # aus allen Bildern entfernt werden und vorherige Daten löschen
            self.laenge_original = np.int(self.sinogramm_plus_info[0, 0])
            self.winkel_max = np.int(self.sinogramm_plus_info[0, 1])
            self.sinogramm = self.sinogramm_plus_info[1:]
            self.img2.setImage(self.sinogramm)
            self.groupBox_rueck.setEnabled(True)

    def rueckButtonPress(self):
        """
        Rueckprojektion. Dabei Auswahl auf grafischen Oberfläache, ob
        gefiltert oder ungefiltert.
        """
        for i in self.alle_buttons:
            i.setEnabled(False)
        self.breaking.setEnabled(True)
        self.groupBox_rueck.setEnabled(False)
        self.groupBox_vor.setEnabled(False)
        self.img3.clear()
        self.img4.clear()
        # Anwendung Filter vor Rueckprojektion
        self.sinogramm_filter = np.copy(self.sinogramm)
        # Auswahl Filter auf grafischen Oberfläche
        filterart = self.radio_mit.isChecked()
        # gefiltert
        if filterart:
            # abspeichern des aktuell ausgewaehlten Filters
            self.currentchoice = self.cb_filter.currentText()
            # Erstellung Rampfilter
            ramp = np.abs(np.fft.fftshift(np.fft.fftfreq(len(self.sinogramm[0]))))
            # Auswahl Rampfilter
            if self.currentchoice == "Ramp":
                filterkern = ramp
            # Hamming-Filter
            else:
                n = np.arange(len(self.sinogramm[0]))
                fenster = 0.54 - 0.46 * \
                          np.cos(2*np.pi*(n/len(self.sinogramm[0])-1))
                filterkern = ramp * fenster
            # Fouriertransformation
            fourier_image = np.fft.fft(self.sinogramm)
            fourier_image = np.fft.fftshift(fourier_image)
            # Anwenden des Filters auf Bild:
            # (Multiplikation im Frequenzraum)
            fourier_gefiltert = fourier_image * filterkern
            fourier_gefiltert = np.fft.ifftshift(fourier_gefiltert)
            self.sinogramm_filter = np.real(np.fft.ifft(fourier_gefiltert))
        alpha_r = np.linspace(0, self.winkel_max, len(self.sinogramm_filter),
                              endpoint=False)
        self.image_r = np.zeros((len(self.sinogramm_filter[0]),
                                 len(self.sinogramm_filter[0])))
        # hier Thread da rechenaufwendig
        self.calculate_rueck = Rueckwaertsprojektion(self.sinogramm_filter,
                                                     self.image_r, alpha_r)
        # Auswahl ob mit oder ohne Animation auf grafischen Oberfläche
        animation_rueck = self.ani_r.isChecked()
        # mit Animation
        if animation_rueck:
            self.calculate_rueck.signal.connect(self.progress_rueck)
            self.calculate_rueck.signal.connect(self.animation_r)
            self.calculate_rueck.signal_finish.connect(self.animation_r_finish)
        # ohne Animation
        else:
            self.calculate_rueck.signal.connect(self.progress_rueck)
            self.calculate_rueck.signal_finish.connect(self.animation_r_finish)
        # Progressbar zeigt Fortschritt während Berechnung
        self.progress_img_r.setMaximum(self.winkel_max)
        self.calculate_rueck.start()
        self.progress_sino.reset()

    def save_imgButtonPress(self):
        """
        In einem sich oeffnenden file dialog kann das erstellte rückprojizierte
        Bild unter selbst gewaehlten Dateinamen abgespeichert werden.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "Save file",
                                                  "Reko_img.npy",
                                                  "rückprojizierte Bilder (*.npy)",
                                                  options=options)
        if fileName:
            # Speichern der Daten
            with open(fileName, "wb") as file:
                np.save(file, self.self.image_r)

    def clearButtonPress(self):
        """ Löscht alle vorher erzeugten/geladenen Bilder. """
        self.img1.clear()
        self.img2.clear()
        self.img3.clear()
        self.img4.clear()
        self.data = None
        self.save_img.setEnabled(False)
        self.saveSino.setEnabled(False)
        self.progress_sino.reset()
        self.progress_img_r.reset()
        self.groupBox_vor.setEnabled(False)
        self.groupBox_rueck.setEnabled(False)

    def breakingButtonPress(self):
        """ Abbruch der aktuellen Berechnung. """
        if self.calculate_vor is not None:
            self.calculate_vor.breaking = True
        if self.calculate_rueck is not None:
            self.calculate_rueck.breaking = True

    def activate_cb_filter(self):
        """ Zusammenspiel activate- inactivate Auswahl an Filtern. """
        self.cb_filter.setEnabled(True)

    def deactivate_cb_filter(self):
        """ Zusammenspiel activate- inactivate Auswahl an Filtern. """
        self.cb_filter.setEnabled(False)

    def animation_cttisch(self):
        """ Animiert CT-Tisch während Vorwärtsprojektion. """
        self.img1.setImage(self.data_gms)

    def animation(self):
        """ Animiert Erstellung Sinogramm während Vorwärtsprojektion. """
        self.img2.setImage(self.sinogramm)

    def animation_finish(self, abgebrochen):
        """
        nach Fertigstellen der Vorwärtsprojektionsberechnung.

        Parameters
        ----------
        abgebrochen: Datentyp bool (True or False), unterscheidet Vorgehen,
        ob aktuelle Berechung mit abgebrochen wurde oder nicht.
        """
        if abgebrochen:
            self.groupBox_vor.setEnabled(True)
            self.groupBox_rueck.setEnabled(False)
            self.saveSino.setEnabled(False)
            self.progress_sino.reset()
            self.img2.clear()
            self.img1.setImage(self.data)
        else:
            self.progress_sino.setValue(self.progress_sino.maximum())
            self.img2.setImage(self.sinogramm)
            self.saveSino.setEnabled(True)
            self.groupBox_rueck.setEnabled(True)
            self.groupBox_vor.setEnabled(True)
            self.saveSino.setEnabled(True)
        self.breaking.setEnabled(False)
        self.load.setEnabled(True)
        self.loadSino.setEnabled(True)
        self.clear.setEnabled(True)
        self.saveSino.setEnabled(True)

    def progress_vor(self, alpha):
        """
        Stellt Fortschritt in der Vorwärtsprojektion als Progressbar dar.

        Parameters
        ----------
        alpha: aktueller Berechnungsschritt (Winkel).
        """
        self.progress_sino.setValue(alpha)

    def animation_r(self):
        """ Animiert Rückprojektion. """
        self.img3.setImage(self.image_r)

    def animation_r_finish(self, abgebrochen):
        """
        nach Fertigstellen der Rückwärtssprojektionsberechnung.

        Parameters
        ----------
        abgebrochen: Datentyp bool (True or False), unterscheidet Vorgehen,
        ob aktuelle Berechung mit abgebrochen wurde oder nicht.
        """
        if abgebrochen:
            self.progress_img_r.reset()
            self.img3.clear()
            self.img4.clear()
            self.save_img.setEnabled(False)
            self.groupBox_rueck.setEnabled(True)
            if self.data is not None:
                self.groupBox_vor.setEnabled(True)
        else:
            self.progress_img_r.setValue(self.progress_img_r.maximum())
            # durch vorherige Vorwärtsprojektion (dabei wurde Ursprungsbild
            # fuer eine verlustfreie Drehung vergroeßert) ist um
            # rueckprojeziertes Bild ein Kreis
            # dieser wird nun entfernt
            diff = (len(self.image_r) - self.laenge_original) // 2
            self.image_r = self.image_r[diff:self.laenge_original+diff,
                           diff:self.laenge_original+diff]
            # Rückprojektion darstellen auf grafischer Oberflaeche
            self.img3.setImage(self.image_r)
            # Differenzbild ezeugen und grafisch darstellen
            if self.data is not None:
                # Skalieren
                self.image_r_scal = rescale(self.data, np.copy(self.image_r))
                self.groupBox_vor.setEnabled(True)
                self.diff_img = np.abs(self.data - self.image_r_scal)
                self.img4.setImage(self.diff_img, levels=(np.min(self.data),
                                                          np.max(self.data)))
            self.save_img.setEnabled(True)
            self.groupBox_rueck.setEnabled(True)
        self.breaking.setEnabled(False)
        self.load.setEnabled(True)
        self.loadSino.setEnabled(True)
        self.clear.setEnabled(True)

    def progress_rueck(self, i):
        """
        Stellt Fortschritt in der Rückwärtsprojektion als Progressbar dar.

        Parameters
        ----------
        i: aktueller Berechnungsschritt
        """
        self.progress_img_r.setValue(i)


def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = MainGui()

    ui.show()
    sys.exit(app.exec_())


class Vorwaertsprojektion(QtCore.QThread):
    # Signale, welche während Projektion erstellt werden
    signal = QtCore.pyqtSignal(float)
    signal_finish = QtCore.pyqtSignal(bool)

    def __init__(self, data_gms, angle_value, cttisch, data_gross, angle_steps,
                 sinogramm, animation):
        super().__init__()
        self.data_gms = data_gms
        self.angle_value = angle_value
        self.data_gross = data_gross
        self.angle_steps = angle_steps
        self.sinogramm = sinogramm
        self.cttisch = cttisch
        self.animation = animation
        # Abbruch
        self.breaking = False

    def run(self):
        # Anzahl an Winkelschritten
        numbers_angle = np.linspace(0, self.angle_value, self.angle_steps,
                                    endpoint=False)
        for count, alpha in enumerate(numbers_angle):
            # Drehung
            data_transform = drehung(self.data_gross, alpha)
            # Bildung von Linienintegralen fuer einzelnen Rotationswinkel
            linienintegral = np.sum(data_transform, axis=0)
            self.sinogramm[count] = linienintegral
            if self.animation:
                cttisch_dreh = drehung(self.cttisch, -alpha)
                self.data_gms[:] = self.data_gross + cttisch_dreh
            self.signal.emit(alpha)
            if self.breaking:
                self.signal_finish.emit(True)
                return
        self.signal_finish.emit(False)


class Rueckwaertsprojektion(QtCore.QThread):
    # Signale, welche wäährend Projektion erstellt werden
    signal = QtCore.pyqtSignal(float)
    signal_finish = QtCore.pyqtSignal(float)

    def __init__(self, sinogramm_filter, image_r, alpha_r):
        super().__init__()
        self.sinogramm_filter = sinogramm_filter
        self.image_r = image_r
        self.alpha_r = alpha_r
        # Abbruch
        self.breaking = False

    def run(self):
        for i in range(len(self.sinogramm_filter)):
            sino2d = self.sinogramm_filter[i] * np.ones_like(self.image_r)
            # Drehung
            sino2d_transform = drehung(sino2d, -self.alpha_r[i])
            self.image_r += sino2d_transform
            self.signal.emit(self.alpha_r[i])
            if self.breaking:
                self.signal_finish.emit(True)
                return
        self.signal_finish.emit(False)


if __name__ == "__main__":
    main()