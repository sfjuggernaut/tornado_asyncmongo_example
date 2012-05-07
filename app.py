import os.path
import asyncmongo
import tornado.web
import tornado.ioloop
import json
from bson.objectid import ObjectId

import pdb

class MongoDBEncoder(json.JSONEncoder):
    "Convert non-JSON serializable Mongo related objs to something serializable"
    def default(self, obj):
        if obj is None:
            return obj
        elif isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

class RootHandler(BaseHandler):
    def get(self):
        self.write("welcome to root")

class WombatsHandler(BaseHandler):
    # This method will exit before the request is complete, thus "asynchronous"
    @tornado.web.asynchronous
    def get(self):
        self.db.wombats.find({}, {"_id" : 0}, limit = 5, callback = self._get_response)

    def post(self, id):
        pass

    def _get_response(self, response, error):
        if error:
            raise tornado.web.HTTPerror(500)
        self.render("wombats.html", wombats = response)

class JSONWombatsHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self, id = None):
        if  id == None:
            self.db.wombats.find({}, limit = 5, callback = self._get_response)
        else:
            self.db.wombats.find_one({'id': int(id)}, callback = self._get_response)

    def _get_response(self, response, error):
        if error:
            raise tornado.web.HTTPerror(500)
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(response, cls = MongoDBEncoder))
        self.finish()

class Application(tornado.web.Application):
    def __init__(self):
        # XXX: there's got to be a better way to handle different formats
        handlers = [
            (r"/",                              RootHandler),
            (r"/wombats.json",                  JSONWombatsHandler),
            (r"/wombats",                       WombatsHandler),
            (r"/wombats/([A-Za-z0-9-]+).json",  JSONWombatsHandler),
        ]
        settings = dict(
            debug           = True,
            template_path   = os.path.join(os.path.dirname(__file__), 'templates'),
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the DB across all handlers
        async_db = asyncmongo.Client(
            pool_id         = 'my_db',
            host            = '127.0.0.1',
            port            = 27017,
            mincached       = 5,
            maxcached       = 15,
            maxconnections  = 30,
            dbname          = 'test'
        )
        self.db = async_db

def main():
    application = Application()
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
