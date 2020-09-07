#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Time: 2020 2020/4/17 18:53
__author__: wei.zhang

"""

if __name__ == '__main__':
    # from monkey.flowerExecute import Execommand
    # #
    # Monkey = Execommand(timeout=60, event_count=5000, device='CLB7N18709015438')
    # Monkey.run(mobile="15388126080")
    # from monkey.flowerExecute import Multi_device_execution
    #
    # Monkey = Multi_device_execution(event_count=500, timeout=60)
    # Monkey.multi_device_run()
    from monkey.monitorDevice import monitorDevice

    m = monitorDevice()
    m.custom_scheduler()
