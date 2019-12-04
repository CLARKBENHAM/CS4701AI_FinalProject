# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 07:34:03 2019
@author: Clark Benham
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random
import timeit
import math
import re
import requests
import pickle
import os
from datetime import datetime, date, timedelta
import time
from pandas.compat import StringIO

import subprocess
import sys
import importlib.util
def check_install(package):#doesn't work?
    spec = importlib.util.find_spec(package)
    if spec == None:
        subprocess.call([sys.executable, "-m", "pip", "install", package])
        #should check return of subprocess
        print("Downloaded", package)
check_install('tika')
from tika import parser
import os
from urllib.request import urlretrieve

#download selenium
check_install('selenium')
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import collections
from selenium.webdriver import ActionChains

check_install('pygu')
import pyautogui as pygu
#login.txt: stored in dir surrounding Final_Project
# linkedin_email = 'my_email'
# linkedin_pwrd = 'my_password'
f = open("..\login.txt", 'r')
for i in f.readlines():
    exec(i)

chromedriver_path = 'C:\Program Files\chromedriver_win32\chromedriver'
#%%
class MyDriver(webdriver.Chrome):
    def __init__(self, time_delay = 10):
        opts = webdriver.ChromeOptions().add_argument("--incognitio")#isn't nessisary since selenium opens a 'fresh' webpage each time
        webdriver.Chrome.__init__(self, 
                                  executable_path = chromedriver_path,
                                  options =opts)
        self._time_delay = time_delay
        self.wait = WebDriverWait(self, self.time_delay)

    def __del__(self):#closes window when garbage collected; not when runtime ends
        #import gc
        #gc.collect() to close windows, method isn't nessisary
        self.close()
        super(MyDriver, self).__del__()#webdriver doesn't have del method!??

    def update(self):#update to the current version of MyDriver
        "Use this function if modify a class function and want persistant object to use new function"
        self.__class__ = MyDriver
      
    #Changing time_delay kills my Kernel for some reason(Spyder specific?)
    @property
    def time_delay(self):
        return self._time_delay
    
    @time_delay.setter
    def time_delay(self, new_delay):
        "Change the maximal amount of time to wait"
        self.time_delay = new_delay
        self.wait = WebDriverWait(self, self.time_delay)
    
    @staticmethod 
    def ignore_missing(default, func, *args, **kwargs):
        if default is not None:
            try:
                return func(*args, **kwargs)
            except (NoSuchElementException, TimeoutException):
                return default
        else:
            return func(*args, **kwargs)
    
    #wanted abbreviations
    def fx(self, path, default = None):
        "default is value to return instead of raising exception"
        return MyDriver.ignore_missing(default, self.find_element_by_xpath, path)
    
    def fx_text(self, path, default = None):
        "Text of element at path; or default"
        fn = lambda p: self.find_element_by_xpath(p).text
        return MyDriver.ignore_missing(default, fn, path)
    
    def fxs(self,path, default = []):
        #find_elements doesn't raise exception, just returns empty list
        return self.find_elements_by_xpath(path) or default

    def wu(self, path, default = None):
        fn = lambda i: self.wait.until(EC.element_to_be_clickable((By.XPATH, i)))
        return MyDriver.ignore_missing(default, fn, path)
    
    def goto_linkedin(self):
        self.get("https://www.linkedin.com")
        self.fx('/html/body/nav/a[3]').click()
        self.fx('//input[@aria-label="Email or Phone"]').send_keys(linkedin_email)
        self.fx('//input[@aria-label="Password"]').send_keys(linkedin_pwrd)
        self.fx('//button[@aria-label="Sign in"]').click()
        #will sometimes get a confirmation request, todo
      
