#!/usr/bin/env python
# coding: utf-8

# # Homework 1 - Solução
# 
# **Aluno:** Franklin Oliveira
# 
# **Descrição:** Nesse homework, devemos criar uma aplicação web que colete dados de autores e papers do [google scholar](https://scholar.google.com.br/) e, então, exibir a informação em uma única página HTML. (vide instruções no arquivo <font color='bricks'>**hw1.pdf**</font>)
# 
# ----------------
# 
# ## Passo 1: Scraping
# 
# ### Imports

# In[1]:


import os
import sys
import bs4
import time
import zipfile
import urllib.request as request

from IPython.display import clear_output

# Selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options 
from selenium.common.exceptions import NoSuchElementException


# ### Acessando a URL e carregando o código HTML (source)

# In[2]:


# definindo caminho de pasta para o chromedriver
path = os.getcwd()

print('Your working directory is set to: {}'.format(path))
print('\nMake sure that chomedriver is at this location.')


# In[3]:


# usar chromedriver para diferentes sistemas operacionais
#sys.platform


# In[4]:


def get_chrome_version(platform='unknown'):
    '''
    Função para fazer download do chromedriver correto (de acordo com a versão do chrome 
    e o sistema operacional). 
    
    Argumentos:
        - platform (str): MacOS, Windows or Linux
    
    Retorna:
        - tupla: (versão_completa, nº da versão - 2 primeiros digitos)
    '''
    # ex. of url: https://chromedriver.storage.googleapis.com/74.0.3729.6/chromedriver_mac64.zip
    # platform list
    plat_list = ['macos', 'windows', 'linux']
    
    # gets platform with sys package if the user didn't input any
    if platform.lower() not in plat_list:
        print('Getting platform info with sys package...')
        platform = sys.platform
        print('Done!')
    
    if platform.lower().startswith('linux'):
        print('Getting chrome version...')
        version_full = str(os.popen('google-chrome --version').read()).replace('\n','')
        version_full = version_full.strip().split(' ')[-1]
        print('Done!')
    
    if platform.lower().startswith('darwin') or platform.lower().startswith('mac'):
        print('Getting chrome version...')
        version_full = str(os.popen('/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version').read()).replace('\n','')
        version_full = version_full.strip().split(' ')[-1]
        print('Done!')
    
    if platform.lower().startswith('win'):
        print('Getting chrome version...')
        version_full = str(os.popen('reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version').read()).replace('\n','')
        version_full = version_full.split(' ')[-1]
        print('Done!')
    
    time.sleep(1)
    #clear_output()
    
    version_number = version_full.split('.')[0]
    print('Your chrome version is {}'.format(version_full))
    
    
    return version_full,version_number


# In[18]:


# https://chromedriver.storage.googleapis.com/74.0.3729.6/chromedriver_mac64.zip
#chromeVersion = get_chrome_version(platform=sys.platform)


# In[26]:


def download_chrome_driver(platform,version_number):
    '''
    Downloads chromedriver from https://sites.google.com/a/chromium.org/chromedriver/downloads
    
    OBS: The driver is going to be saved at your current working directory.
    
    '''
    url = 'https://chromedriver.storage.googleapis.com/{}/chromedriver_{}.zip'
    
    # exact version of chrome to generate download link
    if int(version_number) == 76:
        version2down = '76.0.3809.68'
    
    elif int(version_number) == 75:
        version2down = '75.0.3770.140'
    
    elif int(version_number) == 74:
        version2down = '74.0.3729.6'
    
    elif int(version_number) == 73:
        version2down = '73.0.3683.68'
    
    else:
        print('Check your chrome version manually and download the correct driver at:\n \
        https://sites.google.com/a/chromium.org/chromedriver/downloads')
        return None
    
    # platform info
    if platform.lower().startswith('linux'):
        try:
            request.urlretrieve(url.format(version2down,'linux64'), filename='chromedriver_linux64.zip')
            print('chromedriver downloaded at {}'.format(path))
            
            with zipfile.ZipFile('{}/{}'.format(os.getcwd(),'chromedriver_linux64.zip'), 'r') as zip_ref:
                zip_ref.extractall('{}'.format(os.getcwd()))
        except:
            print('Download failed. Please try again or access \
            https://sites.google.com/a/chromium.org/chromedriver/downloads \
            to download it manually.')
    
    elif platform.lower().startswith('darwin') or platform.lower().startswith('mac'):
        try:
            request.urlretrieve(url.format(version2down,'mac64'),filename='chromedriver_mac64.zip')
            print('chromedriver downloaded at {}'.format(path))
            
            with zipfile.ZipFile('{}/{}'.format(os.getcwd(),'chromedriver_mac64.zip'), 'r') as zip_ref:
                zip_ref.extractall('{}'.format(os.getcwd()))
        except:
            print('Download failed. Please try again or access \
            https://sites.google.com/a/chromium.org/chromedriver/downloads \
            to download it manually.')
    
    elif platform.lower().startswith('win'):
        try:
            request.urlretrieve(url.format(version2down,'win32'), filename='chromedriver_win32.zip')
            print('chromedriver downloaded at {}'.format(path))
            
            with zipfile.ZipFile('{}/{}'.format(os.getcwd(),'chromedriver_win32.zip'), 'r') as zip_ref:
                zip_ref.extractall('{}'.format(os.getcwd()))
        except:
            print('Download failed. Please try again or access \
            https://sites.google.com/a/chromium.org/chromedriver/downloads \
            to download it manually.')

