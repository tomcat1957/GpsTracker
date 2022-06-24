from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDockWidget


def addDoc(main_windows,doc_wiget):
    main_windows.addDockWidget(Qt.RightDockWidgetArea,doc_wiget)
    #main_windows.addPanel(doc_wiget)
    doc_wiget.setFeatures(QDockWidget.AllDockWidgetFeatures)
    doc_wiget.show()
    doc_wiget.raise_()
    doc_wiget.setFocus()
    listWidgets = main_windows.findChildren(QDockWidget)
    list_doc_widgets=[]
    for q_doc in listWidgets:
        area=main_windows.dockWidgetArea(q_doc)


        print(q_doc.windowTitle() )
        if area==Qt.RightDockWidgetArea:
            if not (q_doc==doc_wiget):
                list_doc_widgets.append(q_doc)
            print("ok")
    for right_widget in list_doc_widgets:
        main_windows.tabifyDockWidget(doc_wiget,right_widget)
#mainwindowAxi.tabifyDockWidget(w_doc,list_doc_widgets[0])
#mainwindowAxi.tabifyDockWidget(w_doc,list_doc_widgets[1])
    doc_wiget.setVisible(True)
    doc_wiget.setFocus()
    doc_wiget.raise_()
def existDocWidget(main_windows,s_widget):
    listWidgets = main_windows.findChildren(QDockWidget)
    for q_doc in listWidgets:
        if q_doc==s_widget:
            return True
    return False
def existByTitle(main_windows,title_widget):
    listWidgets = main_windows.findChildren(QDockWidget)
    for q_doc in listWidgets:
        if q_doc.windowTitle()==title_widget:
            return q_doc
    return None
def DelDocWidget(main_windows,s_widget):
    if existDocWidget(main_windows,s_widget):
        main_windows.removeDockWidget(s_widget)
        s_widget.deleteLater()
    ex_widget=existByTitle(main_windows,s_widget.windowTitle())
    if ex_widget is not None:
        main_windows.removeDockWidget(ex_widget)
        ex_widget.deleteLater()
class AxiDocWidget(QDockWidget):
    __child_widget=None
    def __init__(self,widget, obj_name, title, icon=QIcon(), parent=None):
        super().__init__(title, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setObjectName(obj_name)
        self.setWidget(widget)
        self.__child_widget=widget
        self.toggleViewAction().setObjectName(obj_name + "Toggle")
        self.toggleViewAction().setIcon(icon)
    def showEvent(self, QShowEvent):
        print("View Doc")
    # self.__child_widget.setParent(self)
    # self.__child_widget.exec_()
    def focusInEvent(self, event):
        print('Got focus')

    def focusOutEvent(self, event):
        print('Lost focus')