#delays should be learned    
    def click_connect_delay(self):
        return None
        time.sleep(random.random()*5)
  
    def new_search_delay(self):
        return None
        time.sleep(random.random()*3)

    def try_connect(self, search_page = True):
        "Try to click on connect(But are rate limited). Gives up if not possible"
        if search_page:
            c = self.wu('//button[contains(@aria-label, "Connect with ")]')
            i = 0
            while i < 5:#tries 5 times
                #need to add if claueses for if a 3rd connection and navitage to/from their page. Grib
                try:
                    c.click()
                    break 
                except:
                    try:
                        self.click_connect_delay()
                        c = self.wu('//button[contains(@aria-label, "Connect with ")]')
                        ActionChains(self).move_to_element(c).click().perform()
                        c.click()
                    except:
                        i += 1
            else:
                c = self.wu('//button[contains(@aria-label, "Connect with ")]')
                print(f"Failed on: {c.find_element_by_xpath('./../../..').text}")
        else:#Profile Page, 3rd degree connection
            driver.fx('//span[text()="More…"]').click()
            driver.fx('//span[text()="Connect"]').click()
            driver.fx('//span[text()="Send now"]').click()
        
        
    def connect_with(self, names, message = None):
        "Given a list of names, search for each name, and send message to all people on first page them when try to connect"
        inpt = self.fx('//input[@aria-label="Search"]')
        for n in names:
            inpt.clear()
            inpt.send_keys(f"{n}"u'\ue007')
            self.new_search_delay()
            while True:#pause till get results of search
                try:
                    self.fx("//div[@class='search-no-results__container']")#no results
                    break
                except:
                    self.send_keys("u'\ue00c")
                    try:
                        self.wu('//li[@class="search-result search-result__occluded-item ember-view"]')
                        break
                    except:
                        pass
            while self.fxs('//button[contains(@aria-label, "Connect with ")]'):
                try:
                    self.try_connect()
                    if message is not None:
                        self.wu('//span[text()="Add a note"]').click()
                        self.wu('//textarea[@name="message"]').send_keys(message)
                        self.wu('//span[text()="Send invitation"]').click()
                    else:
                        self.wu('//span[text()="Send now"]').click()
                    self.click_connect_delay()
                except TimeoutException:
                    time.sleep(8)
                    pass

    def target_reward_function(self, prev_invites = 0, prev_pending=0):
        "The True reward function, all locaiton information is encapsulated by webdriver page"
        #pages are no where near standardized in xpath(try CSS?)
        # return 20*int('in' in driver.current_url)
        if prev_invites < self.get_invite_counts():
            return 20*(self.get_inivte_counts())
        elif len(self.fxs("/html/body/div[5]/div[4]/div[3]/div/div/div/div/div/section[1]/div[1]/span"))>0:#isSendInvite=true
            txt = self.fx("/html/body/div[5]/div[4]/div[3]/div/div/div/div/div/section[1]/div[1]/span").text
            if re.match(r'Your invitation to [a-zA-Z]+ [a-zA-Z]+ was sent.', txt):
                return 20
        elif self.get_may_know_pending() > prev_pending:
            return 20*(self.get_may_know_pending() - prev_pending)
        else:
            return 0
           
    def get_invite_counts(self):
        "Gets the number of 'Invite Sent' on the search results page"
        if 'https://www.linkedin.com/search/' not in  self.current_url:
            return 0
        cnt = 0
        for i in range(10):
            xpath = "/html/body/div[5]/div[4]/div[3]/div/div[2]/div/div[2]/div/div/div/div/ul/li[{i}]/div/div/div[3]/div/button"
            try:
                cnt += self.fx(x).text == "Invite Sent"
            except:
                pass
        return cnt

    def get_may_know_pending(self):
        "Get counts of people w/ pending connections"
        if 'https://www.linkedin.com/mynetwork/' in self.current_url:
            return sum([i.text=='Pending' for i in self.fxs('//*/span[@class="artdeco-button__text"]')])
        else:
            return None

        # reward = 0
        # header = driver.fx('//div[@class="profile-background-image profile-background-image--loading ember-view"]/following-sibling::div')
        # try:
        #     uni, job, bottom_line, *args = reversed(header.text.split('\n'))
        #     reward += sum(map(len, [uni, job, bottom_line]))
        # except:
        #     pass
        #  #Issue is these 'ember's numbers change each page
        # name = self.fx_text('//*[@id="ember1221"]/div[2]/div[2]/div[1]/ul[1]/li[1]', default="")
        # role = self.fx_text('//*[@id="ember1221"]/div[2]/div[2]/div[1]/h2', default="")
        # about = self.fx_text('//*[@id="ember1311"]', default="")
        # reward += sum(map(len, [name, role, about]))
        # try:
        #     degree = self.fx('//span[@clas="dist-value"]')#default of str won't have text attribute
        #     reward += (int(degree.text[0]) -1)*10#rewardmore distant connections
        #     #handle more distint connections in the future
        # except:
        #     pass
        # return reward
        
    def current_reward_function(self):
        "Not sure how to check that a connect request was sent"
        return self.target_reward_function()
        
    #need to think of a way how to distill page to features?
    def get_state(self):
        "Only a few types of pages it can be on?"
        return self.fxs("//*")#every object will be treated as unique

    def build_search_tree(self, path = None):#This errors somehow, gets 1/5 the elements. HTML vs. XML
        "Recursively build Tree of xpath to nodes"
        if path is None:
            path = '/'
            children = self.find_elements_by_xpath('/*')#all children of root
        else:
            children = self.find_elements_by_xpath(path+'/*')#all children of root
        if len(children) != 0:
            get_att = lambda c: re.match('\<([a-z]+)', c.get_attribute('outerHTML')).groups()[0]
            child_path_cnts = Counter([get_att(c) for c in children])
            make_path = lambda att, cnt:  [path + f"/{att}[{i}]" for i in range(cnt)]\
                                            if cnt > 1 else [path + f"/{att}"]
            paths = (j for att,cnt in child_path_cnts.items() for j in make_path(att,cnt))
            return [self.build_search_tree(path =p) for p in paths]   
        else:#base case
            return [path]
        
    def click_profiles(self, url, connect_xpath = "//*[not(*)]"):
        "Explore tree structure of potential profiles"
        print("new", random.randint(0,1))
        self.get(url)
        time.sleep(0.3)
        url = self.current_url
        # suggestions = self.fx('//h2[text()="More suggestions for you"]/ancestor::section')
        # leaf_elements = list(filter(lambda i: i.text == 'Connect',
        #                             suggestions.find_elements_by_xpath("//*[not(*)]")))
        connect_xpath = '//*'#'[text()="Connect"]/parent::button'
        leaf_elements = self.find_elements_by_xpath(connect_xpath)#isn't true; sometimes click parents
        # leaf_elements =self.fxs()
        
        prev_invites = self.get_invite_counts()
        prev_pending = self.get_may_know_pending()
        other_urls = set()
        cum_reward = 0
        ix = 0
        for c in leaf_elements:#Get reward from connecting on this page; should be learning this
            try:
                print(c.text)
                if 'Connect' == c.text:
                    print(c.text)
                #keep track of reward, grib
                    c.click()
                    ix += 1
                    time.sleep(0.1)
                    reward =  self.target_reward_function(prev_invites=prev_invites, prev_pending=prev_pending)
                    if reward != 0:
                        cum_reward += reward
                        print("Got Reward: ", reward)
                    if url != self.current_url:
                        print("diff url", self.current_url)
                        other_urls.add(self.current_url)
                        # self.back()
                        self.get(url)
                        # suggestions = self.fx('//h2[text()="More suggestions for you"]/ancestor::section')
                        time.sleep(0.3)
                        leaf_elements[:] = list(filter(lambda i: i.text == 'Connect', 
                                                       self.find_elements_by_xpath(connect_xpath))[ix:])
                        ix = 0
                    prev_invites = self.get_invite_counts()
                    prev_pending = self.get_may_know_pending()
            except Exception as e:# StaleElementReferenceException:
                # print(e, url)
                # self.get(url)
                # suggestions = self.fx('//h2[text()="More suggestions for you"]/ancestor::section')
                # leaf_elements[:] = list(filter(lambda i: i.text == 'Connect', 
                #                                self.find_elements_by_xpath("//*[not(*)]")))
                print(e)
                time.sleep(0.3)
                leaf_elements[:] = self.fxs(connect_xpath)[ix:]
                ix = 0
           
        print("index")
        ix = 0
        all_elements = self.fxs("//*")
        for c in all_elements:#get the next URL pages
            try:
                if not c.is_displayed():
                    ActionChains(self).send_keys("u'\ue00c").perform()#escape Key    
                    time.sleep(0.1)
                c.click()
                ix += 1
                time.sleep(0.1)
                # if self.target_reward_function(prev_invites=prev_invites, prev_pending=prev_pending) != 0:
                #     print("Got Reward: ", self.target_reward_function(prev_invites=prev_invites, prev_pending=prev_pending))
                #     return self.target_reward_function(prev_invites=prev_invites, prev_pending=prev_pending), other_urls
                if url != self.current_url:#want to know click did something
                    print("New Page: ", self.current_url)
                    other_urls.add(self.current_url)#potential next to add
                    # self.get(url)
                    self.back()
                    time.sleep(0.3)
                    all_elements[:] = self.fxs("//*")[ix:]
                    ix = 0
                    # if self.target_reward_function(prev_invites=prev_invites, prev_pending=prev_pending) == 0:
                    #     self.back()
                    # else:
                    #     print("Got Reward: ", self.target_reward_function(prev_invites=prev_invites, prev_pending=prev_pending))
                    #     return self.target_reward_function(prev_invites=prev_invites, prev_pending=prev_pending), other_urls
            except:
                all_elements[:] = self.fxs("//*")[ix:]
                ix = 0
            return cum_reward, other_urls
        
    def click_profile_manager(self):
        urls = ["https://www.linkedin.com/mynetwork/"]
        # inpt = self.fx('//input[@aria-label="Search"]')
        # inpt.clear()
        # inpt.send_keys(f"jake"u'\ue007')
        # time.sleep(1)
        # urls = [self.current_url]#starting url
        while True:
            print(urls)
            url = urls[0]#issue here
            if len(urls) > 1:
                del urls[0]
            else:
                print("Repeating website")
            print("TOP", url)
            reward, page_urls = self.click_profiles(url)
            if reward != 0:
                print(url, "had reward of ", reward, "from ")
            urls += list(page_urls)
            # else:
            #     for url in page_urls:
            #         print("Sub: ", url)
            #         reward, urls = self.click_profiles(url)
            #         if reward != 0:
            #             url = self.current_url
            #             break
            #         else:
            #             out += urls
                
