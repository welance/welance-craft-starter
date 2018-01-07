#!/bin/sh


# this variables are the same used in Dockerfile
CRAFTROOT=/data/craft
WEBROOT=/data/craft/web
SCRIPTS_DIR=/data/scripts

# this variables should stay in the docker-compose file
# export CRAFT_USERNAME="admin"
# export CRAFT_EMAIL="admin@welance.de"
# export CRAFT_PASSWORD="welance"
# export CRAFT_SITENAME="example.com"
# export CRAFT_SITEURL="//localhost:7080"
# export CRAFT_LOCALE="en_us"
# export CRAFT_ENVIRONMENT=".dev"

export CRAFT_BASE_PATH=$CRAFTROOT
export CRAFT_APP_PATH="$CRAFT_BASE_PATH/web/"
export CRAFT_CONFIG_PATH="$CRAFT_BASE_PATH/config/"
# export CRAFT_PLUGINS_PATH="$CRAFT_BASE_PATH/plugins/"
export CRAFT_STORAGE_PATH="$CRAFT_BASE_PATH/storage/"
export CRAFT_TEMPLATES_PATH="$CRAFT_BASE_PATH/templates/"
export CRAFT_TEMPLATES_PATH="$CRAFT_BASE_PATH/migrations/"
# export CRAFT_TRANSLATIONS_PATH="$CRAFT_BASE_PATH/translations/"
export CRAFT_PUBLIC_PATH=$WEBROOT
export CRAFT_UPLOADS_PATH="$WEBROOT/uploads"
export ENV_LIVE=$CRAFT_CONFIG_PATH/.live

## move to the plugins folder
cd $CRAFT_PLUGINS_PATH
## download welance-craft-grid-plugin

# if is a live environment (not docker build run schematic)
if [ -f $ENV_LIVE ]; then
 # refresh setup using env vars (will be executed all the time)
 printf "%s\n" \
    '# autogenerated, do not edit' \
    "ENVIRONMENT='$CRAFT_ENVIRONMENT'" \
    "SECURITY_KEY='$CRAFT_SECURITY_KEY'" \
    "DB_DRIVER='$DB_DRIVER'" \
    "DB_SERVER='$DB_HOST'" \
    "DB_USER='$DB_USER'" \
    "DB_PASSWORD='$DB_PASS'" \
    "DB_DATABASE='$DB_NAME'" \
    "DB_SCHEMA='$DB_SCHEMA'" \
    "DB_TABLE_PREFIX=''" \
    "DB_PORT='$DB_PORT'" \
    > $CRAFT_BASE_PATH/.env

 echo "cheking database connection"
 # check if mysql is alive
 OUT=1
 while [ $OUT -eq 1 ]; do
  php -f $SCRIPTS_DIR/poll-db.php
  # php -f $CRAFT_BASE_PATH/craft craft-toolbox/welancecraft/poll-db
  OUT=$?
  echo "connection unavailable waiting 3 seconds before retry"
  sleep 3
 done
 #import schematic
 # cd /data
 # ./vendor/bin/schematic import

 # fix  privleges
 chown -R apache $CRAFTROOT
 chown -R apache $CRAFT_UPLOADS_PATH
 # run apache in foreground
 echo "launch apache2 in foreground"
 set -e
 # Apache gets grumpy about PID files pre-existing
 rm -f /var/www/run/httpd.pid
 /usr/sbin/httpd -DFOREGROUND $HTTPD_OPTIONS
fi
