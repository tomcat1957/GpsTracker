import json
import os
from pathlib import Path

import PySide2
import axipy
from PyQt5.QtPositioning import QGeoPositionInfo
from PySide2 import QtCore
from PySide2.QtCore import QFile
from PySide2.QtPositioning import QNmeaPositionInfoSource
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget
from PySide2.QtSerialPort import QSerialPortInfo
from PySide2.QtSerialPort import QSerialPort
from axipy import CoordSystem, view_manager, Style

#from AxyPy.Gps.UI.DlcControlPort import dataBits, parity, stopBits, flowControl
#from AxyPy.Gps.UI.dopTools.animateLayer import AxiAnimateLayer
from .DlcControlPort import dataBits, parity, stopBits, flowControl
from .dopTools.animateLayer import AxiAnimateLayer
from .dopTools.gpsContainer import DataSpatialContainer
from .dopTools.tableGpsData import factoryTableGpsPoint, GpsTracSaveData, factoryTableGpsTrack, \
    TableGpsTrack

default_name_catalog="gps_data_catalog.gpkg"
def geoPositionToDict(geoposition):
    geo_pos_dict={}
    geo_pos_dict['lon']=geoposition.coordinate().longitude()
    geo_pos_dict['lat']=geoposition.coordinate().latitude()
    geo_pos_dict['speed']=geoposition.attribute(PySide2.QtPositioning.QGeoPositionInfo.GroundSpeed)
    geo_pos_dict['horizontalAccuracy']=geoposition.attribute(PySide2.QtPositioning.QGeoPositionInfo.HorizontalAccuracy) # горизонтальная ошибка в метрах
    geo_pos_dict['time']=geoposition.timestamp()
    return geo_pos_dict
def getValueFromDict(params_dict,key):
    try:
        return params_dict[key]
    except:
        return None
def updateWidgetStyle(widget,new_style_widget):
    count = widget.count()
    item = widget.itemAt(0)
    widget.removeItem(item)
    widget.addWidget(new_style_widget)
