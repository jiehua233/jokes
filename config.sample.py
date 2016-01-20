#!/usr/bin/env python
# -*- coding: utf-8 -*-

MYSQL = {
    "host": "127.0.0.1:3306",
    "user": "root",
    "password": "root",
    "database": "jokes",
}

SERVER = {
    "host": "127.0.0.1",
    "port": 9999,
}

"""Gunicorn setting"""
bind = "127.0.0.1:9999"
workers = 1
worker_class = "gevent"
accesslog = "-"     # log to stderr
errorlog = "-"      # log to stderr
loglevel = "info"
