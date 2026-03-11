# -*- coding: utf-8 -*-

def classFactory(iface):
    from .iconic_plugin import IconicPlugin
    return IconicPlugin(iface)
