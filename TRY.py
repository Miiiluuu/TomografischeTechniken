# -*- coding: utf-8 -*-
"""
Created on Thu Jan 10 13:41:27 2019

@author: MOELLERMI
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QWidget, QSlider)

class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        grid = QGridLayout()
        grid.addWidget(self.createExampleGroup(), 0, 0)
        grid.addWidget(self.createExampleGroup(), 1, 0)
        grid.addWidget(self.createExampleGroup(), 0, 1)
        grid.addWidget(self.createExampleGroup(), 1, 1)
        self.setLayout(grid)

        self.setWindowTitle("PyQt5 Sliders")
        self.resize(400, 300)

    def createExampleGroup(self):
        groupBox = QGroupBox("Slider Example")

        radio1 = QRadioButton("&Radio horizontal slider")

        slider = QSlider(Qt.Horizontal)
        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setTickInterval(10)
        slider.setSingleStep(1)

        radio1.setChecked(True)

        vbox = QVBoxLayout()
        vbox.addWidget(radio1)
        vbox.addWidget(slider)
        vbox.addStretch(1)
        groupBox.setLayout(vbox)

        return groupBox

if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = Window()
    clock.show()
    sys.exit(app.exec_())

import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class sliderdemo(QWidget):
   def __init__(self, parent = None):
      super(sliderdemo, self).__init__(parent)

      layout = QVBoxLayout()
      self.l1 = QLabel("Hello")
      self.l1.setAlignment(Qt.AlignCenter)
      layout.addWidget(self.l1)
		
      self.sl = QSlider(Qt.Horizontal)
      self.sl.setMinimum(10)
      self.sl.setMaximum(30)
      self.sl.setValue(20)
      self.sl.setTickPosition(QSlider.TicksBelow)
      self.sl.setTickInterval(5)
		
      layout.addWidget(self.sl)
      self.sl.valueChanged.connect(self.valuechange)
      self.setLayout(layout)
      self.setWindowTitle("SpinBox demo")

   def valuechange(self):
      size = self.sl.value()
      self.l1.setFont(QFont("Arial",size))
		
def main():
   app = QApplication(sys.argv)
   ex = sliderdemo()
   ex.show()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   main()

from PyQt5.QtWidgets import (QWidget, QSlider, 
    QLabel, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import sys

class Example(QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):      

        sld = QSlider(Qt.Horizontal, self)
        sld.setFocusPolicy(Qt.NoFocus)
        sld.setGeometry(30, 40, 100, 30)
        sld.valueChanged[int].connect(self.changeValue)
        
        self.label = QLabel(self)
        self.label.setPixmap(QPixmap('mute.png'))
        self.label.setGeometry(160, 40, 80, 30)
        
        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('QSlider')
        self.show()
        
        
    def changeValue(self, value):

        if value == 0:
            self.label.setPixmap(QPixmap('mute.png'))
        elif value > 0 and value <= 30:
            self.label.setPixmap(QPixmap('min.png'))
        elif value > 30 and value < 80:
            self.label.setPixmap(QPixmap('med.png'))
        else:
            self.label.setPixmap(QPixmap('max.png'))
            

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())        