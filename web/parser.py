# -*- coding: utf-8 -*-

import logging
import requests

from .throttle import Throttle

class WebParser():
    
    # user agents
    UA_FIREFOX_55 = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'
    
    # TODO proxy params, throttle params
    def __init__(self, url, user_agent=UA_FIREFOX_55, proxy=None,
                 max_req=10, per_sec=1.0, delay_min=0.0, delay_max=0.0, **data):
        # proxy format : http://user:pass@www.proxy.com:80
        
        # THROTTLE ENGINE
        self.throttle = Throttle(max_req, per_sec, delay_min, delay_max)
        
        # REQUEST STUFF
        self.url = url
        self.data = data
        self.headers = {
            'User-Agent': user_agent,
            'Referer': url,
        }
        self.proxy = proxy
        self.s = requests.Session()
    
    def post_request(self):
        self.throttle.tick()
        logging.debug('post data: {}'.format(self.data))
        return self.s.post(self.url, self.data, headers=self.headers, proxies=self.proxy)
    
    def get_input(self):
        pass
    
    def get_ajax_url(self):
        pass
    