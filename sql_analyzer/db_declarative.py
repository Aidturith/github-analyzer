# -*- coding: utf-8 -*-

import zlib
import base64

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative.api import declared_attr
from sqlalchemy.sql.schema import Index

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
    query_type      = Column(String)
    file_extension  = Column(String)
    file_size       = Column(Integer)
    
    count = Column(Integer)
    
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return "<Search(query='{}', count='{}', created='{}')>".format(self.github_format(),
                                                                       self.count,
                                                                       self.time_created)
    
    def github_format(self):
        return u'{} in:file extension:{} size:{}'.format(self.query_type,
                                                         self.file_extension,
                                                         self.file_size)


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    
    def __repr__(self):
        return "<User(name='{}')>".format(self.name)


class Repo(Base):
    __tablename__ = 'repositories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    def __repr__(self):
        return "<Repo(name='{}')>".format(self.name)

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    path = Column(String)
    
    def __repr__(self):
        return "<File(hash='{}', path='{}')>".format(self.hash, self.path)


'''
class Database(Base):
    __tablename__ = 'databases'
    
    id = Column(Integer, primary_key=True)

class Column(Base):
    __tablename__ = 'columns'
    
    id = Column(Integer, primary_key=True)

class Field(Base):
    __tablename__ = 'fields'
    
    id = Column(Integer, primary_key=True)
'''

class Anomaly(Base):
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True)
    sql_query = Column(Text)
    
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
