__version__ = "v0.6.0"

import os

# import cudatext api functions
from cudatext import *
import cudatext_cmd as cmds

# import SQLTools api
from .SQLToolsAPI import Utils
from .SQLToolsAPI.Storage import Storage, Settings
from .SQLToolsAPI.Connection import Connection
from .SQLToolsAPI.History import History

USER_FOLDER                  = None
DEFAULT_FOLDER               = None
SETTINGS_FILENAME            = None
SETTINGS_FILENAME_DEFAULT    = None
CONNECTIONS_FILENAME         = None
CONNECTIONS_FILENAME_DEFAULT = None
QUERIES_FILENAME             = None
QUERIES_FILENAME_DEFAULT     = None
settings                     = None
queries                      = None
connections                  = None
history                      = None

OUTPUT_TO_FILE = 'sqltools_file_output'


def _log(s):
    print('SQL Tools:', s)

def startPlugin():
    global USER_FOLDER, DEFAULT_FOLDER, SETTINGS_FILENAME, SETTINGS_FILENAME_DEFAULT, CONNECTIONS_FILENAME, CONNECTIONS_FILENAME_DEFAULT, QUERIES_FILENAME, QUERIES_FILENAME_DEFAULT, settings, queries, connections, history

    USER_FOLDER = app_path(APP_DIR_SETTINGS)
    DEFAULT_FOLDER = os.path.dirname(__file__)

    SETTINGS_FILENAME            = os.path.join(USER_FOLDER, "cuda_sqltools_settings.json")
    SETTINGS_FILENAME_DEFAULT    = os.path.join(DEFAULT_FOLDER, "cuda_sqltools_settings.json")
    CONNECTIONS_FILENAME         = os.path.join(USER_FOLDER, "cuda_sqltools_connections.json")
    CONNECTIONS_FILENAME_DEFAULT = os.path.join(DEFAULT_FOLDER, "cuda_sqltools_connections.json")
    QUERIES_FILENAME             = os.path.join(USER_FOLDER, "cuda_sqltools_savedqueries.json")
    QUERIES_FILENAME_DEFAULT     = os.path.join(DEFAULT_FOLDER, "cuda_sqltools_savedqueries.json")

    settings    = Settings(SETTINGS_FILENAME, default=SETTINGS_FILENAME_DEFAULT)
    queries     = Storage(QUERIES_FILENAME, default=QUERIES_FILENAME_DEFAULT)
    connections = Settings(CONNECTIONS_FILENAME, default=CONNECTIONS_FILENAME_DEFAULT)
    history     = History(settings.get('history_size', 100))

    Connection.setTimeout(settings.get('thread_timeout', 15))
    Connection.setHistoryManager(history)

    _log("Plugin loaded")


def getConnections():
    connectionsObj = {}

    options = connections.get('connections', {})
    for name, config in options.items():
        connectionsObj[name] = Connection(name, config, settings=settings.all(), commandClass='Command')

    return connectionsObj


def loadDefaultConnection():
    default = connections.get('default', None)
    if not default:
        return
    _log('Default connection set to: %s' % default)
    return default


def output(content, panel=None):
    if not panel:
        panel = getOutputPlace()

    if panel == LOG_PANEL_OUTPUT:
        ed.cmd(cmds.cmd_ShowPanelOutput)
        app_log(LOG_CLEAR, '', panel=panel)
        for s in content.splitlines():
            app_log(LOG_ADD, s, 0, panel=panel)
        return

    toNewTab(content)


def toNewTab(content, discard=None):
    file_open('')
    ed.set_prop(PROP_TAB_TITLE, 'SQL result')
    ed.set_text_all(str(content))


def getOutputPlace():
        if settings.get('show_result_on_window', True):
            return OUTPUT_TO_FILE

        return LOG_PANEL_OUTPUT


def getSelection():
    #api always gets string
    return ed.get_text_sel()


