from flask import Flask, render_template, request, redirect, session
import sqlite3
import pickle
import os
import pandas as pd

from ml.buyer_matching import calculate_match


app = Flask(__name__)

# Used to keep the logged-in user's information in the session
# Change this before deploying the project publicly.
app.secret_key = "agriconnect-development-secret-key"


# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------

def get_db_connection():

    connection = sqlite3.connect(
        "database/agriconnect.db"
    )

    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------------------------
# HOME
# ---------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        location = request.form["location"]
        role = request.form["role"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO users
            (name, email, password, location, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                password,
                location,
                role
            )
        )

        connection.commit()
        connection.close()

        return "Registration successful!"

    return render_template("register.html")


# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            """,
            (
                email,
                password
            )
        ).fetchone()

        connection.close()

        if user:

            # Store the actual logged-in user's information
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "farmer":

                return redirect("/farmer_dashboard")

            elif user["role"] == "buyer":

                return redirect("/buyer_dashboard")

        return "Invalid email or password"

    return render_template("login.html")


# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------------------------------------------
# ADD CROP
# ---------------------------------------------------

@app.route("/add_crop", methods=["GET", "POST"])
def add_crop():

    # Only farmers can add crops
    if session.get("role") != "farmer":

        return redirect("/login")

    if request.method == "POST":

        crop_name = request.form["crop_name"]

        quantity = float(
            request.form["quantity"]
        )

        quality = request.form["quality"]

        expected_price = float(
            request.form["expected_price"]
        )

        location = request.form["location"]

        harvest_date = request.form["harvest_date"]

        available_date = request.form["available_date"]

        # Get the ACTUAL logged-in farmer ID
        farmer_id = session["user_id"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO crop_listings
            (
                farmer_id,
                crop_name,
                quantity,
                quality,
                expected_price,
                location,
                harvest_date,
                available_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                farmer_id,
                crop_name,
                quantity,
                quality,
                expected_price,
                location,
                harvest_date,
                available_date
            )
        )

        connection.commit()
        connection.close()

        return "Crop listed successfully!"

    return render_template("add_crop.html")


# ---------------------------------------------------
# ADD BUYER REQUIREMENT
# ---------------------------------------------------

@app.route("/add_requirement", methods=["GET", "POST"])
def add_requirement():

    # Only buyers can add requirements
    if session.get("role") != "buyer":

        return redirect("/login")

    if request.method == "POST":

        crop_name = request.form["crop_name"]

        quantity = float(
            request.form["quantity"]
        )

        max_price = float(
            request.form["max_price"]
        )

        quality = request.form["quality"]

        location = request.form["location"]

        required_date = request.form["required_date"]

        # Get the ACTUAL logged-in buyer ID
        buyer_id = session["user_id"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO buyer_requirements
            (
                buyer_id,
                crop_name,
                quantity,
                max_price,
                quality,
                location,
                required_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                buyer_id,
                crop_name,
                quantity,
                max_price,
                quality,
                location,
                required_date
            )
        )

        connection.commit()
        connection.close()

        return "Requirement submitted successfully!"

    return render_template("add_requirement.html")


# ---------------------------------------------------
# FARMER DASHBOARD
# ---------------------------------------------------

