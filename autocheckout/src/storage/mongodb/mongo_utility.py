from pymongo import MongoClient
from models.model_merchant import *
from datetime import datetime

def save_merchant(_domain, _merchant_id, _organizitaion,_scam):
    try:
        merchant = Merchant(
            domain=_domain,
            register_date=datetime.now().date().strftime('%Y-%m-%d'),
            merchantId=_merchant_id,
            organizitaion=_organizitaion,
            scam = _scam,
            refrence = 0
        )
        merchant.save()
        print(f"Merchant {_domain} saved with ID: {merchant.id}")
    except Exception as e:
        print(f"Error saving merchat: {e}")
