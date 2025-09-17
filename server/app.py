import os
import csv
import io
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
    return "Flask CSV Upload API is running!"

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "" or not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file"}), 400

    try:
        # Read CSV content
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_reader = csv.reader(stream)
        
        # Get headers
        headers = next(csv_reader)
        
        # Sanitize column names
        headers = [
            col.strip().replace(" ", "_").replace("-", "_").lower()
            for col in headers
        ]
        
        # Read all rows
        rows = list(csv_reader)
        
        if not rows:
            return jsonify({"error": "CSV is empty"}), 400

        # Sanitize table name from file name
        table_name = re.sub(r"[^a-zA-Z0-9_]", "_", os.path.splitext(file.filename)[0].lower())

        # Define dynamic table schema
        metadata = MetaData()
        table = Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            *(Column(col, String) for col in headers),
            extend_existing=True
        )

        # Create table if not exists
        metadata.create_all(db.engine)

        # Prepare records for insertion
        records = []
        for row in rows:
            record = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    record[headers[i]] = str(value) if value is not None else ""
            records.append(record)

        # Insert into DB
        with db.engine.begin() as conn:
            conn.execute(table.insert(), records)

        return jsonify({"message": f"Inserted {len(records)} rows into table '{table_name}'"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))