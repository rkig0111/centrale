#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
import datetime
import memcache
import logging
# from werkzeug.middleware.proxy_fix import ProxyFix

# Application Flask
app = Flask(__name__)   # le nom app est utilisé par le fichier wsgi, on récupère ici 'index'

# Basic logging setup
app.logger.setLevel("INFO")
# suppression des handlers existants
# for h in app.logger.handlers:
#     app.logger.removeHandler(h)
handler = logging.FileHandler("centrale.log")
handler.setLevel("INFO")
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(module)s :: %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
logging.getLogger("werkzeug").addHandler(handler)

shared = memcache.Client(['127.0.0.1:11211'], debug=1)

# Page HTML de base
pageHTML = "index.html"

@app.route("/", methods=['GET', 'POST'])
def index():
    colora = shared.get('colorgroupa')
    colorb = shared.get('colorgroupb')
    colorc = shared.get('colorgroupc')
    colorabc = shared.get('colorgroupabc')
    # print(f"récupération des couleurs  {colora}, {colorb}, {colorc}, {colorabc}")
    now=datetime.datetime.now()
    timeString=now.strftime("%Y-%m-%d %H:%M:%S")
    templateData={
         'title':'Raspberry Pi SOMFY monitoring',
         'time':timeString,
         'colorabc':colorabc,
         'colora':colora,
         'colorb':colorb,
         'colorc':colorc,
         }
    cde_bouton = request.form.get('action')        # Renvoie la zone à allumer ou éteindre
    shared.set('OnOff', cde_bouton, time=5)        # la met à disposition du prg principal
    if cde_bouton:
        pass
        # print(f"envoi de la cde '{cde_bouton}'.")
        app.logger.info(f"envoi de la cde '{cde_bouton}'.")
    return render_template(pageHTML,**templateData)


# Script de débuggage (n'est pas exécuté quand le module est importé par wsgi)
if __name__ == "__main__":
    # app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    # app.run(port=443, ssl_context=("localhost+3.pem", "localhost+3-key.pem"))
    app.run(host='192.168.0.40', debug = False)    #   port 5000 par defaut, port=80  avec sudo


"""
# portion de code pour tuer le pid de gunicorn qui empêche l'application index.py de se relancer.
# mais je ne l'utilise plus.

cmd = "sudo ss -tlpn sport = :4443"
cmdarray = cmd.split()
shell_cmd = subprocess.run(cmdarray, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
# print("shell_cmd.stdout  :  ", shell_cmd.stdout)
# print("shell_cmd.stderr  :  ", shell_cmd.stderr)

lines = []
line = ""
result =""
for x in shell_cmd.stdout:
    if x == "\n":
        lines.append(line)
        line = ""
    else:
        line += x

for line in lines:
    if 'pid' in line:
        # print(line)
        result = line.split()
        print(result[5])

pattern = "pid=[0-9]{3,}"           # pour être sûr que l'on soit bien sur les pid !
liste_pid=re.findall(pattern, result[5])

# >>> liste_pid
# ['pid=3702', 'pid=3701', 'pid=3700', 'pid=3699', 'pid=3697']
# >>> liste_pid[-1]         # c'est le dernier processus de la liste qu'il faut tuer
# 'pid=3697'                # qui est en fait le 1er lancé. ( id le plus petit )!
# >>> liste_pid[-1].split('=')
# ['pid', '3697']
# >>> liste_pid[-1].split('=')[1]
# '3697'
# >>> int(liste_pid[-1].split('=')[1])
# 3697

pid = int(liste_pid[-1].split('=')[1])

import signal

try:
    os.kill(pid, signal.SIGTERM)
    print(f"Sent SIGTERM signal to process {pid}")
except OSError:
    print(f"Failed to send SIGTERM signal to process {pid}")



# ['LISTEN', '0', '2048', '192.168.0.17:4443', '0.0.0.0:*', 'users:(("gunicorn",pid=3702,fd=3),("gunicorn",pid=3701,fd=3),("gunicorn",pid=3700,fd=3),("gunicorn",pid=3699,fd=3),("gunicorn",pid=3697,fd=3))']
#      0      1      2             3                4                     5
#
# 'users:(
# ("gunicorn",pid=3702,fd=3),
# ("gunicorn",pid=3701,fd=3),
# ("gunicorn",pid=3700,fd=3),
# ("gunicorn",pid=3699,fd=3),
# ("gunicorn",pid=3697,fd=3))    <----  os.kill(pid, signal.SIGTERM)

"""