@app.route("/farmer_dashboard")
def farmer_dashboard():

    if session.get("role") != "farmer":

        return redirect("/login")

    # Get actual logged-in farmer ID
    farmer_id = session["user_id"]

    connection = get_db_connection()

    crops = connection.execute(
        """
        SELECT *
        FROM crop_listings
        WHERE farmer_id = ?
        ORDER BY id DESC
        """,
        (farmer_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "farmer_dashboard.html",
        crops=crops,
        farmer_name=session.get("name")
    )


# ---------------------------------------------------
# BUYER DASHBOARD
# ---------------------------------------------------

@app.route("/buyer_dashboard")
def buyer_dashboard():

    if session.get("role") != "buyer":

        return redirect("/login")

    # Get actual logged-in buyer ID
    buyer_id = session["user_id"]

    connection = get_db_connection()

    requirements = connection.execute(
        """
        SELECT *
        FROM buyer_requirements
        WHERE buyer_id = ?
        ORDER BY id DESC
        """,
        (buyer_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "buyer_dashboard.html",
        requirements=requirements,
        buyer_name=session.get("name")
    )


# ---------------------------------------------------
# MATCHING
# ---------------------------------------------------

@app.route("/matches")
def matches():

    # Check whether user is logged in
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    role = session["role"]
    user_name = session["name"]

    conn = get_db_connection()
    cursor = conn.cursor()

    matches_list = []

    # ==========================================
    # FARMER VIEW
    # ==========================================
    if role == "farmer":

        # Get this farmer's crop listings
        cursor.execute("""
            SELECT
                c.id,
                c.crop_name,
                c.quantity,
                c.quality,
                c.expected_price,
                c.location,
                c.harvest_date,
                c.available_date,
                u.name AS farmer_name,
                u.email AS farmer_email
            FROM crop_listings c
            JOIN users u ON c.farmer_id = u.id
            WHERE c.farmer_id = ?
        """, (user_id,))

        farmer_crops = cursor.fetchall()

        # Get all buyer requirements
        cursor.execute("""
            SELECT
                r.id,
                r.crop_name,
                r.quantity,
                r.max_price,
                r.quality,
                r.location,
                r.required_date,
                u.name AS buyer_name,
                u.email AS buyer_email
            FROM buyer_requirements r
            JOIN users u ON r.buyer_id = u.id
        """)

        buyer_requirements = cursor.fetchall()

        # Compare farmer crops with buyer requirements
        for crop in farmer_crops:

            farmer_crop = {
                "crop_name": crop["crop_name"],
                "quantity": float(crop["quantity"]),
                "quality": crop["quality"],
                "expected_price": float(crop["expected_price"]),
                "location": crop["location"]
            }

            for requirement in buyer_requirements:

                buyer_requirement = {
                    "crop_name": requirement["crop_name"],
                    "quantity": float(requirement["quantity"]),
                    "quality": requirement["quality"],
                    "max_price": float(requirement["max_price"]),
                    "location": requirement["location"]
                }

                score = calculate_match(
                    farmer_crop,
                    buyer_requirement
                )

                # Add only actual matches
                if score > 0:

                    matches_list.append({

                        # Match
                        "score": score,

                        # Farmer
                        "farmer_name": crop["farmer_name"],
                        "farmer_email": crop["farmer_email"],
                        "farmer_location": crop["location"],
                        "farmer_quantity": crop["quantity"],
                        "farmer_expected_price": crop["expected_price"],
                        "farmer_quality": crop["quality"],
                        "harvest_date": crop["harvest_date"],
                        "available_date": crop["available_date"],

                        # Buyer
                        "buyer_name": requirement["buyer_name"],
                        "buyer_email": requirement["buyer_email"],
                        "buyer_location": requirement["location"],
                        "buyer_quantity": requirement["quantity"],
                        "buyer_max_price": requirement["max_price"],
                        "buyer_quality": requirement["quality"],
                        "required_date": requirement["required_date"],

                        # Crop
                        "crop_name": crop["crop_name"]
                    })


    # ==========================================
    # BUYER VIEW
    # ==========================================
    elif role == "buyer":

        # Get this buyer's requirements
        cursor.execute("""
            SELECT
                r.id,
                r.crop_name,
                r.quantity,
                r.max_price,
                r.quality,
                r.location,
                r.required_date,
                u.name AS buyer_name,
                u.email AS buyer_email
            FROM buyer_requirements r
            JOIN users u ON r.buyer_id = u.id
            WHERE r.buyer_id = ?
        """, (user_id,))

        buyer_requirements = cursor.fetchall()

        # Get all farmer crop listings
        cursor.execute("""
            SELECT
                c.id,
                c.crop_name,
                c.quantity,
                c.quality,
                c.expected_price,
                c.location,
                c.harvest_date,
                c.available_date,
                u.name AS farmer_name,
                u.email AS farmer_email
            FROM crop_listings c
            JOIN users u ON c.farmer_id = u.id
        """)

        farmer_crops = cursor.fetchall()

        # Compare buyer requirements with farmer crops
        for requirement in buyer_requirements:

            buyer_requirement = {
                "crop_name": requirement["crop_name"],
                "quantity": float(requirement["quantity"]),
                "quality": requirement["quality"],
                "max_price": float(requirement["max_price"]),
                "location": requirement["location"]
            }

            for crop in farmer_crops:

                farmer_crop = {
                    "crop_name": crop["crop_name"],
                    "quantity": float(crop["quantity"]),
                    "quality": crop["quality"],
                    "expected_price": float(crop["expected_price"]),
                    "location": crop["location"]
                }

                score = calculate_match(
                    farmer_crop,
                    buyer_requirement
                )

                # Add only actual matches
                if score > 0:

                    matches_list.append({

                        # Match
                        "score": score,

                        # Farmer
                        "farmer_name": crop["farmer_name"],
                        "farmer_email": crop["farmer_email"],
                        "farmer_location": crop["location"],
                        "farmer_quantity": crop["quantity"],
                        "farmer_expected_price": crop["expected_price"],
                        "farmer_quality": crop["quality"],
                        "harvest_date": crop["harvest_date"],
                        "available_date": crop["available_date"],

                        # Buyer
                        "buyer_name": requirement["buyer_name"],
                        "buyer_email": requirement["buyer_email"],
                        "buyer_location": requirement["location"],
                        "buyer_quantity": requirement["quantity"],
                        "buyer_max_price": requirement["max_price"],
                        "buyer_quality": requirement["quality"],
                        "required_date": requirement["required_date"],

                        # Crop
                        "crop_name": crop["crop_name"]
                    })


    conn.close()

    return render_template(
        "matches.html",
        matches=matches_list,
        role=role,
        user_name=user_name
    )
# ---------------------------------------------------
# PRICE PREDICTION
# ---------------------------------------------------

@app.route("/price_prediction", methods=["GET", "POST"])
def price_prediction():

    if request.method == "POST":

        # ==========================================
        # 1. GET USER INPUT
        # ==========================================

        state = request.form["state"]
        district = request.form["district"]
        market = request.form["market"]
        commodity = request.form["commodity"]
        variety = request.form["variety"]
        grade = request.form["grade"]

        date = pd.to_datetime(request.form["date"])

        previous_price = float(request.form["previous_price"])
        price_7_day_avg = float(request.form["price_7_day_avg"])
        price_30_day_avg = float(request.form["price_30_day_avg"])


        # ==========================================
        # 2. CREATE INPUT DATA
        # ==========================================

        input_data = pd.DataFrame([{
            "STATE": state,
            "District Name": district,
            "Market Name": market,
            "Commodity": commodity,
            "Variety": variety,
            "Grade": grade,

            "Year": date.year,
            "Month": date.month,
            "Day": date.day,
            "DayOfYear": date.dayofyear,

            "Previous_Price": previous_price,
            "Price_7_Day_Avg": price_7_day_avg,
            "Price_30_Day_Avg": price_30_day_avg
        }])


        # ==========================================
        # 3. PROJECT MODEL PATHS
        # ==========================================

        project_folder = os.path.dirname(
            os.path.abspath(__file__)
        )

        price_model_path = os.path.join(
            project_folder,
            "models",
            "price_model.pkl"
        )

        price_mapping_path = os.path.join(
            project_folder,
            "models",
            "price_category_mappings.pkl"
        )

        classifier_path = os.path.join(
            project_folder,
            "models",
            "price_category_classifier.pkl"
        )

        classifier_info_path = os.path.join(
            project_folder,
            "models",
            "price_classification_feature_info.pkl"
        )


        # ==========================================
        # 4. LOAD DECISION TREE MODEL
        # ==========================================

        with open(price_model_path, "rb") as file:
            price_model = pickle.load(file)


        with open(price_mapping_path, "rb") as file:
            price_category_mappings = pickle.load(file)


        # ==========================================
        # 5. ENCODE INPUT FOR DECISION TREE
        # ==========================================

        categorical_features = [
            "STATE",
            "District Name",
            "Market Name",
            "Commodity",
            "Variety",
            "Grade"
        ]

        price_input = input_data.copy()

        for column in categorical_features:

            mapping = price_category_mappings[column]

            price_input[column] = (
                price_input[column]
                .map(mapping)
                .fillna(-1)
                .astype(int)
            )


        price_features = [
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

        price_input = price_input[price_features]


        # ==========================================
        # 6. DECISION TREE PRICE PREDICTION
        # ==========================================

        prediction = price_model.predict(
            price_input
        )[0]

        prediction = round(
            prediction,
            2
        )


        # ==========================================
        # 7. LOAD RANDOM FOREST CLASSIFIER
        # ==========================================

        with open(classifier_path, "rb") as file:
            classifier = pickle.load(file)


        with open(classifier_info_path, "rb") as file:
            classifier_info = pickle.load(file)


        # ==========================================
        # 8. ENCODE INPUT FOR RANDOM FOREST
        # ==========================================

        classifier_input = input_data.copy()

        classifier_categorical_features = (
            classifier_info["categorical_features"]
        )

        for column in classifier_categorical_features:

            mapping = (
                classifier_info["category_mappings"][column]
            )

            classifier_input[column] = (
                classifier_input[column]
                .map(mapping)
                .fillna(-1)
                .astype(int)
            )


        classifier_features = (
            classifier_info["features"]
        )

        classifier_input = classifier_input[
            classifier_features
        ]


        # ==========================================
        # 9. PRICE CATEGORY PREDICTION
        # ==========================================

        price_category = classifier.predict(
            classifier_input
        )[0]


        # ==========================================
        # 10. RENDER RESULT
        # ==========================================

        return render_template(
            "prediction.html",

            prediction=prediction,

            price_category=price_category
        )


    # ==========================================
    # GET REQUEST
    # ==========================================

    return render_template(
        "prediction.html"
    )
# ---------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)