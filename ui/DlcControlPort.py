import json
import os

#import pynmea2
from pathlib import Path

from PySide2 import QtCore
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget
from PySide2.QtSerialPort import QSerialPortInfo
from PySide2.QtSerialPort import QSerialPort

def dataBits(value:int):
    if value==8:
        return QSerialPort.Data8
    if value==5:
        return QSerialPort.Data5
    if value==6:
        return QSerialPort.Data6
    if value==7:
        return QSerialPort.Data7
def parity(value:int):
    if value==0:
        return QSerialPort.NoParity
    if value==1:
        return QSerialPort.EvenParity
    if value==2:
        return QSerialPort.OddParity
    if value==3:
        return QSerialPort.SpaceParity
    if value==4:
        return QSerialPort.MarkParity
    return QSerialPort.UnknownParity
def stopBits(value:int):
    if value==1:
        return QSerialPort.OneStop
    if value==2:
        return QSerialPort.TwoStop
    if value==3:
        return QSerialPort.OneAndHalfStop
    return QSerialPort.UnknownStopBits
def flowControl(value:int):
    if value==0:
        return QSerialPort.NoFlowControl
    if value==1:
        return QSerialPort.HardwareControl
    if value==2:
        return QSerialPort.SoftwareControl
    return QSerialPort.UnknownFlowControl
class DlgPortControl(QWidget):
    def __init__(self,parent_form,parent=None):
        self.__parent_form=parent_form
        self.__test_processStop=False
        self.__actual_params=None
        super(DlgPortControl, self).__init__(parent)
        self.__parentWin=parent
        self.__port=None
        self.load_ui()
        self.__update_ports()
        self.__set_default()
        self.window.pb_update_list_port.clicked.connect(self.__update_ports)
        self.window.pb_run_test.clicked.connect(self.__run_test)
        self.window.pb_stop.clicked.connect(self.__stop_test)
        self.window.pb_save_param.clicked.connect(self.__save_param_port)
        ''' Читаем ранее сохраненые параметры'''
        #self.loadParamsPort()

    def load_ui(self):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "controlComSource.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window  = loader.load(ui_file,self.__parentWin)
        ui_file.close()
    def setParentForm(self,form_gps):
        ''' Установка родительской формы
        Нужна для взаимодействия с остальными Tabs ( можно использовать и сигналы )
         '''
        self.__parent_form=form_gps
    def __update_ports(self):
        self.window.cmb_ports.clear()
        list_ports=QSerialPortInfo().availablePorts()
        for port_info in list_ports:
            self.window.cmb_ports.addItem(port_info.portName())
        self.window.cmb_ports.setCurrentIndex(0)
    def __set_default(self):
        self.window.cmb_baudRates.setCurrentIndex(2)
        self.window.cmb_stopBits.setCurrentIndex(0)
        self.window.cmb_Parity.setCurrentIndex(0)
        self.window.cmb_DataBits.setCurrentIndex(3)
        self.window.label_status_port.setText("Port in Close")
    def __run_test(self):
        if self.__port is not None:
            self.__port.close()
        self.__test_processStop=True
        self.__parent_form.setEnabledMapForm(False)
        self.__port = QSerialPort()
        self.__port.setBaudRate(int(self.window.cmb_baudRates.currentText()))
        self.__port.setPortName(self.window.cmb_ports.currentText())

        self.__port.setDataBits(dataBits(self.window.cmb_DataBits.currentIndex()+5))
        self.__port.setParity( parity(self.window.cmb_Parity.currentIndex()))
        self.__port.setStopBits( stopBits(self.window.cmb_stopBits.currentIndex()+1) )
        self.__port.setFlowControl(  flowControl(self.window.cmb_flowcontrol.currentIndex()))
        status_port=self.__port.open(QtCore.QIODevice.ReadWrite)
        if status_port:
            self.window.label_status_port.setText("Port is Open")
        else:
            self.window.label_status_port.setText('Port open error')
            return
        self.__port.readyRead.connect(self.__readFromPort)
    def __stop_test(self):
        self.__test_processStop=False
        if self.__port is not None:
            self.__port.close()
            self.__port=None
            self.window.label_status_port.setText('Port Close')
    def __readFromPort(self):
        #data = self.__port.readAll()
        data=self.__port.readLineData(256)
        data_out=data.replace("\r\n","")

        if len(data_out)>0:
            self.window.plainTextEdit.appendPlainText(data_out)
            #obj=pynmea2.parse(data_out,True)
            jkl=0
    def loadParamsPort(self):
        ''' Загружаем сохраненые параметры настроек порта'''
        path_base_path=os.path.dirname(__file__)
        path_base_path=os.path.join(path_base_path,'config_gps_port.json')
        if not Path(path_base_path).exists():
            self.__actual_params=None
            return
        with open(path_base_path, 'r') as config_port_file:
            self.__actual_params = json.load(config_port_file)
        ''' Проверяем порт в настройках существует в списке '''
        index_port=self.window.cmb_ports.findText(self.__actual_params['port'])
        if index_port>=0:
            ''' порт есть в списке'''
            self.window.cmb_ports.setCurrentIndex(index_port)
            self.__parent_form.setEnabledMapForm(True)
            ''' И сразу активируем рабочий режим'''
            self.__parent_form.tabwidget.setCurrentIndex(1)
            #self.__parent_form.setActiveMapFrom()
            return
        self.__parent_form.setEnabledMapForm(False)
    def __save_param_port(self):
        path_base_path=os.path.dirname(__file__)
        path_base_path=os.path.join(path_base_path,'config_gps_port.json')
        params={}
        params['port']=self.window.cmb_ports.currentText()
        params['baudRates']=int(self.window.cmb_baudRates.currentText())
        params['DataBits']=self.window.cmb_DataBits.currentIndex()+5
        params['Parity']=self.window.cmb_Parity.currentIndex()
        params['stopBits']=self.window.cmb_stopBits.currentIndex()+1
        params['FlowControl']=self.window.cmb_flowcontrol.currentIndex()
        with open(path_base_path, "w") as outfile:
            json.dump(params, outfile)
        self.__actual_params=params.copy()
        self.__parent_form.setEnabledMapForm(True)

    @property
    def actualParamSource(self):
        ''' получаем актуальные параметры источника'''
        return self.__actual_params


