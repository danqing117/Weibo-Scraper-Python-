# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 12:04:34 2016
Updated on Mar.30 2017

@author: Danqing Yin

This module is for login weibo.com (网页版微博)
"""
import requests
from bs4 import BeautifulSoup
import re, json
from urllib.parse import quote_plus
import base64, rsa, binascii
import time
#import sys
#import random
#from PIL import Image
#from io import BytesIO

class WeiboComLogin(object):
    """ user_account, password are string inputs"""
    
    def __init__(self, user_account, password):
        self.web_name = "weibo.com"
        self.host = "http://weibo.com/"  
        self.agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586"
        self.headers = {
            "User-Agent": self.agent  
        }
        self.user_account = user_account
        self.password = password
        
    def weibo_com_login(self):
        """ 
        This function is to login weibo.com
        Http session is returned
        """
        
        """encode username"""
        username_quote = quote_plus(self.user_account)
        username_base64 = base64.b64encode(username_quote.encode("utf-8"))
        su = username_base64.decode("utf-8")
        
        """preLogin"""
        session = requests.Session()
        server_url = "https://login.sina.com.cn/sso/prelogin.php?entry=sso&callback=sinaSSOController.preloginCallBack&su="+su+"&rsakt=mod&client=ssologin.js(v1.4.15)&_=" +str(int(time.time()*1000))
        r = session.get(server_url, headers = self.headers)
        s = BeautifulSoup(r.content,"lxml")      
        
        """get some parameters from preLogin response"""
        jsonData = re.compile('\((.*)\)').search(s.text).group(1)
        dictData = json.loads(jsonData)
        if dictData["retcode"] == 0:
            print("preLogin success!")
            nonce = dictData['nonce']  # nonce
            rsakv = dictData['rsakv']  # rsakv
            servertime = dictData['servertime'] #servertime
            pubkey = dictData['pubkey'] # pubkey of rsa encryption
        else:
            print("PreLogin failed, retcode = "+dictData["retcode"])
            
            
        """ form data to login 新浪通行证"""
        """ encrypt password using RSA """
        pubkey10 = int(pubkey, 16)
        key = rsa.PublicKey(pubkey10, 65537)
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(self.password)
        message = message.encode(encoding="utf-8")
        pwd_encry = binascii.b2a_hex(rsa.encrypt(message, key)) 
        
        postdata = {
            "entry":"sso",
            "gateway":"1",
            "from":"null",
            "savestate":"30",
            "useticket":"0",
            "pagerefer":"",
            "vsnf":"1",
            "su":su,
            "service":"sso",
            "servicetime": servertime,
            "nonce": nonce,
            "pwencode":"rsa2",
            "rsakv": rsakv,
            "sp":pwd_encry,
            "sr":"1280*720",
            "encoding":"UTF-8",
            "cdult":"3",
            "domain":"sina.com.cn",
            "prelt":"309",
            "returntype":"TEXT"
        }
    
        """ login 新浪通行证 """
        login_url = "https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)&_=1"+str(servertime)
        r = session.post(login_url, data = postdata, headers = self.headers)
        s = BeautifulSoup(r.content,"lxml")
        dictData = json.loads(s.text)
        if dictData["retcode"] == "0":
            print("新浪通行证 login success!")
        else:
            print("新浪通行证 login fail!")
            print(dictData)
        
        """ add cookie to request header to login weibo.com """
        cookies = r.cookies.get_dict()
        cookies = [key + "=" + value for key, value in cookies.items()]
        cookies = "; ".join(cookies)
        session.headers["cookie"] = cookies
        
        """weibo.com login redirection"""
        r = session.get(dictData["crossDomainUrlList"][1], headers = self.headers) # pre-redicretion 
        s = BeautifulSoup(r.content,"lxml")
        if json.loads(s.text)['retcode'] == 20000000:
            print("pre rediction success!")
            weibo_com_r = session.get(self.host, headers = self.headers)
            s_weibo_com_r = BeautifulSoup(weibo_com_r.content,"lxml")
            redir_url = re.compile('location\.replace\([\'"](.*?)[\'"]\)').findall(s_weibo_com_r.text)[0]
        else:
            print("pre-rediction Failed!")
            print(s.text)
            
        """Login weibo.com"""
        r = session.get(redir_url, headers = self.headers)
        s = BeautifulSoup(r.content,"lxml")
        if len(s.title.text) == 17:
            print(s.title.text)
            print("weibo.com login success!")
            del(session.headers["cookie"]) # keep login state
        else:
            print("weibo.com login failed!")
            
        return session
        
