from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import re
import chromedriver_autoinstaller


#add internal libary
from . import loggas, configus

#make logpath
logging= loggas.logger

#loading config data
config_path = 'static\config\config.json'
selenium_path = 'static\config\selenium.json'
message_path = configus.load_config(config_path)['message_path']

def make_excel_data(data,ws_list):
    tc_data ={}
    for row_index in ws_list:
        tc_data[str(row_index)] = str(data[ws_list.index(row_index)].value)
        tc_data['updateDefectList'] = 'true'
    return tc_data

#=================================================================================================
# this is function of selenium 
def moveToNextTestStep(driver):
    #spand step list to 50
    #this is running when test step is over 50 (not need currently)
    time.sleep(0.5)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.ID, 'pagination-dropdown-button')))
    driver.find_element("xpath",'//*[@id="pagination-dropdown-button"]').click()
    time.sleep(0.5)
    return 0

def wait_xpath(driver, xpath):
    wait = WebDriverWait(driver, 30)
    wait.until(EC.visibility_of_element_located((By.XPATH,xpath)))
    return 0

def call_drivier(headless=True):
    #set up chromedriver
    config_data =configus.load_config(config_path)
    selenium_data = configus.load_config(selenium_path)
    if config_data['headless'] == "True":
        headless = True
    else:
        headless = False
    chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]  #크롬드라이버 버전 확인
    options = webdriver.ChromeOptions()
    #options.add_argument('disable-gpu')
    options.add_argument('lang=ko_KR')
    if headless is False:
        logging.info(f'headless is {headless}')
        options.add_argument('headless') # HeadlessChrome 사용시 브라우저를 켜지않고 크롤링할 수 있게 해줌
    else:
        options.add_argument('window-size=1920x1080')

    #options.add_argument('User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36')
    # 헤더에 headless chrome 임을 나타내는 내용을 진짜 컴퓨터처럼 바꿔줌.
    try:
        logging.info('call local chromedriver failed')
        driver = webdriver.Chrome(selenium_data["chromedriver"],options=options)
    except:
        logging.info('loading local chromedriver failed')
        try:
            logging.info('call installed chromedriver')
            driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe',options=options)  
        except:
            logging.info('install new chromedriver')
            chromedriver_autoinstaller.install(True)
            driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe',options=options)
        else:
            logging.info('install new chromedriver failed')
    return driver

def login(driver):
    config_data =configus.load_config(config_path)
    jira_login_url = config_data['jira_login_url']
    jira_id = config_data['id']
    jira_password = config_data['password']
    #start login
    logging.info('start login')
    driver.get(jira_login_url)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.ID, 'login-form-submit')))
    username=driver.find_element("xpath",'//*[@id="login-form-username"]')
    username.send_keys(jira_id)
    password=driver.find_element("xpath",'//*[@id="login-form-password"]')
    password.send_keys(jira_password)
    time.sleep(0.5)
    driver.find_element("xpath",'//*[@id="login-form-submit"]').click()
    return 0

def xpath_element_find(driver,xpath):
    status = False
    #wait_xpath(driver, xpath)
    try:
        xpath_element = driver.find_element("xpath",xpath)
        status = True
    except:
        logging.info(f'xpath_element_find - not found element')
        xpath_element = None
    return status, xpath_element

def xpath_element_get_text(driver,xpath):
    status = False
    #wait_xpath(driver, xpath)
    try:
        xpath_element = driver.find_element("xpath",xpath)
        xpath_element_txt = xpath_element.text
        status = True
    except:
        logging.info(f'xpath_element_get_text - not found element')
        xpath_element_txt = None
    return status, xpath_element_txt

def xpath_element_click(driver,xpath):
    status = False
    #wait_xpath(driver, xpath)
    try:
        xpath_element = driver.find_element("xpath",xpath)
        xpath_element.click()
        status = True
    except:
        logging.info(f'xpath_element_click - not found element')
        xpath_element = None
    return status, xpath_element

def xpath_element_clear(driver,xpath):
    status = False
    #wait_xpath(driver, xpath)
    try:
        text_feild_xpath_comment_area =driver.find_element("xpath",xpath)
        text_feild_xpath_comment_area.clear()
        status = True
    except:
        logging.info(f'xpath_element_clear -not element clear')
        text_feild_xpath_comment_area = None
    return status, text_feild_xpath_comment_area

def driver_get_to_url(driver,url):
    get_to_status = False
    get_url = driver.current_url
    #check url and skip and get to url.
    if url == get_url:
        logging.info('current url is same with previous one so driver doesn\'t get to %s' %(get_url))
        get_to_status = True
    else:
        logging.info('search for %s' %(url))
        loggas.input_message(path = message_path,message = 'search for %s' %(url))
        try:
            x_path = '//*[@id="pagination-dropdown-button"]/span'
            driver.get(url)
            wait = WebDriverWait(driver, 20)
            wait.until(EC.visibility_of_element_located((By.XPATH,x_path)))
            find_status, xpath_element = xpath_element_find(driver,x_path)
            if find_status is True:
                get_to_status = True
            else:
                get_to_status = False
        except:
            get_to_status = False
    return get_to_status, driver


