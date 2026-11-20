#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pour le bon fonctionnement de l'application, remplir le fichier
'centrale.ini' pour définir vos propres codes d'authenfications,
l'adresse IP et le hostname de votre centrale d'alarme.
Cette application est minimaliste et permet pour l'instant
les commandes basiques, cad surveillance de celle-ci et les mises
en route et arrêts des zones prévues sur l' application de la marque.
CURL doit être installé sur votre système pour l'envoi des SMS.
Free propose un portail dédié pour cela.
Je ne sais pas si les autres opérateurs proposent ce service.
J'ai vu qu'il existait un service 'https://www.123-sms.net/' qui le
propose pour pas trop cher. Voir le fichier '123SMS.txt' pour plus d'infos
j'ai adapté le programme pour l'utiliser au cas où...
"""

import time
import subprocess
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import os
from pathlib import Path
import json
from configparser import ConfigParser
import platform
import memcache
import psutil
import logging
import logging.config
from index import app
# import threading
from datetime import datetime, timedelta
import urllib.parse
import urllib.request
import shutil

# def trouverInstanceServeur():
#     for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
#         try:
#             # Récupère les informations du processus
#             cmdline = proc.info['cmdline']
#             if cmdline:
#                 if len(cmdline) ==2:          # ['python3', '/home/romu/developpement/SELENIUM/web/index.py']
#                     if '/centrale/index.py' in cmdline[1]:
#                         #print(f"on peut effacer le fichier ayant le pid : {proc.info['pid']}")
#                         psutil.Process(proc.info['pid']).terminate()
#         except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#             continue

# trouverInstanceServeur()     # on supprime l'éventuel 'serveur web' qui pourrait encore tourner !'

## Basic logging setup
## Réglage du level
#app.logger.setLevel("INFO")
## Éventuellement, on vire tous les handlers déjà créés
## peut être automatiquement par Flask
#for h in app.logger.handlers:
#    app.logger.removeHandler(h)
## Et finalement, on ajoute son propre handler (ici j'en ajoute un seul)
#handler = logging.FileHandler("centrale.log")
## On peut régler le niveau du handler indépendamment (on pourrait avoir
## 2 handlers qui loguent avec deux niveaux différents)
#handler.setLevel("INFO")
#formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(threadName)s :: %(message)s')
#handler.setFormatter(formatter)
#app.logger.addHandler(handler)
## Si on vérifie, il doit y avoir un seul élément dans la liste
#print(app.logger.handlers)
## Au passage, on peut utiliser le même handler pour les messages
## qui viennent de werkzeug
## logging.getLogger("werkzeug").addHandler(handler)

"""logger_config = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s :: %(levelname)s :: %(threadName)s :: %(module)s :: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': "centrale.log",
            'formatter': 'default',
        },
    },
    'root': {
        'level': "INFO",
        'handlers': ['console', 'file']
    }
}
logging.config.dictConfig(logger_config)"""

DEBUG = 0

print("start...")

shared = memcache.Client(['127.0.0.1:11211'], debug=DEBUG)

BASE_DIR = Path(__file__).resolve().parent
# print(f"BASE_DIR : {BASE_DIR}")
fichier_ini = BASE_DIR /"centrale.ini"
# print(f"fichier_ini : {fichier_ini}")

# récupération de la config :
parser = ConfigParser()
parser.read(fichier_ini)
sec = parser.sections()

# affectation des variables
CODE = {}
MOBILE = {}
IP = parser.get('centrale', 'ip')
PORT = int(parser.get('serv_web', 'port'))
# recupération des variables pour envoi SMS FREE
SMS_FREE = parser.get('sms_free', 'sms_free')
if SMS_FREE == 'True':
    USER = parser.get('sms_free', 'user')
    PWD = parser.get('sms_free', 'pwd')
# recupération des variables pour envoi 123-SMS
SMS_123 = parser.get('123_sms', '123_sms')
if SMS_123 == 'True':
    API_URL = "https://www.123-sms.net/http.php"
    EMAIL = parser.get('123_sms', 'email')
    CLE_API = parser.get('123_sms', 'cle_api')
    for name, value in parser.items('123_sms'):
        if 'mob_' in name:
            MOBILE[name] = value

for name, value in parser.items('authentification'):
    CODE[name] = value

# print(f'IP : {IP}')
# print(f'PORT : {PORT}')
# print(f'SMS_FREE : {SMS_FREE}')
# if SMS_FREE == 'True':
#     print(f'USER : {USER}')
#     print(f'PWD : {PWD}')
# # print(f'CODE : {CODE}')
# print(f'SMS_123 : {SMS_123}')
# if SMS_123 == 'True':
#     print(f'EMAIL : {EMAIL}')
#     print(f'CLE_API : {CLE_API}')
#     print(f'MOBILE : {MOBILE}')

options = webdriver.ChromeOptions()

chromium_path = shutil.which("chromium-browser")
service = Service(shutil.which("chromedriver"))

if chromium_path:
    options.binary_location = chromium_path

# if platform.machine() == "aarch64":                # Raspberry pi
#     chromium_path = r"/usr/bin/chromium-browser"
#     service = Service(r"/usr/bin/chromedriver")
#     options.binary_location = chromium_path
# else:
#     chromium_path = r"/usr/bin/chromium-browser"  # mon linux AMD
#     service = Service(r"/home/kligliro/.local/bin/chromedriver")
#     options.binary_location = chromium_path

# Pour le passage des options à Selenium avec python, obtenu des infos sur Stack Overflow :
# Source - https://stackoverflow.com/a/76364265/home/kligliro/.local/bin/chromedriver
# Posted by kit4py, modified by community. See post 'Timeline' for change history
# Retrieved 2026-10-07, License - CC BY-SA 4.0

"""
    # options.add_argument(f"--window-size=1366,768")
    options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--password-store=basic")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--enable-automation")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-software-rasterizer")

    options.add_argument(f"--user-data-dir=PATH_TO_CHROME_PROFILE")
    options.add_argument('--proxy-server=IP_ADRESS:PORT')
