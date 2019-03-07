"""
    Bildrekonstruktion: "Wir basteln uns einen CT".
    Aufgabe 1: Erzeugung eines Satzes von Projektionen aus echten und
    simulierten CT-Bildern, stellt Sinogramm grafisch dar. Dabei koennen
    bestimmte Parameter eingestellt werden und werden bei grafischen
    Darstellung beruecksichtigt.
"""
# TODO: Trennung Aufgabe 1 und 2 ( Vor und Rueck)
# TODO: .show()
# TODO: uebersichtlicher durch mehr Klassen?

import sys

import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtCore
from scipy.ndimage import map_coordinates
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QPushButton, QGridLayout,
                             QVBoxLayout, QHBoxLayout, QSlider, QRadioButton,
                             QGroupBox, QProgressBar, QCheckBox, QLabel,
                             QSpinBox, QComboBox, QToolTip, qApp, QMainWindow,
                             QAction)

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
    # TODO: mitte perfekt runden (auf ganze Zahlen) Jetzt ist es vllt nicht
    # immer exakt die Mitte des Koordinatensystems?
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


class MainGui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.tb = self.addToolBar("")
        self.grid = QGridLayout()
        self.central = Gui(self.grid, self.tb)
        self.central.setLayout(self.grid)
        self.setCentralWidget(self.central)


