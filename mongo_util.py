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