"""

options.add_argument('--ignore-certificate-errors')
options.add_argument("--incognito")
# options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1024,768")
options.add_argument("--remote-debugging-pipe")
driver = webdriver.Chrome(service=service, options=options)
url = f"http://{IP}/fr/login.htm"
# print(f"url = {url}")
driver.get(url)
# print(driver.title)

# GLOBAL VARIABLE
global OK, memo_alarm
OK = True
memo_alarm = False    # au départ, pas d'alarme !
l_delta = []          # liste pour variable deltatime.
l_delta.append(datetime.now())

"""
"btn_zone_on_A    " # btn MARCHE A
"btn_zone_on_B    " # btn MARCHE B
"btn_zone_on_C    " # btn MARCHE C
"btn_zone_on_ABC  " # btn MARCHE ABC
"btn_zone_off_ABC " # btn ARRÊT ABC

"pbattery_ok   " # "Piles OK"
"pcom_ok       " # "Communication radio OK"
"pdoor_ok      " # "Porte ou fenêtre fermée"
"phouse_ok     " # "Pas d'alarme"
"pbox_ok       " # "Boîtier OK"
"pgsm_5_ok     " # "GSM connecté au réseau"
"pcam_serv_off " # "Caméra non activée"
"""

# boutons mise mise en route et arrêt alarme

BTN_ZONE = ["btn_zone_on_A",
            "btn_zone_on_B",
            "btn_zone_on_C",
            "btn_zone_on_ABC",
            "btn_zone_off_ABC",
           ]

# affichage états de la batterie, de la communication radio, d'une des portes
# ou fenêtres, si en alarme ou pas du boitier, de la connexion GSM, ou caméra
# ici, dans ce dictionnaire, il est indiqué l'état par défaut et sans alarme de la centrale.
# dans mon cas, je n'ai pas de caméra et c'est tout à fait normal que la
# dernière clé est à 'False' affichée en rouge dans la page web. Je n'en tiens
# donc pas compte. tout le reste est en vert et c'est cela que je
# surveille et dès que cela passe en rouge, c'est qu'il y a défaut et que je
# dois l' envoyer par SMS. Je suis chez 'free' et il suffit d' activer l'option 'envoi SMS'
# et récupérer son token (dans le compte mobile).
# Pour les autres fournisseurs d'accès, à voir de votre côté et peut-être même contribuer
# à l'amélioration du soft à ce niveau. J'ai vu que du côté Orange, c'est cuit !!! ils ont
# enlevé l'option il y a quelques années déjà !  :-(
# le principe est simple:
# Si je ne vois pas l'une des CLASS_NAME surveillées il suffit d'appeler le lien suivant:
# https://smsapi.free-mobile.fr/sendmsg?user=monn°user&pass=monpasswd&msg=alarme_CLASS_NAME

AF_BTN = {"pbattery_ok": "Piles OK",
          "pcom_ok": "Communication radio OK",
          "pdoor_ok": "Porte ou fenêtre fermée",
          "phouse_ok": "Pas d'alarme",
          "pbox_ok": "Boîtier OK",
          "pgsm_5_ok": "GSM connecté au réseau",
          "pcam_serv_off": "Caméra non activée",
          }

def send_123_sms(numero: str, message: str) -> str:
    """Envoie un SMS et retourne le code reponse de l'API."""
    params = urllib.parse.urlencode({
        "email": EMAIL,
        "pass": CLE_API,
        "numero": numero,
        "message": message,
    })
    # print(f'envoi 123_sms : {API_URL}?{params}')
    with urllib.request.urlopen(API_URL + "?" + params, timeout=15) as reponse:
        return reponse.read().decode("utf-8", "replace").strip()