class Gui(QtWidgets.QWidget):
    def __init__(self, grid, toolbar):
        super().__init__()

        self.data = None
        # Layouteinstellungen
        # grafische Oberflaeche gestalten
        # Erzeugung uebergeordnetes Grid, in dem alle grafischen Objekte 
        # enthalten sind
        self.grid = grid
        self.tb = toolbar

        self.new = QAction("load", self)
        self.tb.addAction(self.new)
        self.new.triggered.connect(self.loadButtonPress)

        self.grid.setSpacing(10)
        self.setWindowTitle("Wir basteln uns ein CT!")


        #self.grid.addLayout(self.tb, 1, 0)



        
        # Erzeugen VBox (jeweils für Vor- und Rücktransformation, diese wird
        # dem Grid hinzufügt
        # in VBox kommen alle Buttons, Auswahlmöglichkeiten für Parameter uÄ
        self.vbox_button_vor = QVBoxLayout()
        self.grid.addLayout(self.vbox_button_vor, 0, 0)
        self.vbox_button_vor.addStretch(1)
        self.vbox_button_rueck = QVBoxLayout()
        self.grid.addLayout(self.vbox_button_rueck, 1, 0)
        self.vbox_button_rueck.addStretch(1)

        
        # Hinzufuegen von Buttons und Ähnlichem zur VBox in grafischen
        # Oberfläche
        # TODO: einige Buttons in QToolBar stecken(funktioniert nicht wirklich
        # TODO: mit Icon ...
        # OpenButton hinzufügen
        self.loadButton = QPushButton("Open")
        self.loadButton.setToolTip('Öffnet ein Bild.')
        self.loadButton.clicked.connect(self.loadButtonPress)
        self.vbox_button_vor.addWidget(self.loadButton)
        # SaveButton Sinogramm hinzufuegen
        self.save_sinoButton = QPushButton("Save Sinogramm")
        self.save_sinoButton.setEnabled(False)
        self.save_sinoButton.setToolTip('Speichert Sinogramm unter selbst'
                                   'gewählten Dateinamen ab.')
        self.save_sinoButton.clicked.connect(self.saveButtonPress)
        self.vbox_button_vor.addWidget(self.save_sinoButton)
        # Knopf zum Laden des Sinogramms
        self.loadsinoButton = QPushButton("Load Sinogramm")
        self.loadsinoButton.setToolTip('Lädt ein abgespeichertes Sinogramm.')
        self.loadsinoButton.clicked.connect(self.loadsinoButtonPress)
        self.vbox_button_vor.addWidget(self.loadsinoButton)
        # ClearButton hinzufuegen
        self.clearButton = QPushButton("Clear")
        self.clearButton.setToolTip('Entfernt alle vorherig geladenen Bilder.')
        self.clearButton.clicked.connect(self.clearButtonPress)
        self.vbox_button_vor.addWidget(self.clearButton)
        # AbbruchButton hinzufuegen
        # TODO: Reko abbrechen!
        self.breakButton = QPushButton("Close")
        self.breakButton.setEnabled(False)
        self.breakButton.setToolTip('Abbruch des Programms.')
        self.breakButton.clicked.connect(qApp.quit)
        self.vbox_button_vor.addWidget(self.breakButton)
        # SaveButton rückprojiziertes Bild hinzufuegen
        self.save_imgButton = QPushButton("Save Reko-bild")
        self.save_imgButton.setEnabled(False)
        self.save_imgButton.setToolTip('Speichert rückprojiziertes Bild'
                                       ' unter selbst gewählten Dateinamen'
                                       ' ab.')
        self.save_imgButton.clicked.connect(self.save_imgButtonPress)
        self.vbox_button_vor.addWidget(self.save_imgButton)

        # Auswahlmoeglichkeiten fuer Vorwärtsprojektion
        # ist Uebersicht zur Auswahl Parameter fuer Vorwaertsprojektion
        # es wird HBox erzeugt
        self.hbox_v = QHBoxLayout()
        # Hinzufuegen zum Layout (VBox)
        self.groupBox_vor = QGroupBox("Vorwärtsprojektion")
        self.vbox_v = QVBoxLayout()
        self.vbox_v.addLayout(self.hbox_v)
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
        self.vbox_angle.addStretch(1)
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
        # TODO: je nachdem ob 180° oder 360° ausgewählt wurde
        # TODO: auch eine für Rückproj machen ...
        # erstellt eine Progressbar, welche den Fortschritt in der
        # Vorwaertsprojektion (des Sinogramms) darstellt.
        self.progress_sino = QProgressBar()
        self.progress_sino.setStyleSheet("text-align: center;")
        # Hinzufuegen zum Layout (VBox)
        self.vbox_v.addWidget(self.progress_sino)
        # Knopf zum Erzeugen des Sinogramms
        # TODO: wenn das zuallererst aufgerufen wird Absturz, nicht ok
        self.sinoButton = QPushButton("Go")
        self.sinoButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.sinoButton.resize(50, 50)
        self.sinoButton.clicked.connect(self.sinoButtonPress)
        self.vbox_v.addWidget(self.sinoButton, 0, QtCore.Qt.AlignCenter)
        self.groupBox_vor.setEnabled(False)

        # Auswahlmoeglichkeiten fuer Rückwärtsprojektion
        # ist Uebersicht zur Auswahl Parameter fuer Rückwaertsprojektion
        # es wird HBox erzeugt
        self.hbox_r = QHBoxLayout()
        # Hinzufuegen zum Layout (VBox)
        self.groupBox_rueck = QGroupBox("Rückwärtsprojektion")
        self.vbox_r = QVBoxLayout()
        self.vbox_r.addLayout(self.hbox_r)
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
        self.vbox_projection.addStretch(1)
        self.groupBox_projection.setLayout(self.vbox_projection)
        self.hbox_r.addWidget(self.groupBox_projection)
        # erstellt ComboBox zur Auswahl der Filter für gefilterte 
        # Rueckprojektion
        self.groupBox_cb = QGroupBox("Filter fuer Rückprojektion:")
        self.cb_filter = QComboBox()
        self.cb_filter.addItem("Ramp")
        self.cb_filter.addItem("Shepp-Logan")
        self.cb_filter.addItems(["Middle"])
        self.vbox_cb = QVBoxLayout()
        self.vbox_cb.addWidget(self.cb_filter)
        self.groupBox_cb.setLayout(self.vbox_cb)
        self.hbox_r.addWidget(self.groupBox_cb)
        self.radio_mit.clicked.connect(self.activate_cb_filter)
        self.radio_ohne.clicked.connect(self.deactivate_cb_filter)
        # erstellt eine Progressbar, welche den Fortschritt in der
        # Vorwaertsprojektion (des Sinogramms) darstellt.
        self.progress_rueck = QProgressBar()
        self.progress_rueck.setStyleSheet("text-align: center;")
        # Hinzufuegen zum Layout (VBox)
        self.vbox_r.addWidget(self.progress_rueck)
        # Knopf fuer Start Rückprojektion
        self.rueckButton = QPushButton("Go")
        self.rueckButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.rueckButton.resize(50, 50)
        self.rueckButton.clicked.connect(self.rueckButtonPress)
        self.vbox_r.addWidget(self.rueckButton, 0, QtCore.Qt.AlignCenter)
        self.groupBox_rueck.setEnabled(False)


        # TODO: Verhaeltnisse Bilder zueinander
        # Hinzufuegen grafischer Bilder zum Layout
        # Bild 1
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


        # Bild 2
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
        
        # Bild 3
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
        #self.img3.setImage(np.eye(5))

        # Bild 4
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
        #self.img4.setImage(np.eye(5))


    def activate_cb_filter(self):
        self.cb_filter.setEnabled(True)


    def deactivate_cb_filter(self):
        self.cb_filter.setEnabled(False)


    def clearButtonPress(self):
        """
        Löscht alle vorher erzeugten/geladenen Bilder.

        Parameters
        ----------
        None

        Return
        ----------
        None
        """
        self.img1.clear()
        self.img2.clear()
        self.img3.clear()
        self.img4.clear()
        self.data = None
        self.save_imgButton.setEnabled(False)
        self.save_sinoButton.setEnabled(False)
        self.progress_sino.reset()
        self.progress_rueck.reset()
        self.breakButton.setEnabled(False)
        self.groupBox_vor.setEnabled(False)
        self.groupBox_rueck.setEnabled(False)



    # TODO: erklären lassen... animieren (in Thread packen)
    # TODO: anderen Filter benutzen
    def rueckButtonPress(self):
        """
        Rueckprojektion. Dabei Auswahl auf grafischen Oberfläache, ob
        gefiltert oder ungefiltert.

        Parameters
        ----------
        None

        Return
        ----------
        None
        """
        self.groupBox_rueck.setEnabled(False)
        self.img3.clear()
        # Anwendung Filter vor Rueckprojektion
        self.sinogramm_filter = np.copy(self.sinogramm)
        # Auswahl Filterung auf grafischen Oberfläche

        filterart = self.radio_mit.isChecked()
        if filterart:
            # abspeichern des aktuell ausgewaehlten Filters
            self.currentchoice = self.cb_filter.currentText()
            if self.currentchoice == "Ramp":
                # Erstellung Rampfilter
                ramp = np.abs(np.fft.fftshift(np.fft.fftfreq(len(self.sinogramm[0]))))
                # Fouriertransformation
                fourier_image = np.fft.fft(self.sinogramm)
                fourier_image = np.fft.fftshift(fourier_image)
                # Anwenden des Filters auf Bild:
                # Multiplikation im Frequenzraum
                fourier_gefiltert = fourier_image * ramp
                # Bild zurueckshiften
                fourier_gefiltert = np.fft.ifftshift(fourier_gefiltert)
                # Ruecktransformation Frequenz- in Ortsraum
                self.sinogramm_filter = np.real(np.fft.ifft(fourier_gefiltert))
        alpha_r = np.linspace(0, self.winkel_max, len(self.sinogramm_filter), endpoint=False)
        self.image_r = np.zeros((len(self.sinogramm_filter[0]), len(self.sinogramm_filter[0])))
        # hier Thread da rechenaufwendig
        self.calculate_rueck = Rueckwaertsprojektion(self.sinogramm_filter, self.image_r, alpha_r)
        self.calculate_rueck.signal.connect(self.animation_r)
        self.calculate_rueck.signal_finish.connect(self.animation_r_finish)
        self.progress_rueck.setMaximum(self.winkel_max)
        self.calculate_rueck.start()
        self.progress_sino.reset()
        self.groupBox_vor.setEnabled(False)




    def loadButtonPress(self):
        """
        Öffnet file dialog um eine Datei zu laden/grafisch darzustellen.

        Parameters
        ----------
        None

        Return
        ----------
        None
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,
                                                  "Open file", ""
                                                  ,"CT Bilder (*.npy)",
                                                  options=options)
        # TODO: was passiert wenn es kein File gibt? bzw man etwas
        # unzureichendes laedt? Kernel died!

        if fileName:
            # nachdem neue Datei geladen wird sollen vorherige Grafiken
            # aus allen Bildern entfernt werden
            self.clearButtonPress()
            # Einlesen der Daten
            self.data = np.load(fileName)
            self.img1.setImage(self.data)
            self.groupBox_vor.setEnabled(True)
                
                
    def sinoButtonPress(self):
        self.groupBox_vor.setEnabled(False)
        """
        Erstellt Sinogramm und stellt es grafisch dar.
        
        Parameters
        ----------
        None
        
        Return
        ----------
        None
        """
        self.laenge_original = len(self.data)
        # Vorverarbeitung fuer Drehung
        self.data_gross = drehung_vorverarbeitung(self.data)
        linienintegrale = []
        # verschiedene (Rotations)winkel durchgehen
        # Auswahl Endpunkt je nachdem, was auf der graphischen Oberflaeche
        # ausgewaehlt wird
        # 180 Grad oder 360 Grad
        angle = self.radio180.isChecked()
        if angle:
            angle_value = 180
        else:
            angle_value = 360
        # TODO: ??
        self.winkel_max = angle_value
        angle_steps = self.sb_anglesteps.value()
        self.sinogramm = np.zeros([angle_steps, len(self.data_gross)])
        # hier Thread!!!
        self.calculate_vor = Vorwaertsprojektion(angle_value, self.data_gross, angle_steps, self.sinogramm)
        self.calculate_vor.signal.connect(self.animation)
        self.calculate_vor.signal_finish.connect(self.animation_finish)
        self.progress_sino.setMaximum(angle_value)
        self.calculate_vor.start()

        print("b")


        # Sinogramm darstellen auf grafischer Oberflaeche


        # TODO:threading, schneller machen, Drehung interpolieren? 
        # TODO: live Erzeugung Sinogramm
        

    def animation(self, alpha):
        self.progress_sino.setValue(alpha)
        self.img2.setImage(self.sinogramm)


    def animation_finish(self):
        self.progress_sino.setValue(self.progress_sino.maximum())
        self.save_sinoButton.setEnabled(True)
        self.groupBox_rueck.setEnabled(True)
        self.groupBox_vor.setEnabled(True)


    def animation_r(self, i):
        self.progress_rueck.setValue(i)
        self.img3.setImage(self.image_r)


    def animation_r_finish(self, i):
        self.progress_rueck.setValue(self.progress_rueck.maximum())
        # durch vorherige Vorwärtsprojektion (dabei wurde Ursprungsbild fuer
        # eine verlustfreie Drehung vergroeßert) ist um rueckprojeziertes
        # Bild ein Kreis
        # dieser wird nun entfernt
        diff = (len(self.image_r) - self.laenge_original) // 2
        print(diff)
        print(self.laenge_original)
        self.image_r = self.image_r[diff:self.laenge_original+diff, diff:self.laenge_original+diff]
        # Rückprojektion darstellen auf grafischer Oberflaeche
        self.img3.setImage(self.image_r)
        #print(np.shape(self.image_r))
        # TODO: noch nicht fertig
        # Differenzbild ezeugen und grafisch darstellen
        if self.data is not None:
            self.diff_img = np.abs(self.data - self.image_r)
            self.img4.setImage(self.diff_img)
        self.save_imgButton.setEnabled(True)
        self.groupBox_rueck.setEnabled(True)

    # TODO: erklaeren lassen! Umbenennung Button
    def saveButtonPress(self):
        """
        In einem sich oeffnenden file dialog kann ein Sinogramm
        unter selbst gewaehlten Dateinamen abgespeichert werden.
        
        Parameters
        ----------
        None
        
        Return
        ----------
        None
        """
        self.sinogramm_plus_info = np.vstack((np.ones((1,
                                                       len(self.sinogramm[0]))),
                                                        self.sinogramm))
        self.sinogramm_plus_info[0, 0] = self.laenge_original
        # TODO: abspeichern ob 180 )oder 360 °)
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
        fileName, _ = QFileDialog.getSaveFileName(self,"Save file", "Sinogramm.milu", "Sinogramme (*.milu)", options=options)
        # TODO: was passiert wenn es kein File gibt? bzw man etwas
        # unzureichendes laedt? Kernel died!
        if fileName:
            # Speichern der Daten
            with open(fileName, "wb") as file:
                np.save(file, self.sinogramm_plus_info)


    def save_imgButtonPress(self):
        """
        In einem sich oeffnenden file dialog kann das erstellte rückprojizierte
        Bild unter selbst gewaehlten Dateinamen abgespeichert werden.

        Parameters
        ----------
        None

        Return
        ----------
        None
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "Save file", "Reko_img.milu",
                                                  "rückprojizierte Bilder (*.milu)",
                                                  options=options)
        if fileName:
            # Speichern der Daten
            with open(fileName, "wb") as file:
                np.save(file, self.self.image_r)


    # TODO: erklaeren lassen!
    def loadsinoButtonPress(self):
        """
        Ladet ein (bereits bestehendes) Sinogramm in einem sich oeffnenden
        file dialog.
        
        Parameters
        ----------
        None
        
        Return
        ----------
        None
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open Sino", "", "Sinogramme (*.milu)", options=options)
        # TODO: Bei Cancel stürzt Programm ab??
        # TODO: was passiert wenn es kein File gibt?
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



        
    # TODO: zu viele weiße Punkte bei Sinogramm?
    # TODO: Kontrast verändern
    

        
                

def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = MainGui()

    # TODO: Title
    ui.show()
    sys.exit(app.exec_())


class Vorwaertsprojektion(QtCore.QThread):
    # fuer Animation
    signal = QtCore.pyqtSignal(float)
    signal_finish = QtCore.pyqtSignal(float)

    def __init__(self, angle_value, data_gross, angle_steps, sinogramm):
        super().__init__()
        print("init")
        self.angle_value = angle_value
        self.data_gross = data_gross
        self.angle_steps = angle_steps
        self.sinogramm = sinogramm

    def run(self):
        # Anzahl an Winkelschritten
        print("run")
        numbers_angle = np.linspace(0, self.angle_value, self.angle_steps, endpoint=False)
        for count, alpha in enumerate(numbers_angle):
            print(count)
            # TODO: Progressbar raus aus Thread!
            # Drehung
            data_transform = drehung(self.data_gross, alpha)
            # Bildung von Linienintegralen fuer einzelnen Rotationswinkel
            linienintegral = np.sum(data_transform, axis=0)
            self.sinogramm[count] = linienintegral
            self.signal.emit(alpha)
        self.signal_finish.emit(alpha)


class Rueckwaertsprojektion(QtCore.QThread):
    # fuer Animation
    signal = QtCore.pyqtSignal(float)
    signal_finish = QtCore.pyqtSignal(float)


    def __init__(self, sinogramm_filter, image_r, alpha_r):
        super().__init__()
        #print("init")
        self.sinogramm_filter = sinogramm_filter
        self.image_r = image_r
        self.alpha_r = alpha_r

    def run(self):
        for i in range(len(self.sinogramm_filter)):
            sino2d = self.sinogramm_filter[i] * np.ones_like(self.image_r)
            # Drehung
            sino2d_transform = drehung(sino2d, -self.alpha_r[i])
            self.image_r += sino2d_transform
            self.signal.emit(self.alpha_r[i])
        self.signal_finish.emit(0)


if __name__ == "__main__":
    main()
    
    
# Buttons: Parameter Anzahl Winkelschritte, pi oder 2pi (Radiobutton, Checkbox)
# TODO: Winkelanzahl: wieviele Winkeschritte
    # moved...slider
    # welcher winkelraum (180 oder 360°) checkbox
    # TODO: ProgressBar
    # TODO: funktioniert nicht mit Windowskonsole?
    # TODO: falsche
    # TODO: alle Buttons richtig verknüpfen, richtig setzen
    # TODO: MenuToolBar oben, grafische Oberfläche überarbeiten
    # auswahl filter nur wenn gefiltert angeklickt ist
    # threading, Animation
    
    # TODO: spacer, progressbar, Progressbar bei Auswahl 180 360
    # TODO: ok Buttons fuer Boxen?
    # rückprojizierte Bilder abspeichern, damit erneut Projektion mgl
    # Progress, Animation Rueck, andere Filter, Speichern rueck Bilder
    # ausgrauen, rescalen?
    # TODO: bei richtigem CT funktioniert Rueckreko nicht
    # TODO: CT Tisch ebenfalls animieren
    # TODO: File dialog Ordner (idea) welches Abgabeformat?r
    # TODO: movie ausschaltbar