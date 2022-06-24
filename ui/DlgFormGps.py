from PySide2.QtWidgets import QWidget, QGridLayout, QToolBox

from .DlcControlPort import DlgPortControl
from .DlgControlMapGpsAxioma import ControlMapViewAxioma


class dlgFromGps(QWidget):
    def __init__(self,parent=None):
        super(dlgFromGps, self).__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)
        #layout.addWidget(self.window.tabWidget,0,0)
        #self.tabwidget = QTabWidget()
        self.tabwidget =QToolBox()
        layout.addWidget(self.tabwidget,0,0)
        self.__tab_port = QWidget()
        self.__tab_map = QWidget()
        self.tabwidget.addItem(self.__tab_port, "Настройка источник")
        self.tabwidget.addItem(self.__tab_map, "Работа с GPS")
        self.__initTabConent()
        self.tabwidget.currentChanged.connect(self.__change_active_tab)
        self.__control_port.loadParamsPort()
    def __initTabConent(self):
        self.__control_port=DlgPortControl(self,self.__tab_port)
        self.__control_map=ControlMapViewAxioma(self,self.__tab_map)
        #self.__control_map.loadConfig()
        #self.__control_port.setParentForm(self)
        #self.__control_map.setParentForm(self)
        self.setEnabledMapForm(False)
    def __change_active_tab(self,index_active):
        if index_active==1:
            self.__control_map.setParamSource(self.__control_port.actualParamSource)
    def setEnabledMapForm(self,enable):
        self.tabwidget.setItemEnabled(1,enable)
    def setEnabledPortForm(self,enable):
        self.tabwidget.setItemEnabled(0,enable)
    '''
    def setActiveMapFrom(self):
        self.tabwidget.setItemEnabled(1,True)
        self.tabwidget.setCurrentIndex(1)
        self.__control_map.setParamSource(self.__control_port.actualParamSource)
    '''


