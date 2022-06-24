from pathlib import Path


from osgeo import gdal, ogr, osr

FIELD_TYPES_MAP={
    'int':ogr.OFTInteger,
    'float':ogr.OFTReal,
    'str':ogr.OFTString,
    'date':ogr.OFTDate,
    'date_time':ogr.OFTDateTime,
    'time':ogr.OFTTime
}

class DataSpatialContainer:
    def __init__(self,path_db):
        self.__ds=None
        self.__base_path=path_db
        self.__driver_name="GPKG"
    def open(self,path_file,nameDriver="GPKG",isNew=True):
        ''' Открываем каталог
        если isNew=True создаем новый
        '''
        if Path(path_file).exists() and isNew:
            self.__driver=ogr.GetDriverByName(nameDriver)
            self.__ds=self.__driver.CreateDataSource(path_file)
        else:
            if not Path(path_file).exists():
                self.__driver=ogr.GetDriverByName(nameDriver)
                self.__ds=self.__driver.CreateDataSource(path_file)
            else:
                self.__ds=ogr.Open(path_file,1)
        if self.__ds is None:
            return False
        self.__base_path=path_file
        self.__driver_name=nameDriver
        return True
    @property
    def pathDb(self):
        return self.__base_path
    def createTable(self,name_tab,schema,cs_def,type_obj=None):
        if self.__ds is None and self.__base_path is not None:
            self.open(self.__base_path,self.__driver_name,False)
        if self.__ds is None and self.__base_path is  None:
            self.open(self.__base_path,self.__driver_name,False)
        gdal_FieldDefs=[]
        gdal_cs=None
        for item in schema:
            name=item['name']
            type=item['type']
            gdal_type=None
            size_field=0

            if type=="str":
                size_field=item['size']
                field_def_str=ogr.FieldDefn(name,ogr.OFTString)
                field_def_str.SetWidth(size_field)

                gdal_FieldDefs.append(field_def_str)
                continue
            try:
                gdal_type=FIELD_TYPES_MAP[type]
            except:
                continue
            gdal_FieldDefs.append(ogr.FieldDefn(name,gdal_type))
        ''' Добавляем колонку стиля линий '''
        field_def_style=ogr.FieldDefn("MI_STYLE",ogr.OFTString)
        field_def_style.SetWidth(254)
        gdal_FieldDefs.append(field_def_style)
        ''' Формируем координатную систему GDAL'''
        srs =  osr.SpatialReference()
        if cs_def is None:
            srs.ImportFromEPSG(4326)
        else:
            if cs_def['type']=='epsg':
                srs.ImportFromEPSG(int(cs_def['value']))
            if cs_def['type']=='proj':
                srs.ImportFromProj4(cs_def['value'])
            if cs_def['type']=='wkt':
                srs.ImportFromWkt(cs_def['value'])
        type_obj_spatial=ogr.wkbUnknown
        if type_obj is not None:
            if type_obj=='point':
                type_obj_spatial=ogr.wkbPoint
        layer=self.__ds.CreateLayer(name_tab,srs,type_obj_spatial)
        for field in gdal_FieldDefs:
            layer.CreateField(field)
        layer=None
        return True
    def close(self):
        if self.__ds is not None:
            self.__ds=None











