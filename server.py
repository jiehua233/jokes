#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @author   http://chenjiehua.me
# @date     2016-01
#

""" falcon server api """

import random
import torndb
import falcon
import ujson as json
from wsgiref import simple_server
from statsd import StatsClient

import config

statsd = StatsClient(**config.STATSD)

class ParamsError(Exception):

    @staticmethod
    def handle(ex, req, resp, params):
        err = {"c": -1001, "d": u"参数错误"}
        resp.status = falcon.HTTP_200
        resp.body = json.dumps(err)


class JokesResource(object):

    def __init__(self, db):
        self.db = torndb.Connection(**db)
        # 数据预加载
        self.category = self.db.query("SELECT `cat`, `cat_id` FROM `category` WHERE `cat_id` <> 0")
        self.category.append({"cat": u"其他", "cat_id": 0})
        self.cat_range = {-1:[]}
        jokes = self.db.query("SELECT `id`, `cat_id` FROM `joke`")
        for joke in jokes:
            self.cat_range.setdefault(joke['cat_id'], [])
            self.cat_range[joke['cat_id']].append(str(joke['id']))
            self.cat_range[-1].append(str(joke['id']))

    @statsd.timer("request")
    def on_get(self, req, resp):
        query = req.params.get("query")
        resp.status = falcon.HTTP_200

        if query == "cat":
            statsd.incr("category")
            resp.body = json.dumps({"c":0, "d": self.category})

        elif query == "joke":
            statsd.incr("joke")
            joke_id = req.params.get("joke_id")
            if joke_id and joke_id.isdigit():
                ids = [joke_id]
            else:
                limit = req.params.get("limit")
                limit = int(limit) if limit and limit.isdigit() else 1
                limit = 10 if limit > 10 else limit

                cat_id = req.params.get("cat_id")
                cat = int(cat_id) if cat_id and cat_id.isdigit() else -1
                if limit > len(self.cat_range[cat]):
                    limit = len(self.cat_range[cat])
                ids = random.sample(self.cat_range[cat], limit)

            with statsd.timer("sql_query"):
                jokes = self.db.query("SELECT `id`, `cat`, `cat_id`, `title`, `content` FROM `joke` WHERE `id` in (%s)" % ','.join(ids))

            if len(jokes) > 0:
                resp.body = json.dumps({"c": 0, "d": jokes})
            else:
                raise ParamsError

        else:
            raise ParamsError

    def parse_int(self, str_num, default=1):
        try:
            int_num = int(str_num)
        except:
            int_num = default

        return int_num

app = falcon.API()
jokes = JokesResource(config.MYSQL)
app.add_route('/', jokes)
app.add_error_handler(ParamsError, ParamsError.handle)


if __name__ == "__main__":
    host = config.SERVER['host']
    port = config.SERVER['port']
    httpd = simple_server.make_server(host, port, app)
    httpd.serve_forever()
