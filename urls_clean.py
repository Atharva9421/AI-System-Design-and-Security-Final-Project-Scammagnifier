import pickle
import re

INPUT = "features_output.pkl"
OUTPUT = "features_output_clean.pkl"

print("[*] Loading PKL...")
X, urls = pickle.load(open(INPUT, "rb"))

def clean_domain(d):
    if not isinstance(d, str):
        d = str(d)

    # remove leading/trailing whitespace
    d = d.strip()

    # remove surrounding quotes: 'like.com' or "like.com"
    if (d.startswith("'") and d.endswith("'")) or (d.startswith('"') and d.endswith('"')):
        d = d[1:-1]

    # ensure lowercase
    d = d.lower()

    # strip slashes
    d = d.strip("/")

    return d

cleaned_urls = [clean_domain(u) for u in urls]

print("\n[*] BEFORE → AFTER (first 20)")
for i in range(min(20, len(urls))):
    print(urls[i], " → ", cleaned_urls[i])

print("\n[*] Saving cleaned PKL...")
pickle.dump((X, cleaned_urls), open(OUTPUT, "wb"))
print("[✔] Saved as features_output_clean.pkl")