def send_sms_free(alarm):
    # print("-->  dans send_sms_free() : envoi SMS...")
    alarm = alarm.replace(" ", "%20")
    msg = f"https://smsapi.free-mobile.fr/sendmsg?user={USER}&pass={PWD}&msg={alarm}"
    # print(msg)
    subprocess.run(["curl", msg])

def login():
    global CODE
    # print("-->  dans login() : ouverture session...")
    # print("------ ACCES AU PORTAIL ------")
    try:
        # recherche dans la page du n° d'authentification
        search_input = driver.find_element(By.TAG_NAME, 'b')
        codea = search_input.text
        # print(f"search_input : {search_input.text}")
        # print(f"code : {code[codea]}" )
        # code d'accès
        search_pwd = driver.find_element(By.NAME, "password")
        search_pwd.send_keys(CODE['code'])
        # code d'authentification
        search_pwd = driver.find_element(By.NAME, "key")
        # print("codea : ", codea.lower())
        # print("CODE[codea] : ", CODE[codea.lower()])
        search_pwd.send_keys(CODE[codea.lower()])
        # validation login, code, authentification
        search_btn = driver.find_element(By.NAME, "btn_login")
        search_btn.click()
    except:
        # validation de la fermeture de la session qui bloque !
        search_btn_ok = driver.find_element(By.NAME, "btn_ok")
        search_btn_ok.click()
        # print("suite à session ouverte, fermeture de celle-ci et on recommence...")
        login()

def pilot():
    # print("-->  dans pilot() : pilotage alarme...")
    # print("------ PILOTAGE ALARME/AUTOMATISMES ------")
    try :
        pilot = driver.find_element(By.LINK_TEXT, "PILOTAGE ALARME/AUTOMATISMES")
        pilot.click()
    except WebDriverException as err:
        app.logger.info(f"pb dans pilot() erreur : {err} ")

def journal():
    # print("-->  dans journal() : pour récupération des infos s'y trouvant...")
    try :
        journal = driver.find_element(By.LINK_TEXT, "JOURNAL DES EVENEMENTS")
        journal.click()
    except WebDriverException as err:
        app.logger.info(f"pb dans journal() erreur : {err}  ")

def refresh():
    """Pour maintenir la session ouverte et continuer de scruter
       la page 'PILOTAGE ALARME/AUTOMATISMES'."""
    # print("-->  dans refresh() : rafraichissement...")
    # app.logger.info("Refresh...")
    # le fait de rafraichir par le lien 'Actualiser' relance la dernière commande!
    # ce n'est pas exactement ce que l'on veut, en repassant par le lien
    # 'PILOTAGE ALARME/AUTOMATISMES' cela fonctionne bien mieux.
    try :
        pilot = driver.find_element(By.LINK_TEXT, "PILOTAGE ALARME/AUTOMATISMES")
        pilot.click()
    except WebDriverException as err:
        app.logger.info(f"pb dans refresh() erreur : {err}  ")

"""  REFRESH :
    <body onload="allowAJAX=true;" onunload="allowAJAX=false;">
        <div id="page">
        <div id="fond">
            <div id="navbar">
            <div id="mode">Utilisateur</div>
            <div id="disconnect"><a href="/logout.htm">Deconnexion</a></div>
            <div id="refresh"><a href="javascript:location.reload(true)">Actualiser</a></div>
            </div>
        </div>
        </div>
    </body>
"""
# /html/body/div/div/div[2]/div[3]


def find_elem():
    # print("-->  dans find_elem() : recuperation des infos de l' alarme en cours'...")
    # lors d'une alarme, elle est inscrite dans le journal.
    result_elem = []
    journal()
    try:
        rows = len (driver.find_elements(By.XPATH, "//*[@class='event']/tbody/tr" ))
        # print(f"decouverte auto du nombre de lignes : {rows}")
        row_elem = 2      # la première est la ligne contenant le descriptif des colonnes
        columns = len (driver.find_elements(By.XPATH, "//*[@class='event']/tbody/tr[2]/td" ))
        # print(f"decouverte auto du nombre de colonnes : {columns}")
        for row in range(2, (row_elem + 4)):    # on lit les 4 dernières lignes inscrites dans le journal
            result_cell = []
            for column in range(1, (columns + 1)):
                XPath = f"//*[@class='event']/tbody/tr[{str(row)}]/td[{str(column)}]"
                cell_text = driver.find_element(By.XPATH, XPath).text
                result_cell.append(cell_text)
            result_elem.append(result_cell)
        # print(f"result_elem :  {result_elem}")
        return result_elem            # on retourne une liste de 4 listes
    except WebDriverException as err:
        app.logger.info(f"pb dans find_elem() erreur : {err}  ")

