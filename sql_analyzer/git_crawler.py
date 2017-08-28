# -*- coding: utf-8 -*-

from sql_analyzer.search_config import SearchConfig
from sql_analyzer.db_declarative import (get_or_create,
                                         Base, User, Search, Anomaly, File, Repo,
                                         Database)

from web.parser import WebParser

from github3 import login
from github3.models import GitHubError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import re
import requests
import gzip
import timeit
import time

from pprint import pprint
import hashlib
from sqlalchemy.sql.expression import exists


class GitCrawler():
    
    def __init__(self, username=None, password=None, token=None):
        self.start_time = timeit.default_timer()
        self.search = SearchConfig()
        self.web_parser = WebParser(url='', max_req=3000, per_sec=2 * 60.0, delay_max=0.01)
        self.github = login(username, password, token)
        
        # database stuff
        # TODO db_config
        #engine              = create_engine('sqlite:///:memory:', echo=False)
        engine              = create_engine('sqlite:///../var/db/database.db', echo=False)
        Base.metadata.bind  = engine
        DBSession           = sessionmaker(bind=engine)
        self.session        = DBSession()
        
        Base.metadata.create_all(engine)
    
    
    def run(self):
            for dict_entry in self.search.query_generator_test():
            break
            param_tupple, query = dict_entry
            query_type, file_extension, file_size_min, file_size_max = param_tupple
            print('>>> {}'.format(query))
            
            created, search_itm = get_or_create(self.session, Search,
                                                query_type=query_type,
                                                file_extension=file_extension,
                                                file_size_min=file_size_min)
            search_itm.file_size_max = file_size_max
            if not created and search_itm.finished:
                continue
            
            findings = self.github.search_code(query)
            self.web_parser.throttle.tick()
            
            i = 0
            while True:
                try:
                    entry = findings.next()
                except StopIteration:
                    break
                except GitHubError as e:
                    print(e)
                    time.sleep(5 * 60.0)
                    continue
                except ConnectionError as e:
                    print(e)
                    time.sleep(5 * 60.0)
                    continue
                    
                
                #print(len(findings.items))
                self.web_parser.throttle.tick()
                
                # results from lookup
                file_url = entry.html_url.replace('/blob', '').replace('github.com',
                                                                       'raw.githubusercontent.com')
                file_path = entry.path
                repository = entry.repository
                
                
                # register user and repo
                user_name, repo_name = str(repository).split('/')
                created, user_itm = get_or_create(self.session, User, name=user_name)
                created, repo_itm = get_or_create(self.session, Repo, name=repo_name)
                repo_itm.user = user_itm
                self.session.commit()
                
                
                #print('lol3')
                #print(file_url)
                # get file
                # content.decode('utf8')
                file_content = u''
                try:
                    file_content = requests.get(file_url).text.strip()
                    self.web_parser.throttle.tick()
                except requests.exceptions.ConnectionError:
                    print('requests error!')
                    continue
                
                # write file on disk
                file_hash = hashlib.md5(file_content.encode('utf8')).hexdigest()
                if not self.session.query(exists().where(File.hash==file_hash)).scalar():
                    with gzip.open('../var/dump/{}.gz'.format(file_hash), 'wb') as f:
                        f.write(bytes(file_content, 'utf8'))
                
                # register file in db
                file_itm = File(hash=file_hash, path='{}/{}'.format(repository, file_path))
                file_itm.repo = repo_itm
                file_itm.search = search_itm
                self.session.add(file_itm)
                self.session.commit()
                
                
                #print(file_content)
                if query_type == self.search.Q_CREATE_DB:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_create_db(match, search_itm, file_itm)
                
                elif query_type == self.search.Q_DROP_DB:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_drop_db(match, search_itm, file_itm)
                
                elif query_type == self.search.Q_CREATE_TABLE:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_create_table(match)
                
                elif query_type == self.search.Q_ALTER_TABLE:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_alter_table(match)
                
                elif query_type == self.search.Q_DROP_TABLE:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_drop_table(match)
                
                elif query_type == self.search.Q_SELECT:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_select(match)
                
                elif query_type == self.search.Q_INSERT:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_insert(match)
                
                elif query_type == self.search.Q_UPDATE:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_update(match)
                
                elif query_type == self.search.Q_DELETE:
                    for match in re.finditer(self.search.QUERIES[query_type],
                                             file_content):
                        self.handle_delete(match)
                
                i += 1
                #print('\n')
            
            # update search count
            search_itm.count = i
            search_itm.finished = True
            
            if search_itm.count == 0:
                self.search.step = self.search.step * 2
            elif search_itm.count > 500:
                self.search.step = max(1, self.search.step - 1)
            print('count: ' + str(search_itm.count))
            print('steps: ' + str(self.search.step))
            #pprint(self.github. rate_limit())
        
        print('Elapsed: {}'.format(timeit.default_timer() - self.start_time))
        #pprint(self.session.query(Search).all())
        pprint(self.session.query(Anomaly).all())
        #pprint(self.session.query(File).all())
        #pprint(self.session.query(User).order_by(User.name).all())
        #pprint(self.session.query(Repo).all())
        #pprint(self.session.query(Database).order_by(Database.count).all())
    
    
    def handle_create_db(self, match, search_itm, file_itm):
        proba_dic = {
            'mysql': 0,
            'postgres': 0,
            'mssql': 0,
            'oracle': 0,
            'db2': 0,
            }
        
        print('db: {}'.format(match.group(0)))
        db_name = match.group(1).lower()
        
        db_name, proba = re.subn(r'(if not exists)', '', db_name)
        proba_dic['mysql'] += proba
        
        db_name, proba = re.subn(r'(default character set)\s*=?.*', '', db_name)
        proba_dic['mysql'] += proba
        
        db_name, proba = re.subn(r'(character set)\s*=?.*', '', db_name)
        proba_dic['mysql'] += proba
        proba_dic['oracle'] += proba
        
        db_name, proba = re.subn(r'(with owner|owner)\s*=?.*', '', db_name)
        proba_dic['postgres'] += proba
        
        db_name, proba = re.subn(r'(with template|template)\s*=?.*', '', db_name)
        proba_dic['postgres'] += proba
        
        #db_name = re.sub(r'(default) .*', '', db_name)
        #db_name = re.sub(r'(character set) .*', '', db_name)
        db_name, proba = re.subn(r'(/\*!).+(\*/)', '', db_name) # remove comments
        proba_dic['mysql'] += proba
        
        
        db_name, proba = re.subn(r'\n+.*', '', db_name) # remove line feeds
        db_name, proba = re.subn(r'[\'"`]*', '', db_name) # remove quotes
        db_name = db_name.strip()
        print('DB: {}'.format(db_name))
        
        if ' ' in db_name or not db_name:
            get_or_create(self.session, Anomaly, sql_query=match.group(0),
                          search=search_itm, file=file_itm)
        else:
            created, db_itm = get_or_create(self.session, Database, name=db_name)
            if not created:
                db_itm.count += 1
            db_itm.search = search_itm
            db_itm.file = file_itm
            self.session.commit()
    
    def handle_drop_db(self, match, search_itm, file_itm):
        print('db: {}'.format(match.group(0)))
        db_name = match.group(1).lower()
        db_name = db_name.replace('if exists', '')              # remove statements
        db_name = re.sub(r'(\/\*).*(\*\/)', '', db_name)        # remove comments
        db_name = re.sub(r'[\'"`]*', '', db_name)               # remove quotes
        db_name = db_name.strip()
        print('DB: {}'.format(db_name))
        
        if not re.match(r'^[a-z0-9\-_]+$', db_name):
        #if ' ' in db_name or not db_name:
            get_or_create(self.session, Anomaly, sql_query=match.group(0),
                          search=search_itm, file=file_itm)
        else:
            created, db_itm = get_or_create(self.session, Database, name=db_name)
            if not created:
                db_itm.count += 1
            db_itm.search = search_itm
            db_itm.file = file_itm
            self.session.commit()
    
    def handle_create_table(self, match):
        # dont lookup if test is mentioned in the repo path
        # split table names: db.table
        # lookup create table a, use a to define db
        # or lookup db in the same repo?
        print('tbl: {}'.format(match.group(0)))
        
        table_name = match.group(1).lower()
        table_name = re.sub(r'(/\*).*(\*/)', '', table_name)  # remove comments
        table_name = re.sub(r'[\'"`]*', '', table_name)       # remove quotes
        table_name = table_name.strip()
        #print('TBL: {}'.format(table_name))
        
        table_definition = match.group(2).lower().split(',')
        #print('DEF: {}'.format(table_definition))
        for line in table_definition:
            try:
                field_name, field_type = re.split('\s+', line.strip())
                print('name & type: {} & {}'.format(field_name, field_type))
            except ValueError:
                pass
        
        
        '''
        if not re.match(r'^[a-z0-9\-_]+$', db_name):
        #if ' ' in db_name or not db_name:
            get_or_create(self.session, Anomaly, sql_query=match.group(0),
                          search=search_itm, file=file_itm)
        else:
            created, db_itm = get_or_create(self.session, Database, name=db_name)
            if not created:
                db_itm.count += 1
            db_itm.search = search_itm
            db_itm.file = file_itm
            self.session.commit()
        '''
    
    def handle_alter_table(self, match):
        pass
    
    def handle_drop_table(self, match):
        pass
    
    def handle_select(self, match):
        pass
    
    def handle_insert(self, match):
        pass
    
    def handle_update(self, match):
        pass
    
    def handle_delete(self, match):
        pass
    

username = u'aidturith'
password = input(u'password for user {}: '.format(username))
gc = GitCrawler(username, password)
gc.run()
