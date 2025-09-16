import os
import zipfile
import tempfile
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Please upload a ZIP file"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, file.filename)
        file.save(zip_path)

        # Extract files
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        all_dataframes = []

        # Walk through extracted files
        for root, _, files in os.walk(tmpdir):
            for f in files:
                if f.endswith((".xlsx", ".xls")):
                    excel_path = os.path.join(root, f)
                    xls = pd.ExcelFile(excel_path)

                    for sheet in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet)
                        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                        df["source_file"] = f
                        df["sheet_name"] = sheet
                        all_dataframes.append(df)

        if not all_dataframes:
            return jsonify({"error": "No Excel files found in ZIP"}), 400

        # Merge all sheets/files
        merged_df = pd.concat(all_dataframes, ignore_index=True)

        # Save merged file
        output_file = os.path.join(tmpdir, "merged_output.xlsx")
        merged_df.to_excel(output_file, index=False)

        # Return merged file
        return send_file(output_file, as_attachment=True, download_name="merged_output.xlsx")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
