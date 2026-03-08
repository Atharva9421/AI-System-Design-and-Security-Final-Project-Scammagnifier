#!/bin/bash

docker run -d \
    -v /mnt/raid1/data/groundtruth/test_ac:/app/data \
    --network=app-network-scamafetcher  \
    --name scamfetchac-$RANDOM \
    -e SELENIUM_ADDRESS="$SELENIUM_ADDRESS" \
    ac \
    python ./src/app.py \
    --input_file /app/data/all_unq.csv \
    --p_log_file_address /app/data/all_data.jsonl \
    --log_file_address /app/data/ \
    --html_file_address /app/data/source_checkout/ \
    --number_proc 20\
    --screen_file_address /app/data/screenshots/

# docker run -it \
#     -v /mnt/raid1/data/groundtruth/test_ac:/app/data \
#     --network=app-network-scamafetcher  \
#     --name scamfetchac-$RANDOM \
#     -e SELENIUM_ADDRESS="$SELENIUM_ADDRESS" \
#     --entrypoint /bin/bash \
#     ac