import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings("ignore")

FEATURE_PKL = "features_output.pkl"
LABELS_CSV = "labels.csv"
MODEL_OUT = "./domain_classifier/xgb_model.json"

print("\n===== XGBOOST TRAINING PIPELINE STARTED =====")


# -------------------------------------------------------------
# DOMAIN CLEANING FUNCTION (STRONG VERSION)
# -------------------------------------------------------------
def clean_domain(d):
    d = str(d).strip()

    # Remove all leading/trailing quotes
    d = d.strip("'").strip('"').strip()

    # Remove URL prefixes
    d = d.replace("https://", "")
    d = d.replace("http://", "")
    d = d.replace("www.", "")

    # Remove path after domain
    d = d.split("/")[0]

    return d.lower().strip()


# -------------------------------------------------------------
# 1) LOAD FEATURES
# -------------------------------------------------------------
print("[1/7] Loading features...")

data = pickle.load(open(FEATURE_PKL, "rb"))

if isinstance(data, tuple) and len(data) == 2:
    print("[INFO] Format: tuple (legacy extractor)")
    features_raw, domains = data
else:
    raise ValueError("Unsupported pickle format")

print(f"[INFO] Loaded {len(features_raw)} feature rows")

# Convert to numpy array
X = np.array(features_raw, dtype=object)

# Handle (N,1,F) shape
if X.ndim == 3 and X.shape[1] == 1:
    print(f"[INFO] Detected shape {X.shape} → squeezing axis 1")
    X = X.squeeze(axis=1)

# Convert object rows into numeric matrix
if X.dtype == object:
    try:
        X = np.vstack(X.tolist())
    except Exception as e:
        print("[ERROR] Could not convert nested features:", e)
        raise

print(f"[INFO] Final numeric feature shape: {X.shape}")

# Build DataFrame
features_df = pd.DataFrame(X)
features_df["domain"] = domains

# CLEAN PKL DOMAINS
features_df["domain"] = features_df["domain"].apply(clean_domain)


# -------------------------------------------------------------
# 2) LOAD LABELS
# -------------------------------------------------------------
print("[2/7] Loading labels...")

labels_df = pd.read_csv(LABELS_CSV)
labels_df["domain"] = labels_df["domain"].astype(str).apply(clean_domain)
labels_df = labels_df[labels_df["label"].isin([0, 1])]

print(f"[INFO] Loaded {len(labels_df)} labeled domains")


# DEBUG PRINTS
print("\n=== DEBUG: FIRST 10 CLEANED PKL DOMAINS ===")
print(features_df["domain"].head(10))

print("\n=== DEBUG: FIRST 10 CLEANED LABEL DOMAINS ===")
print(labels_df["domain"].head(10))

print("\n=== DEBUG: INTERSECTION (domains in both) ===")
intersection = set(features_df["domain"]).intersection(set(labels_df["domain"]))
print(intersection)
print(f"Count intersected: {len(intersection)}\n")


# -------------------------------------------------------------
# 3) MERGE
# -------------------------------------------------------------
print("[3/7] Merging datasets...")

merged = features_df.merge(labels_df, on="domain", how="inner")

print(f"[INFO] Merged dataset size: {len(merged)} rows")

missing = len(features_df) - len(merged)
if missing > 0:
    print(f"[WARNING] {missing} domains had NO LABELS")

if len(merged) < 5:
    print("[ERROR] Too few matched rows — cannot train model.")
    exit()


# -------------------------------------------------------------
# 4) PREPARE DATA
# -------------------------------------------------------------
print("[4/7] Preparing data...")

y = merged["label"].astype(int).values
X = merged.drop(columns=["domain", "label"]).values


# -------------------------------------------------------------
# 5) SPLIT DATA
# -------------------------------------------------------------
print("[5/7] Splitting data...")

unique_classes = np.unique(y)
if len(unique_classes) < 2:
    print("[ERROR] Only ONE class present → cannot train classifier.")
    exit()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

print(f"[INFO] Train size: {len(X_train)}  Test size: {len(X_test)}")
print(f"[INFO] Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")


# -------------------------------------------------------------
# 6) TRAIN MODEL
# -------------------------------------------------------------
print("[6/7] Training XGBoost...")

model = XGBClassifier(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="binary:logistic",
    eval_metric="logloss",
    tree_method="hist",
    random_state=42,
)

model.fit(X_train, y_train)


# -------------------------------------------------------------
# 7) EVALUATE & SAVE
# -------------------------------------------------------------
print("\n[7/7] Evaluating model...\n")

preds = model.predict(X_test)

print("=== CONFUSION MATRIX ===")
print(confusion_matrix(y_test, preds))

print("\n=== CLASSIFICATION REPORT ===")
print(classification_report(y_test, preds))

print(f"[INFO] Saving model → {MODEL_OUT}")
model.save_model(MODEL_OUT)

print("\n===== TRAINING COMPLETE =====")
