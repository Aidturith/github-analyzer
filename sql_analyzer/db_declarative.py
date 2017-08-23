# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


#def compress_data(data):
#    return base64.b64encode(zlib.compress(bytes(data, 'utf8')))

#def decompress_data(data):
#    return zlib.decompress(base64.b64decode(data))


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return (False, instance)
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return (True, instance)


class Search(Base):
    __tablename__ = 'searches'
    
    id              = Column(Integer, primary_key=True)
    query_type      = Column(String, index=True)
    file_extension  = Column(String)
    file_size_min   = Column(Integer)
    file_size_max   = Column(Integer)
    finished        = Column(Boolean, default=False)
    
    count = Column(Integer)
    
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return "<Search(query='{}', count='{}', created='{}')>".format(self.github_format(),
                                                                       self.count,
                                                                       self.time_created)
    
    def github_format(self):
        return u'{} in:file extension:{} size:{}..{}'.format(self.query_type,
                                                             self.file_extension,
                                                             self.file_size_min,
                                                             self.file_size_max)


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    
    def __repr__(self):
        return "<User(name='{}')>".format(self.name)


class Repo(Base):
    __tablename__ = 'repositories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)
    
    def __repr__(self):
        return "<Repo(name='{}')>".format(self.name)

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    hash = Column(String, index=True)
    path = Column(String)
    
    repo_id = Column(Integer, ForeignKey('repositories.id'))
    repo = relationship(Repo)
    
    search_id = Column(Integer, ForeignKey('searches.id'))
    search = relationship(Search)
    
    databases = relationship('Database', secondary='database_file', backref='File')
    tables = relationship('Table', secondary='table_file', backref='File')
    fields = relationship('Field', secondary='field_file', backref='File')
    
    def __repr__(self):
        return "<File(hash='{}', path='{}')>".format(self.hash, self.path)


class Database(Base):
    __tablename__ = 'databases'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    count = Column(Integer, default=1)
    
    files = relationship(File, secondary='database_file', backref='Database')
    
    def __repr__(self):
        return "<DB(name='{}', count='{}')>".format(self.name, self.count)

class DatabaseFile(Base):
    __tablename__ = 'database_file'
    
    id = Column(Integer, primary_key=True)
    
    database_id = Column(Integer, ForeignKey('databases.id'))
    database = relationship(Database, backref=backref("databases_files", cascade="all, delete-orphan"))
    
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship(File, backref=backref("databases_files", cascade="all, delete-orphan"))


class Table(Base):
    __tablename__ = 'tables'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    count = Column(Integer, default=1)
    
    db_id = Column(Integer, ForeignKey('databases.id'))
    db = relationship(Database)
    
    files = relationship(File, secondary='table_file', backref='Table')
    
    def __repr__(self):
        return "<Table(name='{}', type='{}')>".format(self.name)

class TableFile(Base):
    __tablename__ = 'table_file'
    
    id = Column(Integer, primary_key=True)
    
    table_id = Column(Integer, ForeignKey('tables.id'))
    table = relationship(Table, backref=backref("tables_files", cascade="all, delete-orphan"))
    
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship(File, backref=backref("tables_files", cascade="all, delete-orphan"))


class Field(Base):
    __tablename__ = 'fields'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    count = Column(Integer, default=1)
    #column_type = Column(String)
    #value = Column(String)
    
    table_id = Column(Integer, ForeignKey('tables.id'))
    table = relationship(Table)
    
    files = relationship(File, secondary='field_file', backref='Field')
    
    def __repr__(self):
        #return "<Field(name='{}', value='{}')>".format(self.name, self.value)
        return "<Field(name='{}')>".format(self.name)

class FieldFile(Base):
    __tablename__ = 'field_file'
    
    id = Column(Integer, primary_key=True)
    
    field_id = Column(Integer, ForeignKey('fields.id'))
    field = relationship(Field, backref=backref("fields_files", cascade="all, delete-orphan"))
    
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship(File, backref=backref("columns_files", cascade="all, delete-orphan"))


'''
class ColumnType(Base):
    __tablename__ = 'columns_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    
    column_id = Column(Integer, ForeignKey('columns.id'))
    column = relationship(Column)
    
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship(File)
    
    def __repr__(self):
        return "<ColumnType(name='{}')>".format(self.name)

class ColumnValue(Base):
    __tablename__ = 'columns_values'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    
    column_id = Column(Integer, ForeignKey('columns.id'))
    column = relationship(Column)
    
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship(File)
    
    def __repr__(self):
        return "<ColumnValue(name='{}')>".format(self.name)
'''

class Anomaly(Base):
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True)
    sql_query = Column(Text, index=True)
    
    search_id = Column(Integer, ForeignKey('searches.id'))
    search = relationship(Search)
    
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship(File)
    
    def __repr__(self):
        return "<Anomaly(sql_query='{}')>".format(self.sql_query)

#engine = create_engine('sqlite:///:memory:', echo=True)
#Base.metadata.create_all(engine)

#test_user = User(name=u'test')
#print(test_user.name)
#print(test_user.id)
