import sys
import os

dirpath = os.path.dirname(__file__)
if dirpath not in sys.path:
    sys.path.append(dirpath)

from cudatext import *
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
    def bootstrap():
        ST.connectionList = STM.Settings.getConnections()
        ST.checkDefaultConnection()

    @staticmethod
    def setAttrIfNotEmpty(attr, value):
        if isinstance(value, list) and len(value) == 0:
            return
        setattr(ST, attr, value)

    @staticmethod
    def loadConnectionData():
        if not ST.conn:
            return

        ST.conn.getTables(
            lambda tables: ST.setAttrIfNotEmpty('tables', tables))
        ST.conn.getColumns(
            lambda columns: ST.setAttrIfNotEmpty('columns', columns))
        ST.conn.getFunctions(
            lambda functions: ST.setAttrIfNotEmpty('functions', functions))

    @staticmethod
    def setConnection(selected, menu):
        if selected is None:
            return

        selected = menu[selected].split('\t')[0]
        ST.conn = ST.connectionList[selected]
        STM.Log.debug('Connection {0} selected'.format(ST.conn))

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
        ST.setConnection(selected, menu)

    @staticmethod
    def checkDefaultConnection():
        default = STM.Connection.loadDefaultConnectionName()
        if not default:
            return
        try:
            ST.conn = ST.connectionList.get(default)
            ST.loadConnectionData()
        except Exception:
            STM.Log.debug("Invalid connection setted")

    @staticmethod
    def getOutputPanel(output):
        app_log(LOG_SET_PANEL, LOG_PANEL_OUTPUT)
        app_log(LOG_CLEAR, '')
        app_log(LOG_ADD, output, 0)

class Command:
    def __init__(self):
        ST.bootstrap()
        STM.Log.debug("plugin loaded")

    def executeQuery(self):
        if not ST.conn:
            ST.showConnectionMenu()
            return

        query = STM.Selection.get()

        ST.conn.execute(query, ST.getOutputPanel)

    def showHistory(self):
        pass

    def describeFunction(self):
        pass

    def saveQuery(self):
        pass

    def selectConnection(self):
        ST.showConnectionMenu()

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
