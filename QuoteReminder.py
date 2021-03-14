import os
import sys
import time
import json
import smtplib
from selenium import webdriver
from selenium.common.exceptions import *
from email.header import Header
from email.mime.text import MIMEText
import json

def sendMail(title,detail,link):
    with open("config.json","w") as f:
        config = json.load("config.json")
    # 登录Smtp服务器
    smtp_user = config["smtp_user"]
    smtp_password = config["smtp_password"]
    smtp = smtplib.SMTP("smtp.ym.163.com",25)
    smtp.login(user=smtp_user,password=smtp_password)
    # 准备邮件内容
    html_msg = "<p>" + title + "</p>" + "<p>" + detail + "</p>" +"<p><a href=\"" + link + "\">点击这里查看</a></p>"
    msg = MIMEText(html_msg,'html','utf-8')
    msg["From"] = Header(config["from"],"utf-8")
    msg["To"] = Header(config["to"],"utf-8")
    msg["Subject"] = Header("新的报价等待处理", 'utf-8')
    # 发送邮件
    try:
        smtp.sendmail(smtp_user, config["to"], msg.as_string())
    except smtplib.SMTPException:
        return False
    return True

def loadList():
    # 读取json
    global titleList
    global detailList
    global linkList
    filepath = os.path.join(sys.path[0],"lists.json")
    if(os.path.exists(filepath)):
        with open(filepath,"r",encoding="utf-8") as f:
            jsonLists = json.load(f)
        titleList = jsonLists["titleList"]
        detailList = jsonLists["detailList"]
        linkList = jsonLists["linkList"]

def getOptions():
    options = webdriver.ChromeOptions()
    options.binary_location = os.path.join(sys.path[0],"Chrome/Application/chrome.exe")
    options.add_argument("--user-data-dir=" + os.path.join(sys.path[0],"Chrome/UserData"))
    options.add_argument("--disk-cache-dir=" + os.path.join(sys.path[0],"Chrome/Cache"))
    options.add_argument("blink-settings=imagesEnabled=false")
    options.add_argument("--single-process")
    options.add_argument("log-level=3")
    options.add_argument("--headless")
    return options

def getInformation():
    global driver
    # 清除Cookie并刷新页面
    driver.delete_all_cookies()
    driver.refresh()
    # 查找报价列表第一个元素
    try:
        element_link = driver.find_element_by_css_selector("div.alife-bc-brh-rfq-list__row:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > h1:nth-child(1) > a:nth-child(1)")
        element_detail = driver.find_element_by_css_selector("div.alife-bc-brh-rfq-list__row:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3)")
    except NoSuchElementException:
        print("[Error] ","无法找到指定元素，可能是访问受限或网页版面已经修改")
        return None
    # 获取元素link，title,detail
    link = element_link.get_attribute('href')
    title = element_link.get_attribute('title')
    detail = element_detail.get_attribute('textContent')
    return [title,detail,link]

def process(title,detail,link):
    global titleList
    global detailList
    global linkList
    # 判断报价是否已存在
    if(title in titleList and detail in detailList):
        print("[Log] ","报价未更新")
    else:
        # 如果队列中的链接大于五个则删除第一个
        if(len(linkList) >= 5):
           del titleList[0]
           del detailList[0]
           del linkList[0]
        titleList.append(title)
        detailList.append(detail)
        linkList.append(link)
        # 保存到Json文件
        with open(os.path.join(sys.path[0],"lists.json"),"w",encoding="utf-8") as f:
            json.dump({"titleList":titleList,"detailList":detailList,"linkList":linkList},f)
        # 打印信息
        print("[Log] ","找到新报价")
        print("[Log] ","标题：",title)
        print("[Log] ","详细信息：",detail)
        print("[Log] ","链接：",link)
        # 发送邮件
        if(sendMail(title,detail,link)):
            print("[log] ","邮件已发送")
        else:
            print("[Error] ","邮件发送失败")
            return False
    print("[Log] ","等待20秒重新检查")
    return True


# 初始化Lists
linkList = []
titleList = []
detailList = []
loadList()
# 配置、启动浏览器并访问页面
driver = webdriver.Chrome(chrome_options=getOptions())
driver.get("https://sourcing.alibaba.com/rfq_search_list.htm?categoryIds=327&recently=Y")
# 刷新数据
while True:
    informations = getInformation()
    if(informations == None):
        continue
    process(informations[0],informations[1],informations[2])
    time.sleep(20)