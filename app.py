from flask import Flask, request, jsonify
import requests
import io
import pdfplumber
import pandas as pd
from collections import OrderedDict

app = Flask(__name__)

# Google Drive Direct Download Links
SEMESTER_FILES = {
    "1st Semester": "https://drive.google.com/uc?export=download&id=1qaEYSz91fr4wWlg2I600OfUlUY6HYaTa",
    "2nd Semester": "https://drive.google.com/uc?export=download&id=16CY8Dnp2udYvrs3qLEW9wWMw4hRSu8b0",
    "3rd Semester": "https://drive.google.com/uc?export=download&id=1bgNx6tNBhqlPdpsTbe1L0L2hm5Pvxxkp",
    "4th Semester": "https://drive.google.com/uc?export=download&id=1K1UZcEPdJX9UOlP5_HCdlh4aMrlizEgr",
    "5th Semester": "https://drive.google.com/uc?export=download&id=1-ZPnRQr3pNcXJ7asrt2ZdiFLWCFA0Chv"
}

@app.route('/get_result', methods=['POST'])
def get_result():
    data = request.get_json()
    roll_no = data.get("roll_no")
    semester = data.get("semester")

    if not roll_no or not semester:
        return jsonify({"error": "Roll number and semester are required"}), 400

    pdf_url = SEMESTER_FILES.get(semester)
    if not pdf_url:
        return jsonify({"error": "Invalid semester selected"}), 400

    try:
        # Download PDF from Google Drive
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch PDF from Google Drive"}), 500
        
        # Read PDF content using pdfplumber
        all_tables = []
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_tables.append(table)

        # Convert to DataFrame
        df = pd.DataFrame([row for table in all_tables for row in table])
        df.columns = df.iloc[0]  # Set first row as header
        df = df.drop(index=0).reset_index(drop=True)  # Remove header row from data
        df.columns = df.columns.str.replace('\n', ' ', regex=False)  # Clean column names

        # Find student result
        student_result = df[df.iloc[:, 0] == roll_no]
        if student_result.empty:
            return jsonify({"message": f"Roll No. {roll_no} not found in {semester}"}), 404

        # Format result as JSON
        result_data = OrderedDict()
        result_data["Exam Roll No."] = student_result.iloc[0, 0]
        for col in df.columns[1:-1]:
            result_data[col] = student_result[col].values[0]
        result_data[df.columns[-1]] = student_result.iloc[0, -1]

        return jsonify(result_data), 200

    except Exception as e:
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

@app.route('/get_semesters', methods=['GET'])
def get_semesters():
    return jsonify({"semesters": list(SEMESTER_FILES.keys())})

if __name__ == '__main__':
    app.run(debug=True)
