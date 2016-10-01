VERSION = "v0.0.1"

import re
import os
import shutil
import json

from cudatext import *

# Regular expression for comments
comment_re = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)

def parse_json(filename):
    """ Parse a JSON file
        First remove comments and then use the json module package
        Comments look like :
            // ...
        or
            /*
            ...
            */
    """

    with open(filename) as f:
        content = ''.join(f.readlines())

        ## Looking for comments
        match = comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)

        # Return json file
        return json.loads(content)

class SettingsManager:
    @staticmethod
    def default(file):
        return os.path.join(os.path.dirname(__file__), file)

    @staticmethod
    def file(file):
        path = os.path.join(app_path(APP_DIR_SETTINGS), file)
        if not os.path.isfile(path):
            shutil.copy(SettingsManager.default(file), path)
        return path

    @staticmethod
    def asJson(file):
        return parse_json(SettingsManager.file(file))

class Settings:

    @staticmethod
    def get(key, default=None):
        keys = key.split('.')
        settings = SettingsManager.asJson(Const.SETTINGS_FILENAME)
        value = settings
        for key in keys:
            value = value.get(key, None)

        return value

    @staticmethod
    def getConnections():
        connections = {}
        options = SettingsManager.asJson(Const.CONNECTIONS_FILENAME)
        options = options.get('connections')

        for connection in options:
            connections[connection] = Connection(
                connection, options[connection])

        return connections

class Const:
    SETTINGS_EXTENSION = "json"
    SETTINGS_FILENAME = "SQLToolsSettings.{0}".format(SETTINGS_EXTENSION)
    CONNECTIONS_FILENAME = "SQLToolsConnections.{0}".format(SETTINGS_EXTENSION)
    USER_QUERIES_FILENAME = "SQLToolsSavedQueries.{0}".format(
        SETTINGS_EXTENSION)


class Log:

    @staticmethod
    def debug(message):
        if not Settings.get('debug', False):
            return
        print ("SQLTools %s: %s" % (VERSION, message))


class Connection:

    def __init__(self, name, options):

        self.cli = Settings.get('cli')[
            options['type']]
        cli_path = shutil.which(self.cli)

        if cli_path is None:
            msg_box((
                "'{0}' could not be found by Sublime Text.\n\n" +
                "Please set the '{0}' path in your SQLTools settings " +
                "before continue.").format(self.cli), MB_OK)
            return

        self.rowsLimit = SettingsManager.asJson(
            Const.SETTINGS_FILENAME).get('show_records.limit', 50)
        self.options = options
        self.name = name
        self.type = options['type']
        self.host = options['host']
        self.port = options['port']
        self.username = options['username']
        self.database = options['database']

        if 'encoding' in options:
            self.encoding = options['encoding']

        if 'password' in options:
            self.password = options['password']

        if 'service' in options:
            self.service = options['service']

    def __str__(self):
        return self.name

    def _info(self):
        return 'DB: {0}, Connection: {1}@{2}:{3}'.format(
            self.database, self.username, self.host, self.port)

    def toQuickPanel(self):
        return [self.name, self._info()]

    # @staticmethod
    # def killCommandAfterTimeout(command):
    #     timeout = SettingsManager.asJson(
    #         Const.SETTINGS_FILENAME).get('thread_timeout', 5000)
    #     sublime.set_timeout(command.stop, timeout)

    # @staticmethod
    # def loadDefaultConnectionName():
    #     default = SettingsManager.asJson(
    #         Const.CONNECTIONS_FILENAME).get('default', False)
    #     if not default:
    #         return
    #     Log.debug('Default database set to ' + default +
    #               '. Loading options and auto complete.')
    #     return default

    # def getTables(self, callback):
    #     query = self.getOptionsForSgdbCli()['queries']['desc']['query']

    #     def cb(result):
    #         return Utils.getResultAsList(result, callback)

    #     Command.createAndRun(self.builArgs('desc'), query, cb)

    # def getColumns(self, callback):

    #     def cb(result):
    #         return Utils.getResultAsList(result, callback)

    #     try:
    #         query = self.getOptionsForSgdbCli()['queries']['columns']['query']
    #         Command.createAndRun(self.builArgs('columns'), query, cb)
    #     except Exception:
    #         pass

    # def getFunctions(self, callback):

    #     def cb(result):
    #         return Utils.getResultAsList(result, callback)

    #     try:
    #         query = self.getOptionsForSgdbCli()['queries'][
    #             'functions']['query']
    #         Command.createAndRun(self.builArgs(
    #             'functions'), query, cb)
    #     except Exception:
    #         pass

    # def getTableRecords(self, tableName, callback):
    #     query = self.getOptionsForSgdbCli()['queries']['show records'][
    #         'query'].format(tableName, self.rowsLimit)
    #     Command.createAndRun(self.builArgs('show records'), query, callback)

    # def getTableDescription(self, tableName, callback):
    #     query = self.getOptionsForSgdbCli()['queries']['desc table'][
    #         'query'] % tableName
    #     Command.createAndRun(self.builArgs('desc table'), query, callback)

    # def getFunctionDescription(self, functionName, callback):
    #     query = self.getOptionsForSgdbCli()['queries']['desc function'][
    #         'query'] % functionName
    #     Command.createAndRun(self.builArgs('desc function'), query, callback)

    # def execute(self, queries, callback):
    #     queryToRun = ''

    #     for query in self.getOptionsForSgdbCli()['before']:
    #         queryToRun += query + "\n"

    #     if isinstance(queries, str):
    #         queries = [queries]

    #     for query in queries:
    #         queryToRun += query + "\n"

    #     queryToRun = queryToRun.rstrip('\n')
    #     windowVars = sublime.active_window().extract_variables()
    #     if isinstance(windowVars, dict) and 'file_extension' in windowVars:
    #         windowVars = windowVars['file_extension'].lstrip()
    #         unescapeExtension = SettingsManager.asJson(
    #             Const.SETTINGS_FILENAME).get('unescape_quotes')
    #         if windowVars in unescapeExtension:
    #             queryToRun = queryToRun.replace(
    #                 "\\\"", "\"").replace("\\\'", "\'")

    #     Log.debug("Query: " + queryToRun)
    #     History.add(queryToRun)
    #     Command.createAndRun(self.builArgs(), queryToRun, callback)

    # def builArgs(self, queryName=None):
    #     cliOptions = self.getOptionsForSgdbCli()
    #     args = [self.cli]

    #     if len(cliOptions['options']) > 0:
    #         args = args + cliOptions['options']

    #     if queryName and len(cliOptions['queries'][queryName]['options']) > 0:
    #         args = args + cliOptions['queries'][queryName]['options']

    #     if isinstance(cliOptions['args'], list):
    #         cliOptions['args'] = ' '.join(cliOptions['args'])

    #     cliOptions = cliOptions['args'].format(**self.options)
    #     args = args + shlex.split(cliOptions)

    #     Log.debug('Usgin cli args ' + ' '.join(args))
    #     return args

    # def getOptionsForSgdbCli(self):
    #     return Settings.get('cli_options')[self.type]
