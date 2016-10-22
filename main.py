import json

import pymongo
from bson import json_util, ObjectId
from flask import Flask, Response, request, url_for
from flask.views import MethodView

app = Flask(__name__)
conn = pymongo.MongoClient('mongodb://localhost:27017/test')
db = conn.get_default_database()

def json_response(data, **kwargs):
    return Response(
        json.dumps(data, default=json_util.default),
        mimetype='application/json',
        **kwargs)


@app.route('/')
def database_summary():
    return json_response({
        'collections': [
            { 'name': colname,
              'url': url_for('.collection_view',
                             collection=colname,
                             _external=True) }
            for colname in db.collection_names()
        ]
    })

@app.route('/<collection>', methods=['GET', 'POST'])
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
                          id_str=str(result.inserted_id))
        return json_response(
            data=data,
            status=201,
            headers={'Location': new_url},
        )
    else:
        assert False

@app.route('/<collection>/<id_str>')
def document_view(collection, id_str):
    if request.method == 'GET':
        oid = ObjectId(id_str)
        return json_response(db[collection].find_one({'_id': oid}))
    else:
        assert False
