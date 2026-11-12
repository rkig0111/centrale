#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
import datetime
import memcache

shared = memcache.Client(['127.0.0.1:11211'], debug=1)

# Application Flask
app = Flask(__name__)   # le nom app est utilisé par le fichier wsgi

# Page HTML de base
pageHTML = "index2.html"

# @app.route("/")
# def index (action):
#     if action == "rouge" :
#         GPIO.output(rouge, True)
#         GPIO.output(bleue, False)
#         GPIO.output(verte, False)
#     if action == "vert" :
#         GPIO.output(rouge, False)
#         GPIO.output(bleue, False)
#         GPIO.output(verte, True)
        
@app.route("/")
def index(onoffswitch):
    now=datetime.datetime.now()
    timeString=now.strftime("%Y-%m-%d %H:%M:%S")
    templateData={
         'title':'Raspberry Pi SOMFY monitoring',
         'time':timeString,
         }
    # cde_switch = request.form.get('onoffswitch')
    if onoffswitch == 'on':
        print("action = 'on'")
    elif onoffswitch == 'off':
        print("action = 'off'")
    else:
        print("Cde non reconnue !")    
    print(f"'---> index.py' : envoi de la cde {cde_switch}")
    return render_template(pageHTML,**templateData)

if __name__ == "__main__":
    app.run(host='192.168.0.17', debug = False)    #   port 5000 par defaut
						   # , port=80  avec sudo

