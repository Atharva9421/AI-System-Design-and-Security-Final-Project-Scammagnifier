from mongoengine import Document, StringField, DateTimeField, IntField
from datetime import datetime

class Merchant(Document):
    domain = StringField(required=True, unique=False)
    register_date = DateTimeField(default=datetime.now)
    merchantId = StringField(required=False, unique=False)
    organizitaion = StringField(required=False, unique=False)
    scam = IntField(default=-1)
    refrence = IntField(default=0)
    meta = {
        'collection': 'merchant'
    }
