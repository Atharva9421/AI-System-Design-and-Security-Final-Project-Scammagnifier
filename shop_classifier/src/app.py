'''

sudo docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=12 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true --shm-size="2g" seleniarm/standalone-chromium:latest

sample cmd: 
python crawler_mp.py --num_procs 5 --input_file /home/ubuntu/new_drive/backupp/SAC/data/all_data_2023_08_23.json --cache_mode --output_file /home/ubuntu/new_drive/BP/saved_features/features_2023_08_23.pkl

'''


import json
import pickle
import whois
import re
import pandas as pd
import langid
import argparse
import urllib3
import undetected_chromedriver as uc
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from multiprocessing import Pool
import os
from urllib.parse import urlsplit
import IP2Location
from bs4 import BeautifulSoup
import socket
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#import undetected_chromedriver as uc
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from beyondphish_features import extract_beyondphish_features


from config import *

def is_content_parked(content):
    return any(re.findall(r'buy this domain|parked free|godaddy|is for sale'
                          r'|domain parking|renew now|this domain|namecheap|buy now for'
                          r'|hugedomains|is owned and listed by|sav.com|searchvity.com'
                          r'|domain for sale|register4less|aplus.net|related searches'
                          r'|be the first to know when we launch|get notified when we open our online store'
                          r'|related links|search ads|domain expert|united domains'
                          r'|domian name has been registered|this domain may be for sale'
                          r'|domain name is available for sale|premium domain'
                          r'|registrar placeholder|under construction|coming soon'
                          r'|this domain name|this domain has expired|domainpage.io'
                          r'|sedoparking.com|parking-lander'
                          r'|create your website'
                          r'|something really good is coming very soon'
                          r'|this domain is available on auction'
                          r'|opening soon'
                          r'|this page isn\'t working'
                          r'|sorry, you have been blocked'
                          r'|you are unable to access'
                          r'|this content isn\'t available right now'
                          r'|redirected you too many times', content, re.IGNORECASE))

def filter_lang(text, selected_langs):
    language, _ = langid.classify(text)
    if language in selected_langs:
        return True
    return False

def normalize_url(url):
    prefixes = ['https://www.', 'http://www.', 'www.']
    for prefix in prefixes:
        if url.startswith(prefix):
            return url[len(prefix):]
    return url

def write_log(data,file=None,verbose=True):
    if verbose:
        current_date_time=datetime.now()
        current_date_time_str = current_date_time.strftime('%Y-%m-%d %H:%M:%S')
        print(current_date_time_str+"||"+data)
        if file:
            file.write(current_date_time_str+"||"+data+"\n")
            file.flush()

def check_url(url):
    u = urlsplit(url)
    # Check if the scheme of the URL is HTTP or HTTPS
    if u.scheme in ['http', 'https']:
        return u.netloc
    else:
        return u.path

def extract_body_text(page_source):
    # Parse the page source using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')  # You can also use 'html.parser' instead of 'lxml'
    
    # Extract the body text. If the body tag is not found, return an empty string
    body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ''
    
    return body_text
  
