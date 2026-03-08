import json
from collections import defaultdict
import os
import re
import sys
from storage.mongodb.mongo_utility import *


def create_merch_info(domains, output_path,checkout_html_dir):
  
    res = [
        r'"(merchantID|payerID)":"?([A-Z0-9]{13})"?',
        r'"(merchantId|payerId)":"?([A-Z0-9]{13})"?',
        r'"(merchantid|payerid)":"?([A-Z0-9]{13})"?',
        r'merchant-id="?([A-Z0-9]{13})"?',
    ]
    domain_red = defaultdict()
    for domain in domains:
        merchant_ids = defaultdict(list)

        # look for merchant id in the source code
        source_fname = domain.replace('https://', 'https___')
        source_path = None

        # open the related source path
        for i in range(2):
            source_path = os.path.join(checkout_html_dir, source_fname+ str(i) + '.html')
            if os.path.exists(source_path):
               
                f = open(source_path, 'r')
                for line2 in f.readlines():
                    line2 = line2.strip().replace("&quot;", '"').replace('\\', '')
                                
                    for r in res:
                        results = re.findall(r, line2)
                        if results:
                            for mid in set(results):
                                if type(mid) is tuple and len(mid) > 1:
                                    merchant_ids[i].append(mid[1])
                                    print(f"MERCHANTID:{mid[1]}")
                                elif type(mid) is str:
                                    merchant_ids[i].append(mid)
                                    print(f"MERCHANTID:{mid}")
                               
            else:
                continue
           
        if merchant_ids:
            tmp = defaultdict()
            tmp['merch_id'] = merchant_ids
            domain_red[domain] = tmp
                                    

    json.dump(domain_red, open(output_path, 'w'), indent=4)
    return domain_red

"""
Parse Redirection log and Checkout Page

This function processes the performancelog log and the checkout pages HTML to extract the merchantID.

Parameters:
performance_log (string): The file path to `performancelog.jsonl`
output_path (string): The file path where the extracted merchantID will be saved.
checout_html_dir (String): The directory path where checkout page HTML files are stored

Returns:
None
"""
def parse_data(performance_log, output_path, checkout_html_dir):
    
    fin = open(performance_log, 'r')
    print(performance_log, '....')
    domains = []
    for line in fin.readlines():
        line = line.strip()
        line_dict = json.loads(line)
        #domains.append(line_dict['domain'])
        if 'domain' in line_dict:
            domains.append(line_dict['domain'])
        else:
            print(f"[WARN] Missing domain in line: {line_dict}")
    return create_merch_info(domains, output_path, checkout_html_dir)

