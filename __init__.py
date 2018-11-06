__version__ = "v0.6.0"

import os

# import CudaText api
from cudatext import *
import cudatext_cmd as cmds

# import SQLTools api
from .SQLToolsAPI import Utils
from .SQLToolsAPI.Storage import Storage, Settings
from .SQLToolsAPI.Connection import Connection
from .SQLToolsAPI.History import History
from .SQLToolsAPI.Completion import Completion

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


def _log(s):

    print('SQL Tools:', s)

def msg_er(s):

    msg_box(s, MB_OK+MB_ICONWARNING)

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

    try:
        settings = Settings(SETTINGS_FILENAME, default=SETTINGS_FILENAME_DEFAULT)
    except:
        settings = None
        _log('Error parsing '+SETTINGS_FILENAME)

    try:
        queries = Storage(QUERIES_FILENAME, default=QUERIES_FILENAME_DEFAULT)
    except:
        queries = None
        _log('Error parsing '+QUERIES_FILENAME)

    try:
        connections = Settings(CONNECTIONS_FILENAME, default=CONNECTIONS_FILENAME_DEFAULT)
    except:
        connections = None
        _log('Error parsing '+CONNECTIONS_FILENAME)

    if settings:
        history     = History(settings.get('history_size', 100))

        Connection.setTimeout(settings.get('thread_timeout', 15))
        Connection.setHistoryManager(history)

    _log("Plugin loaded")


def getConnections():

    connectionsObj = {}

    options = connections.get('connections', {})
    allSettings = settings.all()

    for name, config in options.items():
        connectionsObj[name] = Connection(name, config, settings=allSettings, commandClass='Command')

    return connectionsObj


def loadDefaultConnection():

    default = connections.get('default', None)
    if not default:
        return
    _log('Default connection set to: %s' % default)
    return default


def output(content):

    opt = settings.get('show_result_on_window', False)
    if not opt:
        if settings.get('focus_on_result', False):
            ed.cmd(cmds.cmd_ShowPanelOutput_AndFocus)
        else:
            ed.cmd(cmds.cmd_ShowPanelOutput)

        if settings.get('clear_output', False):
            app_log(LOG_CLEAR, '', panel=LOG_PANEL_OUTPUT)

        for s in content.splitlines():
            app_log(LOG_ADD, s, 0, panel=LOG_PANEL_OUTPUT)

    else:
        toNewTab(content)


def toNewTab(content, discard=None):

    file_open('')
    ed.set_prop(PROP_TAB_TITLE, 'SQL result')
    ed.set_text_all(str(content))


def editor_insert(text):
    
    ed.cmd(cmds.cCommand_TextInsert, text=text)
    

def get_editor_text():

    s = ed.get_text_sel()
    if s:
        return s

    '''
    // Possible options:
    //  "file"      - entire file contents
    //  "paragraph" - text between newlines relative to cursor(s)
    //  "line"      - current line of cursor(s)
    "expand_to": "file",
    '''
    opt = settings.get('expand_to', 'file')

    if opt=='file':
        return ed.get_text_all()
    elif opt=='line':
        x0, y0, x1, y1 = ed.get_carets()[0]
        return ed.get_text_line(y0)
    else:
        _log('Option "expand_to" value "%s" not supported'%opt)
        return ''


