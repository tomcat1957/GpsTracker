from time import sleep

from axipy import attr, CoordSystem, provider_manager, Style, MapView, Layer, Point, Feature, Pnt

from .axiSymbol import AxiSymbol


class AxiAnimateLayer:
    ''' Псевдо анимационный слой'''
    def __init__(self,name="GPS",cs=None):
        self.__name_layer=name
        self.__createTable(cs)
        self.__layer = Layer.create(self.__table)
        self.__layer.title=self.__name_layer
    def __createTable(self,cs=None):
        if cs is None:
            self.__cs=CoordSystem.from_prj('1, 104')
        else:
            self.__cs=cs
        definition = {
            'src': '',
            'schema': attr.schema(
                attr.integer('id'),
                coordsystem=self.__cs
            )
            ,
            'hidden': True
        }
        self.__table= provider_manager.create(definition) # type: Table
    def setStyle(self,style_object):
        self.__base_style_axi=AxiSymbol(style_object)

        if isinstance(style_object,str):
            self.__base_style=Style.from_mapinfo(style_object)
            jkl=0
        else:
            self.__base_style=style_object
    @property
    def activeMapView(self):
        return self.__base_map_view
    def addLayerToMap(self,active_map:MapView):
        ''' Добавляем слой к карте'''
        isExist=self.__existLayerInMap(active_map.map)
        if isExist:
            return
        self.__source_map_title=active_map.title
        self.__base_map_view=active_map

        #self.__layer.data_changed.connect(self.__update_data_layer)

        count_layer=self.__base_map_view.map.layers.count
        self.__base_map_view.map.layers.add(self.__layer)
        self.__base_map_view.map.layers.move(count_layer,0)
        self.__base_map_view.widget.windowTitleChanged.connect(self.__restore_win_title)
        self.__base_map_view.title=self.__source_map_title
    def updatePoint(self,x,y,angle=0):
        point = Point(x, y,self.__cs)
        cur_style=self.__base_style_axi.getStyle(angle)
        fpoint = Feature(
            geometry=point,
            style=cur_style
        )
        self.__table.restore()
        self.__table.insert([fpoint])
        ''' Проверяем точка попадает в bound карты'''
        isEqCoordSys=self.__base_map_view.coordsystem ==self.__cs
        if isEqCoordSys:
            if not self.__base_map_view.scene_rect.contains(Pnt(x,y)):
                ''' Точка вышла за пределы карты'''
                ''' Устанавливаем новый центр карты '''
                self.__base_map_view.center=(x,y)
        else:
            point_map=point.reproject(self.__base_map_view.coordsystem)
            if not self.__base_map_view.scene_rect.contains(Pnt(point_map.x,point_map.y)):
                ''' Точка вышла за пределы карты'''
                ''' Устанавливаем новый центр карты '''
                self.__base_map_view.center=(point_map.x,point_map.y)
        '''
        self.__updateLayer=False
        
        while not self.__updateLayer:
            sleep(10)
        '''
    def __update_data_layer(self):
        self.__updateLayer=True
    def __existLayerInMap(self,map):
        layers_name=list(filter(lambda x: x.title==self.__name_layer, map.layers))
        if len(layers_name)>0:
            return True
        return False
    def __restore_win_title(self,title_new):
        self.__base_map_view.title=self.__source_map_title
