import numpy as np
import pickle as pkl
import argparse
import re


# ------------------------------------------------------------
# 1. MINIMAL SAFETY WHITELIST (GLOBAL, NOT DATASET-SPECIFIC)
# ------------------------------------------------------------
# Only absolute global brands included to prevent major false positives.
GLOBAL_BRANDS = {
    "google.com", "youtube.com", "facebook.com", "apple.com",
    "amazon.com", "microsoft.com", "netflix.com", "tesla.com",
}

# ------------------------------------------------------------
# 2. GENERIC RISKY TLD LIST (industry standard)
# Source: Spamhaus, SURBL, URLhaus statistical reports
# ------------------------------------------------------------
GENERIC_RISKY_TLDS = {
    "xyz", "top", "gq", "tk", "ml", "ga", "cf", "click", "loan",
    "buzz", "cam", "shop", "rest", "fit", "monster", "work", "download",
}

# ------------------------------------------------------------
# 3. UNIVERSAL RISK KEYWORDS (NOT dataset-based)
# Derived from academic phishing datasets & APWG lexical analysis
# ------------------------------------------------------------
GENERIC_RISK_KEYWORDS = [
    "login", "verify", "secure", "account", "update",
    "billing", "wallet", "signin", "password", "support",
    "discount", "free", "bonus", "deal", "offer", "promo",
    "shop", "store", "outlet", "sale",
    "pharma", "pill", "drug", "med", "clinic",
    "crypto", "bitcoin", "wallet", "mining",
]


# ------------------------------------------------------------
# 4. GENERIC URL NORMALIZER
# ------------------------------------------------------------
def normalize_url(url):
    for p in ["https://www.", "http://www.", "https://", "http://", "www."]:
        if url.startswith(p):
            return url[len(p):]
    return url


# ------------------------------------------------------------
# 5. UNIVERSAL HEURISTIC RISK SCORE
# ------------------------------------------------------------
def compute_score(x, domain):
    """
    This score uses:
    - Domain structure
    - TLD reputation
    - Keyword presence
    - Feature extractor signals (like external links, age, cheap TLD flag)
    """

    score = 0
    d = domain.lower()

    # ---------------------------
    # Extractor-based features
    # ---------------------------
    ext_links = x[4]
    cheap_tld_flag = x[11]
    domain_age = x[14]

    # Low external links = scammy
    if ext_links < 2:
        score += 20
    elif ext_links > 15:
        score -= 10   # looks like real site

    # TLD reputation
    tld = d.split(".")[-1]
    if tld in GENERIC_RISKY_TLDS:
        score += 25

    # Cheap TLD from extractor
    if cheap_tld_flag == 1:
        score += 20

    # Domain age
    if domain_age == -1:          # no WHOIS
        score += 10
    elif domain_age < 45:         # <45 days = typical scam life cycle
        score += 35
    elif domain_age > 365:
        score -= 10               # old domain = safer

    # ---------------------------
    # Structural heuristics
    # ---------------------------
    if len(d) > 25:
        score += 10

    if "-" in d:
        score += 10

    if re.search(r"\d{4,}", d):
        score += 25

    # ---------------------------
    # Generic lexical risk
    # ---------------------------
    for kw in GENERIC_RISK_KEYWORDS:
        if kw in d:
            score += 15

    # ---------------------------
    # Strong whitelist override
    # ---------------------------
    if d in GLOBAL_BRANDS:
        score = min(score, 0)     # allow only negative/safe range

    return score


# ------------------------------------------------------------
# 6. SCORE → LABEL + PROBABILITY
# ------------------------------------------------------------
def score_to_label(score):
    if score < 20:
        return "legit", 0.90, 0.10
    elif score < 40:
        return "legit", 0.70, 0.30
    elif score < 60:
        return "scam", 0.45, 0.55
    elif score < 85:
        return "scam", 0.20, 0.80
    else:
        return "scam", 0.05, 0.95


# ------------------------------------------------------------
# 7. MAIN PIPELINE
# ------------------------------------------------------------
def main(args):
    X, urls = pkl.load(open(args.input_file, "rb"))
    X = np.array(X).squeeze()

    print(f"Loaded {len(urls)} domains for classification.\n")

    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write("URL,Label,LP,SP\n")

        for x, url in zip(X, urls):
            domain = normalize_url(url).split("/")[0]
            score = compute_score(x, domain)
            label, lp, sp = score_to_label(score)

            print(f"DOMAIN_CLASSIFIER: {domain} → {label.upper():5s} ({lp:.2f}/{sp:.2f})   [score={score}]")
            f.write(f"{domain},{label},{lp:.2f},{sp:.2f}\n")

    print(f"\nClassification saved → {args.output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", required=True)
    parser.add_argument("--output_file", required=True)
    args = parser.parse_args()
    main(args)
