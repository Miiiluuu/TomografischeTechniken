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
from scipy.ndimage import map_coordinates
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFileDialog, QPushButton, QGridLayout,
                             QVBoxLayout, QHBoxLayout, QSlider, QRadioButton,
                             QGroupBox, QProgressBar, QCheckBox, QLabel,
                             QSpinBox, QComboBox)
import pyqtgraph


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
        self.sb_anglesteps.setValue(30)
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
        self.vbox_buttons.addLayout(self.hbox_r)                                                                    
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
        self.cb_filter.addItem("None")
        self.cb_filter.addItem("Ramp")
        self.cb_filter.addItem("Shepp-Logan")
        self.cb_filter.addItems(["Middle"])
        # abspeichern des aktuell ausgewaehlten Filters
        currentchoice = self.cb_filter.currentText()
        self.vbox_cb = QVBoxLayout()
        self.vbox_cb.addWidget(self.cb_filter)
        self.groupBox_cb.setLayout(self.vbox_cb)
        self.hbox_r.addWidget(self.groupBox_cb) 

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
        label_img3 = QLabel("Sinogramm")
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
        print("a")
        alpha_r = np.linspace(0, self.winkel_max, len(self.sinogramm), endpoint=False)
        self.image_r = np.zeros((len(self.sinogramm[0]), len(self.sinogramm[0])))
        for i in range(len(self.sinogramm)):
            print(i)
            sino2d = self.sinogramm[i] * np.ones_like(self.image_r)
            # Drehung
            sino2d_transform = self.drehung(sino2d, -alpha_r[i])
            self.image_r += sino2d_transform
        # Rückprojektion darstellen auf grafischer Oberflaeche
        self.img3.setImage(self.image_r)
        print("b")
    
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
        data_groß = self.drehung_vorverarbeitung(self.data)
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
        # Anzahl an Winkelschritten
        angle_steps = self.sb_anglesteps.value()
        for alpha in np.linspace(0, angle_value, angle_steps, endpoint=False):
            self.progress_sino.setValue(alpha+1)
            # Drehung
            data_transform = self.drehung(data_groß, alpha)
            # Bildung von Linienintegralen fuer einzelnen Rotationswinkel
            linienintegral = np.sum(data_transform, axis=0)
            linienintegrale.append(linienintegral)
        self.progress_sino.setValue(self.progress_sino.maximum())
        # Sinogramm darstellen auf grafischer Oberflaeche
        self.sinogramm = np.array(linienintegrale)
        self.img2.setImage(self.sinogramm)
        self.winkel_max = angle_value
        # TODO:threading, schneller machen, Drehung interpolieren? 
        # TODO: live Erzeugung Sinogramm
        
        
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
        self.sinogramm_plus_info[0, 1] = 180
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


    def drehmatrix(self, grad):
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
    
    
    def drehung_vorverarbeitung(self, image):
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
        self.laenge_original = len(image)
        # Wie groß muss vergroeßertes Bild sein fuer anschließende verlustfreie
        # Drehung? (nach Satz des Pythagoras berechnet)
        # (auf)runden und Integer damit keine halben Pixel als Ergebnis erhalten
        # werden (c)
        c = np.int(np.ceil(np.sqrt(2) * self.laenge_original))
        # Pruefen, ob Originalsbild ueberhaupt mittig reingelegt werden kann:
        b = c - self.laenge_original
        # ist b eine ungerade Zahl, dann vergroeßere c um Eins, damit b im
        # anschließenden gerade Zahl ist
        if b % 2 == 1:
            c += 1
            b = c - self.laenge_original
        # ansonsten ist b gerade und Originalbild kann mittig reingelegt werden   
        # Anlegen eines (groeßeren) Arrays, indem Originalbild anschließend 
        # (mittig!!) gespeichert wird
        image_groß = np.zeros((c, c))
        # nun wird vergroeßertes Bild ins Originalbild gelegt
        image_groß[np.int(b/2):self.laenge_original+np.int(b/2), np.int(b/2):self.laenge_original+np.int(b/2)] = image
        # oder mit b//2 (rundet zwar ab, aber b kann nur ganze Zahl sein)
        return image_groß
    
    
    def drehung(self, image, grad):
        """ Drehung eines Bildes in positivem Drehsinne.
    
            Parameter:
            ----------
            image: Array, Eingabewerte.
    
            transform: Transformationsmatrix, fuehrt Drehung (im positiven Sinn)
            durch.
        """
        # Erzeugen einer Drehmatrix mit gewaehltem Winkel
        transform = self.drehmatrix(grad)
        # Anlegen Null-Array
        image_transform = np.zeros_like(image)
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
    #    koord_rotate = []
        for x in range(-pixel_mitte, pixel_mitte):
            for y in range(-pixel_mitte, pixel_mitte):
                # Rotationsmatrix auf alle x-Werte anwenden
                koord_xy_transform = (transform @ np.array([x, y, 1]))
                x_transform = np.int_(np.round(koord_xy_transform[0]))
                y_transform = np.int_(np.round(koord_xy_transform[1]))
                # Pixel des Null-Arrays (image_transform) auffuellen:
                # Pruefen, ob rotierter Wert innerhalb Bereich Originalbild
                # vorkommt
                # wenn Bedingung erfuellt existieren Grauwerte im Originalbild,
                # die ins rotierte Bild an der richtigen Stelle uebernommen werden
                # (ansonsten Nullen an dieser Stelle)
                # Addieren von 128 (pixel_quadrant), um Array nicht mit
                # negativen Indices anzusprechen (wuerde falsche Werte liefern)
                # RandNullen werden abgeschnitten, ist egal
                if (-pixel_mitte <= x_transform < pixel_mitte) and \
                   (-pixel_mitte <= y_transform < pixel_mitte):
    #                koord_rotate.append((x_transform + pixel_mitte,
    #                                     y_transform + pixel_mitte))
                    # Addieren von 128 (pixel_mitte), um Array nicht mit
                    # negativen Indices anzusprechen (wuerde falsche Werte liefern)
                    # map coordinates fier Grauwertapproximation?
                    image_transform[y + pixel_mitte, x + pixel_mitte] = \
                        map_coordinates(image,
                                        np.array([(y_transform + pixel_mitte,
                                                   x_transform + pixel_mitte)]).T)
        return image_transform
    # TODO: zu viele weiße Punkte bei Sinogramm?
    # TODO: Kontrast verändern
    

        
                

def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = Gui()
    # TODO: Title
    ui.show()
    sys.exit(app.exec_())
    

if __name__ == "__main__":
    main()
    
    
# Buttons: Parameter Anzahl Winkelschritte, pi oder 2pi (Radiobutton, Checkbox)
# TODO: Winkelanzahl: wieviele WInkeschritte
    # moved...slider
    # welcher winkelraum (180 oder 360°) checkbox
    # TODO: ProgressBar
    # TODO: funktioniert nicht mit Windowskonsole?
    
    