# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 22:28:00 2016
update user_scrap_com() - 19/06/2016 

@author: Danqing Yin
"""
from bs4 import BeautifulSoup
import re

def user_scrap_cn(login_obj, session, url):
    """
    login to weibo.cn, obtain user information, and the information on user's profolio page will be returned
    
    login_obj: WeiboCnLogin object
    session: weibo.cn login session
    url: url of user's main page on weibo.cn
    """
    
    r = session.get(url, headers = login_obj.headers)
    s = BeautifulSoup(r.content,"lxml")
    text = s.find("div",{"class":"tip2"}).text
    
    # basic information
    num_weibo = re.compile("微博\[(\d+)\]").findall(text)[0]  # numbers of post
    num_follower = re.compile("粉丝\[(\d+)\]").findall(text)[0] # numbers of followers
    num_follow = re.compile("关注\[(\d+)\]").findall(text)[0] # numbers of followed
    
    # other information
    ref = s.find("div",{"class":"ut"}).findAll("a")[-4]["href"]
    r2 = session.get("http://weibo.cn"+ref, headers = login_obj.headers)
    s2 = BeautifulSoup(r2.content,"lxml")
    s2_items = [x.text for x in s2.findAll('div',{'class':'tip'})]
    try:
        s_edu_index = s2_items.index('学习经历') # education 
        edu = s2.findAll('div',{'class':'tip'})[s_edu_index].findNext().text
    except:
        edu = "Null"
    
    info = str(s2.findAll("div",{"class":"c"})[2]).split("<br/>")
    
    nick_name = re.compile("昵称:(.*)").findall(info[0])[0]
    gender = [re.compile("性别:(.*)").findall(x)[0] for x in info if re.compile("性别:(.*)").findall(x)!=[]]
    location = [re.compile("地区:(.*)").findall(x)[0] for x in info if re.compile("地区:(.*)").findall(x)!=[]]
    birth = [re.compile("生日:(.*)").findall(x)[0] for x in info if re.compile("生日:(.*)").findall(x)!=[]]
    intro = [re.compile("简介:(.*)").findall(x)[0] for x in info if re.compile("简介:(.*)").findall(x)!=[]]
    info_list = [gender, location, birth, intro]
    for i in range(4):
        if info_list[i] == []:
            info_list[i] = "Null"
        else:
            info_list[i] = info_list[i][0]
    
    return num_weibo, num_follower, num_follow, info_list[0], info_list[1], info_list[2], info_list[3], nick_name, edu
    

def user_scrap_com(login_obj, session, url):
    """
    login to weibo.com, obtain user's registration time
    !!! must login to weibo.com first!!!
    It is not the best way to obtain user's information since the cookie is needed 
    when scraping user's page on weibo.com and also the web page of weibo.com  is much
    more complicated.
    """
    if url.find(r"/u/")!= -1:
        url = url[2:]
        
    # trying to scrape the user's page
    r = session.get("http://weibo.com"+url+"/info?mod=pedit_more", headers = login_obj.headers)
    s = BeautifulSoup(r.content,"lxml")
    print("try to check the user's page first time...")
    
    # add cookie to request header if needed, then do scraping again
    if s.find("body").text.find("正在登录")!= -1:
        relocate_url = re.compile(r"location\.replace\((.*)\)").findall(s.text)[0][1:-1]
        r = session.get(relocate_url,headers = login_obj.headers)
        s = BeautifulSoup(r.content,"lxml")
        print("check the user's page second time after relocation")
        
    try:
        if s.find("meta")["content"][0] == "0":
            cookies = r.cookies.get_dict()
            cookies = [key + "=" + value for key, value in cookies.items()]
            cookies = "; ".join(cookies)
            session.headers["cookie"] = cookies
            r = session.get("http://weibo.com"+url+"/info?mod=pedit_more", headers = login_obj.headers)
            s = BeautifulSoup(r.content,"lxml")
            
            # if relocation is found
            if s.find("body").text.find("正在登录")!= -1:
                relocate_url = re.compile(r"location\.replace\((.*)\)").findall(s.text)[0][1:-1]
                r = session.get(relocate_url,headers = login_obj.headers)
                s = BeautifulSoup(r.content,"lxml")
                print("check the user's page third time after relocation")
            
    except: pass
    
    try:
        # some user on weibo.com is restricted and cannot be seen
        if s.find("div",{"class":"note"}).text.find("抱歉，您当前访问的帐号异常，暂时无法访问")!=-1:
            error = 1
            register_t = "Null"; nick_name = "Null"; location = "Null"; gender = "Null";birth = "Null"; intro="Null"
            
    except:
        # obtain user's information
        error = 0
        register_t = re.compile("注册时间.*t(\d+\-\d+\-\d+)").findall(s.text)[0]
        nick_name = re.compile("昵称：\<\\\\\/span\>\<span class\=\\\\\"pt_detail\\\\\"\>(.{0,100})\<\\\\\/span\>").findall(s.text)[0]
        location = re.compile("所在地：\<\\\\\/span\>\<span class\=\\\\\"pt_detail\\\\\"\>(.{0,100})\<\\\\\/span\>").findall(s.text)[0]
        gender = re.compile("性别：\<\\\\\/span\>\<span class\=\\\\\"pt_detail\\\\\"\>(.{0,1})\<\\\\\/span\>").findall(s.text)[0]
        try: birth = re.compile("生日：\<\\\\\/span\>\<span class\=\\\\\"pt_detail\\\\\"\>(.{0,50})\<\\\\\/span\>").findall(s.text)[0]
        except: birth = "Null"
        try: intro = re.compile("简介.{0,50}\<span class\=\\\\\"pt_detail\\\\\"\>(.*)\<\\\\\/span\>.*注册时间").findall(s.text)[0]
        except: intro = "Null"
    
    return register_t, nick_name, location, gender, birth, intro, error
    