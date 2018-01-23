#! /usr/bin/env python
# -*- coding: utf-8 -*-
""" butler allows to setup a welance craft3 cms project """

import sys
import inspect
from pathlib import Path
import os
import secrets
import subprocess
import json
import yaml


""" name of the out configuration file """
SCRIPT_NAME = "butler.py"


class Commander(object):
    """ main class for command exectution"""
    STAGE_DOMAIN = "staging.welance.de"
    DEFAULT_SLACK_CHANNEL = "general"
    DEFAULT_SITE_NAME = "Welance"
    DEFAULT_LOCAL_URL = "localhost"
    DEFAULT_DB_DRIVER = "mysql"

    # dictionary with the messages to print in th prompt
    prompts = {
        "project_ovverride":"The project is already setup boss, do you want to overwrite the configuration? (yes/no)? [no]: ",
        "setup_abort":"orrait boss, setup canceled, bye!",
        "customer_number":"Please enter the customer number, boss: ",
        "project_number":"Now enter the project number: ",
        "slack_channel": "What is the slack channel for this project? [%s]:  " % DEFAULT_SLACK_CHANNEL,
        "site_name": "And the site name? [%s]: " % DEFAULT_SITE_NAME,
        "local_url": "Url for development: [%s]" % DEFAULT_LOCAL_URL,
        "db_driver": "which database will you use pgsql/mysql? [%s]:" % DEFAULT_DB_DRIVER,
        "setup_confirm": "are this info correct? (yes/no)? [no]: ",
        "project_teardown" : "This action will remove all containers including data, do you want to continue (yes/no)? [no] "
    }

    def __init__(self):
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        script_path = Path(filename).resolve()
        self.project_path = script_path.parent.parent
        self.config_path = "%s/%s" % (script_path.parent, '.env.json')
        self.project_conf = {}
        if os.path.exists(self.config_path):
            fp = open(self.config_path, 'r')
            self.project_conf = json.load(fp)
            fp.close()
        # path for staging and local yaml
        self.local_yml = os.path.join(self.project_path, "docker",
                                      "docker-compose.yml")
        self.stage_yml = os.path.join(self.project_path, "docker",
                                      "docker-compose-staging.yml")

    def prjc(self, sep="_"):
        """shortcut to get project coordinates like C_P"""
        return "%s%s%s" % (self.project_conf['customer_number'], sep, 
                               self.project_conf['project_number'])

    def docker_compose(self, params, yaml_path="docker-compose.yaml"):
        """ execte docker-compose commmand """
        cmd = "docker-compose -f %s %s " % (yaml_path, params)
        print(cmd)
        subprocess.run(cmd,shell=True,check=True)

    def docker_exec(self, container_target, command, additional_options=""):
        """ execte docker exec commmand """
        cmd = """docker exec -i "%s" sh -c '%s' %s""" % (container_target, command, additional_options)
        print(cmd)
        subprocess.run(cmd, shell=True, check=True)

    def prompt_yesno(self, prompt_key):
        """ prompt the user for a yes/no question, when yes return true, false otherwise"""
        val = input(self.prompts[prompt_key])
        if val.strip().lower() == 'yes':
            return True
        return False

    def prompt_int(self, prompt_key):
        """ prompt user for a int value, keep asking until a correct value is entered"""
        val = ""
        while True:
            try:
                val = input(self.prompts[prompt_key])
                if int(val) < 0:
                    raise ValueError("")
                break
            except ValueError:
                print(" sorry boss, must be a number greater than 0")
        return val

    def prompt_string(self, prompt_key, default_val=""):
        """ read a string from a command line, apply default_val if the input is empty"""
        val = input(self.prompts[prompt_key]).strip()
        if not val:
            val = default_val
        return val

    def write_file(self, filepath, data):
        """ write a file to the filesystem """
        fp = open(filepath, 'w')
        fp.write(data)
        fp.close()
    
    #
    #  COMMANDS
    #
    
    def cmd_help(self):
        """ print help """
        print ('%s <command>' % SCRIPT_NAME)
        print ('where command are')

        # get all the commands
        for name, obj in inspect.getmembers(self, inspect.ismethod):
            if (name.startswith('cmd_')):
                print(" %14s - %s" % (name[4:].replace("_","-"), obj.__doc__))

    def cmd_setup(self):
        """ set up the application """

        # if the config  already exists prompt what to do
        if self.project_conf and not self.prompt_yesno('project_ovverride'):
            print(self.prompts['setup_abort'])
            return
        ## ask for customer number
        self.project_conf['customer_number'] = self.prompt_int('customer_number')
        self.project_conf['project_number'] = self.prompt_int('project_number')
        self.project_conf['slack_channel'] = self.prompt_string(
            'slack_channel', self.DEFAULT_SLACK_CHANNEL)
        self.project_conf['site_name'] = self.prompt_string('site_name',
                                                       self.DEFAULT_SITE_NAME)
        self.project_conf['local_url'] = self.prompt_string('local_url',
                                                       self.DEFAULT_LOCAL_URL)
        self.project_conf['db_driver'] = self.prompt_string('db_driver',
                                                       self.DEFAULT_DB_DRIVER)
        # build stage domain
        self.project_conf['stage_url'] = '%s.%s' % (self.prjc(sep=".") ,self.STAGE_DOMAIN)

        ## print summary
        print("")
        print("Customer Number: %s" % self.project_conf['customer_number'])
        print("Project  Number: %s" % self.project_conf['project_number'])
        print("Slack channel  : %s" % self.project_conf['slack_channel'])
        print("Site Name      : %s" % self.project_conf['site_name'])
        print("Local Url      : %s" % self.project_conf['local_url'])
        print("Staging Url    : %s" % self.project_conf['stage_url'])
        print("Db Driver      : %s" % self.project_conf['db_driver'])
        print("")
        ## ask for confirmation
        if (not self.prompt_yesno('setup_confirm')):
            print(self.prompts['setup_abort'])
            return
        # generate security key
        self.project_conf["security_key"] = secrets.token_hex(32)
        # set the other default values
        self.project_conf["docker_image_craft"] = "welance/craft3"
        self.project_conf["db_schema"] = "public"
        self.project_conf["db_server"] = "database"
        self.project_conf["db_database"] = "craft"
        self.project_conf["db_user"] = "craft"
        self.project_conf["db_password"] = "craft"
        self.project_conf["db_table_prefix"] = "craft_"
        self.project_conf["craft_username"] =  "admin"
        self.project_conf["craft_email"] =  "admin@welance.de"
        self.project_conf["craft_password"] =  "welance"
        self.project_conf["lang"] = "C.UTF-8"
        self.project_conf["environment"] = "dev"
        self.project_conf["craft_locale"] = "en_us"
        self.project_conf["httpd_options"] = ""

        # docker-compose.ymk
        docker_compose = {
            "version": "2.1",
            "services": {
                "craft": {
                    "image": self.project_conf["docker_image_craft"],
                    "container_name": "craft_%s" % self.prjc(),
                    "ports": ["80:80", "443:443"],
                    "volumes": [
                        # webserver and php mounts
                        "/var/log",
                        "./craft/conf/apache2/ssl:/etc/apache2/ssl",
                        "./craft/conf/apache2/craft.conf:/etc/apache2/conf.d/craft.conf",
                        "./craft/conf/php/php.ini:/etc/php7/php.ini",
                        "./craft/logs/apache2:/var/log/apache2",
                        # adminer utility
                        "./craft/adminer:/data/adminer",
                        # craft
                        "../config:/data/craft/config",
                        "../templates:/data/craft/templates",
                        "../migrations:/data/craft/migrations",
                        "../plugins:/data/craft/plugins",
                        "../web/uploads:/data/craft/web/uploads",
                        "../composer.json:/data/craft/composer.json"
                    ],
                    "links": ["database"],
                    "environment": {
                        "LANG": self.project_conf["lang"],
                        "DB_DRIVER": self.project_conf['db_driver'],
                        "DB_SCHEMA": self.project_conf["db_schema"],
                        "DB_SERVER": self.project_conf["db_server"],
                        "DB_DATABASE": self.project_conf["db_database"],
                        "DB_USER": self.project_conf["db_user"],
                        "DB_PASSWORD": self.project_conf["db_password"],
                        "DB_TABLE_PREFIX": self.project_conf["db_table_prefix"],
                        "SECURITY_KEY": self.project_conf['security_key'],
                        "ENVIRONMENT": self.project_conf["environment"],
                        "CRAFT_USERNAME": self.project_conf["craft_username"],
                        "CRAFT_EMAIL": self.project_conf["craft_email"],
                        "CRAFT_PASSWORD": self.project_conf["craft_password"],
                        "CRAFT_SITENAME": self.project_conf['site_name'],
                        "CRAFT_SITEURL": self.project_conf['local_url'],
                        "CRAFT_LOCALE": self.project_conf["craft_locale"],
                        "HTTPD_OPTIONS": self.project_conf["httpd_options"]
                    }
                }
            }
        }
        if self.project_conf['db_driver'] == 'mysql':
            docker_compose["services"]["database"] = {
                "image":
                "mysql:5.7",
                "command":
                "mysqld --character-set-server=utf8  --collation-server=utf8_unicode_ci --init-connect='SET NAMES UTF8;'",
                "container_name":
                "database_%s" % self.prjc(),
                "environment": {
                    "MYSQL_ROOT_PASSWORD": self.project_conf["db_password"],
                    "MYSQL_DATABASE": self.project_conf["db_database"],
                    "MYSQL_USER": self.project_conf["db_user"],
                    "MYSQL_PASSWORD": self.project_conf["db_password"]
                },
                "volumes": ["/var/lib/mysql"]
            }
            # set the correct DB_PORT for craft env
            docker_compose["services"]["craft"]["environment"]["DB_PORT"] = "3306"
        elif self.project_conf['db_driver'] == 'pgsql':
            docker_compose["services"]["database"] = {
                "image": "postgres:10-alpine",
                "container_name": "database_%s" % self.prjc(),
                "environment": {
                    "POSTGRES_PASSWORD": self.project_conf["db_password"],
                    "POSTGRES_USER": self.project_conf["db_user"],
                    "POSTGRES_DB": self.project_conf["db_database"]
                },
                "volumes": ["/var/lib/postgresql/data"]
            }
            # set the correct DB_PORT for craft env
            docker_compose["services"]["craft"]["environment"]["DB_PORT"] = "5432"
        else:
            print("the value for Db Driver must be mysql or pgsql")
            print(self.prompts['setup_abort'])
            return

        # save docker-composer
        self.write_file(self.local_yml,
                        yaml.dump(docker_compose, default_flow_style=False))
        # edit for docker-compose.staging.yaml
        docker_compose["services"]["craft"].pop("ports")
        docker_compose["services"]["craft"]["expose"] = [80, 443]
        docker_compose["services"]["craft"]["network_mode"] = "bridge"
        docker_compose["services"]["craft"]["environment"][
            "VIRTUAL_HOST"] = self.project_conf['stage_url']

        # save docker-composer
        self.write_file(self.stage_yml, yaml.dump(docker_compose))

        # save project conf
        self.write_file(self.config_path, json.dumps(self.project_conf, indent=2))
        # all done

        print("pull doker images images")
        self.docker_compose("pull --ignore-pull-failures", self.local_yml)
        print("create containers")
        self.docker_compose("--project-name %s up --no-start " % self.prjc(), self.local_yml)
        print("setup completed")

    def cmd_restore(self):
        """restore a project that has been teardown, recreating the configurations """
        # if the config  already exists prompt what to do
        if self.project_conf:
            print("pull doker images images")
            self.docker_compose("pull --ignore-pull-failures", self.local_yml)
            print("create containers")
            self.docker_compose("--project-name %s up --no-start " % self.prjc(), self.local_yml)
            print("setup completed")
            return
        print("there is nothing to restore, perhaps you want to setup?")

    def cmd_local_start(self):
        """start the local docker environment"""
        self.docker_compose("--project-name %s up -d" % self.prjc(), self.local_yml )

    def cmd_local_stop(self):
        """stop the local docker environment"""
        self.docker_compose("--project-name %s stop" % self.prjc(),
                            self.local_yml)

    def cmd_local_teardown(self):
        """destroy the local docker environment"""
        if self.prompt_yesno('project_teardown'):
            self.docker_compose("--project-name %s down -v" % self.prjc(),
                                self.local_yml)

    def cmd_seed_export(self):
        """export the database-seed.sql"""
        seed_file = os.path.join(self.project_path, "config",
                                 "database-seed.sql")
        # run mysql dump
        container_target = "database_%s" % self.prjc()
        command = """exec mysqldump -uroot -p"craft" --add-drop-table craft"""
        if self.project_conf["db_driver"] == "pgsql":
            command = """exec pg_dump --clean --if-exists -U craft -d craft"""
        additional_options = "> %s" % seed_file
        self.docker_exec(container_target, command, additional_options)

    def cmd_seed_import(self):
        """export the database-seed.sql"""
        seed_file = os.path.join(self.project_path, "config",
                                 "database-seed.sql")
        # run mysql dump
        container_target = "database_%s" % self.prjc()
        command = """exec mysql -uroot -p"craft" craft"""
        if self.project_conf["db_driver"] == "pgsql":
            command = """exec psql --quiet -U craft -d craft"""
        additional_options = "< %s" % seed_file
        self.docker_exec(container_target,command, additional_options)

    def cmds(self):
        pass

# main function
def main():
    """run the butler system"""

def cmd2method(cmd):
  return "cmd_%s" % cmd.replace("-","_")


if __name__ == '__main__':
    SCRIPT_NAME = sys.argv[0]
    c = Commander()
    if len(sys.argv) == 1 or not hasattr(c, cmd2method(sys.argv[1])):
        c.cmd_help()
        exit(0)
    getattr(c, cmd2method(sys.argv[1]))()
