# -*- coding: utf-8 -*-

import re

class SearchConfig():
    
    # TODO grant, alter user, create user > sql specific
    Q_CREATE_DB     = u'"create database"'
    Q_DROP_DB       = u'"drop database"'
    Q_CREATE_TABLE  = u'"create table"'
    Q_ALTER_TABLE   = u'"alter table"'
    Q_DROP_TABLE    = u'"drop table"'
    Q_SELECT        = u'select from where'
    Q_INSERT        = u'"insert into" values'
    Q_UPDATE        = u'update set'
    Q_DELETE        = u'"delete from"'
    
    REGEX_CREATE_DB     = re.compile(r'create\s*database\s*([^;#]{,200})', re.IGNORECASE)
    REGEX_DROP_DB       = re.compile(r'drop\s*database\s*([^;#]{,200})', re.IGNORECASE)
    REGEX_CREATE_TABLE  = re.compile(r'create\s*table\s*(.*)\s*\(([^;#]+)\)', re.IGNORECASE)
    REGEX_ALTER_TABLE   = re.compile(r'', re.IGNORECASE)
    REGEX_DROP_TABLE    = re.compile(r'', re.IGNORECASE)
    REGEX_SELECT        = re.compile(r'', re.IGNORECASE)
    REGEX_INSERT        = re.compile(r'', re.IGNORECASE)
    REGEX_UPDATE        = re.compile(r'', re.IGNORECASE)
    REGEX_DELETE        = re.compile(r'', re.IGNORECASE)
    
    REGEX_TABLE_DEF = re.compile(r'(.+)\s+([^,]+)', re.IGNORECASE)
    
    QUERIES = {Q_CREATE_DB:     REGEX_CREATE_DB,
               Q_DROP_DB:       REGEX_DROP_DB,
               Q_CREATE_TABLE:  REGEX_CREATE_TABLE,
               Q_ALTER_TABLE:   REGEX_ALTER_TABLE,
               Q_DROP_TABLE:    REGEX_DROP_TABLE,
               Q_SELECT:        REGEX_SELECT,
               Q_INSERT:        REGEX_INSERT,
               Q_UPDATE:        REGEX_UPDATE,
               Q_DELETE:        REGEX_DELETE,
               }
    
    EXT_PHP = u'php'
    EXT_JS = u'js'
    EXT_SQL = u'sql'
    EXT_C = u'c'
    EXT_H = u'h'
    EXT_JAVA = u'java'
    EXT_PY = u'py'
    EXT_HTML = u'html'
    EXT_TXT = u'txt'
    EXT_XML = u'xml'
    EXT_CS = u'cs'
    EXT_CPP = u'cpp'
    EXT_CSS = u'css'
    
    EXTENSIONS = [EXT_PHP,
                  EXT_JS,
                  EXT_SQL,
                  EXT_C,
                  EXT_H,
                  EXT_JAVA,
                  EXT_PY,
                  EXT_HTML,
                  EXT_TXT,
                  EXT_XML,
                  EXT_CS,
                  EXT_CPP,
                  EXT_CSS]
    
    MIN_SIZE = 10
    MAX_SIZE = 500000
    
    def __init__(self):
        self.file_size = 0
        self.step = 1
    
    def query_generator(self):
        self.file_size = 0
        for file_extension in self.EXTENSIONS:
            for query_type in self.QUERIES:
                while self.file_size < self.MAX_SIZE:
                    self.file_size += self.step + 1
                    param_tupple = (query_type, file_extension, self.file_size - self.step, self.file_size)
                    yield (param_tupple, u'{} in:file extension:{} size:{}..{}'.format(query_type,
                                                                                       file_extension,
                                                                                       self.file_size - self.step,
                                                                                       self.file_size))
    
    def query_generator_test(self):
        self.file_size = 1000
        for file_extension in [self.EXT_SQL]:
            for query_type in [self.Q_CREATE_DB]:
                while self.file_size < 2000:
                    self.file_size += self.step
                    param_tupple = (query_type, file_extension, self.file_size - self.step, self.file_size)
                    yield (param_tupple, u'{} in:file extension:{} size:{}..{}'.format(query_type,
                                                                                       file_extension,
                                                                                       self.file_size - self.step,
                                                                                       self.file_size))

#search = SearchConfig()
#for q in search.query_generator():
#    print(q)