class ST:
    conn = None
    tables = None
    functions = None
    columns = None
    connectionList = None
    autoCompleteList = []

    @staticmethod
    def bootstrap():
        ST.connectionList = getConnections()
        ST.checkDefaultConnection()

    @staticmethod
    def checkDefaultConnection():
        default = loadDefaultConnection()
        if not default:
            return
        try:
            ST.conn = ST.connectionList.get(default)
            ST.loadConnectionData()
        except Exception:
            _log("Invalid connection setted")

    @staticmethod
    def loadConnectionData(tablesCallback=None, columnsCallback=None, functionsCallback=None):
        if not ST.conn:
            return

        def tbCallback(tables):
            setattr(ST, 'tables', tables)
            if tablesCallback:
                tablesCallback()

        def colCallback(columns):
            setattr(ST, 'columns', columns)
            if columnsCallback:
                columnsCallback()

        def funcCallback(functions):
            setattr(ST, 'functions', functions)
            if functionsCallback:
                functionsCallback()

        ST.conn.getTables(tbCallback)
        ST.conn.getColumns(colCallback)
        ST.conn.getFunctions(funcCallback)

    @staticmethod
    def setConnection(selected, menu, tablesCallback=None, columnsCallback=None, functionsCallback=None):
        if selected is None:
            return

        selected = menu[selected].split('\t')[0]
        ST.conn = ST.connectionList[selected]

        ST.loadConnectionData(tablesCallback, columnsCallback, functionsCallback)

        _log('Connection {0} selected'.format(ST.conn))

    @staticmethod
    def selectConnection(tablesCallback=None, columnsCallback=None, functionsCallback=None):

        ST.connectionList = getConnections()
        if len(ST.connectionList) == 0:
            msg_box('You need to setup your connections first.', MB_OK + MB_ICONWARNING)
            return

        menu = []
        for conn in ST.connectionList.values():
            menu.append(
                conn.name+'\t'+
                conn.info()
                )
        menu.sort()

        selected = dlg_menu(MENU_LIST, '\n'.join(menu))
        ST.setConnection(selected, menu, tablesCallback, columnsCallback, functionsCallback)

    @staticmethod
    def selectTable(callback):
        if len(ST.tables) == 0:
            msg_box('Your database has no tables.', MB_OK + MB_ICONWARNING)
            return

        selected = dlg_menu(MENU_LIST, '\n'.join(ST.tables))
        callback(selected)

    @staticmethod
    def selectFunction(callback):
        if not ST.functions:
            msg_box('Your database has no functions.', MB_OK + MB_ICONWARNING)
            return

        selected = dlg_menu(MENU_LIST, '\n'.join(ST.functions))
        callback(selected)


