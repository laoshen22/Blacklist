from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Define the live token and base URL
live_token = "FB03D421-4F81-4C69-93E6-E24A1F5D8565-5842661"
base_url = "https://lect.smartborder.com/ecommapi/projects/hts/Restricted"

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle file upload and processing
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    # Read the Excel file
    df = pd.read_excel(file)

    # Function to transform HTC values
    def transform_htc(htc_value):
        htc_str = str(htc_value)
        return f"{htc_str[:4]}.{htc_str[4:6]}.{htc_str[6:]}"

    # Apply the transformation to the HTS column
    df['Transformed_HTS'] = df['HTS'].apply(transform_htc)

    # Replace the original HTS values with the transformed ones
    df['HTS'] = df['Transformed_HTS']

    # Drop the helper column
    df = df.drop(columns=['Transformed_HTS'])


    # Add required fields
    arrival_date = "2024-06-01T13:47:32.6620077-04:00"
    country_of_origin = "CN"  


    # Prepare the request payload
    hts_lines = []
    for _, row in df.iterrows():
        hts_lines.append({
            "HtsNumber": str(row['HTS']),
            "ArrivalDate": arrival_date,
            "CountryOfOrigin": country_of_origin
        })

    # Define the request body
    data = {
      "htsLines": hts_lines
    }

    # Make the POST request
    full_url = f"{base_url}?token={live_token}"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(full_url, headers=headers, json=data)

    
    if response.status_code == 200:
        response_json = response.json()
        
        # Convert JSON to pandas DataFrame
        hts_information_df = pd.DataFrame(response_json['HtsInformationDateDtos'])
        restricted_dtos_df = pd.DataFrame(response_json['TodaysHtsRestrictedDtos'])
        
        # Create a Pandas Excel writer using XlsxWriter as the engine
        output_file = 'response_data.xlsx'
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            hts_information_df.to_excel(writer, sheet_name='HTSInformation', index=False)
            restricted_dtos_df.to_excel(writer, sheet_name='RestrictedHTS', index=False)
        
        return jsonify({"message": "Data has been processed and saved to response_data.xlsx"})
    else:
        return f"Failed with status code: {response.status_code}", 500


if __name__ == '__main__':
    app.run(debug=True)
