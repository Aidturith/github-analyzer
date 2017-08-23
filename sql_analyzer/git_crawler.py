# -*- coding: utf-8 -*-

from sql_analyzer.search_config import SearchConfig
from sql_analyzer.db_declarative import (get_or_create,
                                         Base, User, Search, Anomaly, File, Repo,
                                         Database)

from web.parser import WebParser

from github3 import login

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import re
import requests
import gzip
import timeit

from pprint import pprint
import hashlib
from sqlalchemy.sql.expression import exists

class GitCrawler():
    
    def __init__(self, username=None, password=None, token=None):
        self.start_time = timeit.default_timer()
        self.search = SearchConfig()
        self.web_parser = WebParser(url='', max_req=3000, per_sec=2 * 60.0)
        self.github = login(username, password, token)
        
        # database stuff
        # TODO db_config
        engine              = create_engine('sqlite:///:memory:', echo=False)
        #engine              = create_engine('sqlite:///database.db', echo=False)
        Base.metadata.bind  = engine
        DBSession           = sessionmaker(bind=engine)
        self.session        = DBSession()
        
        # TODO only once
        Base.metadata.create_all(engine)
    
    
    def run(self):
        for dict_entry in self.search.query_generator_test():
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
            for i, entry in enumerate(findings):
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
                    with gzip.open('../dump/{}.gz'.format(file_hash), 'wb') as f:
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
                        self.handle_drop_db(match)
                
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
                #print('\n')
            
            # update search count
            search_itm.count = i
            search_itm.finished = True
            
            if search_itm.count == 0:
                self.search.step += 1
            elif search_itm.count > 500:
                self.search.step = max(0, self.search.step - 1)
            print('count: ' + str(search_itm.count))
            print('steps: ' + str(self.search.step))
            #pprint(self.github. rate_limit())
        
        print('Elapsed: {}'.format(timeit.default_timer() - self.start_time))
        #pprint(self.session.query(Search).all())
        pprint(self.session.query(Anomaly).all())
        #pprint(self.session.query(File).all())
        #pprint(self.session.query(User).order_by(User.name).all())
        #pprint(self.session.query(Repo).all())
        pprint(self.session.query(Database).order_by(Database.count).all())
    
    
    def handle_create_db(self, match, search_itm, file_itm):
        #print('db: {}'.format(match.group(0)))
        db_name = match.group(1).lower()
        db_name = db_name.replace('if not exists', '')  # remove statements
        db_name = re.sub(r'(owner) .*', '', db_name)
        db_name = re.sub(r'(with template) .*', '', db_name)
        db_name = re.sub(r'(default) .*', '', db_name)
        db_name = re.sub(r'(character set) .*', '', db_name)
        db_name = re.sub(r'(/\*).*(\*/)', '', db_name)  # remove comments
        db_name = re.sub(r'[\'"`]*', '', db_name)       # remove quotes
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
    
    def handle_drop_db(self, match):
        pass
    
    def handle_create_table(self, match):
        pass
    
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