def convert_to_feature(icann_data, countries, html_string, url, data_file="IP2LOCATION-LITE-DB1.BIN"):
    ip_location = IP2Location.IP2Location(data_file)
    _url = check_url(url)
    u = normalize_url(_url)
    X = []

    # range
    try:
        created_date = datetime.datetime.strptime(icann_data[url]['creation_date'].split(' ')[0], '%Y-%m-%d')
        exp_date = datetime.datetime.strptime(icann_data[url]['expiration_date'].split(' ')[0], '%Y-%m-%d')
        total_age = (exp_date - created_date).days / 365.0
    except:
        total_age = -1

    # set country
    country_feature = [0 for i in range(255)]
    if 'country' in icann_data[url] and icann_data[url]['country'] in countries:
        country = countries.index(icann_data[url]['country'])
        country_feature[country] = 1
    else:
        country = -1

    # whois guard
    names = icann_data[url]['registrar'] if 'registrar' in icann_data[url] else None
    if isinstance(names, list):
        names = names[0]

    whois_guard_keywords = ['whoisguard', 'redacted for privacy', 'private whois', 'domain privacy']
    guard = 0
    for kw in whois_guard_keywords:
        if names and (kw in names.lower() or 'priva' in names.lower()):
            guard = 1
            break
        elif names is None:
            guard = -1

    # DOM parsing
    parsed_tree = BeautifulSoup(html_string, 'html.parser')
    script_tags = parsed_tree.find_all('script', src=True)
    
    link_tags = parsed_tree.find_all('a', href=True)
    num_external_links = 0
    if link_tags:
        for link_tag in link_tags:
            link = link_tag['href']
            if link.startswith("http") and u not in link:
                num_external_links += 1

    # social media
    total_social_medias = [-1, -1, -1]
    social_media_regex = [
        r'instagram\.com\/[a-zA-Z0-9_\-]+',
        r'facebook\.com\/[a-zA-Z0-9_\-]+',
        r'twitter\.com\/[a-zA-Z0-9_\-]+',
    ]
    
    for i, r in enumerate(social_media_regex):
        found = re.findall(r, html_string)
        if found:
            total_social_medias[i] = 1 if found[0].split('/')[-1] in url else 0

    # Host country
    host_country_feature = [0 for i in range(255)]
    try:
        host_ip = socket.gethostbyname(u)
        response = ip_location.get_all(host_ip)
        host_country = response.country_short.decode()
        host_domain_same = 1 if countries.index(host_country) == country else 0
        host_country = countries.index(host_country)
        host_country_feature[host_country] = 1
    except:
        host_domain_same = -1
        host_country = -1

    # cheap domains
    has_digit = any(i.isdigit() for i in url)

    is_cheap = 0
    cheap_registrars = ['namecheap', 'godaddy', 'porkbun', 'namesilo', 'danesco', 'hostinger']
    if names:
        for cr in cheap_registrars:
            if cr in names.lower():
                is_cheap = 1
                break
    
    top_cheap_domains = ['club', 'buzz', 'xyz', 'ua', 'icu', 'space', 'agency', 
                         'monster', 'pw', 'click', 'website', 'site', 'online', 
                         'link', 'shop', 'feedback', 'uno', 'press', 'best', 
                         'fun', 'host', 'store', 'tech', 'top', 'it']
    uses_cheap_domain = 1 if any(t in url for t in top_cheap_domains) else 0
            
    # domain in body text
    if parsed_tree.find('body') is not None:
        domain_in_text = parsed_tree.find('body').text.count(u)
    else:
        domain_in_text = -1
        
    # base feature vector
    domain_name = '.'.join(u.split('.')[:-1])
    
    X.append([
        guard, 
        total_social_medias[0], 
        total_social_medias[1], 
        total_social_medias[2], 
        num_external_links, 
        host_domain_same,
        len(script_tags),
        1 if '-' in url else 0,
        domain_name.count('.'),
        1 if has_digit else 0,
        is_cheap,
        uses_cheap_domain,
        domain_in_text,
        1 if u.split('.')[-1] not in ['com', 'net', 'org', 'uk', 'gov', 'au'] else 0,
        total_age,
    ])

    # add country vectors
    X[-1].extend(country_feature)
    X[-1].extend(host_country_feature)

    # ⭐⭐⭐ ADD BEYONDPHISH FEATURES HERE ⭐⭐⭐
    bp_vector = extract_beyondphish_features(html_string)
    X[-1].extend(bp_vector)

    return X


def get_source(driver, url, output_file):

    try:
        if not url.startswith('http'):
            url = 'https://' + url
        print(url)
        driver.get(url)
        time.sleep(5)
        # Get page source or content
        content = driver.page_source

        # # save the content
        # fout = open(output_file, 'w')
        # fout.write(content)
        # fout.close()
        # return content
        # Save using UTF-8 encoding (fixes \uf10d etc.)
        with open(output_file, 'w', encoding='utf-8', errors='ignore') as fout:
            fout.write(content)
        return content
        
    except Exception as e:
        print('Remote Error:', e)
        return None


