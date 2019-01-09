"""
    Bildrekonstruktion: "Wir basteln uns einen CT".
    Aufgabe 1: Erzeugung eines Satzes von Projektionen aus echten und
    simulierten CT-Bildern.
"""

import numpy as np
import matplotlib.pyplot as plt


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
        Originalbildes abgeschnitten werden).

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
    a = len(image)
    # Wie groß muss vergroeßertes Bild sein fuer anschließende verlustfreie
    # Drehung? (nach Satz des Pythagoras berechnet)
    # (auf)runden und Integer damit keine halben Pixel als Ergebnis erhalten
    # werden (c)
    c = np.int(np.ceil(np.sqrt(2) * a))
    # Pruefen, ob Originalsbild ueberhaupt mittig reingelegt werden kann:
    b = c - a
    # ist b eine ungerade Zahl, dann vergroeßere c um Eins, damit b im
    # anschließenden gerade Zahl ist
    if b % 2 == 1:
        c += 1
        b = c - a
    # ansonsten ist b gerade und Originalbild kann mittig reingelegt werden   
    # Anlegen eines (groeßeren) Arrays, indem Originalbild anschließend 
    # (mittig!!) gespeichert wird
    image_groß = np.zeros((c, c))
    # nun wird vergroeßertes Bild ins Originalbild gelegt
    image_groß[np.int(b/2):a+np.int(b/2), np.int(b/2):a+np.int(b/2)] = image
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
            if (-pixel_mitte <= x_transform < pixel_mitte) and \
               (-pixel_mitte <= y_transform < pixel_mitte):
                # Addieren von 128 (pixel_quadrant), um Array nicht mit
                # negativen Indices anzusprechen (wuerde falsche Werte liefern)
                image_transform[y + pixel_mitte, x + pixel_mitte] = \
                    image[y_transform + pixel_mitte, x_transform + pixel_mitte]
    return image_transform


def main():
    # Einlesen der Daten
    data = np.load("dreiNadel32.npy")
    # Kontrolldarstellung
    plt.figure()
    plt.imshow(data)
    # Vorverarbeitung fuer Drehung
    data_groß = drehung_vorverarbeitung(data)
#    # Drehung um 90°
#    data_transform = drehung(data_groß, 90)
#    # Kontrolldarstellung gedrehtes Bild
#    plt.figure()
#    plt.imshow(data_transform)
    linienintegrale = []
    # verschiedene (Rotations)winkel durchgehen:
    for alpha in np.linspace(0, 180, 10, endpoint=False):
        # Drehung
        data_transform = drehung(data_groß, alpha)
        # Bildung von Linienintegralen fuer einzelnen Rotationswinkel alpha:
        # einzelnen Zeilenwerte (ausgehend von Koerperoberflaeche Bauch zu
        # Ruecken) aufaddieren
        linienintegral = np.sum(data_transform, axis=0)
        #print(linienintegral)
        # einzelnen Linienintegrale abspeichern in Liste
        linienintegrale.append(linienintegral)
    # Sinogramm darstellen
    linienintegrale_array = np.array(linienintegrale)
    plt.figure()
    plt.imshow(linienintegrale_array)


if __name__ == "__main__":
    main()
    
    

    