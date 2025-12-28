from mongoengine import Document, StringField, DateTimeField, IntField
from datetime import datetime

class Domain(Document):
    domain = StringField(required=True, unique=True)
    register_date = DateTimeField(default=datetime.now)
    last_crawl = DateTimeField()
    next_crawl = DateTimeField(default=datetime(1970, 1, 1))
    crawl_freq = IntField(required=True,default=48)
    status = IntField(default=0)
    monitor = IntField(default=1)

    meta = {
        'collection': 'domains'
    }