# exemple du journal lors d'une alarme :
#
#     Date	    Heure	  Evénements	            Eléments concernés
#
#   30/09/26	16h27	Fin appels tél	            TRANSMETTEUR(123456)
#   30/09/26	16h26	Mise OFF (Zone ABC)  	    TELECDE ROMU(654321)
#   30/09/26	16h26	Alarme (Zone A)	            VOL. SALON(135790)
#   30/09/26	16h26	Début appels tél	        TRANSMETTEUR(123456)
#   30/09/26	16h23	Mise ON (Zone ABC)	        TRANSMETTEUR(123456)

#   14/10/26	12h27	Mise OFF (Zone ABC)	        CLAVIER LCD(024680)
#   14/10/26	10h33	Fin appels tél	            TRANSMETTEUR(123456)
#   14/10/26	10h32	Début appels tél	        TRANSMETTEUR(123456)
#   14/10/26	10h32	Perte reseau gsm	        TRANSMETTEUR(123456)
#   14/10/26	09h46	Mise ON (Zone ABC)	        CLAVIER LCD(024680)
#   14/10/26	07h06	Mise OFF (Zone ABC)	        TELECDE(654321)
#   14/10/26	04h21	Fin appels tél	            TRANSMETTEUR(123456)
#   14/10/26	04h20	Début appels tél	        TRANSMETTEUR(123456)
#   14/10/26	04h20	Piles faibles (Zone SYS)	TRANSMETTEUR(123456)
#   13/10/26	23h49	Mise ON (Zone ABC)	        TRANSMETTEUR(123456)