class ControlMapViewAxioma(QWidget):
    def __init__(self,parent_form,parent=None):

        super(ControlMapViewAxioma, self).__init__(parent)
        self.__out_db_track=None
        self.__tabSaveTrack=None
        self.__actual_params=None
        self.__style_point_in_map=Style.from_mapinfo('Symbol (85,255,24,"MapInfo Transportation",0,0)')
        self.__style_point_to_save=Style.from_mapinfo('Symbol (60,16711935,9,"MapInfo Symbols",0,0) ')
        self.__style_line_to_save=Style.from_mapinfo('Pen (2, 54, 255)')


        self.__parent_form=parent_form
        self.__source=None
        self.__portSource=None
        self.__parentWin=parent
        self.__path_save_catalog=None
        self.load_ui()
        self.__loadConfig()
        self.window.btn_run_map_gps.clicked.connect(self.__start_process)
        self.window.btn_stop_map_gps.clicked.connect(self.__stop_process)
        self.window.pb_save_property.clicked.connect(self.__save_property)
        default_index_time_interval=1
        config_time_delta_update=getValueFromDict(self.__actual_params,"interval_update")
        if config_time_delta_update is not None:
            index_iterval=self.window.cmb_time_interval.findText(config_time_delta_update)
            if index_iterval>=0:
                default_index_time_interval=index_iterval
        self.window.cmb_time_interval.setCurrentIndex(default_index_time_interval)
        self.__pb_style_db_point = axipy.StyledButton(self.__style_point_in_map, self)
        self.window.wg_point_style.addWidget(self.__pb_style_db_point)
        self.__initSave()
        ''' Тестовое создание Animate Layer'''
        cs=CoordSystem.from_prj('1, 104')
        self.__animate_layer=AxiAnimateLayer("GPS",cs)
        #self.window.cmb_time_interval.currentIndexChanged.connect(self.__change_interval)
        '''
        style_point_mi='Symbol (85,255,24,"MapInfo Transportation",0,30)'
        self.__animate_layer.setStyle(style_point_mi)
        active_map_view= view_manager.mapviews[0]
        self.__animate_layer.addLayerToMap(active_map_view)
        '''
        self.__initListMap()
    def setParentForm(self,form_gps):
        ''' Установка родительской формы
        Нужна для взаимодействия с остальными Tabs ( можно использовать и сигналы )
         '''
        self.__parent_form=form_gps
    def load_ui(self):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "controlMapView.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window  = loader.load(ui_file,self.__parentWin)
        ui_file.close()
    def __initSave(self):
        ''' Инициализируем контрол сохранения наблюдений'''
        isSaveData=False
        defaultIsSave=getValueFromDict(self.__actual_params,'save_data')
        if defaultIsSave is not None:
            self.window.grbx_save.setChecked(defaultIsSave)
            #self.window.grbx_save.setEnabled(defaultIsSave)

        if self.__path_save_catalog is None:
            home_path=Path.home()
            self.__path_save_catalog=os.path.join(home_path,default_name_catalog)
        self.__pb_style_save = axipy.StyledButton(self.__style_point_to_save, self)
        path_db_for_save=getValueFromDict(self.__actual_params,"save_to_db")
        if path_db_for_save is not None and Path(path_db_for_save).exists():
            self.__path_save_catalog=path_db_for_save
        self.window.ln_path_catalog.setText(self.__path_save_catalog)
        type_obj_save=getValueFromDict(self.__actual_params,"type_obj_track")
        if type_obj_save is not None:
            if type_obj_save=='point':
                self.window.cmb_type_obj.setCurrentIndex(0)
            else:
                self.window.cmb_type_obj.setCurrentIndex(0)
        else:
            self.window.cmb_type_obj.setCurrentIndex(0)
        self.window.wg_style_save.addWidget(self.__pb_style_save)
        self.window.cmb_type_obj.currentTextChanged.connect(self.__change_type_obj)
    def setParamSource(self,param_source):
        if self.__portSource is not None:
            self.__portSource.close()
        self.__portSource = QSerialPort()
        self.__portSource.setBaudRate( param_source['baudRates'])
        self.__portSource.setPortName(param_source['port'])

        self.__portSource.setDataBits(dataBits(param_source['DataBits']))
        self.__portSource.setParity( parity(param_source['Parity']))
        self.__portSource.setStopBits( stopBits(param_source['stopBits']) )
        self.__portSource.setFlowControl(  flowControl(param_source['FlowControl']))
        status_port=self.__portSource.open(QtCore.QIODevice.ReadOnly)
        #if status_port:
        self.window.btn_run_map_gps.setEnabled(status_port)
        if status_port:
            if self.__source is not None:
                self.__source.stopUpdates()
                self.__source.positionUpdated.disconnect()
                #self.__source.error.disconnect()
            else:
                self.__source=QNmeaPositionInfoSource(QNmeaPositionInfoSource.RealTimeMode)
            self.__source.setDevice(self.__portSource)
            self.__source.positionUpdated.connect(self.__coordUpdated)
            #self.__source.error.connect(self.__errorCoordUpdated)
    def __coordUpdated(self, pos):
        x_gps=pos.coordinate().longitude()
        y_gps=pos.coordinate().latitude()
        speed=pos.attribute(PySide2.QtPositioning.QGeoPositionInfo.GroundSpeed) # скорость в м/сек
        direction=pos.attribute(PySide2.QtPositioning.QGeoPositionInfo.Direction) #Азимут в градусах
        horizontalAccuracy=pos.attribute(PySide2.QtPositioning.QGeoPositionInfo.HorizontalAccuracy) # горизонтальная ошибка в метрах
        satellite_time=pos.timestamp()
        str_time=satellite_time.toString("h:m:s dd.MM.yy")
        ''' Обнавляем данные в панели информации'''
        self.window.ln_date_time.setText(str_time)
        self.window.ln_speed.setText("{:.1f}".format(speed*3.6))
        self.window.ln_longitude.setText("{:.5f}".format(x_gps))
        self.window.ln_latitude.setText("{:.5f}".format(y_gps))
        self.window.ln_azimut.setText("{:.1f}".format(direction))
        self.window.ln_erorr.setText("{:.1f}".format(horizontalAccuracy))
        self.__animate_layer.updatePoint(x_gps,y_gps,-direction)
        ''' Записываем данные в таблицу трека '''
        if self.__isSaveToTab:
            dict_geopos=geoPositionToDict(pos)
            self.__tabSaveTrack.addPoint(dict_geopos)

    def __errorCoordUpdated(self,err):
        jkl=2
    def __change_interval(self,index):
        if self.__source is None:
            return
        interval_update=int(self.window.cmb_time_interval.currentText())*1000 #Таймаут милисекундах секундах
        self.__source.requestUpdate(interval_update)
        self.__source.setUpdateInterval(interval_update)
    def __start_process(self):
        ''' Устнавливаем свойства animate слою ( на котором будет отображатся позиция)'''
        self.__animate_layer.setStyle(self.__pb_style_db_point.style())
        name_sel_map=self.window.cmb_mapviews.currentText()
        map_view_gps=list(filter(lambda x: x.title==name_sel_map, view_manager.mapviews))
        self.__animate_layer.addLayerToMap(map_view_gps[0])
        ''' Данные сохранять в таблицу '''
        self.__isSaveToTab=self.window.grbx_save.isChecked()
        if self.__isSaveToTab:
            ''' Настраиваем сохранение в таблицу '''
            self.__initWriteTrackData()
        ''' Запуск процесса сбора данных GPS'''
        interval_update=int(self.window.cmb_time_interval.currentText())*1000 #Таймаут милисекундах секундах
        self.__source.requestUpdate(interval_update)
        self.__source.setUpdateInterval(interval_update)
        self.window.btn_stop_map_gps.setEnabled(True)
        self.window.btn_run_map_gps.setEnabled(False)
        self.__source.startUpdates()
    def __initWriteTrackData(self):
        ''' Инициализируем таблицу для записи данных трека'''
        path_db=self.window.ln_path_catalog.text()
        if self.__out_db_track is not None:
            self.__out_db_track.close()
        self.__out_db_track=DataSpatialContainer(path_db)
        id_typeObject=self.window.cmb_type_obj.currentIndex()
        isViewInMap=self.window.ch_view_in_map.isChecked()
        if id_typeObject==0:
            ''' Track Point '''
            self.__tabSaveTrack=factoryTableGpsPoint(self.__out_db_track,self.__pb_style_save.style())
        else:
            name_layer_tab=None
            if self.__tabSaveTrack is not None and isinstance(self.__tabSaveTrack,TableGpsTrack):
                name_layer_tab=self.__tabSaveTrack.axiTable.name
            self.__tabSaveTrack=factoryTableGpsTrack(self.__out_db_track,name_layer_tab,self.__pb_style_save.style())
        ''' Добавляем слой трека в активную карту '''
        self.__layerTrackView=GpsTracSaveData(self.__tabSaveTrack,self.__animate_layer.activeMapView)
        self.__parent_form.setEnabledPortForm(False)
    def __stop_process(self):
        if self.__source is None:
            return
        self.__source.stopUpdates()
        self.window.btn_stop_map_gps.setEnabled(False)
        self.window.btn_run_map_gps.setEnabled(True)
        self.__parent_form.setEnabledPortForm(True)
    def __initListMap(self):
        ''' Список активных карт '''
        self.window.cmb_mapviews.clear()
        for map_v in view_manager.mapviews:
            self.window.cmb_mapviews.addItem(map_v.title)
        default_index_map=0
        config_active_map=getValueFromDict(self.__actual_params,"interval_update")
        if config_active_map is not None:
            index_iterval=self.window.cmb_mapviews.findText(config_active_map)
            if index_iterval>=0:
                default_index_map=index_iterval
        self.window.cmb_mapviews.setCurrentIndex(default_index_map)

    def __change_type_obj(self):
        index_type=self.window.cmb_type_obj.currentIndex()
        if index_type==0:
            self.__style_line_to_save=self.__pb_style_save.style()
            self.__pb_style_save=axipy.StyledButton(self.__style_point_to_save, self)
        else:
            self.__style_point_to_save=self.__pb_style_save.style()
            self.__pb_style_save=axipy.StyledButton(self.__style_line_to_save, self)
        #self.__pb_style_save.update()
        #self.window.wg_style_save.update()
        #count = self.window.wg_style_save.count()
        item = self.window.wg_style_save.itemAt(0)
        self.window.wg_style_save.removeItem(item)
        self.window.wg_style_save.addWidget(self.__pb_style_save)
    def __save_property(self):
        ''''
        Сохранение настроек рабочего режима
        '''
        path_base_path=os.path.dirname(__file__)
        path_base_path=os.path.join(path_base_path,'config_gps_map.json')
        params={}
        params['interval_update']=self.window.cmb_time_interval.currentText()
        params['style_gps_point']=self.__pb_style_db_point.style().to_mapinfo()
        params['map_for_view']=self.window.cmb_mapviews.currentText()
        params['save_data']=self.window.grbx_save.isChecked()
        params['save_to_db']=self.window.ln_path_catalog.text()
        if self.window.cmb_type_obj.currentIndex()==0:
            params['type_obj_track']='point'
        else:
            params['type_obj_track']='line'
        params['style_point_map']=self.__style_point_to_save.to_mapinfo()
        params['style_point_map']=self.__style_line_to_save.to_mapinfo()
        with open(path_base_path, 'w', encoding='utf8') as json_file:
            json.dump(params, json_file, ensure_ascii=False)
    def __loadConfig(self):
        ''' загрузка сохраненых настроек'''
        path_base_path=os.path.dirname(__file__)
        path_base_path=os.path.join(path_base_path,'config_gps_map.json')
        if not Path(path_base_path).exists():
            return
        with open(path_base_path, 'r', encoding='utf8') as config_map_file:
            self.__actual_params = json.load(config_map_file)
        if self.__actual_params is None:
            return

        mi_str_style_gps=self.__actual_params['style_gps_point']
        if mi_str_style_gps is not None:
            self.__style_point_in_map=Style.from_mapinfo(mi_str_style_gps)
















