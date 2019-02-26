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
                             QSpinBox, QComboBox)
import pyqtgraph


def drehmatrix(grad):
    """ Erzeugt eine Drehmatrix.

        Parameter:
        ----------
        grad: Angabe der Drehung in Grad (im positivem Drehsinne) in Grad.
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
    # Seitenlaenge quadrat. Matrix (der Eingangswerte) (a)
    laenge_original = len(image)
    # Wie groß muss vergroeßertes Bild sein fuer anschließende verlustfreie
    # Drehung? (nach Satz des Pythagoras berechnet)
    # (auf)runden und Integer damit keine halben Pixel als Ergebnis erhalten
    # werden (c)
    c = np.int(np.ceil(np.sqrt(2) * laenge_original))
    # Pruefen, ob Originalsbild ueberhaupt mittig reingelegt werden kann:
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
    # nun wird vergroeßertes Bild ins Originalbild gelegt
    image_groß[np.int(b / 2):laenge_original + np.int(b / 2), np.int(b / 2):laenge_original + np.int(b / 2)] = image
    # oder mit b//2 (rundet zwar ab, aber b kann nur ganze Zahl sein)
    return image_groß


def drehung(image, grad):
    """ Drehung eines Bildes in positivem Drehsinne.

        Parameter:
        ----------
        image: Array, Eingabewerte.

        transform: Transformationsmatrix, fuehrt Drehung (im positiven Sinn)
        durch.
    """
    # Erzeugen einer Drehmatrix mit gewaehltem Winkel
    transform = drehmatrix(grad)
    # Anlegen Null-Array
    image_transform = np.zeros_like(image)
    print(np.shape(image_transform))
    # Schleife:
    # jeden Pixel einzeln durchgehen, auf diesem Drehmatrix anwenden
    # und neue rotierte Koordinaten berechnen
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
    #print(np.shape(x))
    koord_xy_transform = (np.array([x, y, np.ones_like(x)]).T @ transform).T
    #print(np.shape(koord_xy_transform))
    x_transform = (koord_xy_transform[0])
    y_transform = (koord_xy_transform[1])
    bed1 = (-pixel_mitte <= x_transform) * (x_transform < pixel_mitte)
    bed2 = (-pixel_mitte <= y_transform) * (y_transform < pixel_mitte)
    bed = bed1 * bed2
    #print(np.shape(bed))
    image_transform[bed] = \
        map_coordinates(image, np.array([(y_transform[bed] + pixel_mitte),
                                         (x_transform[bed] + pixel_mitte)]))
    return image_transform

class Gui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        # Layouteinstellungen
        # grafische Oberflaeche gestalten
        # Erzeugung uebergeordnetes Grid, in dem alle grafischen Objekte 
        # enthalten sind
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(10)
        self.setWindowTitle("Wir basteln uns ein CT!")
        
        # Erzeugen VBox erzeugen, diese wird dem Grid hinzufuegt
        # in VBox kommen alle Buttons, Auswahlmoeglichkeiten fuer Parameter uÄ
        self.vbox_buttons = QVBoxLayout()
        self.grid.addLayout(self.vbox_buttons, 0, 0)
        self.vbox_buttons.addStretch(1)
        
        self.vbox_buttons2 = QVBoxLayout()
        self.grid.addLayout(self.vbox_buttons2, 1, 0)
        self.vbox_buttons2.addStretch(1)
        
        # Hinzufuegen von Buttons und Aehnlichem zur VBox in grafischen
        # Oberflaeche
        
        # TODO: einige Buttons in QMenuBar oder QToolBar, QTab? QScrollbar?
        # TODO: Benennung aendern
        # OpenButton hinzufuegen
        self.loadButton = QPushButton("Open")
        # TODO: naehere Beschreibung des Buttons mit Cursor drauf?
        self.loadButton.clicked.connect(self.loadButtonPress)
        self.vbox_buttons.addWidget(self.loadButton)
        # Knopf zum Erzeugen des Sinogramms
        # TODO: wenn das zuallererst aufgerufen wird Absturz, nicht ok
        self.sinoButton = QPushButton("Erstelle Sinogramm")
        self.sinoButton.clicked.connect(self.sinoButtonPress)
        self.vbox_buttons.addWidget(self.sinoButton)
        # SaveButton hinzufuegen
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveButtonPress)
        self.vbox_buttons.addWidget(self.saveButton)
        # Knopf zum Laden des Sinogramms
        self.loadsinoButton = QPushButton("Load Sinogramm")
        self.loadsinoButton.clicked.connect(self.loadsinoButtonPress)
        self.vbox_buttons.addWidget(self.loadsinoButton)
        # RueckprojectionButton hinzufuegen
        self.rueckButton = QPushButton("Rückwärtsprojektion")
        # TODO: naehere Beschreibung des Buttons mit Cursor drauf?
        self.rueckButton.clicked.connect(self.rueckButtonPress)
        self.vbox_buttons.addWidget(self.rueckButton)
        # ClearButton hinzufuegen
        self.clearButton = QPushButton("Clear")
        # TODO: naehere Beschreibung des Buttons mit Cursor drauf?
        self.clearButton.clicked.connect(self.clearButtonPress)
        self.vbox_buttons.addWidget(self.clearButton)
        
        # Auswahlmoeglichkeiten fuer Vorwaertsprojektion
        # ist Uebersicht zur Auswahl Parameter fuer Vorwaertsprojektion
        # es wird HBox erzeugt
        self.hbox_v = QHBoxLayout()
        # Hinzufuegen zum Layout (VBox)
        self.vbox_buttons.addLayout(self.hbox_v)
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
    
        # erstellt eine Progressbar, welche den Fortschritt in der
        # Vorwaertsprojektion (des Sinogramms) darstellt.
        self.progress_sino = QProgressBar()
        self.progress_sino.setMaximum(180)
        # Hinzufuegen zum Layout (VBox)
        self.vbox_buttons.addWidget(self.progress_sino)
    
        # Auswahlmoeglichkeiten fuer Rueckwaertsprojektion
        # ist Uebersicht zur Auswahl Parameter fuer Rueckwaertsprojektion
        # es wird HBox erzeugt
        self.hbox_r = QHBoxLayout()
        # Hinzufuegen zum Layout (VBox)
        self.vbox_buttons2.addLayout(self.hbox_r)                                                                    
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
        self.img3.setImage(np.eye(5))

        # Bild 4
        self.vbox_img4 = QVBoxLayout()
        label_img4 = QLabel("Sinogramm")
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
        self.img4.setImage(np.eye(5))


    def activate_cb_filter(self):
        self.cb_filter.setEnabled(True)


    def deactivate_cb_filter(self):
        self.cb_filter.setEnabled(False)


    def clearButtonPress(self):
        """
        Löscht alle Bilder.
        
        Parameters
        ----------
        None
        
        Return
        ----------
        None
        """
    
    
    def rueckButtonPress(self):
        """
        (ungefilterte) Rueckprojektion.
        
        Parameters
        ----------
        None
        
        Return
        ----------
        None
        """
        self.img3.clear()
        alpha_r = np.linspace(0, self.winkel_max, len(self.sinogramm), endpoint=False)
        self.image_r = np.zeros((len(self.sinogramm[0]), len(self.sinogramm[0])))
        filterart = self.radio_mit.isChecked()
        # Anwendung Filter vor Rueckprojektion
        self.sinogramm_filter = np.copy(self.sinogramm)
        # Filterung ausgewaehlt
        if filterart:
            # abspeichern des aktuell ausgewaehlten Filters
            self.currentchoice = self.cb_filter.currentText()
            if self.currentchoice == "Ramp":
                # Erstellung Rampfilter
                ramp = np.abs(np.fft.fftshift(np.fft.fftfreq(len(self.sinogramm[0]))))
                for i in range(len(self.sinogramm)):
                    # Fouriertransformation erstellen
                    fourier_image = np.fft.fft(self.sinogramm[i])
                    fourier_image = np.fft.fftshift(fourier_image)
                    # Anwenden des Filters auf Bild
                    # Multiplikation im Frequenzraum
                    fourier_gefiltert = fourier_image * ramp
                    # Bild zurueckshiften
                    fourier_gefiltert = np.fft.ifftshift(fourier_gefiltert)
                    # Ruecktransformation Frequenz- in Ortsraum
                    self.sinogramm_filter[i] = np.fft.ifft(fourier_gefiltert)
        alpha_r = np.linspace(0, self.winkel_max, len(self.sinogramm_filter), endpoint=False)
        self.image_r = np.zeros((len(self.sinogramm_filter[0]), len(self.sinogramm_filter[0])))
        for i in range(len(self.sinogramm_filter)):
            sino2d = self.sinogramm_filter[i] * np.ones_like(self.image_r)
            # Drehung
            sino2d_transform = drehung(sino2d, -alpha_r[i])
            self.image_r += sino2d_transform
        self.self_image_r = self.image_r[self.laenge_original:self.laenge_original+1,
                     self.laenge_original:self.laenge_original+1]
        # Rückprojektion darstellen auf grafischer Oberflaeche
        self.img3.setImage(self.image_r)
        # durch vorherige Vorwärtsprojektion (dabei wurde Ursprungsbild fuer
        # eine verlustfreie Drehung vergroeßert) ist um rueckprojeziertes
        # Bild ein Kreis
        # dieser wird nun entfernt
        diff = (len(self.image_r) - self.laenge_original) // 2
        self.image_r = self.image_r[diff:self.laenge_original+diff, diff:self.laenge_original+diff]
        self.img3.setImage(self.image_r)
        print(np.shape(self.image_r))
            

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
                                                  ,"All Files (*);;Python Files (*.py)",
                                                  options=options)
        # TODO: was passiert wenn es kein File gibt? bzw man etwas
        # unzureichendes laedt? Kernel died!
        
        if fileName:
                # Einlesen der Daten
                self.data = np.load(fileName)
                # nachdem neue Datei geladen wird sollen vorherige Grafiken
                # aus allen Bildern entfernt werden
                self.img1.clear()
                self.img2.clear()
                self.img3.clear()
                self.img4.clear()
                self.img1.setImage(self.data)
                
                
    def sinoButtonPress(self):
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
        self.winkel_max = angle_value
        angle_steps = self.sb_anglesteps.value()
        self.sinogramm = np.zeros([angle_steps, len(self.data_gross)])
        # hier Thread!!!
        self.calculate_vor = Vorwaertsprojektion(angle_value, self.data_gross, angle_steps, self.sinogramm)
        self.calculate_vor.signal.connect(self.animation)
        self.calculate_vor.signal_finish.connect(self.animation_finish)
        self.calculate_vor.start()
        print("b")


        # Sinogramm darstellen auf grafischer Oberflaeche


        # TODO:threading, schneller machen, Drehung interpolieren? 
        # TODO: live Erzeugung Sinogramm
        

    def animation(self, alpha):
        self.progress_sino.setValue(alpha + 1)
        self.img2.setImage(self.sinogramm)

    def animation_finish(self, alpha):
        self.progress_sino.setValue(self.progress_sino.maximum())


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
        fileName, _ = QFileDialog.getSaveFileName(self,"Save file", "","All Files (*);;Python Files (*.py)", options=options)
        # TODO: was passiert wenn es kein File gibt? bzw man etwas
        # unzureichendes laedt? Kernel died!
        if fileName:
            # Speichern der Daten
            np.save(fileName, self.sinogramm_plus_info)


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
        fileName, _ = QFileDialog.getOpenFileName(self,"Open Sino", "","All Files (*);;Python Files (*.py)", options=options)
        # TODO: Bei Cancel stürzt Programm ab??
        # TODO: was passiert wenn es kein File gibt?
        if fileName:
            # Einlesen der Daten
            self.sinogramm_plus_info = np.load(fileName)
            # nachdem neue Datei geladen wird sollen vorherige Grafiken
            # aus allen Bildern entfernt werden
            self.img1.clear()
            self.img2.clear()
            self.img3.clear()
            self.img4.clear()
            self.laenge_original = self.sinogramm_plus_info[0, 0]
            self.winkel_max = self.sinogramm_plus_info[0, 1]
            self.sinogramm = self.sinogramm_plus_info[1:]
            self.img2.setImage(self.sinogramm)



        
    # TODO: zu viele weiße Punkte bei Sinogramm?
    # TODO: Kontrast verändern
    

        
                

def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = Gui()
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



if __name__ == "__main__":
    main()
    
    
# Buttons: Parameter Anzahl Winkelschritte, pi oder 2pi (Radiobutton, Checkbox)
# TODO: Winkelanzahl: wieviele Winkeschritte
    # moved...slider
    # welcher winkelraum (180 oder 360°) checkbox
    # TODO: ProgressBar
    # TODO: funktioniert nicht mit Windowskonsole?
    # TODO: alle Buttons richtig verknüpfen, richtig setzen
    # TODO: MenuToolBar oben, grafische Oberfläche überarbeiten
    # TODO: Beschreibung wenn man auf Cursor raufkommt
    # auswahl filter nur wenn gefiltert angeklickt ist
    # threading, Animation
    
    # TODO: spacer, progressbar, Progressbar bei Auswahl 180 360
