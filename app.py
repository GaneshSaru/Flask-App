from flask import Flask, request, jsonify
from flask_cors import CORS  
import pdfplumber
import pandas as pd
from collections import OrderedDict

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Dictionary to map semester names to PDF file paths
SEMESTER_FILES = {
    "1st Semester": "static/BE_Computer_1st.pdf",
    "2nd Semester": "static/BE_Computer_2nd.pdf",
    "3rd Semester": "static/BE_Computer_3rd.pdf",
    "4th Semester": "static/BE_Computer_4th.pdf",
    "5th Semester": "static/BE_Computer_5th.pdf"
    # Add more semesters as needed
}

@app.route('/get_result', methods=['POST'])
def get_result():
    data = request.get_json()
    roll_no = data.get("roll_no")
    semester = data.get("semester")

    if not roll_no or not semester:
        return jsonify({"error": "Roll number and semester are required"}), 400

    pdf_path = SEMESTER_FILES.get(semester)
    if not pdf_path:
        return jsonify({"error": "Invalid semester selected"}), 400

    # preprocessing pdf
    try:
        all_tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_tables.append(table)

        df = pd.DataFrame([row for table in all_tables for row in table])
        df.columns = df.iloc[0]
        df = df.drop(index=0).reset_index(drop=True)
        df.columns = df.columns.str.replace('\n', ' ', regex=False)

        student_result = df[df.iloc[:, 0] == roll_no]
        if student_result.empty:
            return jsonify({"message": f"Roll No. {roll_no} not found in {semester}"}), 404

        result_data = OrderedDict()
        result_data["Exam Roll No."] = student_result.iloc[0, 0]
        for col in df.columns[1:-1]:
            result_data[col] = student_result[col].values[0]
        result_data[df.columns[-1]] = student_result.iloc[0, -1]

        return jsonify(result_data), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to process {pdf_path}: {str(e)}"}), 500

@app.route('/get_semesters', methods=['GET'])
def get_semesters():
    try:
        semesters = list(SEMESTER_FILES.keys())
        return jsonify({"semesters": semesters})
    except Exception as e:
        return jsonify({"error": "Failed to fetch semesters"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
