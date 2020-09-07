#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
__author__ = 'Heng Xin'
__date__ = '2018/8/11'
"""

import yaml
from os.path import abspath, dirname

from common import log

def get_config(file_path=None):
    if file_path is None:
        file_path = dirname(abspath(__file__))
        file_path = file_path + '/config.yaml'

    with open(file_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)
        if config.get('which_project') in config.keys():
            return config.get(config.get('which_project'))
        else:
            log.error('未选择项目配置!')
            exit(0)
