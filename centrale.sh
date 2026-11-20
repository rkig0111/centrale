#! /usr/bin/bash

echo "Date : $(date)"

echo "lancement du serveur web"
# notre interface avec la programme de surveillance.
# version https avec le fichier gunicorn.conf.py
cd /home/romu/developpement/centrale && source .centrale/bin/activate && screen -d -m -S index gunicorn 'index:app'

echo "lancement du prg centrale.py"
# surveille notre centrale par son interface web intégrée et met à jour notre serveur web lanncé ci-dessus
cd /home/romu/developpement/centrale && source .centrale/bin/activate && screen -d -m -S centrale python ~/developpement/centrale/centrale.py
