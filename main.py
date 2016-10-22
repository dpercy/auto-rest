import json

from werkzeug.routing import BaseConverter

import pymongo
from bson import ObjectId, json_util
from flask import Flask, Response, redirect, request, url_for
from flask.views import MethodView

app = Flask(__name__)
conn = pymongo.MongoClient('mongodb://localhost:27017/blog')
db = conn.get_default_database()
config = json.load(open('example/config.json'))

def json_response(data, **kwargs):
    return Response(
        json.dumps(data, default=json_util.default),
        mimetype='application/json',
        **kwargs)

class ObjectIdConverter(BaseConverter):
    def to_python(self, value):
        return ObjectId(value)
    def to_url(self, value):
        assert isinstance(value, ObjectId)
        return str(value)
app.url_map.converters['oid'] = ObjectIdConverter


def assert_valid_collection_name(value):
    if '.' in value:
        raise ValueError("collection name contains a dot: {}".format(value))

def is_valid_collection_name(value):
    try:
        assert_valid_collection_name(value)
    except ValueError:
        return False
    else:
        return True

class CollectionNameConverter(BaseConverter):
    def to_python(self, value):
        assert_valid_collection_name(value)
        return value
    def to_url(self, value):
        assert_valid_collection_name(value)
        return value
app.url_map.converters['collection'] = CollectionNameConverter


@app.before_request
def my_basic_auth_middleware():
    """ Super insecure HTTP basic auth!!! """
    auth = request.authorization
    nobody = {
        '_id': None,
        'username': None,
        'password': None,
    }
    if not auth:
        request.user = nobody
    else:
        user = db['meta.users'].find_one({ 'username': auth.username,
                                           'password': auth.password })
        if user is not None:
            request.user = user
        else:
            request.user = nobody
@app.route('/login')
def hack_login():
    """ hack to get browsers to respect basic auth """
    if request.user['_id'] is None:
        return Response("please log in", 401, {'WWW-Authenticate':'Basic realm="Login Required"'})
    return redirect(url_for('.meta_whoami'))


@app.route('/')
def database_summary():
    return json_response({
        'collections': [
            { 'name': colname,
              'url': url_for('.collection_view',
                             collection=colname,
                             _external=True) }
            for colname in db.collection_names()
            if is_valid_collection_name(colname)
        ]
    })


@app.route('/meta.whoami')
def meta_whoami():
    return json_response({
        'user_id': request.user['_id'],
        'username': request.user['username'],
    })


@app.route('/<collection:collection>', methods=['GET', 'POST'])
def collection_view(collection):
    query = {}
    if collection in config['permissions']:
        query = { '$and': [
            query,
            parse_query(config['permissions'][collection],
                        user_id=request.user['_id'])
        ] }
    if request.method == 'GET':
        return json_response({
            'count': db[collection].count(),
            # TODO smarter pagination??
            'items': list(db[collection].find().limit(100)),
        })
    elif request.method == 'POST':
        data = request.get_json(force=True)
        result = db[collection].insert_one(data)
        new_url = url_for('.document_view',
                          collection=collection,
                          id=result.inserted_id)
        return json_response(
            data=data,
            status=201,
            headers={'Location': new_url},
        )
    else:
        assert False

@app.route('/<collection:collection>/<oid:id>', methods=['GET', 'PUT'])
def document_view(collection, id):
    if request.method == 'GET':
        return json_response(db[collection].find_one({'_id': id}))
    elif request.method == 'PUT':
        # http://www.restapitutorial.com/lessons/httpmethods.html
        # return 201 if created
        # return full resource representation? redundant?
        assert False, "TODO"
    else:
        assert False
