while read line; do

cd /edx/app/edxapp/edx-platform
source /edx/app/edxapp/edxapp_env
echo ============$line=============================
sudo -E -u edxapp env "PATH=$PATH" /edx/app/edxapp/venvs/edxapp/bin/python manage.py cms sqlmigrate --settings=aws $line
done < cms_upgrade.log > cms_migration_sql.sql
