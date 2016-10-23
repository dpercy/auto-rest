import json

import pymongo
from flask import Flask, Response, redirect, request, url_for
from flask_util import install_helpers, json_response, try_url_for
from mongo_util import subst_query

app = Flask(__name__)

install_helpers(app)
conn = pymongo.MongoClient('mongodb://localhost:27017/blog')
db = conn.get_default_database()
config = json.load(open('example/config.json'))


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
        return Response("please log in", 401, {
            'WWW-Authenticate': 'Basic realm="Login Required"',
        })
    return redirect(url_for('.meta_whoami'))


@app.route('/')
def database_summary():
    return json_response({
        'collections': [
            {
                'name': colname,
                'url': url,
            }
            for colname in db.collection_names()
            for url in [try_url_for('.collection_view',
                                    collection=colname,
                                    _external=True)]
            if url is not None
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
    permission_filter = []
    if collection in config['permissions']:
        q = subst_query(config['permissions'][collection],
                        user_id=request.user['_id'])
        permission_filter = permission_filter + (q if isinstance(q, list) else [q])
    if request.method == 'GET':
        page_size = 100
        result = list(db[collection].aggregate(permission_filter + [{'$limit': page_size + 1}]))
        return json_response({
            'items': result[:page_size],
            'hasMore': len(result) > page_size,
        })
    elif request.method == 'POST':
        # TODO the permissions filter should also apply to the insert!
        # - you shouldn't be able to insert a document that you can't view
        # - failure to insert a document should not give you clues about the
        #   existence of other documents.
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
