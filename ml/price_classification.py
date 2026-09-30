import pandas as pd
import pickle
import os

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ==========================================
# 1. PROJECT PATH
# ==========================================

project_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

dataset_path = os.path.join(
    project_folder,
    "dataset",
    "mandi_prices.csv"
)


# ==========================================
# 2. LOAD DATASET
# ==========================================

print("Loading dataset...")

df = pd.read_csv(dataset_path)

print("Dataset loaded successfully!")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ==========================================
# 3. PREPARE DATE
# ==========================================

df["Price Date"] = pd.to_datetime(df["Price Date"])

df["Year"] = df["Price Date"].dt.year
df["Month"] = df["Price Date"].dt.month
df["Day"] = df["Price Date"].dt.day
df["DayOfYear"] = df["Price Date"].dt.dayofyear


# ==========================================
# 4. SORT DATA BY DATE
# ==========================================

df = df.sort_values("Price Date").reset_index(drop=True)


# ==========================================
# 5. CREATE PREVIOUS PRICE
# ==========================================

df["Previous_Price"] = (
    df.groupby(
        ["STATE", "District Name", "Market Name", "Commodity"]
    )["Modal_Price"]
    .shift(1)
)


# ==========================================
# 6. CREATE 7-DAY AVERAGE
# ==========================================

df["Price_7_Day_Avg"] = (
    df.groupby(
        ["STATE", "District Name", "Market Name", "Commodity"]
    )["Modal_Price"]
    .transform(
        lambda x: x.shift(1).rolling(7, min_periods=1).mean()
    )
)


# ==========================================
# 7. CREATE 30-DAY AVERAGE
# ==========================================

df["Price_30_Day_Avg"] = (
    df.groupby(
        ["STATE", "District Name", "Market Name", "Commodity"]
    )["Modal_Price"]
    .transform(
        lambda x: x.shift(1).rolling(30, min_periods=1).mean()
    )
)


# ==========================================
# 8. REMOVE MISSING VALUES
# ==========================================

df = df.dropna(
    subset=[
        "Previous_Price",
        "Price_7_Day_Avg",
        "Price_30_Day_Avg"
    ]
).reset_index(drop=True)


# ==========================================
# 9. CREATE PRICE CATEGORIES
# ==========================================

low_threshold = df["Modal_Price"].quantile(0.33)
high_threshold = df["Modal_Price"].quantile(0.66)

print("\nPrice category thresholds:")
print("Low threshold    :", round(low_threshold, 2))
print("High threshold   :", round(high_threshold, 2))


def classify_price(price):

    if price <= low_threshold:
        return "Low"

    elif price <= high_threshold:
        return "Medium"

    else:
        return "High"


df["Price_Category"] = df["Modal_Price"].apply(classify_price)


print("\nCategory distribution:")
print(df["Price_Category"].value_counts())


# ==========================================
# 10. FEATURES
# ==========================================

categorical_features = [
    "STATE",
    "District Name",
    "Market Name",
    "Commodity",
    "Variety",
    "Grade"
]

numeric_features = [
    "Year",
    "Month",
    "Day",
    "DayOfYear",
    "Previous_Price",
    "Price_7_Day_Avg",
    "Price_30_Day_Avg"
]


features = categorical_features + numeric_features


# ==========================================
# 11. ENCODE CATEGORICAL FEATURES
# ==========================================

category_mappings = {}

for column in categorical_features:

    df[column] = df[column].astype(str)

    unique_values = df[column].unique()

    mapping = {
        value: index
        for index, value in enumerate(unique_values)
    }

    category_mappings[column] = mapping

    df[column] = df[column].map(mapping)


# ==========================================
# 12. PREPARE X AND Y
# ==========================================

X = df[features]

y = df["Price_Category"]


# ==========================================
# 13. TIME-BASED TRAIN TEST SPLIT
# ==========================================

split_index = int(len(df) * 0.80)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print("\nTraining rows:", len(X_train))
print("Testing rows :", len(X_test))

print(
    "\nTraining period:",
    df["Price Date"].iloc[0].date(),
    "to",
    df["Price Date"].iloc[split_index - 1].date()
)

print(
    "Testing period :",
    df["Price Date"].iloc[split_index].date(),
    "to",
    df["Price Date"].iloc[-1].date()
)


# ==========================================
# 14. SHOW FEATURES
# ==========================================

print("\nFeatures used:")

for feature in features:
    print("-", feature)


# ==========================================
# 15. TRAIN RANDOM FOREST
# ==========================================

print("\nTraining Random Forest Classifier...")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)

model.fit(X_train, y_train)

print("Model training completed!")


# ==========================================
# 16. PREDICTION
# ==========================================

y_pred = model.predict(X_test)


# ==========================================
# 17. EVALUATION
# ==========================================

accuracy = accuracy_score(y_test, y_pred)

print("\n========================================")
print("RANDOM FOREST CLASSIFICATION RESULTS")
print("========================================")

print("\nAccuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred
    )
)

print("\nConfusion Matrix:")

print(
    confusion_matrix(
        y_test,
        y_pred
    )
)


# ==========================================
# 18. SAVE MODEL
# ==========================================

models_folder = os.path.join(
    project_folder,
    "models"
)

os.makedirs(models_folder, exist_ok=True)


model_path = os.path.join(
    models_folder,
    "price_category_classifier.pkl"
)

feature_info_path = os.path.join(
    models_folder,
    "price_classification_feature_info.pkl"
)


with open(model_path, "wb") as file:
    pickle.dump(model, file)


feature_info = {
    "categorical_features": categorical_features,
    "numeric_features": numeric_features,
    "features": features,
    "category_mappings": category_mappings,
    "low_threshold": low_threshold,
    "high_threshold": high_threshold
}


with open(feature_info_path, "wb") as file:
    pickle.dump(feature_info, file)


print("\n========================================")
print("MODEL SAVED SUCCESSFULLY")
print("========================================")

print("\nModel:", model_path)

print(
    "Feature information:",
    feature_info_path
)

print("\nPRICE CLASSIFICATION MODEL READY!")