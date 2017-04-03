# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 15:58:30 2016

@author: Danqing Yin

Python project：
search some keywords on weibo.cn and then save all the results(image, map, users' information) and analyzed them.
All the images are saved on local pc, and users' information is written in an excel file.
"""

import WeiboCnLogin as wl
from weibo_function import user_scrap_cn
from bs4 import BeautifulSoup
import re, os, urllib
import pandas as pd
import time

keywords = ['keywords1','keywords2']
user_account = ['account1','account2','account3'] # better to use more than 1 account in case of being restricted
password = "a123456" 

for key in range(len(keywords)):
    keyword = keywords[key]
    print('keyword: ', keyword)
    user_account = user_account[1:] + [user_account[0]]
    flag = 1
    
    try:
        del(cur_page2)
    except: pass
    weibo_dict = []
    
    while flag == 1:
        
        print('Current keywords: '+keyword)
        ''' login '''
        print("login...")
        wb = wl.WeiboCnLogin(user_account[0], password)
        session = wb.weibo_cn_login()
        
        ''' search page '''
        search_request_url = "http://weibo.cn/search/?pos=search"  # url of searching page
        postdata = {
            "keyword":keyword,
            "smblog": "搜微博"
        }
        r = session.post(search_request_url, headers = wb.headers, data = postdata)
        s = BeautifulSoup(r.content, "lxml")
        print("response status: ", r)
        
        # if your account is restricted
        if str(r) == "<Response [403]>":
            user_account = user_account[1:] + [user_account[0]]
            print("Change account")
            continue
            
        try:
            num_info = s.findAll("div",{"class":"c"})[2].text
            print("search succeed")
            print(num_info)
            if re.compile('抱歉').findall(num_info)!=[]:
                nkeywords.append(keyword)
                print('no results, change another keywords')
                break
        except:
            print("search failed")
            break
            
        ''' scraping search results'''
        # number of pages
        try:
            num_pages_text = s.find("div",{"class":"pa"}).text
            num_pages = int(re.compile("\/(\d+)").findall(num_pages_text)[0])
            print('numbers of pages: ', num_pages)
            if num_pages==100:
                lkeywords.append(keyword)
                print('too many results')
                break
        except:
            num_pages_text = 'Null'
            num_pages = 1
            print('numbers of pages: ', num_pages)
        
        next_page_text = '下页'
        cur_page = 1
        initial_cur_page = cur_page
        try:
            if cur_page2 >num_pages:
                break
            else:
                cur_page = cur_page2
                initial_cur_page = cur_page2
        except:
            s_next = s
    
        while next_page_text == '下页':
            
            print('page: ', cur_page)
            try:
                next_page_text = s_next.find('div',{'class':'pa'}).find('a').text
                next_page_url = 'http://weibo.cn' + s_next.find('div',{'class':'pa'}).find('a')['href']
            except:
                next_page_text = 'Null'
            print(next_page_text)
            
            # scraping on each result
            items_current_page = s_next.findAll('div',{'class':'c','id':re.compile('M_.*')})
            
            for item in items_current_page:
                print('scraping weibo on current page')
                weibo_id = item['id']
                user_url = item.find('a',{'class':'nk'})['href']
                user_info = user_scrap_cn(wb, session, user_url)
                weibo_text = item.find('span',{'class':'ctt'}).text[1:]
                weibo_time = item.find('span',{'class':'ct'}).text.split('\xa0')[0]
                weibo_url = item.find('a',{'class':'cc'})['href']
                
                div1_list = item.findAll('div')[0].findAll('a')
                # find images and map
                l_find_image_map = [x.text for x in div1_list]
                for i in range(len(l_find_image_map)):
                    if re.compile("显示地图").findall(l_find_image_map[i]) != []:
                        map_index = i
                        continue
                    if re.compile("组图").findall(l_find_image_map[i]) != []:
                        images_index = i
                        
                # create file for each search result
                path = r'C:\Users\\' + keyword + '\\' + weibo_id
                try:
                    os.makedirs(path)
                except FileExistsError:
                    pass
                im_flag = False
                map_flag = False
                map_im_url = 'Null'
                
                # save images
                try:
                    images_url = div1_list[images_index]['href'] 
                    r = session.get(images_url, headers = wb.headers)
                    s = BeautifulSoup(r.content,'lxml')
                    images_url = [x.findNext()['href'] for x in s.findAll('span',{'class':'tc'})]
                    for x in range(len(images_url)):
                        r = session.get('http://weibo.cn'+images_url[x],headers = wb.headers)
                        print('save image...')
                        im = urllib.request.urlretrieve(r.url, path+'\\'+weibo_id+'_'+str(x+1)+'_image.jpg')
                        print('image saved')
                    im_flag = True
                    del(images_index)
                except:
                    if len(item.findAll('div')) >1:
                        div2_list = item.findAll('div')[1].findAll('a')
                        div2_list_text = [x.text for x in div2_list]
                        try:
                            image_url = div2_list[div2_list_text.index('原图')]['href']
                            r = session.get(image_url,headers = wb.headers)
                            print('save image...')
                            im = urllib.request.urlretrieve(r.url, path+'\\'+weibo_id+'_image.jpg')
                            print('image saved')                            
                            im_flag = True
                        except: pass
                
                #save map
                try:
                    map_url = div1_list[map_index]['href']
                    r = session.get(map_url, headers = wb.headers)
                    s = BeautifulSoup(r.content,'lxml')
                    if s.find('div',{'class':'c'}).text != '未知地点':
                        map_im_url = s.find('img')['src']
                        #im = urllib.request.urlretrieve(map_im_url, path+'\\'+weibo_id+'_map.jpg')
                        map_flag = True
                    del(map_index)
                except: pass
                        
                weibo_dict.append({
                                    '_id':weibo_id,
                                    'weibo_url':weibo_url,
                                    'user_url':user_url,
                                    'user_nickname': user_info[-2],
                                    'user_gender':user_info[3],
                                    'user_birth':user_info[5],
                                    'education':user_info[-1],
                                    'weibo_text':weibo_text,
                                    'weibo_time':weibo_time,
                                    'images':im_flag,
                                    'map_url':map_im_url
                                    })
            # scraping next page
            cur_page += 1
            try:
                r = session.get(next_page_url, headers = wb.headers)
                s_next = BeautifulSoup(r.content, 'lxml')
            except: pass
         
            cur_page2 = cur_page
            # change account if the current account has been scraping more than 10 pages
            if cur_page == initial_cur_page+10:
                user_account = user_account[1:] + [user_account[0]]
                print("change account")
                break
       
        # finish the search of current keyword and save results in an excel file
        if cur_page2 > num_pages:
            flag = 0
            print('save results')
            df = pd.DataFrame(weibo_dict)
            csv_path = r'C:\Users\\' + keyword + '\\'+ keyword +'.csv'
            df.to_csv(csv_path,index = False)
    
            
        
    
    
    
    
