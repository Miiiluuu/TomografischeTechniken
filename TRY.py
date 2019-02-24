# -*- coding: utf-8 -*-
"""
Created on Thu Jan 10 13:41:27 2019

@author: MOELLERMI
"""

import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class combodemo(QWidget):
   def __init__(self, parent = None):
      super(combodemo, self).__init__(parent)
      
      layout = QHBoxLayout()
      self.cb = QComboBox()
      self.cb.addItem("C")
      self.cb.addItem("C++")
      self.cb.addItems(["Java", "C#", "Python"])
      self.cb.currentIndexChanged.connect(self.selectionchange)

        
      layout.addWidget(self.cb)
      self.setLayout(layout)
      self.setWindowTitle("combo box demo")

   def selectionchange(self):
      currentchoice = self.cb.currentText()
      print(currentchoice)

		
def main():
   app = QApplication(sys.argv)
   ex = combodemo()
   ex.show()
   sys.exit(app.exec_())

if __name__ == '__main__':
   main()