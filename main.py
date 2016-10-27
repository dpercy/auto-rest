import json
import os

import pymongo
from bson import ObjectId
from flask import Flask, Response, abort, redirect, request, url_for
from flask_cors import CORS
from flask_util import get_bson, install_helpers, json_response, try_url_for
from mongo_util import document_matches_filter, subst_query

app = Flask(__name__)
CORS(app) # TODO security! config file?

install_helpers(app)
# TODO make this uri configurable
conn = pymongo.MongoClient('mongodb://localhost:27017/autoRest')
db = conn.get_default_database()
config_file = os.environ.get('AUTOREST_CONFIG_FILE')
if config_file:
    with open(config_file) as f:
        config = json.load(f)
else:
    config = {
        'permissions': {}
    }


@app.route('/favicon.ico')
def no_favicon():
    return Response("go away", 404)


@app.before_request
def my_basic_auth_middleware():
    """ Super insecure HTTP basic auth!!! """
    auth = request.authorization
    if not auth:
        # Omitting auth is perfectly ok.
        # Individual collections may require auth or not,
        # depending on their permissions filters.
        request.user = {
            '_id': None,
            'username': None,
            'password': None,
        }
    else:
        user = db['meta.users'].find_one({ 'username': auth.username,
                                           'password': auth.password })
        if user is None:
            # Incorrect auth must result in an error;
            # Silently leaving you anonymous would be much more confusing.
            # TODO decide on JSON-based error pages
            abort(401)
        else:
            request.user = user


@app.errorhandler(401)
def basic_auth_error_handler(e):
    return Response("", 401, {
        'WWW-Authenticate': 'Basic realm="Login Required"',
    })


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


def get_permission_filter(collection):
    if collection not in config['permissions']:
        return []

    if request.user['_id'] is None:
        abort(401)

    query = subst_query(config['permissions'][collection],
                        user_id=request.user['_id'])
    return query if isinstance(query, list) else [query]


def _id_to_link(collection, doc):
    """
    Takes a collection name and a document,
    and converts the _id field into a link.

    Note this both mutates doc in place, and returns it.
    """
    if '_id' in doc and isinstance(doc['_id'], ObjectId):
        doc['_id'] = url_for('.document_view',
                             collection=collection,
                             id=doc['_id'],
                             _external=True)
    return doc


@app.route('/<collection:collection>', methods=['GET', 'POST'])
def collection_view(collection):
    if request.method == 'GET':
        page_size = 100
        result = list(db[collection].aggregate(
            get_permission_filter(collection) + [{'$limit': page_size + 1}]))
        return json_response({
            'items': [_id_to_link(collection, doc)
                      for doc in result[:page_size]],
            'hasMore': len(result) > page_size,
        })
    elif request.method == 'POST':
        # The permissions filter should also apply to the insert!
        # - you shouldn't be able to insert a document that you can't view
        # - failure to insert a document should not give you clues about the
        #   existence of other documents.
        data = get_bson(request)
        if '_id' in data:
            abort(400, "Client should not specify the _id")
        if not document_matches_filter(data,
                                       get_permission_filter(collection),
                                       db=db):
            abort(403)
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


@app.route('/<collection:collection>/<oid:id>', methods=['GET', 'PUT', 'DELETE'])
def document_view(collection, id):
    if request.method == 'GET':
        result = list(db[collection].aggregate(
            get_permission_filter(collection) + [{'$match': {'_id': id}},
                                                 {'$limit': 1}]))
        if len(result) == 0:
            abort(404)
        return json_response(_id_to_link(collection, result[0]))
    elif request.method == 'DELETE':
        # TODO permissions on DELETE
        db[collection].delete_one({'_id': id})
        return Response('', 204)
    elif request.method == 'PUT':
        # TODO This doesn't check the before state.
        #      Need to make sure a user can't change a doc's visibliliyt with a PUT.
        data = get_bson(request)
        # If the client specified an _id URL, make sure it
        # matches the request URL.
        if '_id' in data and data['_id'] != request.url:
            abort(400, "_id field did not match the resource URL")
        # Fix the _id field for use in MongoDB.
        data['_id'] = id
        if not document_matches_filter(data,
                                       get_permission_filter(collection),
                                       db=db):
            abort(403)
        result = db[collection].replace_one({'_id': id}, data, upsert=True)
        new_url = url_for('.document_view',
                          collection=collection,
                          id=id)
        if result.upserted_id is not None:
            # 201 created
            return Response("", 201, headers={'Location': new_url})
        elif result.modified_count > 0:
            # 204 no content (means it was modified successfully)
            return Response("", 204, headers={'Location': new_url})
        else:
            # error?
            assert False, "upsert failed? how?"
    else:
        assert False

# TODO write some end-to-end tests
