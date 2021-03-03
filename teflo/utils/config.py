# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
    teflo.utils.config

    Teflos own config module for loading configuration settings defined by
    the user.

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os
from .._compat import RawConfigParser
from ..constants import DEFAULT_CONFIG, DEFAULT_CONFIG_SECTIONS, DEFAULT_TASK_CONCURRENCY, DEFAULT_TIMEOUT
from ..ansible_helpers import AnsibleCredentialManager
from dynaconf import Dynaconf


class Config(dict):
    """The config class.

    Its desired state is for loading the configuration settings supplied by
    the user. The config object is based on pythons dictionary data structure.
    """
    def __init__(self):
        """Constructor."""
        super(Config, self).__init__(DEFAULT_CONFIG)
        self.__set_parser__()
        self.dynaconf_settings = Dynaconf(envvar_prefix="TEFLO"
                                          # includes=["/home/rushinde/teflo_changes/e2e-acceptance-tests_or/teflo.cfg"],
                                          # ignore_unknown_envvars=True
                                          )

    def __set_parser__(self):
        """Set the raw config parser."""
        self.parser = RawConfigParser()

    def __del_parser__(self):
        """Delete the raw config parser."""
        del self.parser

    def override_with_env_variables(self, match_str, list_config_dict = None):
        # looking at the TEFLO env variables and overriding the cfg options
        for k, v in self.dynaconf_settings.items():
            if not k.startswith(match_str):
                continue
            if match_str == 'DEFAULTS_':
                name = k.split(match_str, 1)[-1]
                self.__setitem__(name, v)
            elif match_str == 'CREDENTIALS_':
                continue
            else:
                name, prop = k.split(match_str, 1)[-1].split('_', 1)
                name_not_found = 1
                for item in list_config_dict:
                    if item['name'] == name.lower():
                        item[prop.lower()] = v
                        name_not_found = 0
                if name_not_found:
                    list_config_dict.append({'name': name.lower(), prop.lower(): v})

        return list_config_dict

    def __set_defaults__(self):
        """Set the default configuration settings."""
        # A check to continue the flow if default section is not provided in teflo.cfg
        if getattr(self.parser, '_sections').get('defaults'):
            for k, v in getattr(self.parser, '_sections')['defaults'].items():
                if k == '__name__':
                    continue
                if self.dynaconf_settings.get(k.upper(), None):
                    self.__setitem__(k.upper(), self.dynaconf_settings[k.upper()])
                else:
                    self.__setitem__(k.upper(), v)
        self.override_with_env_variables('DEFAULTS_')

    def __set_credentials__(self, **kwargs):
        """Set the credentials configuration settings."""
        if not kwargs.get("parser"):
            parser = self.parser
        else:
            parser = kwargs["parser"]
        credentials = []

        for section in getattr(parser, '_sections'):
            if not section.startswith('credentials'):
                continue

            _credentials = {}

            for option in parser.options(section):
                _credentials[option] = \
                    parser.get(section, option)
            _credentials['name'] = section.split(':')[-1]
            credentials.append(_credentials)

        self.__setitem__('CREDENTIALS', credentials)

    def __set_orchestrator__(self):
        """Set the orchestrator configuration settings."""
        orchestrator_options = []
        for section in getattr(self.parser, '_sections'):
            if not section.startswith('orchestrator'):
                continue

            _orchestrator_options = {}
            # removing any dashes (-)
            orchestrator = section.split(':')[-1].replace('-', '')
            # checking the config file first
            for option in self.parser.options(section):
                _orchestrator_options[option] = self.parser.get(section, option)
            _orchestrator_options['name'] = orchestrator
            orchestrator_options.append(_orchestrator_options)

        # looking at the TEFLO env variables and overriding the cfg options
        env_options = self.override_with_env_variables('ORCHESTRATOR_', orchestrator_options)
        self.__setitem__('ORCHESTRATOR_OPTIONS', env_options)

    def __set_executor__(self):
        """Set the executor configuration settings."""

        executor_options = []
        for section in getattr(self.parser, '_sections'):
            if not section.startswith('executor'):
                continue
            _executor_options = {}
            # removing any dashes (-)
            executor = section.split(':')[-1].replace('-', '')
            # checking the config file first
            for option in self.parser.options(section):
                _executor_options[option] = self.parser.get(section, option)
            _executor_options['name'] = executor
            executor_options.append(_executor_options)

        # looking at the TEFLO env variables and overriding the cfg options
        env_options = self.override_with_env_variables('EXECUTOR_', executor_options)

        self.__setitem__('EXECUTOR_OPTIONS', env_options)

    def __set_importer__(self):
        """Set the importer configuration settings."""
        importer_options = []
        for section in getattr(self.parser, '_sections'):
            if not section.startswith('importer'):
                continue
            _importer_options = {}
            # removing any dashes (-)
            importer = section.split(':')[-1].replace('-', '')
            # checking the config file first
            for option in self.parser.options(section):
                _importer_options[option] = self.parser.get(section, option)
            _importer_options['name'] = importer
            importer_options.append(_importer_options)

        # looking at the TEFLO env variables and overriding the cfg options
        env_options = self.override_with_env_variables('IMPORTER_', importer_options)
        self.__setitem__('IMPORTER_OPTIONS', env_options)


    def __set_notifications__(self):
        """Set the notification configuration settings."""
        notifications = []

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('notifier'):
                continue

            _notifications = {}

            # removing any dashes (-)
            notifier = section.split(':')[-1].replace('-', '')
            # checking the config file first
            for option in self.parser.options(section):
                 _notifications[option] = self.parser.get(section, option)
            _notifications['name'] = notifier
            notifications.append(_notifications)

        # looking at the TEFLO env variables and overriding the cfg options
        env_options = self.override_with_env_variables('NOTIFIER_', notifications)

        self.__setitem__('NOTIFICATIONS', env_options)

    def __set_provisioner__(self):
        """Set the provisioner configuration settings."""
        provisioner_options = []

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('provisioner'):
                continue

            _provisioner_options = {}

            for option in self.parser.options(section):
                _provisioner_options[option] = self.parser.get(section, option)
            _provisioner_options['name'] = section.split(':')[-1].replace('-', '')

            provisioner_options.append(_provisioner_options)

        # looking at the TEFLO env variables and overriding the cfg options
        env_options = self.override_with_env_variables('PROVISIONER_', provisioner_options)

        self.__setitem__('PROVISIONER_OPTIONS', env_options)

    def __set_feature_toggles__(self):
        """Set the feature toggle configuration settings."""
        toggles = []

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('feature_toggles'):
                continue

            _toggles = {}

            for option in self.parser.options(section):
                _toggles[option] = self.parser.get(section, option)
            _toggles['name'] = section.split(':')[-1].replace('-', '')
            toggles.append(_toggles)

        # looking at the TEFLO env variables and overriding the cfg options
        env_options = self.override_with_env_variables('FEATURE_TOGGLES_', toggles)

        self.__setitem__('TOGGLES', env_options)

    def __set_task_concurrency__(self):
        """Set the task if it should be executed concurrently."""

        _concurrency_settings = DEFAULT_TASK_CONCURRENCY

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('task_concurrency'):
                continue

            for option in self.parser.options(section):
                _concurrency_settings.update({option.upper(): self.parser.get(section, option)})
            for keys in _concurrency_settings.keys():
                match_str = 'TASK_CONCURRENCY_' + keys
                if self.dynaconf_settings.get(match_str, None):
                    _concurrency_settings[keys] = self.dynaconf_settings[match_str]

        self.__setitem__('TASK_CONCURRENCY', _concurrency_settings)

    # TODO need to modify this method to use dynaconf_settings
    def __set_setup_logger__(self):
        """
        Set new loggers that teflo should configure logging. This
        is so those libraries/utils log their logger output to
        teflo's console and filehandler using teflo's formatter.
        """
        _logging_settings = []

        # [setup_logger]
        # reportportal=carbon_rppreproc_plugin

        # [setup_logger:reportportal]
        # logger=carbon_rppreproc_plugin

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('setup_logger'):
                continue

            for option in self.parser.options(section):
                _logging_settings.append(self.parser.get(section, option))

        self.__setitem__('SETUP_LOGGER', _logging_settings)

    def __set_timeout__(self):
        """
        Set timeout for each tasks. The task will be terminated within the time
        you set up from teflo.cfg [timrout] section
        e.x.:
        [timeout]
        provision=500
        orchestrate=500
        cleanup=700
        report=100
        """
        _timeout = DEFAULT_TIMEOUT
        for section in getattr(self.parser, "_sections"):
            if not section.startswith("timeout"):
                continue
            for option in self.parser.options(section):
                _timeout.update({option.upper(): int(self.parser.get(section, option))})
            for keys in _timeout:
                match_str = 'TIMEOUT_' + keys
                if self.dynaconf_settings.get(match_str, None):
                    _timeout[keys] = int(self.dynaconf_settings[match_str])

        self.__setitem__('TIMEOUT', _timeout)

    def load(self):
        """Load configuration settings.

        Configuration will be loaded from the following order:
            - /etc/teflo/teflo.cfg
            - ./teflo.cfg
            - TEFLO_SETTINGS env variable setting the config file
        """
        files = [
            '/etc/teflo/teflo.cfg',
            os.path.join(os.getcwd(), 'teflo.cfg')
        ]

        if os.getenv('TEFLO_SETTINGS'):
            files.append(os.getenv('TEFLO_SETTINGS'))

        for filename in files:
            if not os.path.exists(filename):
                # file not found
                continue

            # read the file
            self.parser.read(filename)

            # set user supplied configuration settings overriding defaults
            for config in DEFAULT_CONFIG_SECTIONS:
                getattr(self, '__set_%s__' % config)()

        cred_man = AnsibleCredentialManager(self)
        cred_man.populate_teflo_cfg_credentials()
