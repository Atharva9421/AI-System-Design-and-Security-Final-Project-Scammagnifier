import os
import datetime
import pandas as pd
import time
import re
from tqdm import tqdm
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from collections import defaultdict
import argparse
import requests
import urllib.request
from random import randint
from time import sleep
import random
import numpy as np
import sys
from multiprocessing import Pool
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from datetime import datetime
from merch_extractor import *
from config import *
from datetime import datetime
import os
from storage.dabase import Database
from storage.mongodb.mongo_utility import *

'''
sudo docker container ls
sudo docker attach <ID>

sudo docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=3 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true --shm-size="2g" seleniarm/standalone-chromium:latest

or 

sudo docker run --rm -it -p 4444:4444 -p 5900:5900 -p 7900:7900 -e SE_NODE_MAX_SESSIONS=9 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true --shm-size 2g seleniarm/standalone-chromium:latest

'''

info = {
    'email': 'somian123@gmail.com',
    'size': 'M',
    'first': 'Som',
    'name': 'joshua',
    'last' : 'Somian',
    'country': 'US',
    'address': '774 Davis Avenue',
    'apt': '345',
    'city': 'Fortuna',
    'state': 'CA', 
    'zipcode': '95540',
    'phone': '7077261518'
}
keys = {
    'id': 'name',
    'name': 'name',
    'first': 'first',
    'last': 'last',
    'address': 'address',
    'city': 'city',
    'cty': 'city',
    'town': 'city',
    'zip': 'zipcode',
    'postcode': 'zipcode',
    'postalCode': 'zipcode',
    'postalcode': 'zipcode',
    'phone': 'phone',
    'email': 'email',
    'state': 'state',
    'zone': 'state',
    'country': 'country',
    'addr': 'address',
}
    

_sleep_time = 4
_sleep_time_dialog = 5
 
def write_log(file,data,verbose=True):
    if verbose:
        current_date_time=datetime.now()
        current_date_time_str = current_date_time.strftime('%Y-%m-%d %H:%M:%S')
        print(current_date_time_str+"||"+data)
        if file:
            file.write(current_date_time_str+"||"+data+"\n")
            file.flush()

def search_elem(driver, xpath_str, text_list, single=True):
    res = []

    if type(xpath_str) is str:
        # get all of the buttons and check their text
        elems = driver.find_elements("xpath", xpath_str)
        for elem in elems:
            elem_text = elem.text
            for text in text_list:
                if text.lower() in elem_text.lower().strip():
                    if single: return elem
                    res.append(elem)  
    else:
        # get all of the buttons and check their text
        for search_xpath in xpath_str:
            elems = driver.find_elements("xpath", search_xpath)
            
            for elem in elems:
                elem_text = []
                if elem.text.lower().strip():
                    elem_text.append(elem.text.lower().strip())
                if not elem_text:
                    inner_elements = elem.find_elements(By.XPATH,".//*")
                    for item in inner_elements:
                        if item.text.lower().strip():    
                            elem_text.append(item.text.lower().strip())
                for text in text_list:
                    for e_text in elem_text:
                        if text.lower() in e_text:
                            if single: return elem
                            res.append(elem)            
    return None if single else res

def clean_url(url):
    # Remove http:// or https://
    url = re.sub(r'^https?:\/\/', '', url)
    # Remove www.
    url = re.sub(r'^www\.', '', url)
    return url

def shallow_filter(raw_links, domain):
    # shallow filter on urls
    domain = clean_url(domain)
    links = []
    shallow_filter = ['/search', '/story', '/live', '/help', '/email', '/account', '/cookie', '/about', '/cart', 
                      '/track', '/contact',  '/ privacy', '/policy', '/terms', '/refund', '/login', '/bag', '/faq', 
                      '/support', '/customer-service', '/returns', '/shipping', '/signup', '/register', '/forgot-password', 
                      '/profile', '/legal', '/disclaimer', '/news', '/events', '/blog'
                    ]
    for link in raw_links:
        avoid = False
        for s in shallow_filter:
            if s in link:
                avoid = True
                break

        # shallow filter for product category 
        if 'category' in link or 'product-category' in link:
            avoid = True

        if not avoid and domain in link:
            links.append(link)
    return links