class Crawler:
    def __init__(self, pid, cache_mode, source_path, lang_list):
        self.pid = pid
        self.cache_mode = cache_mode
        self.source_path = source_path
        self.lang_list = lang_list

        # load whois data
        self.whois_data = {}

        # load contries
        #self.countries = list(json.load(open('./assets/country.json', 'r', encoding='utf-8')).keys())
        assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'country.json')
        self.countries = list(json.load(open(assets_path, 'r', encoding='utf-8')).keys())

        self.X, self.Y, self.collected_urls = [], [], []
        self.ip_failed_urls = []

    def close_all(self):
        # self.info_getter.close_driver()
        pass

    def crawl(self, data):
        print(f"crawl {data}")
        url = data
        if '"' in url:
            url = url.replace('"', '')

        unified_url_whois = {check_url(url): value for url, value in self.whois_data.items()}

        # get whois data
        icann_data = {}
        try:
            if url in unified_url_whois :
                icann_data = unified_url_whois[url]
            else:
                icann_data = whois.whois(url)
                self.whois_data[url] = icann_data

            # if icann_data == {} or 'creation_date' not in icann_data or icann_data['creation_date'] == None:
            #     self.ip_failed_urls.append((url, 'whois'))
            #     return
        except Exception as e:
            print(f"get whois error : {e}")
  

        # get page source (from cache or DL)
        page_content = None
        fpath = os.path.join(os.path.abspath(self.source_path), url.replace('/', '').replace('?', '').replace('!', '').replace('@', '').replace(':', '') + '.html')
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        print(f"start ...")
        if not os.path.exists(fpath):
            try:
                options = Options()
                options.add_argument("--headless")  # run silently, no GUI
                options.add_argument("--incognito")
                options.add_argument("--enable-javascript")
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")

                prefs = {
                "translate_whitelists": {"fr": "en", "es": "en"},
                "translate": {"enabled": "true"}
                }
                options.add_experimental_option("prefs", prefs)

                # Create a local Chrome driver instance instead of remote
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                driver.set_page_load_timeout(30)

            except Exception as e:
                print(f"[ERROR] Could not load page {url}: {e}")
                self.ip_failed_urls.append((url, 'content'))

            print(f"[INFO] Fetching: {url}")
            page_content = get_source(driver, url, fpath)
            driver.quit()
        
            try:
                 d = DesiredCapabilities.CHROME
                 d['goog:loggingPrefs'] = { 'performance':'ALL', 'browser':'ALL' }
                 options = uc.ChromeOptions()
                 options.add_argument("--incognito")
                 options.add_argument("--enable-javascript")
                 options.add_argument("--ignore-certificate-errors")
                 prefs = {
                     "translate_whitelists": {"fr":"en", "es":"en"},
                     "translate":{"enabled":"true"}
                 }
                 options.add_experimental_option("prefs", prefs)
                 print(f"sel add : {selenium_address}")
                 driver = webdriver.Remote(selenium_address, d, options=options)
                 driver.set_page_load_timeout(10)
                 print(f'************************************ {fpath} ***********')
                 page_content = get_source(driver, url, fpath)
                 # Close the browser
                 driver.quit()


            except Exception as e:
                print(f"error in get page source {e}")
                self.ip_failed_urls.append((url, 'content'))
                pass
        else:
            page_content = open(fpath, 'r', errors='ignore').read()

        if page_content:
            page_text = extract_body_text(page_content)
            # create features
            print(f"parked : {is_content_parked(page_content)}")
            print(f"lang : {filter_lang(page_text, self.lang_list)}")
            #if len(page_content) > 3000 and not is_content_parked(page_content) and filter_lang(page_text, self.lang_list):
            if len(page_content) > 3000 and not is_content_parked(page_content) :
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'IP2LOCATION-LITE-DB1.BIN')
                sample_features = convert_to_feature({url: icann_data}, self.countries, page_content, url, db_path)
                #sample_features = convert_to_feature({url: icann_data}, self.countries, page_content, url, './assets/IP2LOCATION-LITE-DB1.BIN')

                self.X.append(sample_features)
                self.collected_urls.append(url)
            else:
                self.ip_failed_urls.append((url, 'too little content'))


def crawl_list(urls):
    # urls[0] has:: u, ind, args.cache_mode, args.source_path
    print("start thread ...")
    cache_mode = urls[0][2]
    source_path = urls[0][3]
    lang_list = urls[0][4]
    crawler = Crawler(os.getpid(), cache_mode, source_path, lang_list)

    # get process num
    if urls[0][1] == 0:
        iterator = urls # tqdm(urls, total=len(urls))
    else:
        iterator = urls

    for url in iterator:
        crawler.crawl(url[0])

    collected_urls = crawler.collected_urls
    X = crawler.X
    failed = crawler.ip_failed_urls
    crawler.close_all()
    return [collected_urls, X, failed]