# driver.update()
# driver.click_profiles = MyDriver.click_profiles
# 

# driver.click_profiles("https://www.linkedin.com/mynetwork/")
# MyDriver.click_profile_manager(driver)
driver.click_profile_manager()#will end up on the home page; that gives it some reward.

#%%       
driver = MyDriver()
driver.goto_linkedin()  
# driver.get('https://www.linkedin.com/in/clark-benham-2068b0152/')
#%
# time.sleep(1)
driver.click_profile_manager()#will end up on the home page; that gives it some reward.
#%%


driver = MyDriver()
driver.goto_linkedin()  
#%%





#%%
#An attempt at clicking through all availible nodes. Not building the xpath search tree correctly.
from copy import deepcopy

driver.get('https://www.linkedin.com/in/grant-janart/')
a = driver.build_search_tree()

def flatten_list(nested_list):
    "https://gist.github.com/Wilfred/7889868"
    nested_list = deepcopy(nested_list)
    while nested_list:
        sublist = nested_list.pop(0)
        if isinstance(sublist, list):
            nested_list = sublist + nested_list
        else:
            yield sublist
def clickable(pth):
    url = driver.current_url
    try:
        wt = WebDriverWait(driver, 0.5)
        wt.until(EC.element_to_be_clickable((By.XPATH, pth))).click()
        if driver.current_url != url:#doesn't go back appropriatly
            print("Changed page")
            driver.get(url)
        return True
    except:
        return False
cnt = 0
trys = 0
for i in flatten_list(a):
    trys += 1
    if clickable(i):
        cnt += 1
print(cnt/trys)
#%%
#Automatic XML parser
from collections import Counter
from lxml import etree
root = etree.Element('/*')
root.getpath(y)
#%%
import io
page_html = driver.fx('//*').get_attribute('outerHTML')
tree = etree.fromstring(page_html)#(io.BytesIO(page_html))
rt = tree.getroot()
rt.getpath(y)
#%%
names = ["Clarkasdf", "Peter", "Ardy"]
message = "I'm adding everyone from the Citadel Correlation-1 slack."
driver.connect_with(names)
driver.wu('//li[@class="search-result search-result__occluded-item ember-view"]')
#actionChains.move_to_element(c).click().perform()