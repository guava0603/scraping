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


def collect_data(_para):
    _website = _para[0]
    _section = _para[1]
    _region = region_list[region]
    _driver = open_website(_website)
    pageSource = _driver.page_source  # 取得網頁原始碼
    soup = BeautifulSoup(pageSource, 'html.parser')
    
    res = { '網址': _website }
    try:
        title_element = soup.select('.detail-title-content')
        title = ''
        if len(title_element) > 0:
            title = title_element[0].text.strip()
        else:
            title_element = soup.select('.build-name')
            if len(title_element) > 0:
                title = title_element[0].text.strip()
            else:
                print('[no title] ', _website)

        price_element = soup.select('.info-price-left')
        price = ''
        if (len(price_element) > 0):
            p1 = price_element[0].select('.info-price-num')[0].text.strip()
            price_dump = soup.select('.sale-fluctuation')
            if len(price_dump) > 0:
                p1 = p1.split(' ')[0]
            price = p1 + price_element[0].select('.info-price-unit')[0].text.strip()
        else:
            price_element = soup.select('.build-price')
            if len(price_element) > 0:
                p1 = price_element[0].select('.price')
                p2 = price_element[0].select('.unit')
                p1 = p1[0].text.strip() if len(p1) > 0 else ''
                p2 = p2[0].text.strip() if len(p2) > 0 else ''
                price = p1+p2
            else:
                print('[no price] ', _website)

        res = {
            '名稱': title,
            '價格': price,
            '縣市': _region,
            '鄉鎮區': _section
        }

        phone_ele = soup.select('.info-host-phone .info-host-word')
        if (len(phone_ele) > 0):
            res['電話'] = ','.join([p.text.strip() for p in phone_ele])
        else:
            phone_ele = soup.select('.call-phone .phone strong')
            if (len(phone_ele) > 0):
                res['電話'] = ','.join([p.text.strip() for p in phone_ele])
            else:
                print('[no phone] ', _website)

        price_per_element = soup.select('.info-price-per')
        if (len(price_per_element) > 0):
            t = price_per_element[0].text.strip()
            label = t.split(':')[0].strip()
            txt = t.split(':')[1].strip()
            res[label] = txt


        other_info = soup.select('.info-price-pay')
        for info in other_info:
            label_ele = info.select('span.tag')
            text_ele = info.select('a')
            if len(label_ele) > 0 and len(text_ele) > 0:
                label = label_ele[0].text.strip().replace('：','')
                txt = text_ele[0].text.strip()
                res[label] = txt

        other_info = soup.select('.info-item')
        for info in other_info:
            label_ele = info.select('span.label')
            text_ele = info.select('span.text')
            if len(label_ele) > 0 and len(text_ele) > 0:
                label = label_ele[0].text.strip()
                txt = text_ele[0].text.strip()
                res[label] = txt

        other_info = soup.select('.info-floor-left')
        for info in other_info:
            label = info.select('.info-floor-value')[0].text.strip()
            txt = info.select('.info-floor-key')[0].text.strip()
            res[label] = txt

        other_info = soup.select('.info-addr-content')
        for info in other_info:
            label = info.select('.info-addr-key')[0].text.strip()
            txt = info.select('.info-addr-value')[0].text.strip()
            res[label] = txt

        address_ele = soup.select('.info-addr-value a')
        if len(address_ele) > 0:
            _driver.find_element_by_css_selector('.info-addr-value a.info-addr-tip').click()
            time.sleep(3)

            iframe = _driver.find_element(By.CSS_SELECTOR, "iframe#detail-map-free")
            _driver.switch_to.frame(iframe)
            address = _driver.find_elements_by_css_selector('.address')
            if len(address) > 0:
                res['地址'] = address[0].text.strip()
        else:
            address_ele = soup.select('.info-item.address .address-right')
            if len(address_ele) > 0:
                res['地址'] = address_ele[0].text.strip().replace('查看地圖>', '')
            else:
                print('找不到', title , '地址')
    except:
        print('Something wrong. ', _website)
    
    _driver.close()
    return res


# In[4]:


region_list = {
    "3": "新北市",
    "6": "桃園市",
    "1": "台北市",
    "24": "澎湖縣"
}

role_list = {
    "1": "屋主刊登",
    "2": "代理人刊登",
    "3": "仲介刊登"
}

success = False
while not success:
    region = input("請輸入縣市代表數字（1: 台北市, 3: 新北市, 6: 桃園市)：")
    if region != "1" and region != "3" and region != "6" and region != "24":
        success = False
    else:
        success = True

success = False
while not success:
    role = input("請輸入經辦人代表數字（1: 屋主刊登, 2: 代理人刊登, 3: 仲介刊登)：")
    if role != "1" and role != "3" and role != "2":
        success = False
    else:
        success = True

website = "https://sale.591.com.tw/?shType=list&regionid=" + region + "&role=" + role


# In[5]:


data = []
err_data = []


# In[ ]:


chrome = open_website(website)
time.sleep(3)

test = 0
first_row = 810
total_rows = int(chrome.find_element_by_css_selector('.houseList-head-title em').text)

print('共有', total_rows, '筆')

while first_row < total_rows:
    if first_row > 0:
        chrome = open_website(website + "&firstRow=" + str(first_row) + "&totalRows=" + str(total_rows))
        time.sleep(5)
        
    all_website = chrome.find_elements_by_css_selector('.houseList-body .houseList-item-main')
    all_para = [(web.find_element_by_css_selector('.houseList-item-title > a').get_attribute('href'), web.find_element_by_css_selector('.houseList-item-section').text.replace('-','')) for web in all_website]
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        result = list(executor.map(collect_data, all_para))
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


name = './' + str(total_rows) + "_" + region_list[region] + "_" + role_list[role] + "_" + f"{datetime.now():%Y%m%d-%H%M}" + ".xlsx"
df = pd.DataFrame(data=data)
df.to_excel(name, index=False)
print('共有', len(data), '筆成功抓取的資料，已輸出至"', name, '"檔案')


# In[ ]:


if len(err_data) > 0:
    name = './' + region_list[region] + "_" + role_list[role] + "_" + f"{datetime.now():%Y%m%d-%H%M}" + ".xlsx"
    df = pd.DataFrame(data=err_data)
    df.to_excel(name, index=False)
    print('共有', len(err_data), '筆無法抓取的資料，已輸出至"', name, '"檔案')
else:
    print('資料全數抓取成功')


#  