# In[25]:


#chromeVersion[1]


# In[27]:


#download_chrome_driver(sys.platform,chromeVersion[1])


# In[28]:


def scrape(author, path_to_driver = os.getcwd()):
    
    # identifica o driver correto com base no sistema operacional
    # inicializa o driver
    chrome_options = Options()  
    chrome_options.add_argument("--headless")    
    
    if sys.platform.lower() == 'windows':
        driver = webdriver.Chrome('{}/chromedriver.exe'.format(path_to_driver), chrome_options = chrome_options)
    else:
        driver = webdriver.Chrome('{}/chromedriver'.format(path_to_driver), chrome_options = chrome_options)

    # acessa URL
    # https://scholar.google.com.br/scholar?hl=EN&as_sdt=0,5&q=renato+rocha+souza
    driver.get("https://scholar.google.com.br/")
    time.sleep(0.5)

    # encontra campo de busca
    search_term = driver.find_element_by_id('gs_hdr_tsi')

    try:
        # input para pesquisa
        search_term.clear() # limpa a caixa de texto
        search_term.send_keys("{}".format(author))  # insere elemento de busca
        search_term.send_keys(Keys.RETURN) # envia o termo de busca

        # clica no botão de busca
        search_btn = driver.find_element_by_class_name('gs_rt') 
        res = search_btn.find_element_by_tag_name('a') 
        res.click()
        time.sleep(0.3)
        
        # clica no primeiro autor (resultado da busca)
        res_photo = driver.find_element_by_class_name('gs_ai_pho')
        res_photo.click()


        # scrolling and loading more
        SCROLL_PAUSE_TIME = 0.3

        # Altura do scroll
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            show_more = driver.find_element_by_id('gsc_bpf_more')
            show_more.click()

            # Espera para carregar a página
            time.sleep(SCROLL_PAUSE_TIME)

            # Calcula a nova altura de Scroll e compara com a última
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
            time.sleep(SCROLL_PAUSE_TIME)

        # url + source code (totalmente carregado)
        full_url = driver.current_url
        source = driver.page_source

        print('Dados coletados. Verifique código html na variável source.')

    except NoSuchElementException as E:
        print('Autor não encontrado. Verifique se o nome pesquisado está correto.')
        print('Fechando driver...')
        full_url = driver.current_url
        source = ''

    driver.quit()
    
    # returns a tuple
    return full_url, source


# In[29]:


#data = scrape('Jeffrey Heer')
#source = data[1]


# ### Coletando informações de papers e autores

# In[53]:


def find_papers_and_authors(scholar_source):
    
    # html coletada do google scholar
    html = bs4.BeautifulSoup(scholar_source)
    
    # tags com a informação que queremos (artigos e autores)
    attr = html.find_all('tr')
    
    # coletando autores
    authors = [str(tag.find('div')).split('>')[1].split('<')[0].replace(', ...','').strip() for 
           tag in attr[6:]]
    
    # ajustando formato (autor:[aut1,aut2,aut3])
    res = []
    for lista in [autor.split(',') for autor in authors]:
        res_1 = []
        for i in lista:
            res_1.append(i.strip())
        res.append(res_1)
    authors = res
    
    # coletando papers (obs: tratando para remover <i> some_text </i> de alguns títulos)
    works = [str(tag.find('a')).replace('<i>','').replace('</i>','').split('">')[1].split('</')[0]
          for tag in attr[6:]]
    
    papers = [{'titulo':work , 'autores':author} for (work,author) in zip(works,authors)]
    
    return papers


# In[54]:


#find_papers_and_authors(source)


# <br>
# 
# **Fim do Notebook**