def alarmstate():
    global memo_alarm
    #global l_delta
    # date_alarme = datetime.now()
    # date_alarme_reset = datetime.now() + timedelta(seconds=60)

    # print("-->  dans alarmstate() : y-a-t-il une alarme ?")
    # <div id="alarmstate">
    #     <div id="alarmstatedetails">
    #             <a href="u_listelmt.htm">Détails</a>
    #     </div>
    #     <div id="alarmstatetitle">Etat du système</div>
    #         <div class="pbattery_ok">Piles OK</div>                   <!-- <div class="pbattery_nok">Piles faibles</div> -->
    #         <div class="pcom_ok">Communication radio OK</div>
    #         <div class="pdoor_ok">Porte ou fenêtre fermée</div>
    #         <div class="phouse_ok">Pas d'alarme</div>                 <!-- <div class="phouse_int">Alarme Intrusion</div> -->
    #         <div class="pbox_ok">Boîtier OK</div>
    #         <div class="pgsm_5_ok">GSM connecté au réseau</div>       <!-- <div class="pgsm_0_ok">Echec de connexion au réseau GSM</div> -->
    #                                                                   <!-- <div class="pgsm_0_nok">Echec de connexion au réseau GSM</div> -->
    #         <div class="pcam_serv_off">Caméra non activée</div>
    #     </div>

    AF_BTN = {"pbattery_ok": "Piles OK", "pbattery_nok": "Piles faibles",
              "pcom_ok": "Communication radio OK",
              "pdoor_ok": "Porte ou fenêtre fermée",
              "phouse_ok": "Pas d'alarme", "phouse_int": "Alarme Intrusion",
              "pbox_ok": "Boîtier OK",
              "pgsm_5_ok": "GSM connecté au réseau", "pgsm_5_KO": "Defaut reseau gsm",
              "pcam_serv_on": "Caméra activée", "pcam_serv_off": "Caméra non activée",
              }

    try:
        # search_asur = driver.find_elements(By.XPATH, "/html/body/div/div/div[4]/div[1]/div")
        # search_asur = driver.find_elements(By.XPATH, "//div[@id='alarmstate']/div[@class='pcom_ok']")
        search_asur = driver.find_elements(By.XPATH, "//div[@id='alarmstate']/div[contains(class, '')]")
        if not memo_alarm :
            # print("si pas d'alarme")
            # now = datetime.now()
            for el in search_asur:
                # print("el : ", el)
                if el.get_attribute("class"):
                    elem = el.get_attribute("class")
                    # print(elem, "\t\t", el.text)
                    if elem not in ["pbattery_ok",  # "pbattery_nok"
                                    "pcom_ok",
                                    "pdoor_ok",
                                    "phouse_ok",    # "phouse_int"
                                    "pbox_ok",
                                    # "pgsm_5_ok",  # "pgsm_5_nok" ?
                                    "pgsm_missing",   # suite arrêt 2G, pgsm_5_ok passe à pgsm_0_ok puis à pgsm_0_nok le lendemain !
                                    "pcam_serv_off"] :
                        alarme = f"alarme pour l'élément : {elem}    detail :  {el.text}"
                        memo_alarm = True
                        app.logger.info(f"alarme pour l'élément : {elem}    detail :  {el.text}")
                        # print('alarme : ', alarme)
                        if SMS_FREE:
                            send_sms_free(alarme)
                        if SMS_123:
                            for name, numero in MOBILE.items():
                                rep_123_sms = send_123_sms(numero, alarme)
                                app.logger.info(f" réponse envoi 123_sms : {rep_123_sms}")
                        rep_find_elem = find_elem()
                        date = ""
                        heure = ""
                        evenement = ""
                        element_concerne = ""
                        for line in rep_find_elem:
                            if 'Piles faibles' in line[2] or 'Alarme' in line[2]:
                                # or 'Perte reseau gsm' in line[2]   retiré car réseau 2G arrété le 19/10/2026 !
                                date = line[0] or datetime.now()
                                heure = line[1] or "00h00"
                                evenement = line[2] or "pas d'évènement !"
                                element_concerne = line[3].replace('\n', ' ') or "élément concerné non trouvé !"
                            else:
                                pass
                                # print("Pas d éléments en alarme.")
                        if date and heure and evenement and element_concerne:
                            app.logger.info(f" élément : {date}  {heure}  {evenement}  {element_concerne}")
                            if SMS_FREE:
                                send_sms_free(f"{date}  {heure}  {evenement}  {element_concerne}")
                            if SMS_123:
                                for name, numero in MOBILE.items():
                                    rep_123_sms = send_123_sms(numero, f"{date}  {heure}  {evenement}  {element_concerne}")
                                    app.logger.info(f" réponse envoi 123_sms : {rep_123_sms}")

                        # Alarme VOL.ENTREE.
                        # Alarme VOL.SALON.
                        # Alarme GRENIER.
                        # Alarme SOUS-SOL.
                        # Coupure secteur
                        # Piles faibles SIR. INT..
                        # Piles faibles CLAVIER LCD.
                        # Piles faibles VOL.SALON.
                        # Piles faibles TRANSMETTEUR.
                        # Defaut reseau gsm
                        # Perte reseau gsm
                        # Module GSM absent          après avoir enlevé le module GSM désormais inutile !
                        # Echec de connexion au réseau GSM
                        # etc...
                        pilot()
                        return
        else :
            pass
            # print("Alarme !")

    except WebDriverException as err:
        # print("pb de lecture des class_name sur 'alarmstatetitle'")
        app.logger.info(f"pb de lecture des class_name sur 'alarmstatetitle'  erreur : {err} ")
        error_alarme = f"problème dans alarmstate() ! \n  erreur : {err} "
        return error_alarme

    ''' 			    Détails  Etat du système
               quand pas alarme :              |           quand alarme :
          class          classe.text           |       class        classe.text
                                               |
        pbattery_ok    Piles OK                +   pbattery_nok    Piles faibles
        pcom_ok        Communication radio OK  |
        pdoor_ok       Porte ou fenêtre fermée |
        phouse_ok      Pas d'alarme            +   phouse_int      Alarme Intrusion
        pbox_ok        Boîtier OK              |
        pgsm_5_ok      GSM connecté au réseau  |
                                               |   pcam_serv_off   Caméra non activée '''


