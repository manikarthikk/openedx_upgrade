while read line; do

sudo su edxapp -s /bin/bash
cd ~ && source edxapp_env    
cd edx-platform 
echo "/*============$line=============================*/"
python manage.py cms sqlmigrate --settings=aws tagging 0001
done > cms_migration_sql.sql