class Command:
    def __init__(self):
        self.on_start(None)

    def on_start(self, ed_self):
        startPlugin()
        ST.bootstrap()

    def selectConnection(self):
        ST.selectConnection()

    def showRecords(self):

        if not ST.conn:
            ST.selectConnection(tablesCallback=lambda: self.showRecords())
            return

        def cb(selected):
            if selected is None:
                return None
            return ST.conn.getTableRecords(ST.tables[selected], output)

        ST.selectTable(cb)

    def describeTable(self):
        if not ST.conn:
            ST.selectConnection(tablesCallback=lambda: self.describeTable())
            return

        def cb(selected):
            if selected is None:
                return None
            return ST.conn.getTableDescription(ST.tables[selected], output)

        ST.selectTable(cb)

    def describeFunction(self):
        if not ST.conn:
            ST.selectConnection(functionsCallback=lambda: self.describeFunction())
            return

        def cb(selected):
            if selected is None:
                return None
            functionName = ST.functions[selected].split('(', 1)[0]
            return ST.conn.getFunctionDescription(functionName, output)

        # get everything until first occurence of "(", e.g. get "function_name"
        # from "function_name(int)"
        ST.selectFunction(cb)

    def executeQuery(self):
        text = getSelection()
        if not text:
            #get current line
            x0, y0, x1, y1 = ed.get_carets()[0]
            text = ed.get_text_line(y0)
            if not text:
                msg_status('Text not selected/ current line empty')
                return

        if not ST.conn:
            ST.selectConnection(tablesCallback=lambda: ST.conn.execute(text, output))
        else:
            ST.conn.execute(text, output)


    def explainPlan(self):
        text = getSelection()
        if not text:
            #get current line
            x0, y0, x1, y1 = ed.get_carets()[0]
            text = ed.get_text_line(y0)
            if not text:
                msg_status('Text not selected/ current line empty')
                return

        if not ST.conn:
            ST.selectConnection(tablesCallback=lambda: ST.conn.explainPlan([text], output))
        else:
            ST.conn.explainPlan([text], output)


    def formatQuery(self):
        carets = ed.get_carets()
        if len(carets)!=1:
            msg_status('Need single caret')
            return

        text = getSelection()
        all = False
        if not text:
            text = ed.get_text_all()
            if not text: return
            all = True
            
        with_eol = text.endswith('\n')

        text = Utils.formatSql(text, settings.get('format', {}))
        if not text: return
        
        if with_eol and not text.endswith('\n'):
            text += '\n'

        if all:
            ed.set_text_all(text)
            msg_status('SQL Tools: formatted all text')
        else:
            x0, y0, x1, y1 = carets[0]
            if (y1 > y0) or ((y1 == y0) and (x1 >= x0)):
                pass
            else:
                x0, y0, x1, y1 = x1, y1, x0, y0

            ed.set_caret(x0, y0)
            ed.delete(x0, y0, x1, y1)
            ed.insert(x0, y0, text)
            msg_status('SQL Tools: formatted selection')

    def showHistory(self):
        if not ST.conn:
            ST.selectConnection(functionsCallback=lambda: self.showHistory())
            return

        if len(history.all()) == 0:
            msg_status('SQL Tools: History is empty')
            return

        selected = dlg_menu(MENU_LIST, '\n'.join(history.all()))
        if selected is None:
            return None
        return ST.conn.execute(history.get(selected), output)

    def saveQuery(self):
        text = getSelection()
        if not text:
            msg_status('SQL Tools: Text not selected')
            return

        alias = dlg_input('Query alias:', '')
        if alias: #can be None or empty str
            queries.add(alias, text)

    def showSavedQueries(self, mode="list"):
        if not ST.conn:
            ST.selectConnection(functionsCallback=lambda: self.showSavedQueries(mode))
            return

        queriesList = queries.all()
        if len(queriesList) == 0:
            msg_box('No saved queries.', MB_OK + MB_ICONWARNING)
            return

        options = []
        for alias, query in queriesList.items():
            options.append('\t'.join([str(alias), str(query)]))
        options.sort()

        selected = dlg_menu(MENU_LIST, '\n'.join(options))
        if selected is None:
            return None

        param2 = output if mode == "run" else None
        func = ST.conn.execute if mode == "run" else toNewTab

        return func(queriesList.get(options[selected].split('\t')[0]), param2)

    def deleteSavedQuery(self):
        if not ST.conn:
            ST.selectConnection(functionsCallback=lambda: self.deleteSavedQuery())
            return

        queriesList = queries.all()
        if not queriesList:
            msg_box('No saved queries.', MB_OK + MB_ICONWARNING)
            return

        options = []
        for alias, query in queriesList.items():
            options.append('\t'.join([str(alias), str(query)]))
        options.sort()

        selected = dlg_menu(MENU_LIST, '\n'.join(options))
        if selected is None:
            return None
        return queries.delete(options[selected].split('\t')[0])

    def runSavedQuery(self):
        return self.showSavedQueries('run')

    def editConnections(self):
        file_open(CONNECTIONS_FILENAME)

    def editSettings(self):
        file_open(SETTINGS_FILENAME)