def main(args):
    # create processes to crawl
    all_urls = []
    if args.url:
        all_urls.append(args.url)
    else:
        with open(args.input_file, 'r', encoding='utf-8') as fin:
            for line in fin.readlines():
                line = line.strip().replace('"', '')
                if line == '':
                    continue

                u = check_url(line)
                # unify urls
                u = u.replace('https://', '').replace('http://', '')

                if '/' in u:
                    u = u.split('/')[0]
                all_urls.append(u)

    write_log(data=f'Total number of domains = {len(all_urls)}')

    all_urls_added = []
    selected_langs_str = args.selected_languages
    lang_list = selected_langs_str.split(',')
    visited_domains = set()

    for ind, u in enumerate(list(set(all_urls))):
        domain = u
        if domain not in visited_domains:
            visited_domains.add(domain)
        else:
            continue

        all_urls_added.append([
            u, ind, cache_mode, args.source_path, lang_list
        ])

    print('Total number of domains = %d' %len(all_urls_added))

    # create batches according to num_procs
    if len(all_urls_added) // number_proc == 0 :
        n = 1
    else:
        n = len(all_urls_added) // number_proc
    
    urls = [all_urls_added[i * n:(i + 1) * n] for i in range((len(all_urls_added) + n - 1) // n )] 
    print(f"urls : {len(urls)} , num_procs : {number_proc} , n :{n}")
    pool = Pool(number_proc)
    results = pool.map(crawl_list, urls)
    #pool.close()
    #pool.join()

    print('Merging the results ...')

    all_urls = []
    all_X = []
    all_failed = []
    results = [i for i in results]
    for i in results:
        for failed in i[2]:
            all_failed.append(failed)
        for url, x in zip(i[0], i[1]):
            print(url, x)
            all_urls.append(url)
            all_X.append(x)

    print('Results len = %d' %len(all_X))
    # pickle.dump((all_X, all_urls), open(args.output_file, 'wb'))
    # df = pd.DataFrame(all_failed, columns=["Failed URLs", "Reason"])

    # # Write to a CSV file
    # df.to_csv(args.output_file.replace('.pkl', '-failed.csv'), index=False)
    # if len(all_X) > 0:
    #     df_features = pd.DataFrame(all_X)
    #     df_features["URL"] = all_urls
    #     df_features.to_csv(args.output_file, index=False)
    #     print(f"✅ Features saved to {args.output_file}")

    if len(all_X) > 0:
        with open(args.output_file, "wb") as f:
            pickle.dump((all_X, all_urls), f)
        print(f"✅ Pickle features saved to {args.output_file}")

        # (Optional) also save a readable CSV copy
        df_preview = pd.DataFrame([x[0] for x in all_X])
        df_preview["URL"] = all_urls
        df_preview.to_csv(args.output_file.replace(".pkl", "_preview.csv"), index=False)
        print(f"📄 CSV preview saved to {args.output_file.replace('.pkl', '_preview.csv')}")

    # Save failed URLs (if any)
    if len(all_failed) > 0:
        df_failed = pd.DataFrame(all_failed, columns=["Failed URLs", "Reason"])
        df_failed.to_csv("features_output_failed.csv", index=False)
        print("⚠️ Some URLs failed, logged in features_output_failed.csv")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('--url', type=str, help='input urls', required=False)
    parser.add_argument('--input_file', type=str, help='input txt/json of urls', required=False)
    parser.add_argument('--source_path', type=str, help='directory , save html file', required=True)
    parser.add_argument('--output_file', type=str, help='output file', required=True)
    parser.add_argument('--selected_languages', type=str, help='list of desired languages, comma seprated, no space', required=True)

    args = parser.parse_args()

    print("[+] start create dir")
    directory = os.path.dirname(args.output_file)

    if not directory:
        directory = '.' 
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")
    subdirectories = ['source_home', 'screenshots', 'source_checkout']
    for subdir in subdirectories:
        sub_path = os.path.join(directory, subdir)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
            print(f"Created subdirectory: {sub_path}")
        else:
            print(f"Subdirectory already exists: {sub_path}")

    main(args)
