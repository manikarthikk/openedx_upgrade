#!/bin/bash

while read line; do

cd /edx/app/edxapp/edx-platform
source /edx/app/edxapp/edxapp_env
sudo -E -u edxapp env "PATH=$PATH" /edx/app/edxapp/venvs/edxapp/bin/python manage.py lms sqlmigrate --settings=aws $line
done < lms_upgrade.log > lms_migration_sql.sql
