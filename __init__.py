import sys
import os
import shutil
from cudatext import *

dirpath = os.path.dirname(__file__)
if dirpath not in sys.path:
    sys.path.append(dirpath)

import SQLToolsModels as STM

class ST:
    conn = None
    history = []
    tables = []
    functions = []
    columns = []
    connectionList = {}
    autoCompleteList = []

    @staticmethod
    def setAttrIfNotEmpty(attr, value):
        if isinstance(value, list) and len(value) == 0:
            return
        setattr(ST, attr, value)

    @staticmethod
    def showConnectionMenu():
        ST.connectionList = STM.Settings.getConnections()
        if len(ST.connectionList) == 0:
            msg_box('You need to setup your connections first.', MB_OK)
            return

        menu = []
        for conn in ST.connectionList.values():
            menu.append('\t'.join(conn.toQuickPanel()))
        menu.sort()

        selected = dlg_menu(MENU_LIST, '\n'.join(menu))
        if selected is None:
            return

        selected = menu[selected].split('\t')[0]
        ST.conn = ST.connectionList[selected]
        STM.Log.debug('Connection {0} selected'.format(ST.conn))


class Command:
    def executeQuery(self):
        if not ST.conn:
            self.showConnectionMenu()

        # continue execution

        pass
    def shoeHistory(self):
        pass
    def describeFunction(self):
        pass
    def saveQuery(self):
        pass
    def selectConnection(self):
        self.showConnectionMenu()

    def describeTable(self):
        pass
    def deleteSavedQuery(self):
        pass
    def showRecords(self):
        pass
    def formatQuery(self):
        pass
    def showSavedQueries(self):
        pass
    def runSavedQuery(self):
        pass

    def editConnections(self):
        file_open(STM.SettingsManager.file(STM.Const.CONNECTIONS_FILENAME))

    def editSettings(self):
        file_open(STM.SettingsManager.file(STM.Const.SETTINGS_FILENAME))

