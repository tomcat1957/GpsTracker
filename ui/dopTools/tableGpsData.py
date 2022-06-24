from datetime import datetime

import axipy
from axipy import provider_manager, Point, Feature, Pnt, LineString, Layer


class TableGpsPoint:
    def __init__(self,style,table):
        self.__style=style
        self.__table=table
        self.__count=0
    def addPoint(self,geopos):
        point = Point(geopos['lon'],geopos['lat'],self.__table.coordsystem)
        feature = Feature({}, geometry=point, style=self.__style)
        feature['fid']=self.__count
        feature['lon']=geopos['lon']
        feature['lat']=geopos['lat']
        str_time_sat=geopos['time'].toString("h:m:s dd.MM.yy")
        feature['satelitte_time']=str_time_sat
        self.__table.insert([feature])
        self.__count=self.__count+1
    def setAxiTable(self,table):
        self.__table=table
    @property
    def axiTable(self):
        return self.__table
class TableGpsTrack:
    def __init__(self,style,table):
        self.__style=style
        self.__table=table
        self.__curent_obj=None
        self.__count_points=0
        self.__getCountRecordInTable()
    def __getCountRecordInTable(self):
        sql_row_max="Select Max (fid) as max_id From "+self.__table.name
        table_query=axipy.app.mainwindow.catalog.query_hidden(sql_row_max)
        features=list(table_query.items())
        self.__curent_id=features[0].get('max_id')
        if self.__curent_id is None :
            self.__curent_id=0
        if isinstance(self.__curent_id,str):
            self.__curent_id=0
        self.__curent_id=self.__curent_id+1
        table_query.close()
        return
    def __selectLastFeature(self):
        ''' Выбираем последнию вставленную запись '''
        sql="Select * From "+self.__table.name+" where fid="+str(self.__curent_id)
        table_query=axipy.app.mainwindow.catalog.query_hidden(sql)
        features=list(table_query.items())
        ft=features[0]
        table_query.close()
        return ft
    def addPoint(self,geoposition):
        self.__count_points=self.__count_points+1
        if self.__count_points==1:
            self.__first_geoposition=geoposition
            return
        feature=None
        if self.__count_points==2:
            ''' Создаем полилинию '''
            pnt_1=Pnt(self.__first_geoposition['lon'],self.__first_geoposition['lat'])
            pnt_2=Pnt(geoposition['lon'],geoposition['lat'])
            self.__curent_obj=LineString([pnt_1,pnt_2],cs=self.__table.coordsystem)

            feature = Feature({}, geometry=self.__curent_obj, style=self.__style)
            #str_time_sat=self.__first_geoposition['time'].strftime("%d-%m-%Y %H:%M:%S")
            str_time_sat=self.__first_geoposition['time'].toString("%d-%m-%Y %H:%M:%S")
            feature['fid']=self.__curent_id
            feature['start_satelitte_time']=str_time_sat
            str_time_sat=geoposition['time'].toString("%d-%m-%Y %H:%M:%S")
            feature['end_satelitte_time']=str_time_sat
            self.__table.insert([feature])
            #fts=list(self.__table.items())
            *_, last=self.__table.items()
            self.__last_id=last.id
            return

        pnt_cur=Pnt(geoposition['lon'],geoposition['lat'])
        self.__curent_obj.points.append(pnt_cur)
        #feature = Feature({}, geometry=self.__curent_obj, style=self.__style)
        #ft_update = Feature({}, geometry=self.__curent_obj, style=self.__style,id=self.__last_id)
        #ft_update=self. __selectLastFeature()
        ft_update=list(self.__table.itemsByIds([self.__last_id]))[0]

        str_time_sat=self.__first_geoposition['time'].toString("%d-%m-%Y %H:%M:%S")
        ft_update['start_satelitte_time']=str_time_sat
        str_time_sat=geoposition['time'].toString("%d-%m-%Y %H:%M:%S")
        ft_update['end_satelitte_time']=str_time_sat
        ft_update.geometry=self.__curent_obj
        self.__table.update(ft_update)

    @property
    def axiTable(self):
        return self.__table

def factoryTableGpsTrack(dbContainer,name_table_exist,style_point,cs=None):
    if name_table_exist is not None:
        tableAxi=provider_manager.openfile(dbContainer.pathDb, dataobject=name_table_exist)

        tableGps=TableGpsTrack(style_point,tableAxi)
        return tableGps
    now = datetime.now()
    str_time= now.strftime("%H_%M_%S")
    str_date=now.strftime("%d%m%Y")
    table_name="gps_track_"+str_time+"_"+str_date
    att_def=[]
    #att_def.append({'name':'id_track','type':'int'})
    att_def.append({'name':'start_satelitte_time','type':'date_time'})
    att_def.append({'name':'end_satelitte_time','type':'date_time'})

    isOk=dbContainer.createTable(table_name,att_def,None,type_obj='linestring')
    dbContainer.close()
    tableAxi=provider_manager.openfile(dbContainer.pathDb, dataobject=table_name)

    tableGps=TableGpsTrack(style_point,tableAxi)
    return tableGps





def factoryTableGpsPoint(dbContainer,style_point,cs=None):
    ''' Создаем таблицу для сохранения точечных объектов наблюдений'''
    now = datetime.now()
    str_time= now.strftime("%H_%M_%S")
    str_date=now.strftime("%d%m%Y")
    table_name="gps_point_"+str_time+"_"+str_date
    att_def=[]

    att_def.append({'name':'satelitte_time','type':'date_time'})
    att_def.append({'name':'lon','type':'float'})
    att_def.append({'name':'lat','type':'float'})
    isOk=dbContainer.createTable(table_name,att_def,None,type_obj='point')
    dbContainer.close()
    tableAxi=provider_manager.openfile(dbContainer.pathDb, dataobject=table_name)

    tableGps=TableGpsPoint(style_point,tableAxi)
    return tableGps
class GpsTracSaveData:
    def __init__(self,table,active_map_view,isView=True):
        self.__table_track=table
        self.__active_map_view=active_map_view
        self.__layer=Layer.create(table.axiTable)
        self.__add_to_map(isView)
    def __add_to_map(self,isView):
        layer_exist=list(filter(lambda layer: layer.title==self.__layer.title, self.__active_map_view.map.layers))
        if len(layer_exist)>0:
            return
        self.__active_map_view.map.layers.add(self.__layer)
        count_layer=self.__active_map_view.map.layers.count

        self.__active_map_view.map.layers.move(count_layer-1,1)


