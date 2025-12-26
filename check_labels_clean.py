import pandas as pd

df = pd.read_csv("labels.csv")

print("=== FIRST 20 ROWS with REPR ===")
for i, row in df.head(20).iterrows():
    print(repr(row['domain']), repr(row['label']))
