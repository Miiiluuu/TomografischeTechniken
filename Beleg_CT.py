"""
    Bildrekonstruktion: "Wir basteln uns einen CT".
    Aufgabe 1: Erzeugung eines Satzes von Projektionen aus echten und
    simulierten CT-Bildern, stellt Sinogramm grafisch dar. Dabei koennen
    bestimmte Parameter eingestellt werden und werden bei grafischen
    Darstellung beruecksichtigt.
"""

import sys

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFileDialog, QPushButton, QGridLayout,
                             QVBoxLayout, QSlider, QRadioButton, QGroupBox,
                             QProgressBar)
import pyqtgraph


class Gui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        # Layouteinstellungen
        # (1) Griderzeugung und -bearbeitung
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(10)
        self.setWindowTitle("Wir basteln uns ein CT!")
        
        # (2) VBox erzeugen, bearbeiten und dem Grid hinzufuegen
        self.vbox = QVBoxLayout()
        self.grid.addLayout(self.vbox, 0, 0)
        self.vbox.addStretch(1)
        
        # (3) Hinzufuegen von Buttons und Aehnlichem
        # OpenButton hinzufuegen
        self.loadButton = QPushButton("Open")
        # TODO: naehere Beschreibung des Buttons mit Cursor drauf?
        self.loadButton.clicked.connect(self.loadButtonPress)
        self.vbox.addWidget(self.loadButton)
        # Knopf zum Erzeugen des Sinogramms
        # wenn das zuallererst aufgerufen wird Absturz
        self.sinoButton = QPushButton("Erstelle Sinogramm")
        self.sinoButton.clicked.connect(self.sinoButtonPress)
        self.vbox.addWidget(self.sinoButton)
        # SaveButton hinzufuegen
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveButtonPress)
        self.vbox.addWidget(self.saveButton)
        # Knopf zum Laden des Sinogramms
        self.loadsinoButton = QPushButton("Load Sinogramm")
        self.loadsinoButton.clicked.connect(self.loadsinoButtonPress)
        self.vbox.addWidget(self.loadsinoButton)
        # Hinzufuegen eines SLiders zum Auswaehlen der Winkelschritte
        self.vbox.addWidget(self.slider())
        # Hinzufuegen einer Progressbar fuer die Vorwaertsprojektion
        self.vbox.addWidget(self.progressbar())
        
        # Hinzufuegen grafischer Bilder zum Layout
        # Bild 1
        self.graphic1 = pyqtgraph.GraphicsLayoutWidget()
        self.view1 = self.graphic1.addViewBox()
        self.view1.setAspectLocked(True)
        # damit verhalten wie Mathplotlib
        self.view1.invertY(True)
        self.img1 = pyqtgraph.ImageItem()
        # damit verhalten wie Mathplotlib
        self.img1.setOpts(axisOrder='row-major')
        self.view1.addItem(self.img1)
        self.grid.addWidget(self.graphic1, 0, 1)
        
        # Bild 2
        self.graphic2 = pyqtgraph.GraphicsLayoutWidget()
        self.view2 = self.graphic2.addViewBox()
        self.view2.setAspectLocked(True)
        # damit verhalten wie Mathplotlib
        self.view2.invertY(True)
        self.img2 = pyqtgraph.ImageItem()
        # damit verhalten wie Mathplotlib
        self.img2.setOpts(axisOrder='row-major')
        self.view2.addItem(self.img2)
        self.grid.addWidget(self.graphic2, 0, 2)
        
        # Bild 3
        self.graphic3 = pyqtgraph.GraphicsLayoutWidget()
        self.view3 = self.graphic3.addViewBox()
        self.view3.setAspectLocked(True)
        # damit verhalten wie Mathplotlib
        self.view3.invertY(True)
        self.img3 = pyqtgraph.ImageItem()
        # damit verhalten wie Mathplotlib
        self.img3.setOpts(axisOrder='row-major')
        self.view3.addItem(self.img3)
        self.grid.addWidget(self.graphic3, 1, 1)
        self.img3.setImage(np.eye(5))
        
        # Bild 4
        self.graphic4 = pyqtgraph.GraphicsLayoutWidget()
        self.view4 = self.graphic4.addViewBox()
        self.view4.setAspectLocked(True)
        # damit verhalten wie Mathplotlib
        self.view4.invertY(True)
        self.img4 = pyqtgraph.ImageItem()
        # damit verhalten wie Mathplotlib
        self.img4.setOpts(axisOrder='row-major')
        self.view4.addItem(self.img4)
        self.grid.addWidget(self.graphic4, 1, 2)
        self.img4.setImage(np.eye(5))
        
        
    def slider(self):
        """
        Erstellt einen Schieberegler zur Auswahl der Anzahl an WInkelschritten,
        die fuer eine anschließende Vorwaertsprojektion.
        
        Parameters
        ----------
        None
        
        Return
        ----------
        None
        """
        groupBox = QGroupBox("Anzahl der Winkelschritte")

        slider = QSlider(Qt.Horizontal)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setTickInterval(15)
        slider.setSingleStep(1)
        vbox = QVBoxLayout()
        vbox.addWidget(slider)
        vbox.addStretch(1)
        groupBox.setLayout(vbox)

        return groupBox
        
    
    def progressbar(self):
        """
        Erstellt eine Progressbar, welche den Fortschritt im Erstellen
        der Vorwaertsprojektion (des Sinogramms) darstellt.
        
        Parameters
        ----------
        None
        
        Return
        ----------
        None
        """
        self.setWindowTitle('bla')
        self.progress = QProgressBar(self)
        self.progress.setMaximum(180)
        
        return self.progress
        
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
    #    # Einlesen der Daten
    #    data = np.load("Bilder/dreiNadeln32.npy")
        # Kontrolldarstellung
#        plt.figure()
#        plt.imshow(data)
        # Vorverarbeitung fuer Drehung
        data_groß = self.drehung_vorverarbeitung(self.data)
    #    # Drehung um 90°
    #    data_transform = drehung(data_groß, 90)
    #    # Kontrolldarstellung gedrehtes Bild
    #    plt.figure()
    #    plt.imshow(data_transform)
        linienintegrale = []
        # verschiedene (Rotations)winkel durchgehen:
        for alpha in np.linspace(0, 180, 10, endpoint=False):
            self.progress.setValue(alpha+1)
            # Drehung
            data_transform = self.drehung(data_groß, alpha)
            # Bildung von Linienintegralen fuer einzelnen Rotationswinkel alpha:
            # einzelnen Zeilenwerte (ausgehend von Koerperoberflaeche Bauch zu
            # Ruecken) aufaddieren
            linienintegral = np.sum(data_transform, axis=0)
            #print(linienintegral)
            # einzelnen Linienintegrale abspeichern in Liste
            linienintegrale.append(linienintegral)
        self.progress.setMaximum()    
        # Sinogramm darstellen
        self.sinogramm = np.array(linienintegrale)
#        plt.figure()
#        plt.imshow(linienintegrale_array)
        # darstellen in img2 wenn auf knopf gedrueckt
        self.img2.setImage(self.sinogramm)
                
        
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
            # Einlesen der Daten
            np.save(fileName, self.sinogramm_plus_info)


    def loadsinoButtonPress(self):
        """
        Ladet ein (bereits bestehendes) Sinogramm.
        
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
    
    
    def rueckproj(self):
        """
        (ungefilterte) Rueckprojektion.
        
        Parameters
        ----------
        None
        
        Return
        ----------
        None
        """
        self.sinogramm_proj = self.sinogramm[:] * np.ones(len(self.laenge_original))
        
        
        
    
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
    
    