# -*- coding: utf-8 -*-

from sql.search_config import SearchConfig
from web.web_parser import WebParser

from github3 import login

import re
import requests

class GitCrawler():
    
    def __init__(self, username=None, password=None, token=None):
        
        self.search = SearchConfig()
        self.web_parser = WebParser(url='', max_req=3000, per_sec=60.0)
        self.github = login(username, password, token)
    
    def run(self):
        for dict_entry in self.search.query_generator_test():
            query_type, query = dict_entry
            print('>>> {}'.format(query))
            # TODO db stuff
            # test si la query est en base
            # oui: l'enregistrer
            # non: requete suivante
            
            findings = self.github.search_code(query, number=5) # TODO remove
            self.web_parser.throttle.tick()
            
            for i, entry in enumerate(findings):
                #print('repo:\t{}'.format(entry.repository))
                #print('\t{}'.format(entry.path))
                #print('\t{}'.format(entry.html_url))
                #print(len(findings.items))
                self.web_parser.throttle.tick()
                
                url = entry.html_url
                raw_url = url.replace('/blob', '').replace('github.com',
                                                           'raw.githubusercontent.com')
                file_path = entry.path
                repo = entry.repository
                
                # TODO db stuff
                file_content = requests.get(raw_url).text.strip()
                self.web_parser.throttle.tick()
                
                #print(file_content)
                if query_type == self.search.Q_CREATE_DB:
                    for match in re.finditer(self.search.QUERIES[query_type], file_content):
                        self.handle_db_create(match)
                print('\n')
    
    def handle_db_create(self, match):
        # remove quotes, {[, is not exists
        db_name = match.group(1).lower().replace('if not exists', '').strip()
        print('DB: {}'.format(db_name))
        

gc = GitCrawler('aidturith')
gc.run()