def checkout_shop(domain, driver,f_log, args):
    write_log(f_log,"checkout_shop")
    flag = False

    # Ensure screenshot and HTML folders exist
    os.makedirs(args.screen_file_address, exist_ok=True)
    os.makedirs(args.html_file_address, exist_ok=True)


    time.sleep(5)

    # check for popups
    write_log(f_log,"Search for popup")
    for i in ["//button[contains(@aria-label, 'Close')]", "//button[contains(@aria-label, 'close')]"]:
        close_btn = driver.find_elements('xpath', i)
        if close_btn != []:
            try:
                close_btn[0].click()
                write_log(f_log,"click on close btn in popup")
            except:
                pass

    write_log(f_log,"start finding links")
    raw_links = []
    raw_links.extend([i.get_attribute('href') for i in driver.find_elements("xpath", "//a[contains(@href, \"%s\")]" % ('/product'))])
    raw_links.extend([i.get_attribute('href') for i in driver.find_elements("xpath", "//link[contains(@href, \"%s\")]" % ('/product'))])
    raw_links.extend([i.get_attribute('href') for i in driver.find_elements("xpath", "//a[contains(@href, \"%s\")]" % ('?product'))])
    links = shallow_filter(raw_links, domain)

    if links == []:
        for e in driver.find_elements("xpath", "//a"):
            link = e.get_attribute('href')
            if link is not None:
                raw_links.append(link)
    links = shallow_filter(raw_links, domain)

    write_log(f_log,"Start checking links")

    all_links = list(set(links))
    links = [link for link in all_links if not link.endswith('.css') and not link.endswith('.xml')]
    for i in range(10):
        try: 
            # try to get second page items
            raw_links = []
            raw_links.extend([i.get_attribute('href') for i in driver.find_elements("xpath", "//a[contains(@href, \"%s\")]" % ('/product'))])
            raw_links.extend([i.get_attribute('href') for i in driver.find_elements("xpath", "//link[contains(@href, \"%s\")]" % ('/product'))])
            raw_links.extend([i.get_attribute('href') for i in driver.find_elements("xpath", "//a[contains(@href, \"%s\")]" % ('?product'))])
            raw_links = shallow_filter(raw_links, domain)
            if raw_links == []:
                for e in driver.find_elements("xpath", "//a"):
                    link = e.get_attribute('href')
                    if link is not None:
                        raw_links.append(link)
            raw_links = shallow_filter(raw_links, domain)

            links.extend(raw_links)
            links = list(set(links))
            prod_link = []
            if links:
                prod_link = links[randint(0, len(links) - 1)]
                write_log(f_log,f"product : {prod_link}")
                driver.get(prod_link)
            else:
                continue
            
            try:
                write_log(f_log,f"Close second popup")
                time.sleep(_sleep_time_dialog)
                actions = ActionChains(driver)
                actions.move_by_offset(2, 2).click().perform()
                write_log(f_log,f"Popup is closed")
            except Exception as e:
                write_log(f_log,f"Error clicking the second popups button")
            
            time.sleep(randint(1, _sleep_time))

            # try to fill out item size etc
            write_log(f_log,f"selecting item options")
            for select in driver.find_elements(By.XPATH, "//select"):
                try:
                    select_item = Select(select)
                    select_item.select_by_index(randint(0, len(select_item.options) - 1))
                    write_log(f_log, f"selected {select_item.options}")
                except:
                    pass
            # check for size div/spans
            for size_elem in driver.find_elements("xpath", "//div[contains(@class, \"size-selector\")]"):
                try:
                    write_log(f_log,f"clicking on {size_elem}")
                    size_elem.click()
                except:
                    pass
            write_log(f_log,f"done selecting item options")

            # find cart button
            cart_elem = search_elem(driver, '//button', ['Add to Bag', 'add to cart', 'buy now', 'buy product', 'Añadir al carrito', 
                                                         'Ajouter au panier', ' Aggiungi al carrello ', 'add to bag', 'add to basket', 
                                                         'purchase', 'order now', 'get it now', 'shop now',  'add item', 'add this item'
                                                        ])
            if cart_elem:
                write_log(f_log,f"try add to cart")
                cart_elem.click()
                time.sleep(_sleep_time)
                write_log(f_log,f"product added")
                break

            if 'amazon' in driver.current_url:
                continue

        except Exception as e:
            write_log(f_log,f"An error occurce : {e}")
            pass

    # if paypal iframe exist swith to paypal iframe
    write_log(f_log,f"looking for paypal button in the product page")
    write_log(f_log,f"first, swith to paypal iframe if exists")
    driver.switch_to.default_content()
    iframes = driver.find_elements("xpath", "//iframe[contains(@name, 'paypal') or contains(@id, 'paypal')]")
    print(iframes)
    if iframes:
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                jq = 'document.querySelectorAll(\'[role="link"]\').forEach(function (el){el.click();});'
                driver.execute_script(jq)
                flag = True
            except Exception as e:
                write_log(f_log,f"An error occure in swith to paypal iframe : {e}")
                pass

    # try finding the actual cart link first
    cart_links = [i.get_attribute('href') for i in driver.find_elements("xpath", "//a[contains(@href, \"%s\")]" % ('/cart'))]
    
    for l in cart_links:
        if 'remove' not in l:
            driver.get(l)
            break

    # try to find and click paypal button
    if not flag:
        write_log(f_log,f"Start looking paypal (1)")
        for paypal_filter in ['//img[contains(@alt, "PayPal")]', '//div[contains(@role, "link")]', '//div[contains(@class, "paypal-button-number-0")]', '//a[contains(@href, "paypal")]', '//div[contains(@class, "paypal")]']:
            try:
                paypal_buttons = driver.find_elements("xpath", paypal_filter)
                for btn in paypal_buttons:
                    try:
                        if '//a' in paypal_filter:
                            driver.get(btn.get_attribute('href'))
                            flag = True
                            write_log(f_log,f"paypal link (1)")
                            break
                        else:
                            write_log(f_log,f"paypal button (1)")
                            driver.save_screenshot(args.screen_file_address + domain.replace('/', '_').replace(':', '_') + '.png')
                            btn.click()
                            flag = True
                            break
                    except Exception as e:
                        write_log(f_log,f"error in looking paypal (1) {e}")
                        pass
                    if flag:
                        time.sleep(_sleep_time)
                        break
                if flag:
                    break
            except Exception as e:
                write_log(f_log,f"Filter Issue in looking paypal (1) {e}")
                pass

        write_log(f_log,f"flag : {flag}")

    time.sleep(randint(1,2))
    
    # proceed to checkout
    if not flag:
        write_log(f_log,f"Looking for checkout")
        checkout_elem = search_elem(driver, ['//button', '//a'], ['proceed to checkout', 'checkout', 'check out' ,'Finalizar compra', 'Voir mon panier', 'mon panier', 
                                                                  'Finaliser ma commande', 'Procedi all\'acquisto', 'Vai al carrello',  'proceed with purchase', 'complete purchase', 
                                                                  'finish order', 'review order', 'proceed to payment', 'confirm order', 'complete order'], False)
        for e in checkout_elem:
            try:
                driver.execute_script("arguments[0].click();", e)
                time.sleep(1)
            except Exception as ex:
                write_log(f_log,f"An error occure in checkout: {e}")
                continue

    if not flag:
        for i in range(1):
            try:
                all_inputs = driver.find_elements("xpath", '//input')
                for inp in all_inputs:
                    try:
                        for k, v in keys.items():
                            if k in inp.get_attribute('id').lower() or k in inp.get_attribute('name').lower():
                                inp.clear()
                                inp.send_keys(info[v])
                    except Exception as e:
                        write_log(f_log,f"internal error in filling form : {e}")
                        continue
                    
                all_selects = driver.find_elements(By.XPATH, "//select")
                for select in all_selects:
                    select_ok = Select(select)
                    if 'state' in select.get_attribute('name').lower() or 'zone' in select.get_attribute('name').lower():
                        select_ok.select_by_value(info['state'])
                    elif 'country' in select.get_attribute('name').lower():
                        select_ok.select_by_value(info['country'])
            except Exception as ex:
                write_log(f_log,f"Error : {ex}")
            finally:
                time.sleep(_sleep_time + 3)
                # special form of PayPal 
            write_log(f_log,f"Find paypal span")
            try:
                possible_paypal_chks = ["//span[contains(text(), 'PayPal')]", "//span[contains(text(), 'paypal')]"]
                for chk in possible_paypal_chks:
                    elems = driver.find_elements("xpath", chk)
                    if elems:
                        for e in elems:
                            e.click()
                            write_log(f_log,f"click paypal span btn")
            except Exception as ex:
                write_log(f_log,f"Error : {ex}")

    if not flag:
        write_log(f_log,f"Start looking paypal button at checkout page")
        for paypal_filter in ['//img[contains(@class, "paypal-button-logo")]', '//div[contains(@role, "link")]', '//div[contains(@class, "paypal-button-number-0")]', '//a[contains(@href, "paypal")]', '//div[contains(@class, "paypal")]', '//img[contains(@class, "paypal-logo")]']:
                try:
                    paypal_buttons = driver.find_elements("xpath", paypal_filter)
                    for btn in paypal_buttons:
                        try:
                            if '//a' in paypal_filter:
                                driver.get(btn.get_attribute('href'))
                                write_log(f_log,f"paypal link (2)")
                                flag = True
                                break
                            else:
                                write_log(f_log,f"paypal btn (2)")
                                driver.save_screenshot(args.screen_file_address + domain.replace('/', '_').replace(':', '_') + '.png')
                                btn.click()
                                flag = True
                                break
                            # break
                        except Exception as e:
                            write_log(f_log,f"error : {e}")
                            pass
                        if flag:
                            time.sleep(_sleep_time)
                            break
                    if flag:
                        break
                except Exception as e:
                    write_log(f_log,f"error in Filter: {e}")
                    pass
        write_log(f_log,f"Paypal first try:" + str(flag))

    if not flag:
        write_log(f_log,f"Second try")
        # perform general checkout
        for chk in ["//form[contains(@name, 'checkout')]", "//form[contains(@id, 'checkout')]", "//form[contains(@type, 'submit')]"]:
            try:
                elems = driver.find_elements("xpath", chk)
                if elems:
                    elems[0].submit()
                    flag = True
                    break
            except Exception as e:
                write_log(f_log,f"second try error: {e}")
                pass
            
    if not flag:
        for chk in ["form[name*=checkout]", "form[id*=checkout]"]:
            s = """var form = document.querySelector("{CHK}");
            if (form) { form.submit(); }""".replace('{CHK}', chk)
            driver.execute_script(s) 
            write_log(f_log,f"Third try: ", s)
            driver.switch_to.default_content()
            if not flag and driver.find_elements("xpath", "//iframe"):
                write_log(f_log,f"looking for iframe")
                for iframe in driver.find_elements("xpath", "//iframe"):
                    try:
                        driver.switch_to.frame(iframe)
                        jq = 'document.querySelectorAll(\'[role="link"]\').forEach(function (el){el.click();});'
                        driver.execute_script(jq)
                    except Exception as ex:
                        write_log(f_log,f"error in looking for iframe {ex}")
                        pass
                        
        write_log(f_log,f"flag : {flag}")

    
    time.sleep(8)
    write_log(f_log,f"finally ...")
    # -------------------------------------------------
    log_entries = []
    write_log(f_log,f"save windows.")

    for index, handle in enumerate(driver.window_handles):
        driver.switch_to.window(handle)
        html_path = os.path.join(args.html_file_address, f"{domain.replace('/', '_').replace(':', '_')}_{index}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # ✅ Safe attempt at getting logs (won’t crash if unsupported)
        try:
            logs = driver.get_log("performance")
            log_entries.append(logs)
        except Exception as e:
            write_log(f_log, f"[WARN] Performance logs not available: {e}")
            log_entries.append([])

        log_entries.append(driver.current_url)

    # ✅ Always save fallback screenshots even if logs fail
    try:
        timestamp = int(time.time())
        screenshot_path = os.path.join(args.screen_file_address, f"{domain.replace('/', '_')}_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        write_log(f_log, f"[+] Screenshot saved at {screenshot_path}")
    except Exception as e:
        write_log(f_log, f"[ERROR] Screenshot save failed: {e}")



    try:
        # ✅ Sanitize filename for Windows
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', domain)
        timestamp = int(time.time())
        screenshot_path = os.path.join(args.screen_file_address, f"{safe_name}_{timestamp}.png")
        html_path = os.path.join(args.html_file_address, f"{safe_name}_{timestamp}.html")

        # ✅ Save screenshot and page source
        driver.save_screenshot(screenshot_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        write_log(f_log, f"✅ Screenshot and HTML saved for {domain}")
    except Exception as e:
        write_log(f_log, f"⚠️ Error saving screenshot/HTML for {domain}: {e}")

    return log_entries

def run_fc(data_pack):
    # ✅ 1. Properly unpack args for this worker process
    my_id, urls, args = data_pack

    results = []

    # ✅ 2. Fix incorrect log_dir construction (use dirname)
    log_dir = os.path.join(os.path.dirname(args.log_file_address), "logs")
    os.makedirs(log_dir, exist_ok=True)

    f_log_path = os.path.join(log_dir, f"log_{my_id}.log")
    f_log = open(f_log_path, "w", encoding="utf-8")
    write_log(f_log, f"Hi, I'm process number {my_id}")

    iterator = tqdm(urls) if my_id == 0 else urls
    for domain in iterator:
        d = DesiredCapabilities.CHROME
        d["goog:loggingPrefs"] = {"performance": "ALL", "browser": "ALL"}
        options = uc.ChromeOptions()
        # Run headless in Docker (no GUI)
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        options.add_argument("--incognito")
        options.add_argument("--enable-javascript")
        options.add_argument("--ignore-certificate-errors")
        prefs = {"translate_whitelists": {"fr": "en", "es": "en"}, "translate": {"enabled": "true"}}
        options.add_experimental_option("prefs", prefs)

        try:
            write_log(f_log, f"selenium address : {selenium_addr}")
            driver = uc.Chrome(options=options)
        except Exception as e:
            write_log(f_log, f"Error in open selenium : {e}")
            continue

        write_log(f_log, f"domain : {domain}")
        if domain:
            try:
                if "https://" not in domain:
                    domain = "https://" + domain

                write_log(f_log, f"final domain : {domain}")
                try:
                    driver.get(domain)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    write_log(f_log, f"domain get")
                except Exception as e:
                    write_log(f_log, f"Error in get domain: {e}")

                try:
                    action = ActionChains(driver)
                    action.move_by_offset(10, 20).perform()
                    write_log(f_log, f"Dialog close")
                except Exception as e:
                    write_log(f_log, f"Error in close dialog: {e}")

                time.sleep(5)
                log = checkout_shop(domain, driver, f_log,args)
                write_log(f_log, f"Checkout Done")
                results.append(
                    json.dumps({"refs": get_redirections_all({"domain": domain, "log": log}), "domain": domain})
                )

            except Exception as e:
                write_log(f_log, f"Error in run_fc : {e}")
                pass

        try:
            driver.close()
        except:
            pass

        try:
            driver.quit()
        except:
            pass

    return results


def get_redirections_all(log):
    domain = log['domain'].replace('https://', '').replace('http://', '').replace('/', '')
    ref_res = []

    for l in log['log'][0]:
        if 'paypal.com' in l['message']:
            try:

                ref = json.loads(l['message'])['message']['params']['request']['headers']['Referer']
                if domain not in ref and 'paypal' not in ref and ref != '':
                    headers = json.loads(l['message'])['message']['params']['request']
                    ref_res.append({
                        'domain': log['domain'],
                        'referer': headers['headers']['Referer'],
                        'paypal_link': headers['url']
                    })

            except:
                pass
    return ref_res

def perform_checkout(urls, out_file,number_of_proc):
    
    batch_size = max(1,len(urls)//number_of_proc)
    print(f"[*] len {len(urls)} , number_of_proc {number_of_proc} , batch_size {batch_size}")
    data_packs = []
    proc_ind = 0
    for i in range(0, len(urls), batch_size):
        data_packs.append([
            proc_ind,
            urls[i:i+batch_size],
            args
        ])
        proc_ind += 1
    
    with Pool(number_of_proc) as p:
        results = p.map(run_fc, data_packs)

    with open(out_file, 'a+', encoding="utf-8") as fout:
        for process_result in results:
            # ✅ Handle case when a domain fails or produces no result
            if not process_result:
                fout.write(json.dumps({
                    "status": "no_data",
                    "timestamp": str(datetime.now())
                }) + '\n')
            else:
                for res_str in process_result:
                    fout.write(res_str + '\n')
        fout.flush()

    # with open(out_file, 'a+') as fout:
    #     for process_result in results:
    #         for res_str in process_result:
    #             fout.write(res_str + '\n')
    #     fout.close()

def read_txt_file(fpath):
    out_list = []
    with open(fpath, 'r') as file:
        # Iterate over each line in the file
        for line in file:
            out_list.append(line.strip())
    return out_list

def read_csv_file(filepath):
    df = pd.read_csv(filepath)
    
    # Check if the 'Label' column exists
    if 'Label' in df.columns:
        labels = df['Label']
        data = df.drop(columns=['Label'])
        return data, labels
    else:
        return df, None
    
def get_label_for_url(url_value, data, labels):
    if labels is not None and 'URL' in data.columns:
        row_index = data[data['URL'] == url_value].index
        if not row_index.empty:
            return 1 if labels.iloc[row_index[0]] != 0 else 0
        else:
            return None
    else:
        return None

def clean_url(url):
    # Regular expression pattern to match and remove the desired prefixes
    pattern = re.compile(r'^(http:\/\/|https:\/\/|www\.)+')
    # Replace the matched prefixes with an empty string
    cleaned_url = re.sub(pattern, '', url)
    return cleaned_url

def dump_list_to_file(_list,file_path):
    with open(file_path,'w') as file:
        for item in _list:
            file.write(f"{item} \n")
        file.flush()


def main(args):

    mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}?authSource={mongo_db}"
    database = Database.instance()
    print(mongo_uri)
    database.create_connection(mongo_uri)
    urls= []

    if args.url:
        urls.append(args.url)

    elif args.input_file:
        data, labels = read_csv_file(args.input_file)
        urls = data['URL'].tolist()

    outpath = args.p_log_file_address

    if urls and len(urls) > 0:
        if args.filteredlist_log:
            dump_list_to_file(urls,args.filteredlist_log)
        perform_checkout(urls, outpath, args.number_proc)
        # extract merchant IDs
        final_outpath = outpath.replace('log', 'merch-info').replace('.jsonl', '.json')
        os.makedirs(os.path.dirname(final_outpath), exist_ok=True)
        m_data = parse_data(outpath, final_outpath,args.html_file_address)
        if args.save_db and args.save_db == "yes" and m_data:
            for url, details in m_data.items():
                print("URL:", url)
                unique_values = set()
                for idx, merch_ids in details['merch_id'].items():
                    unique_values.update(merch_ids)
                for value in unique_values:
                    if len(value)>1:
                        save_merchant(_domain=clean_url(url), _merchant_id=value, _organizitaion="N/A", _scam=1)

def mkdir_if_not_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Optional app description')

    parser.add_argument('--input_file', type=str, help='input containing bp results', required=False)
    parser.add_argument('--url', type=str, help='URL to checkout , do not need to set bp and ec if you set URL', required=False)
    parser.add_argument('--log_file_address', type=str, help='log file address', required=True)
    parser.add_argument('--p_log_file_address', type=str, help='redirection file address (jsonl)', required=True)
    parser.add_argument('--screen_file_address', type=str, help='screenshot directory', required=True)
    parser.add_argument('--html_file_address', type=str, help='directory to save checkoutpage', required=True)
    parser.add_argument('--number_proc', type=int, help='number of proc', required=False, default=1)
    parser.add_argument('--filteredlist_log', type=str, help='filteredlist_log', required=False)
    parser.add_argument('--save_db', type=str, help='save_db', required=False , default="yes")

    args = parser.parse_args()

    print("[+] start create dir")

    # Base directory (for logs, screenshots, html)
    base_dir = os.path.dirname(args.log_file_address)

    # Ensure base directory exists
    mkdir_if_not_exists(base_dir)

    # Create all necessary subfolders once
    subdirectories = ["screenshots", "checkout_html", "logs"]
    for subdir in subdirectories:
        sub_path = os.path.join(base_dir, subdir)
        mkdir_if_not_exists(sub_path)
        print(f"Ensured subdirectory exists: {sub_path}")

    main(args)
