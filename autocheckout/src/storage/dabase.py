from mongoengine import connect
import os

class Database:
    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.db_uri = ""
        
    
    def create_connection(self,_db_uri):
        self.db_uri = _db_uri
        print(f"connection url : {_db_uri}")
        connect(host = self.db_uri)
        print('MongoDB is connected successfully')