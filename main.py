#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Time: 2020 2020/4/17 18:53
__author__: wei.zhang

"""
import sys

if __name__ == '__main__':
    from monkey.flowerMonkey import Execommand

    Monkey = Execommand(event_count=5000, device=sys.argv[0])
    print(Monkey.run(timeout=60 * 60 * 3))
