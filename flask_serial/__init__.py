#!usr/bin/python
#-*- coding: utf-8 -*-
"""flask-serial Package.
:author: Redfalsh <13693421942@163.com>
:license: MIT, see license file or https://opensource.org/licenses/MIT
:created on 2019-01-10 10:59:22
:last modified by:   Ketchu13
:last modified time: 2020-08-26 19:20:00
:describe:
        flask-serial package is used in flask website, it can receive or send serial's data,
        you can use it to send or receive some serial's data to show website with flask-socketio
"""
__version__ = "1.1.0"

from .serial import Serial, PortSettings
