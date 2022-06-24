import os

import axipy
from PySide2.QtGui import QIcon
from axipy import AxiomaPlugin, state_manager

from .ui.DlgFormGps import dlgFromGps
from .ui.docWidget import AxiDocWidget, addDoc, existDocWidget


class Plugin(AxiomaPlugin):
    def load(self):
        self.__form_gps=None
        self.__gps__doc=None
        self.__observer_map_view=None
        ''' Наблюдатель за открытыми картами '''
        self.__observer_map_view=state_manager.find(axipy.da.DefaultKeys.MapView)
        if self.__observer_map_view is not None:
            self.__observer_map_view.changed.connect(self.__change_map_view)
        local_file_icon=os.path.join(os.path.dirname(os.path.realpath(__file__)),'ui', 'satellite_32.png')
        self.__action = self.create_action('GpsTracker',
                                           icon=local_file_icon, on_click=self.__run_gps,
                                           enable_on = axipy.da.DefaultKeys.MapView)
        position = self.get_position("Дополнительно", "Действия")
        position.add(self.__action)

    def __change_map_view(self):
        val=self.__observer_map_view.value()
        jkl=0
    def __run_gps(self):
        mainwindowAxi=axipy.app.mainwindow.qt_object()
        if self.__form_gps is None:
            self.__form_gps=dlgFromGps()
        if self.__gps__doc is None:
            self.__gps__doc=AxiDocWidget(self.__form_gps,"Gps","GpsTracker",QIcon(),mainwindowAxi)
            addDoc(mainwindowAxi,self.__gps__doc)

        self.__gps__doc.show()
        jkl=0


