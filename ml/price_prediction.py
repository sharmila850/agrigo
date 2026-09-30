import pandas as pd
import os
import pickle

from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ==========================================
# 1. LOAD DATASET
# ==========================================

file_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "dataset",
    "mandi_prices.csv"
)

data = pd.read_csv(file_path)

print("Dataset loaded successfully!")
print("\nOriginal dataset shape:")
print(data.shape)


# ==========================================
# 2. CONVERT DATE
# ==========================================

data["Price Date"] = pd.to_datetime(data["Price Date"])

data = data.sort_values("Price Date").reset_index(drop=True)

data["Year"] = data["Price Date"].dt.year
data["Month"] = data["Price Date"].dt.month
data["Day"] = data["Price Date"].dt.day
data["DayOfYear"] = data["Price Date"].dt.dayofyear


# ==========================================
# 3. CREATE HISTORICAL PRICE FEATURES
# ==========================================

print("\nCreating historical price features...")

group_columns = [
    "STATE",
    "District Name",
    "Market Name",
    "Commodity"
]


data["Previous_Price"] = (
    data.groupby(group_columns)["Modal_Price"]
    .shift(1)
)


data["Price_7_Day_Avg"] = (
    data.groupby(group_columns)["Modal_Price"]
    .transform(
        lambda x: x.shift(1).rolling(
            window=7,
            min_periods=1
        ).mean()
    )
)


data["Price_30_Day_Avg"] = (
    data.groupby(group_columns)["Modal_Price"]
    .transform(
        lambda x: x.shift(1).rolling(
            window=30,
            min_periods=1
        ).mean()
    )
)


print("Historical price features created!")


# ==========================================
# 4. REMOVE MISSING HISTORY
# ==========================================

data = data.dropna(
    subset=[
        "Previous_Price",
        "Price_7_Day_Avg",
        "Price_30_Day_Avg"
    ]
).reset_index(drop=True)


print("\nDataset after historical features:")
print(data.shape)


# ==========================================
# 5. SELECT FEATURES
# ==========================================

features = [
    "STATE",
    "District Name",
    "Market Name",
    "Commodity",
    "Variety",
    "Grade",
    "Year",
    "Month",
    "Day",
    "DayOfYear",
    "Previous_Price",
    "Price_7_Day_Avg",
    "Price_30_Day_Avg"
]

target = "Modal_Price"


X = data[features].copy()
y = data[target].copy()


# ==========================================
# 6. CREATE CATEGORY MAPPINGS
# ==========================================

categorical_features = [
    "STATE",
    "District Name",
    "Market Name",
    "Commodity",
    "Variety",
    "Grade"
]

print("\nEncoding categorical features...")


category_mappings = {}


for column in categorical_features:

    X[column] = X[column].astype("category")

    category_mappings[column] = {
        category: index
        for index, category
        in enumerate(X[column].cat.categories)
    }

    X[column] = X[column].cat.codes


print("Encoding completed!")


# ==========================================
# 7. TRAIN-TEST SPLIT
# ==========================================

split_index = int(len(data) * 0.8)


X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print("\nTraining data:")
print(X_train.shape)

print("\nTesting data:")
print(X_test.shape)


print("\nTraining date range:")
print(
    data["Price Date"].iloc[:split_index].min(),
    "to",
    data["Price Date"].iloc[:split_index].max()
)


print("\nTesting date range:")
print(
    data["Price Date"].iloc[split_index:].min(),
    "to",
    data["Price Date"].iloc[split_index:].max()
)


# ==========================================
# 8. CREATE DECISION TREE
# ==========================================

print("\nCreating Decision Tree model...")


model = DecisionTreeRegressor(
    max_depth=15,
    min_samples_split=20,
    min_samples_leaf=10,
    random_state=42
)


# ==========================================
# 9. TRAIN MODEL
# ==========================================

print("\nTraining Decision Tree model...")

model.fit(
    X_train,
    y_train
)

print("Model training completed!")


# ==========================================
# 10. MAKE PREDICTIONS
# ==========================================

print("\nMaking predictions...")

y_pred = model.predict(X_test)

print("Predictions completed!")


# ==========================================
# 11. DISPLAY PREDICTIONS
# ==========================================

print("\nFirst 10 predictions:")
print(y_pred[:10])


print("\nFirst 10 actual prices:")
print(y_test.iloc[:10].values)


# ==========================================
# 12. MODEL EVALUATION
# ==========================================

mae = mean_absolute_error(
    y_test,
    y_pred
)

rmse = mean_squared_error(
    y_test,
    y_pred
) ** 0.5

r2 = r2_score(
    y_test,
    y_pred
)


print("\n==========================================")
print("MODEL EVALUATION")
print("==========================================")

print("\nMAE:")
print(mae)

print("\nRMSE:")
print(rmse)

print("\nR² Score:")
print(r2)


# ==========================================
# 13. CREATE MODELS FOLDER
# ==========================================

project_folder = os.path.dirname(
    os.path.dirname(__file__)
)

models_folder = os.path.join(
    project_folder,
    "models"
)

os.makedirs(
    models_folder,
    exist_ok=True
)


# ==========================================
# 14. SAVE MODEL
# ==========================================

model_path = os.path.join(
    models_folder,
    "price_model.pkl"
)


with open(model_path, "wb") as file:
    pickle.dump(model, file)


print("\nPrice model saved successfully!")
print(model_path)


# ==========================================
# 15. SAVE CATEGORY MAPPINGS
# ==========================================

mapping_path = os.path.join(
    models_folder,
    "price_category_mappings.pkl"
)


with open(mapping_path, "wb") as file:
    pickle.dump(category_mappings, file)


print("\nCategory mappings saved successfully!")
print(mapping_path)


# ==========================================
# 16. SAVE FEATURE INFORMATION
# ==========================================

feature_info = {
    "features": features,
    "categorical_features": categorical_features,
    "target": target,
    "group_columns": group_columns
}


feature_path = os.path.join(
    models_folder,
    "price_feature_info.pkl"
)


with open(feature_path, "wb") as file:
    pickle.dump(feature_info, file)


print("\nFeature information saved successfully!")
print(feature_path)


# ==========================================
# 17. FINAL RESULT
# ==========================================

print("\n==========================================")
print("PRICE PREDICTION MODEL READY!")
print("==========================================")

print("\nSaved files:")

print("1. price_model.pkl")
print("2. price_category_mappings.pkl")
print("3. price_feature_info.pkl")