import os

mongo_username = os.getenv('MONGO_USERNAME','mongoadmin')
mongo_password = os.getenv('MONGO_PASSWORD','secret')
mongo_host = os.getenv('MONGO_HOSTNAME','localhost')
mongo_port = os.getenv('MONGO_PORT','27017')
mongo_db = os.getenv('MONGO_DB','mydatabase')
save_limit = int(os.getenv('LIMIT',100000))
scheduler_time_interval = int(os.getenv('SCHEDULER_JOB_INTERVAL',0))