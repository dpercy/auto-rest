import json

import pymongo
from bson import json_util, ObjectId
from flask import Flask, Response, request, url_for
from flask.views import MethodView
from werkzeug.routing import BaseConverter

app = Flask(__name__)
conn = pymongo.MongoClient('mongodb://localhost:27017/test')
db = conn.get_default_database()

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

@app.route('/<collection:collection>', methods=['GET', 'POST'])
def collection_view(collection):
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

@app.route('/<collection:collection>/<oid:id>')
def document_view(collection, id):
    if request.method == 'GET':
        return json_response(db[collection].find_one({'_id': id}))
    else:
        assert False
