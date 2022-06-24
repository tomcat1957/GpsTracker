from axipy import PointStyle, Style
class AxiSymbol:
    ''' Надстройка на точечным символом
    для обеспечения формирования динамического угла поворота
    '''
    def __init__(self,style_symbol):
        if isinstance(style_symbol,str):
            self.__mi_style=style_symbol
        else:
            self.__mi_style=PointStyle.to_mapinfo(style_symbol)
        self.__prepreStyle()
    def __prepreStyle(self):
        i1,i2=self.__mi_style.find('('), self.__mi_style.find(')')
        str_parm=self.__mi_style[i1+1:i2]
        self.__params=str_parm.split(",")
        self.__rotate=False
        if len(self.__params)==6:
            del self.__params[5]
            self.__rotate=True
        self.__base_style=PointStyle.from_mapinfo(self.__mi_style)
    def getStyle(self,angle_rot=0.0):
        if not self.__rotate:
            return self.__base_style
        angle=angle_rot
        if angle<0:
            angle=360+angle_rot
        ''' Создаем новый стиль с углом поворота'''
        '''
        str_params_style=",".join(self.__params)
        str_rotate="{0:.2f}".format(angle)
        str_rotate=str_rotate.replace(",",".")
        str_params_style=str_params_style+","+str_rotate
        str_params_style="Symbol ("+str_params_style+")"
        symbol_style_axi=Style.from_mapinfo(str_params_style)
        print(symbol_style_axi.to_mapinfo())
        '''
        symbol_style_axi=PointStyle.create_mi_font(int(self.__params[0]),int(self.__params[1]),int(self.__params[2]),self.__params[3],int(self.__params[4]),angle)
        return symbol_style_axi