def groupstate():
    # print("-->  dans groupstate() : état des zones alarme  Marche/Arrêt , en alarme Oui/Non...")
    # print("------ RECUPERATION DE L'ETAT DE L'ALARME'' ------")
    ### <div id="groupstate"><div id="groupa"><div class="alarmoff ">Arrêté ###
    ### </div><br><div class="noalarm ">Pas d'alarme                        ###
    ### </div></div><div id="groupb"><div class="alarmoff ">Arrêté          ###
    ### </div><br><div class="noalarm ">Pas d'alarme                        ###
    ### </div></div><div id="groupc"><div class="alarmoff ">Arrêté          ###
    ### </div><br><div class="noalarm ">Pas d'alarme                        ###
    ### </div></div></div>

    #  "zone_A" :    ["groupa"  ,  alarmoff/alarmon   ,  noalarm/alarm]
    #  "zone_B" :    ["groupb"  ,  alarmoff/alarmon   ,  noalarm/alarm]
    #  "zone_C" :    ["groupc"  ,  alarmoff/alarmon   ,  noalarm/alarm]

    # ZONE par défaut arrêtée et sans alarme:
    # ZONE = {"zone_A": ["grpa", "off ", "no "],
    #         "zone_B": ["grpb", "off ", "no "],
    #         "zone_C": ["grpc", "off ", "no" ],
    #         }

    cpt_grp = 0          # compteur groupe[abc] en arrêt
    red = '#F23535'
    green = '#32AA35'
    black = '#000000'
    color = black
    err_elem = 0
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "groupstate")))
    # si 'groupa' est présent, on suppose que 'groupb' et 'groupc' le sont aussi.
    for group in ["groupa", "groupb", "groupc",]:
        rech_off = f"//div[@id='{group}']/div[@class='alarmoff ']"
        rech_on = f"//div[@id='{group}']/div[@class='alarmon ']"
        try:
            # WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "groupstate")))
            result_off = driver.find_element(By.XPATH, rech_off)
            # print(f'-----> result_off : {result_off}')
            if result_off.text == 'Arrêté' :    # confirme le 'rech_off'
                color = green
                cpt_grp += 1
        except WebDriverException as err:
            # app.logger.info(f"groupstate result_off erreur : {err} ")
            # err_elem += 1
            try:
                # WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "groupstate")))
                result_on = driver.find_element(By.XPATH, rech_on)
                # print(f'-----> result_on : {result_on}')
                if result_on.text == 'En marche' :  # confirme le 'rech_on'
                    color = red
            except WebDriverException as err:
                # print("impossible de trouverl'état des alarmes")
                # app.logger.info(f"groupstate result_on erreur : {err} ")
                #err_elem += 1
                color = black
        finally:
            # if err_elem > 4:
            #     # on relance
            #     app.logger.info(f"groupstate: ne trouve pas la class 'alarmoff ou alarme_on'")
            # la met à disposition du serveur web
            # print ("f'color{group}', color   :  ", f'color{group}', color)
            # app.logger.info(f"color{group} : {color}")
            shared.set(f'color{group}', color)      # , time=50

    if cpt_grp > 0:
        color = green
    else :
        color = red
    shared.set('colorgroupabc', color)
    # print ("'colorgroupabc', color   :  ", 'colorgroupabc', color)


def boucle_principale():
    while OK:
        # print("-->  dans boucle principale...")
        # OK = False
        t_boucle = 3                     # tempo pour la boucle de surveillance (sec.)
        t_refresh = 310                    # [5mn] temps rafraichissement page (sec.)
        t_cpt = t_refresh // t_boucle      # nb de 't_boucle' total pour avoir 't_refresh'
        v_cpt = 0                          # compteur de 't_boucle'
        # app.logger.info(f"Actuellement, le taux de rafraichissement est de : {t_refresh//60} mn et {t_refresh%60} sec")
        while True:
            try:
                v_cpt += 1
                debut = time.perf_counter()
                groupstate()
                fin = time.perf_counter()
                duree = fin - debut
                if duree > 0.5:
                    app.logger.info(f"Temps d'exécution de groupstate() un peu long... : {duree:.6f} secondes")
                debut = time.perf_counter()
                alarmstate()
                fin = time.perf_counter()
                duree = fin - debut
                if duree > 0.5:
                    app.logger.info(f"Temps d'exécution d'alarmstate() un peu long... : {duree:.6f} secondes")
                cde = shared.get('OnOff')      # index.py : shared.set('OnOff', cde_bouton, time=5)
                if cde:
                    # print(f"reception de la cde '{cde}'.")
                    # app.logger.info(f"reception de la cde '{cde}'.")
                    if cde == 'Marche A':
                        search_btn = driver.find_element(By.NAME, "btn_zone_on_A")
                        search_btn.click()
                        app.logger.info(f"Mise en route de la zone A !")
                    elif cde == 'Marche B':
                        search_btn = driver.find_element(By.NAME, "btn_zone_on_B")
                        search_btn.click()
                        app.logger.info(f"Mise en route de la zone B !")
                    elif cde == 'Marche C':
                        search_btn = driver.find_element(By.NAME, "btn_zone_on_C")
                        search_btn.click()
                        app.logger.info(f"Mise en route de la zone  !")
                    elif cde == 'Marche A B C':
                        search_btn = driver.find_element(By.NAME, "btn_zone_on_ABC")
                        search_btn.click()
                        app.logger.info(f"Mise en route de la zone ABC !")
                    elif cde == 'Arrêt A B C':
                        search_btn = driver.find_element(By.NAME, "btn_zone_off_ABC")
                        search_btn.click()
                        app.logger.info(f"Arrêt de l'alarme demandée !")
                    elif cde == 'Test':
                        pass
                        app.logger.info(f"Bouton TEST appuyé !")
                    else:
                        info_cmd = f"---  commande '{cde}' non reconnue  ---"
                        app.logger.info(f"---  commande '{cde}' non reconnue  ---")
                        if SMS_FREE:
                            send_sms_free(info_cmd)
                        if SMS_123:
                            for name, numero in MOBILE.items():
                                rep_123_sms = send_123_sms(numero, info_cmd)
                                app.logger.info(f" réponse envoi 123_sms : {rep_123_sms}")
                    info_cmd = f" '{cde}' a été envoyé à la centrale"
                    # app.logger.info(f"'{cde}' a été envoyé à la centrale")
                    if SMS_FREE:
                        send_sms_free(info_cmd)
                    if SMS_123:
                        for name, numero in MOBILE.items():
                            rep_123_sms = send_123_sms(numero, info_cmd)
                            app.logger.info(f" réponse envoi 123_sms : {rep_123_sms}")
                    shared.set('OnOff', None)        # on efface la valeur de 'cde'
                    time.sleep(0.2)
                    cde = None
                time.sleep(t_boucle)
                if v_cpt > t_cpt:
                    refresh()         # permet le rafraichissement de la fenêtre de pilotage des automatismes
                    v_cpt = 0         # tous les 't_refresh' secondes.
                # print(f"boucle : {v_cpt}")
            except WebDriverException as err:
                app.logger.info(f"boucle principale, erreur WebDriverException : {err} ")
                # trouverInstanceServeur()
                # login()
                # pilot()
            except Exception as err:
                app.logger.info(f"boucle principale, erreur Exception Python: {err} ")
            finally:
                time.sleep(1)
                # print(f"sleep 1sec.")

