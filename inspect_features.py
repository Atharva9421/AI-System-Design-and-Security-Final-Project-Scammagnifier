import pickle as pkl
import numpy as np
import argparse
import os
import pandas as pd

def main(args):
    path = args.input_file

    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        return

    with open(path, "rb") as f:
        data = pkl.load(f)

    # Handle both (X, urls) and more complex tuples
    if isinstance(data, tuple) and len(data) >= 2:
        X, urls = data[0], data[1]
    else:
        print("[ERROR] Unexpected pickle format. Expected (X, urls).")
        print(f"Type of loaded object: {type(data)}")
        return

    X = np.array(X)
    print("=== RAW SHAPE OF X ===")
    print(X.shape)

    # If X has an extra singleton dimension, squeeze it
    if X.ndim == 3 and X.shape[1] == 1:
        print("\n[INFO] Detected shape (N, 1, F). Squeezing dimension 1.")
        X = np.squeeze(X, axis=1)
        print("New shape:", X.shape)

    elif X.ndim == 1:
        print("\n[WARNING] X is 1D. Trying to expand to 2D.")
        X = np.expand_dims(X, axis=1)
        print("New shape:", X.shape)

    print("\n=== BASIC STATS ===")
    print(f"Num domains: {len(urls)}")
    print(f"Num feature columns: {X.shape[1]}")

    # Show first few URLs
    print("\n=== FIRST 5 URLS ===")
    for u in urls[:5]:
        print(" -", u)

    # Show first few rows of features
    print("\n=== FIRST 5 FEATURE VECTORS (rows) ===")
    print(X[:5])

    # Show per-feature summary using pandas
    try:
        df = pd.DataFrame(X)
        print("\n=== PER-FEATURE SUMMARY (first 15 features) ===")
        print(df.iloc[:, :15].describe().T)  # describe first 15 columns

    except Exception as e:
        print("\n[WARNING] Could not create DataFrame summary:")
        print(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect domain features pickle file.")
    parser.add_argument("--input_file", type=str, required=True,
                        help="Path to features_output.pkl")
    args = parser.parse_args()
    main(args)
