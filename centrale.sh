#! /usr/bin/bash

# cd /home/romu/developpement/SELENIUM
# source .centrale/bin/activate
echo "Date : $(date)"
echo "lancement du serveur web, notre interface avec la programme de surveillance."

# version http://localhost:5000
# cd /home/romu/developpement/SELENIUM && source .centrale/bin/activate && screen -d -m -S index gunicorn --bind 0.0.0.0:5000 --workers 1 'index:app'

# version https://localhost:4443
# cd /home/romu/developpement/SELENIUM && source .centrale/bin/activate && screen -d -m -S index gunicorn --certfile=/PATH/certificate.pem --keyfile=/PATH/key.pem --bind 192.168.0.40:4443 --workers 4 'index:app'

# version https avec le fichier gunicorn.conf.py
cd /home/kligliro/developpement/centrale/centrale && source ../.centrale/bin/activate && screen -d -m -S index gunicorn 'index:app'

echo "lancement du prg centrale.py (surveille notre centrale par son interface web intégrée et met à jour notre serveur web lanncé ci-dessus))"
cd /home/kligliro/developpement/centrale/centrale && source ../.centrale/bin/activate && screen -d -m -S centrale python /home/kligliro/developpement/centrale/centrale/centrale.py
