ScamMagnifier++ – Fraudulent E-Commerce Website Detection Pipeline

Graduate-Level Reproduction & Extension Project
University of Wisconsin–Milwaukee
AI System Security – Fall 2025

--Overview
This project reproduces the key stages of the ScamMagnifier framework, a system designed to detect and analyze fraudulent e-commerce websites that mimic legitimate online stores.
The pipeline automatically classifies new domains, extracts web features, detects potential scams, and performs an automated checkout to analyze merchant information.

--Pipeline Overview
The project consists of five main stages:
Domain_Feed → Shop_Classifier → Feature_Extractor → Domain_Classifier → AutoCheckout


Stage 1 — Domain Feed:
Input list of candidate domains (CSV).
A curated subset of the Tranco Top Sites Dataset was used for additional realism and coverage

Stage 2 — Shop Classifier:
Uses Sentence-BERT (all-MiniLM-L6-v2) to compute vector similarity between domain tokens and seven category embeddings
This method classifies domains even when keywords are missing (e.g., “shopee”, “temu”, “ozon”).
It avoids hand-crafted rules and provides generalizable semantic behavior.

Stage 3 — Domain Feature Extractor:
Collect WHOIS, HTML, language, and IP-based features for each domain.
Filters out pages with low content (page length < 3000) to ensure valid data. Implements and extends ScamMagnifier’s feature extractor with several BeyondPhish inspired features

Stage 4 — Domain Classifier:
The domain classifier uses an explainable heuristic model that blends domain-structure signals, WHOIS age thresholds, TLD-risk lists, and keyword-based scoring. It also incorporates HTML quality penalties and external-link reputation features to reflect real scam-site behavior.
These factors combine into a transparent risk score that outputs a scam/legit label with confidence.

Stage 5 — AutoCheckout:
The AutoCheckout module simulates a real browser-based checkout using undetected-chromedriver to extract merchant IDs, payment gateways, script URLs, and redirection chains.
Because this stage functions as a runtime operational component rather than a research-focused module, it was not extended further.
It is retained in the pipeline to ensure end-to-end completeness and functional realism of the ScamMagnifier framework.

--Environment Setup
1️--Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

2️--Set up Docker containers
Run Selenium Chrome container:
docker run -d --name scam-selenium -p 4444:4444 --shm-size=2g ^
  -e SE_NODE_MAX_SESSIONS=3 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true ^
  selenium/standalone-chrome:latest

Verify containers:
docker ps
Expected output:
CONTAINER ID   IMAGE       STATUS          PORTS                      NAMES
8c123a4b5d6e   mongo:6     Up 10 seconds   0.0.0.0:27017->27017/tcp   scam-mongo
Running Each Stage

Stage 2 — Shop Classifier
python .\shop_classifier\src\app.py --input_file "./domain_feed/domain_list.csv" --output_file "./shop_classifier/shop_results.csv"

Stage 3 — Domain Feature Extractor
Install dependencies:
pip install langid IP2Location webdriver-manager

Then run:
python .\domain_feature_extractor\src\app.py ^
  --input_file ".\domain_feed\domain_list.csv" ^
  --source_path ".\domain_feature_extractor\data" ^
  --output_file ".\domain_feature_extractor\features_output.pkl" ^
  --selected_languages "en"

Stage 4 — Domain Classifier
python .\domain_classifier\src\app.py ^
  --input_file ".\domain_feature_extractor\features_output.pkl" ^
  --output_file ".\domain_classifier\classification_results.csv"

Stage 5 — AutoCheckout
Install additional dependencies:
pip install undetected-chromedriver setuptools pymongo mongoengine
Run AutoCheckout:
python .\autocheckout\src\app.py ^
  --input_file ".\domain_classifier\classification_results.csv" ^
  --log_file_address ".\autocheckout\logs\autocheckout.log" ^
  --p_log_file_address ".\autocheckout\logs\autocheckout.jsonl" ^
  --screen_file_address ".\autocheckout\screenshots\" ^
  --html_file_address ".\autocheckout\checkout_html\" ^
  --number_proc 1 --save_db no

Output Files
Stage Output File	Description
Shop Classifier	shop_results.csv	Domains classified as shops or not
Feature Extractor	features_output.pkl	Extracted features for each domain
Domain Classifier	classification_results.csv	Scam / Legit predictions
AutoCheckout	.log, .jsonl, .html, .png	Checkout logs, merchant data, screenshots

Troubleshooting
Selenium fails to connect:
Ensure the scam-selenium container is running and accessible on port 4444.
Feature extractor stops early:
Check if HTML pages are too short (page length < 3000) — add valid sites.