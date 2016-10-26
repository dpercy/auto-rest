def subst_query(query, **subst_vars):
    if isinstance(query, basestring):
        if query and query[0] == '$' and query[1:] in subst_vars:
            return subst_vars[query[1:]]
        else:
            return query
    elif isinstance(query, dict):
        return { k: subst_query(v, **subst_vars)
                 for k, v in query.items() }
    elif isinstance(query, list):
        return [ subst_query(v, **subst_vars)
                 for v in query ]
    else:
        return query


def _test_subst_query():
    assert subst_query("$user_id", user_id=123) == 123
    assert subst_query("$foo", user_id=123) == "$foo"
    assert subst_query("", user_id=123) == ""
    assert (subst_query({'x': "$user_id", 'y': "", 'z': ['foo', "$user_id"]},
                        user_id=123)
            == {'x': 123, 'y': "", 'z': ['foo', 123]})


def document_matches_filter(data, agg_filter, db):
    """
    data : any BSON document
    agg_filter : an aggregation pipeline.

    Checks whether the agg_filter produces any documents when given
    the data as input. Returns True or False.
    """
    # Ensure that db.meta.one collection exists and is nonempty.
    # We need a nonempty collection to kick off the aggregation query.
    db['meta.one'].replace_one({'_id': 1}, {'_id': 1}, upsert=True)
    results = list(db['meta.one'].aggregate(
        # Start the pipeline with a single document: `data`
        [{'$limit': 1}, _document_as_projection(data)]
        # Send it through the filter
        + agg_filter
        # Minimize the output from the DB by returning 0 or 1 results,
        # with no fields.
        + [{'$limit': 1}, {'$project': {'_id': 0}}]))
    return len(results) > 0


def _document_as_projection(data):
    """
    {x: 1, y: "hi"}  -> {$project: { x: {$literal: 1}, y: {$literal: "hi"} }}
    """
    return {
        '$project': {
            k: {'$literal': v}
            for k, v in data.items()
        }
    }


def _test_document_matches_filter(db):
    assert document_matches_filter({'x': 1},
                                   [{'$match': {'x': {'$gt': 0}}}],
                                   db=db)
    assert not document_matches_filter({'x': 1},
                                       [{'$match': {'x': {'$lt': 0}}}],
                                       db=db)
