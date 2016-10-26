import json

from werkzeug.routing import BaseConverter

from bson import ObjectId, json_util
from flask import Response, url_for


def json_response(data, **kwargs):
    return Response(
        json.dumps(data, default=json_util.default),
        mimetype='application/json',
        **kwargs)


def get_bson(request):
    data = request.get_json(force=True)
    # Convert "$oid" to ObjectId, etc
    data = json.loads(json.dumps(data),
                      object_hook=json_util.object_hook)
    return data


class ObjectIdConverter(BaseConverter):
    def to_python(self, value):
        return ObjectId(value)

    def to_url(self, value):
        assert isinstance(value, ObjectId)
        return str(value)


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


def install_helpers(app):
    app.url_map.converters['collection'] = CollectionNameConverter
    app.url_map.converters['oid'] = ObjectIdConverter


def try_url_for(*args, **kwargs):
    try:
        return url_for(*args, **kwargs)
    except ValueError:
        return None
