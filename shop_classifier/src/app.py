import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
import numpy as np
import re


# ===============================
# 1. CATEGORY DESCRIPTIONS
# ===============================

CATEGORY_DESCRIPTIONS = {
    "Electronics": "online electronics store selling gadgets, computers, phones, cameras, tech accessories",
    "Fashion": "online clothing store offering apparel, shoes, accessories, womenswear menswear fashion products",
    "Home": "home improvement furniture decor lighting kitchen appliances home store",
    "Kids": "baby store kids clothing toys children's products newborn items",
    "Beauty/Health": "beauty skincare makeup health wellness pharmacy supplements cosmetics",
    "Marketplace": "large online marketplace with many sellers categories wide variety of products",
    "General Merchandise": "general online store selling various items across categories",
}


# ===============================
# 2. CLEAN HTML FUNCTION
# ===============================

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts, styles, meta
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.extract()

    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ===============================
# 3. CLASSIFY USING SBERT
# ===============================

def classify_with_sbert(model, page_text):
    if not page_text or len(page_text) < 50:
        return "General Merchandise", 0.20

    # Embed page text
    page_emb = model.encode(page_text, convert_to_tensor=True)

    # Create embeddings for categories
    cat_embeddings = {
        cat: model.encode(desc, convert_to_tensor=True)
        for cat, desc in CATEGORY_DESCRIPTIONS.items()
    }

    # Compute similarity
    scores = {}
    for cat, emb in cat_embeddings.items():
        sim = util.cos_sim(page_emb, emb).item()
        scores[cat] = sim

    # Pick best match
    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]

    return best_cat, round(best_score, 3)


# ===============================
# 4. FETCH PAGE HTML
# ===============================

def fetch_text(domain):
    try:
        url = domain if domain.startswith("http") else f"https://{domain}"
        response = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        return extract_visible_text(response.text)
    except:
        return ""


# ===============================
# 5. MAIN PIPELINE
# ===============================

def main(args):
    print("[INFO] Loading SBERT model…")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    df = pd.read_csv(args.input_file)
    domains = df["URL"].tolist()

    print(f"Loaded {len(domains)} URLs.")

    results = []

    for domain in domains:
        print(f"\n[PROCESS] {domain}")

        page_text = fetch_text(domain)
        category, confidence = classify_with_sbert(model, page_text)

        print(f" → {category} ({confidence})")

        results.append([domain, category, confidence])

    # Save results
    out = pd.DataFrame(results, columns=["URL", "Category", "Confidence"])
    out.to_csv(args.output_file, index=False)

    print(f"\n✅ SBERT-only classification saved to {args.output_file}")


# ===============================
# ENTRY POINT
# ===============================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SBERT-only Shop Classifier")
    parser.add_argument("--input_file", type=str, required=True)
    parser.add_argument("--output_file", type=str, required=True)
    args = parser.parse_args()
    main(args)
