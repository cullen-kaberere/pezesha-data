# app.py
import os
import pandas as pd
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, String, MetaData
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database config
DATABASE_URL = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


@app.route("/")
def index():
    return "Flask CSV Upload API is running!"


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "" or not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file"}), 400

    try:
        # Read CSV into pandas DataFrame
        df = pd.read_csv(file)

        if df.empty:
            return jsonify({"error": "CSV is empty"}), 400

        # Extract CSV headers
        columns = df.columns.tolist()

        # Create table dynamically
        metadata = MetaData(bind=db.engine)
        table = Table(
            "uploaded_data",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            *(Column(col, String) for col in columns),
            extend_existing=True
        )
        metadata.create_all()

        # Convert DataFrame to list of dicts
        records = df.astype(str).to_dict(orient="records")

        # Bulk insert
        with db.engine.begin() as conn:
            conn.execute(table.insert(), records)

        return jsonify({"message": f"Inserted {len(records)} rows into 'uploaded_data'"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