class ST:
    connectionList = None
    conn = None
    tables = None
    functions = None
    columns = None
    completion = None

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

        # clear the list of identifiers (in case connection is changed)
        ST.tables = []
        ST.columns = []
        ST.functions = []
        ST.completion = None
        callbacksRun = 0

        if not ST.conn:
            return

        def tbCallback(tables):
            ST.tables = tables
            nonlocal callbacksRun
            callbacksRun += 1
            if callbacksRun == 3:
                ST.completion = Completion(ST.tables, ST.columns, ST.functions, settings=settings)

            if tablesCallback:
                tablesCallback()

        def colCallback(columns):
            ST.columns = columns
            nonlocal callbacksRun
            callbacksRun += 1
            if callbacksRun == 3:
                ST.completion = Completion(ST.tables, ST.columns, ST.functions, settings=settings)

            if columnsCallback:
                columnsCallback()

        def funcCallback(functions):
            ST.functions = functions
            nonlocal callbacksRun
            callbacksRun += 1
            if callbacksRun == 3:
                ST.completion = Completion(ST.tables, ST.columns, ST.functions, settings=settings)

            if functionsCallback:
                functionsCallback()

        callbacksRun = 0
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

        ST.reset_cache(tablesCallback, columnsCallback, functionsCallback)
        _log('Connection {0} selected'.format(ST.conn))


    @staticmethod
    def reset_cache(tablesCallback=None, columnsCallback=None, functionsCallback=None):

        # clear list of identifiers in case connection is changed
        ST.tables = []
        ST.columns = []
        ST.functions = []
        ST.loadConnectionData(tablesCallback, columnsCallback, functionsCallback)

    @staticmethod
    def selectConnection(tablesCallback=None, columnsCallback=None, functionsCallback=None):

        ST.connectionList = getConnections()
        if len(ST.connectionList) == 0:
            msg_er('You need to setup your connections first')
            return

        menu = []
        for conn in ST.connectionList.values():
            menu.append(
                conn.name+'\t'+
                conn.info()
                )
        menu.sort()

        selected = dlg_menu(MENU_LIST, menu, caption='Connections')
        ST.setConnection(selected, menu, tablesCallback, columnsCallback, functionsCallback)

    @staticmethod
    def selectTable(callback):
        if len(ST.tables) == 0:
            msg_er('Your database has no tables')
            return

        selected = dlg_menu(MENU_LIST, ST.tables, caption='Tables')
        callback(selected)

    @staticmethod
    def selectFunction(callback):
        if not ST.functions:
            msg_er('Your database has no functions')
            return

        selected = dlg_menu(MENU_LIST, ST.functions, caption='Functions')
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

        text = get_editor_text()
        if not text:
            msg_status('Text not selected')
            return

        if not ST.conn:
            ST.selectConnection(tablesCallback=lambda: ST.conn.execute(text, output))
        else:
            ST.conn.execute(text, output)


    def explainPlan(self):

        text = get_editor_text()
        if not text:
            msg_status('Text not selected')
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

        text = ed.get_text_sel()
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

        selected = dlg_menu(MENU_LIST, history.all(), caption='History')
        if selected is None:
            return None
        return ST.conn.execute(history.get(selected), output)

    def saveQuery(self):

        text = get_editor_text()
        if not text:
            msg_status('Text not selected')
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
            msg_er('No saved queries')
            return

        options = []
        for alias, query in queriesList.items():
            options.append('\t'.join([str(alias), str(query)]))
        options.sort()

        selected = dlg_menu(MENU_LIST, options, caption='Queries')
        if selected is None:
            return None
        text = queriesList.get(options[selected].split('\t')[0])

        if mode=='run':
            ST.conn.execute(text, output)
        elif mode=='insert':
            editor_insert(text)
        else:
            toNewTab(text, None)

    def deleteSavedQuery(self):

        if not ST.conn:
            ST.selectConnection(functionsCallback=lambda: self.deleteSavedQuery())
            return

        queriesList = queries.all()
        if not queriesList:
            msg_status('SQL Tools: No saved queries')
            return

        options = []
        for alias, query in queriesList.items():
            options.append('\t'.join([str(alias), str(query)]))
        options.sort()

        selected = dlg_menu(MENU_LIST, options, caption='Queries')
        if selected is None:
            return None
        text = options[selected].split('\t')[0]

        return queries.delete(text)

    def runSavedQuery(self):

        return self.showSavedQueries('run')

    def insertSavedQuery(self):

        return self.showSavedQueries('insert')

    def editConnections(self):

        file_open(CONNECTIONS_FILENAME)

    def editSettings(self):

        file_open(SETTINGS_FILENAME)

    def refreshConnData(self):

        if not ST.conn:
            return
        ST.loadConnectionData()
        _log('Refreshed connection data')

    def clearCache(self):

        if not ST.conn:
            return
        ST.reset_cache()
        _log('Cleared cache')
