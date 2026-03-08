import os

selenium_addr = os.getenv("SELENIUM_ADDRESS","http://127.0.0.1:4444/wd/hub")
DOCKER_VOLUME = "/app/data/"
mongo_username = os.getenv('MONGO_USERNAME','mongoadmin')
mongo_password = os.getenv('MONGO_PASSWORD','secret')
mongo_host = os.getenv('MONGO_HOSTNAME','localhost')
mongo_port = os.getenv('MONGO_PORT','27017')
mongo_db = os.getenv('MONGO_DB','mydatabase')
