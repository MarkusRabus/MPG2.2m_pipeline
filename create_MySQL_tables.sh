#!/bin/bash

cd django
python manage.py migrate
python manage.py makemigrations FEROS
python manage.py sqlmigrate FEROS 0001
python manage.py migrate