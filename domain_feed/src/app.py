"""
Domain Feed (Demo Version)
--------------------------
This module prepares the initial list of candidate domains
for ScamMagnifier to analyze.

✅ Filters out unwanted domains (adult, gambling, crypto).
✅ Saves clean URLs to `domain_list.csv` (used by feature extractor).
"""

import pandas as pd
import re
import os
import whois
import undetected_chromedriver as uc

def website_filtering(url_list):
    """Filter out unwanted domains (adult, gambling, crypto, etc.)"""
    gambling = re.compile(r"casino|bet|poker|gambling", re.I)
    adult = re.compile(r"adult|sex|porn|xxx|erotic|nude|dating|romance", re.I)
    crypto = re.compile(r"crypto|bitcoin|blockchain|coin|wallet", re.I)

    filtered = []
    for url in url_list:
        if not (gambling.search(url) or adult.search(url) or crypto.search(url)):
            filtered.append(url)
    print(f"🔹 Filtered down to {len(filtered)} safe domains out of {len(url_list)}.")
    return filtered

def main():
    print("🚀 Starting Domain Feed module...")

    # Step 1: Sample domains (you can add or load from file later)
    seed_domains = [
        "https://www.amazon.com",
        "https://www.zara.com",
        "https://www.newegg.com",
        "https://www.shein.com",
        "https://www.etsy.com",
        "https://www.betway.com",      # Gambling (filtered)
        "https://www.pornhub.com",     # Adult (filtered)
        "https://www.coinbase.com",    # Crypto (filtered)
        "https://www.target.com",
        "https://www.shopify.com"
    ]

    # Step 2: Filter out unsafe ones
    clean_domains = website_filtering(seed_domains)

    # Step 3: Save clean domains for the feature extractor
    df = pd.DataFrame(clean_domains, columns=["URL"])
    output_file = os.path.abspath("domain_list.csv")
    df.to_csv(output_file, index=False)
    print(f"✅ Domain list saved successfully to: {output_file}")

    # Optional next step: print user guidance
    print("\nNext Step:")
    print("Run this command to extract features for these domains:\n")
    print(f"python ../domain_feature_extractor/src/app.py --input_file \"{output_file}\" --source_path \"./data\" --output_file \"./features_output.pkl\" --selected_languages \"en\"")

if __name__ == "__main__":
    main()