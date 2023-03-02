#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import time
from datetime import datetime
import concurrent.futures

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

import pandas as pd

import warnings
warnings.filterwarnings('ignore')


# In[2]:


def open_website(_website):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(_website)  # 輸入範例網址，交給瀏覽器
    return driver


# In[3]:


def collect_data(_website):
    _region = region_list[region]
    _driver = open_website(_website)
    time.sleep(5)
    pageSource = _driver.page_source  # 取得網頁原始碼
    soup = BeautifulSoup(pageSource, 'html.parser')
    
    title_element = soup.select('.house-title h1')
    title = ''
    if len(title_element) > 0:
        title = title_element[0].text.strip()
    else:
        print('[no title] ', _website)
    
    
    name_element = soup.select('.contact-info .base-info .name')
    name = ''
    if len(name_element) > 0:
        name = name_element[0].text.strip()
        warn_element = soup.select('.contact-info .base-info .name .warmmsg')
        if len(warn_element) > 0:
            warn_msg = warn_element[0].text.strip()
            name = name.replace(warn_msg, '').strip()
        name_arr = name.split(': ')
        while len(name_arr) < 2:
            name_arr = [''] + name_arr
    else:
        print('[no name] ', _website)
    
    price_element = soup.select('.house-price span.price')
    price = ''
    if (len(price_element) > 0):
        price = price_element[0].text.strip()
    else:
        print('[no price] ', _website)
        
    pattern_element = soup.select('.house-pattern > span')
    patterns = [p.text for p in pattern_element]
    while '' in patterns: patterns.remove('')
    while len(patterns) < 4: patterns.append('')
    
    address_element = soup.select('.address .load-map')
    address = ''
    if len(address_element) > 0:
        address = address_element[0].text.strip()
    
    res = {'網址': _website}
    try:
        res = {
            '名稱': title,
            '聯絡人身份': name_arr[0],
            '聯絡人稱謂': name_arr[1],
            '租金': price,
            '格局': patterns[0],
            '坪數': patterns[1],
            '樓層': patterns[2],
            '房屋類型': patterns[3],
            '位置': address
        }
    
        around_ele = soup.select('.surround-list-item')
        for around in around_ele:
            a_key = soup.select('.surround-list-box .name')[0].text
            a_val = [p.text.strip() for p in soup.select('.surround-list-box > p')]
            other_val = [p.text.strip() for p in soup.select('.surround-list-text > p')]
            res[a_key] = '|'.join(a_val + other_val)

        phone_ele = soup.select('#rightConFixed .reference .tel-txt')
        if (len(phone_ele) > 0):
            res['聯絡電話'] = ','.join([p.text.strip() for p in phone_ele])
    
    except:
        print('Something wrong. ', _website)
    
    _driver.close()
    return res


# In[4]:


region_list = {
    "3": "新北市",
    "6": "桃園市",
    "1": "台北市",
    "24": "澎湖縣",
    "22": "台東縣"
}

success = False
while not success:
    region = input("請輸入縣市代表數字（1: 台北市, 3: 新北市, 6: 桃園市)：")
    if region != "1" and region != "3" and region != "6" and region != "24" and region != "22":
        success = False
    else:
        success = True

website = "https://rent.591.com.tw/?region=" + region


# In[5]:


data = []
err_data = []


# In[6]:


chrome = open_website(website)
time.sleep(3)

# ad = chrome.find_element_by_css_selector('.tips-popbox-img')
# if ad.is_displayed():
#     ad.click()

test = 0
first_row = 0
total_rows = int(chrome.find_element_by_css_selector('.switch-amount span').text.replace(',', ''))
name = str(total_rows) + '_' + '屋主直租_' + region_list[region] + "_" + f"{datetime.now():%Y%m%d-%H%M}" + ".xlsx"

print('共有', total_rows, '筆')

while first_row < total_rows:
    if first_row > 0:
        chrome = open_website(website + "&firstRow=" + str(first_row) + "&totalRows=" + str(total_rows))
        time.sleep(5)
        
    all_website = chrome.find_elements_by_css_selector('.switch-list-content .vue-list-rent-item')
    all_href = [web.find_element_by_css_selector('a').get_attribute('href') for web in all_website]
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        result = list(executor.map(collect_data, all_href))
        for x in result:
            if x.get('網址'):
                err_data.append(x)
            else:
                data.append(x)
        
    end_time = time.time()
    
    print(len(data), '/', total_rows, '(P.', int(first_row / 30) + 1, ') ... ', end_time-start_time, '秒')
    
    first_row += 30


# In[ ]:


chrome.close()  # 關閉瀏覽器


# In[ ]:


name = './' + str(total_rows) + '_' + '屋主直租_' + region_list[region] + "_" + f"{datetime.now():%Y%m%d-%H%M}" + ".xlsx"
df = pd.DataFrame(data=data)
df.to_excel(name, index=False)
print('共有', len(data), '筆成功抓取的資料，已輸出至"', name, '"檔案')


# In[ ]:


if len(err_data) > 0:
    name = './' + '屋主直租_' + region_list[region] + "(問題資料)_" + f"{datetime.now():%Y%m%d-%H%M}" + ".xlsx"
    print('共有', len(err_data), '筆無法抓取的資料，已輸出至"', name, '"檔案')
    df = pd.DataFrame(data=err_data)
    df.to_excel(name, index=False)
else:
    print('資料全數抓取成功')


#  