def main():
    login()
    time.sleep(0.5)
    pilot()
    time.sleep(0.5)
    boucle_principale()

if __name__ == "__main__":
        main()

#   driver.quit()
#   send_sms_free("L'application monitoring de la centrale s'est terminée anormalement")


"""                                                                    colonne ci dessous si une des alarmes est activée
<div id="content" class="contentdrive">
    <div id="alarmstate">
        <div id="alarmstatedetails">
                <a href="u_listelmt.htm">Détails</a>
        </div>
        <div id="alarmstatetitle">Etat du système</div>
            <div class="pbattery_ok">Piles OK</div>                   <!-- <div class="pbattery_nok">Piles faibles</div> -->
            <div class="pcom_ok">Communication radio OK</div>
            <div class="pdoor_ok">Porte ou fenêtre fermée</div>
            <div class="phouse_ok">Pas d'alarme</div>                 <!-- <div class="phouse_int">Alarme Intrusion </div> -->
            <div class="pbox_ok">Boîtier OK</div>
            <div class="pgsm_5_ok">GSM connecté au réseau</div>
            <div class="pcam_serv_off">Caméra non activée</div>
        </div>
    <div id="groupstate">
        <div id="groupa">
            <div class="alarmoff ">Arrêté</div>
            <br>
            <div class="noalarm ">Pas d'alarme</div>
        </div>
        <div id="groupb">
            <div class="alarmoff ">Arrêté</div>
            <br>
            <div class="noalarm ">Pas d'alarme</div>
        </div>
        <div id="groupc">
            <div class="alarmoff ">Arrêté</div>
            <br>
            <div class="noalarm ">Pas d'alarme</div>
        </div>
    </div>
<form method="post" action="u_pilotage.htm" name="u_pilotage">
    <input type="hidden" name="hidden" value="hidden">
    <div id="groupdrive">
        <input type="submit" name="btn_zone_on_A" value="Marche A" class="emptydark">
        <input type="submit" name="btn_zone_on_B" value="Marche B" class="emptydark">
        <input type="submit" name="btn_zone_on_C" value="Marche C" class="emptydark">
        <input type="submit" name="btn_zone_on_ABC" value="Marche A B C" class="longemptydark">
        <input type="submit" name="btn_zone_off_ABC" value="Arrêt A B C" class="fatemptydark">
    </div>
    <div id="stuffdrive">
        <div id="shutterdrive">
            <input type="submit" name="btn_vol_up" value="" class="shutterupdark">
            <input type="submit" name="btn_vol_stop" value="" class="shutterstopdark">
            <input type="submit" name="btn_vol_down" value="" class="shutterdowndark">
        </div>
        <div id="shutterimg">&nbsp;
        </div>
        <div id="lightdrive">
            <input type="submit" name="btn_lum_on" value="ON" class="roundemptydark">
            <input type="submit" name="btn_lum_off" value="OFF" class="roundemptydark">
        </div>
        <div id="lightimg">&nbsp;
        </div>
    </div>f
</form>
</div>
"""





