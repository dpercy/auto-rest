"""
conftest.py - py.test checks this file for fixtures and other config.
"""
import pytest


@pytest.fixture
def db():
    import uuid
    import pymongo
    conn = pymongo.MongoClient('mongodb://localhost:27017',
                               serverSelectionTimeoutMS=500)
    db = conn.get_database('test_' + str(uuid.uuid4()).replace('-', ''))
    assert db.name not in conn.database_names()
    yield db
    conn.drop_database(db)
