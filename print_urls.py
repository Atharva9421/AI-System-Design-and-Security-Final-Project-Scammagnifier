import pickle
import pandas as pd

data = pickle.load(open("features_output.pkl", "rb"))
features, domains = data

print("=== RAW DOMAINS FROM PKL ===")
for d in domains[:50]:
    print(repr(d))

df = pd.read_csv("labels.csv")
print("\n=== RAW DOMAINS FROM LABELS.CSV ===")
print(df.head(10))
print("Rows:", len(df))

import pandas as pd
df = pd.read_csv("labels.csv")
print(df.columns)
print(df.head())
print(len(df))