"""
    Selenium Exception	                                        Description

DetachedShadowRootException ([msg, écran, ...])       Lancé lorsque la racine fantôme référencée n'est plus attachée au DOM.
ElementClickInterceptedException ([msg, ...])         Une exception est levée lorsque le clic sur un élément échoue car un autre élément le masque.
ElementNotInteractableException ([msg, ...])          Lancé lorsque des interactions entre éléments risquent d'en toucher un autre en raison de l'ordre de peinture.
ElementNotSelectableException ([msg, écran, ...])     Erreur levée lors de la tentative de sélection d'un élément non sélectionnable.
ElementNotVisibleException ([msg, écran, ...])        Cette exception est levée lorsqu'un élément est présent dans le DOM, mais qu'il n'est pas visible et qu'il est donc impossible d'interagir avec lui.
ImeActivationFailedException ([msg, écran, ...])      Lancé en cas d'échec de l'activation d'un moteur IME.
ImeNotAvailableException ([msg, écran, ...])          Erreur levée lorsque la prise en charge IME n'est pas disponible.
InsecureCertificateException ([msg, écran, ...])      Lancé lorsque l'agent utilisateur rencontre un avertissement de certificat  (certificat TLS expiré ou invalide).
InvalidArgumentException ([msg, écran, ...])          Les arguments passés à une commande sont soit invalides, soit mal formés.
InvalidCookieDomainException ([msg, écran, ...])      Une exception est levée lors de la tentative d'ajout d'un cookie sous un domaine différent.
InvalidCoordinatesException ([msg, écran, ...])       Les coordonnées fournies à l'opération d'interaction sont invalides.
InvalidElementStateException ([msg, écran, ...])      Levée lorsqu'une commande n'a pas pu être exécutée car l'élément se trouve dans un état invalide.
InvalidSelectorException ([msg, écran, ...])          Exception levée lorsque le sélecteur utilisé pour trouver un élément ne renvoie pas un WebElement.
InvalidSessionIdException ([msg, écran, ...])         Levée lorsque l'identifiant de session donné ne figure pas dans la liste des sessions actives.
InvalidSwitchToTargetException ([msg, ...])           Exception levée lorsque la fenêtre ou le cadre cible à basculer n'existe pas.
JavascriptException ([msg, écran, trace de pile])     Une erreur s'est produite lors de l'exécution du code JavaScript fourni par l'utilisateur.
MoveTargetOutOfBoundsException ([msg, ...])           Lancé lorsque la cible fournie à la méthode move () d'ActionsChains est invalide, c'est-à-dire hors du document.
NoAlertPresentException ([msg, écran, ...])           Erreur générée lors du passage à l'absence d'alerte.
NoSuchAttributeException ([msg, écran, ...])          Une exception est levée lorsque l'attribut de l'élément est introuvable.
NoSuchCookieException ([msg, écran, trace de pile])   Une exception est levée lorsqu'aucun cookie correspondant au nom de chemin spécifié n'a été trouvé.
NoSuchDriverException ([msg, écran, trace de pile])   Erreur levée lorsque le conducteur n'est pas spécifié et ne peut être localisé.
NoSuchElementException ([msg, écran, trace de pile])  Une exception est levée lorsque l'élément est introuvable.
NoSuchFrameException ([msg, écran, trace de pile])    Une exception est levée lorsque la cible de la trame à changer n'existe pas.
NoSuchShadowRootException ([msg, écran, ...])         Levée lors de la tentative d'accès à la racine fantôme d'un élément alors qu'aucune racine fantôme n'y est attachée.
NoSuchWindowException ([msg, écran, trace de pile])   Exception levée lorsque la fenêtre cible à basculer n'existe pas.
ScreenshotException ([msg, écran, trace de pile])     La capture d'écran s'est avérée impossible.
SessionNotCreatedException ([msg, écran, ...])        Impossible de créer une nouvelle session.
StaleElementReferenceException ([msg, ...])           Lancé lorsqu'une référence à un élément est désormais « obsolète ».
TimeoutException ([msg, écran, trace de pile])        Exception levée lorsqu'une commande ne s'exécute pas dans un délai suffisant.
UnableToSetCookieException ([msg, écran, ...])        Une exception est levée lorsqu'un pilote ne parvient pas à définir un cookie.
UnexpectedAlertPresentException ([msg, ...])          Déclenché lorsqu'une alerte inattendue est apparue.
UnexpectedTagNameException ([msg, écran, ...])        Une exception est levée lorsqu'une classe de support n'a pas reçu l'élément web attendu.
UnknownMethodException ([msg, écran, trace de pile])  La commande demandée correspondait à une URL connue, mais ne correspondait à aucune méthode pour cette URL.
WebDriverException ([msg, écran, trace de pile])      Exception du pilote Web de base.

"""
