# -*- coding: utf-8 -*-
# author: aidturith
# v0.1

import time
import random

class Throttle():
    
    def __init__(self, max_req, per_sec=1.0, delay_min=0.0, delay_max=0.0):
        self.max_req = max_req
        self.per_sec = per_sec
        self.delay_min = delay_min
        self.delay_max = delay_max
        
        self.begin_t = time.time()
        self.req_count = 0
    
    # TODO mutex for multithreading?
    def tick(self):
        self.req_count += 1
        
        if self.delay_max:
            sleep_t = random.uniform(self.delay_min, self.delay_max)
            time.sleep(sleep_t)
        
        if self.req_count == self.max_req - 1:
            sleep_t = round(self.per_sec - (time.time() - self.begin_t))
            time.sleep(max(0, sleep_t)) # sleep_t can't be negative for sleep_t > per_sec
            self.begin_t = time.time()
            self.req_count = 0

#thr = Throttle(5, per_sec=2.0, delay_min=0.1, delay_max=0.5)
#for i in range(20):
#    print(i)
#    thr.tick()