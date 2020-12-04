#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
import redis
from common import log


class Redis(object):

    def __init__(self, host='qa-redis.worldfarm.com', db=1):
        # QA Redis配置
        if host == 'qa-redis.worldfarm.com':
            pool = redis.ConnectionPool(host=host, port=6379, db=db, password='MiaoShu_2018@dnkj')
        # DEV Redis配置
        elif host == '192.168.62.242':
            pool = redis.ConnectionPool(host=host, port=6379, db=0, password='MiaoShu_2018@dnkj')
        # PROD Redis配置
        # elif host == '67.218.159.111':
        #     pool = redis.ConnectionPool(host=host, port=6699, db=7, password='Knight01')
        else:
            raise Exception("Redis HOST %s is incorrect" % host)
        self.r = redis.Redis(connection_pool=pool)

    def set(self, key, value):
        self.r.set(key, value)
        log.debug('Set %s = %s' % (str(key), str(value)))

    def get(self, key):
        value = self.r.get(key)
        log.debug('Get %s = %s' % (str(key), str(value)))
        if value is not None:
            value = value.decode()
        return value

    def delete(self, key):
        self.r.delete(key)
        log.debug('Delete %s' % str(key))

    def exists(self, key):
        exist = self.r.exists(key)
        log.debug('exist? %s' % str(exist))
        return exist

    def lpush(self, key, *values):
        self.r.lpush(key, *values)
        log.debug('Set %s= %s' % (str(key), ','.join(values)))

    def lrange(self, key):
        valuelist = self.r.lrange(key, 0, -1)
        return valuelist

    def lrem(self, key, value):
        self.r.lrem(key, 0, value)
        log.debug('lrem %s %s ' % (key, value))


