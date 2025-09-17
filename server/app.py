import os
import pandas as pd
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, String, MetaData
from flask_cors import CORS
from dotenv import load_dotenv
import re


load_dotenv()

app = Flask(__name__)
CORS(app) 

# Database config
DATABASE_URL = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


@app.route("/")
def index():
    return " Flask CSV Upload API is running!"


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "" or not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file"}), 400

    try:
        #  UTF-8, fallback to latin1 for special characters like £
        try:
            df = pd.read_csv(file, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file, encoding="latin1")

        if df.empty:
            return jsonify({"error": "CSV is empty"}), 400

        # Sanitize column names
        df.columns = [
            col.strip().replace(" ", "_").replace("-", "_").lower()
            for col in df.columns
        ]
        columns = df.columns.tolist()

        # Sanitize table name from file name
        table_name = re.sub(r"[^a-zA-Z0-9_]", "_", os.path.splitext(file.filename)[0].lower())

        # Define dynamic table schema
        metadata = MetaData()
        table = Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            *(Column(col, String) for col in columns),
            extend_existing=True
        )

        # Create table if not exists
        metadata.create_all(db.engine)

        # Convert DataFrame rows to list of dicts (all values as strings)
        records = df.astype(str).to_dict(orient="records")

        # Insert into DB
        with db.engine.begin() as conn:
            conn.execute(table.insert(), records)

        return jsonify({"message": f"Inserted {len(records)} rows into table '{table_name}'"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
