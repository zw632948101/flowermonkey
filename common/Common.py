#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
__author__ = 'Zhang Wei'
__date__ = '2019/ / '

"""
import datetime
import json
import time
from random import uniform


class TimestampTransform(object):
    def __init__(self):
        super(TimestampTransform, self).__init__()

    @staticmethod
    def str_time_timestamp(timestamp, formats="%Y-%m-%d %H:%M:%S"):
        """
        转换成时间戳
        :param timestamp:
        :param formats:
        :return:
        """
        sql_end_time_array = time.strptime(timestamp, formats)
        sql_end_time_stamp = int(time.mktime(sql_end_time_array)) * 1000
        return sql_end_time_stamp

    @staticmethod
    def get_timestamp():
        """
        直接获取当前时间戳
        :return:
        """
        return int(round(time.time()) * 1000)

    @staticmethod
    def timestamp_formatting(timestamp, formats="%Y-%m-%d %H:%M:%S"):
        """
        转换成指定格式
        :param timeStamp:
        :return:
        """
        timeArray = time.localtime(timestamp)
        otherStyleTime = time.strftime(formats, timeArray)
        return otherStyleTime

    @staticmethod
    def get_standardtime_by_offset(type=1, week=0, day=0, hour=0, minute=0, second=0, formats="%Y-%m-%d %H:%M:%S"):
        """
        根据现在时间和设定偏移量获取标准时间
        :param type:偏移类型，1为加法，其他为减法
        :param year:
        :param month:
        :param day:
        :param hour:
        :param minute:
        :param second:
        :return:
        """
        if type == 1:
            return (datetime.datetime.now() + datetime.timedelta(weeks=week, days=day, hours=hour, minutes=minute,
                                                                 seconds=second)).strftime(formats)
        return (datetime.datetime.now() - datetime.timedelta(weeks=week, days=day, hours=hour, minutes=minute,
                                                             seconds=second)).strftime(formats)

    @staticmethod
    def get_standardtime_timestamp(type=1, week=0, day=0, hour=0, minute=0, second=0, formats="%Y-%m-%d %H:%M:%S"):
        """
        根据现在时间和设定偏移量获取标准时间的时间戳
        :param type:偏移类型，1为加法，其他为减法
        :param year:
        :param month:
        :param day:
        :param hour:
        :param minute:
        :param second:
        :return:
        """
        t = TimestampTransform.get_standardtime_by_offset(type=type, week=week, day=day, hour=hour, minute=minute,
                                                          second=second, formats=formats)
        return TimestampTransform.str_time_timestamp(t, formats=formats)
