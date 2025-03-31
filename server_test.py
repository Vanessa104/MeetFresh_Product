
from flask import Flask, render_template, request
import pandas as pd
from flask import send_from_directory

app = Flask(__name__)

questions = {
        "Is this your first time trying a Meet Fresh product(check first time trying)是否是新顾客":['Yes','No'],
        "What ingredients you prefer (e.g. grass jelly, mini taro…)主料": ["Grass Jelly",'Taro Balls','Taro','Red Bean', 'Coco Sago', 'Almond Soup', 'Almond Flakes','Purple Rice','Pudding','Shaved Ice','Ice Cream'],
        "What taste you prefer (e.g. how much sweetness)甜度":['High','Low','Medium'],
        "Cold or Hot冷热":["Cold","Hot"],
        "Preferred size大小":['M','L'],
        "How many people (so we can recommend combo)人数":["Single","2 - 3","4 - 5","6 or above"],
        "How long you can wait (take into consider both product making and peak hour)等待时长":["Less than 5 min","Greater than 5 min"]
        }
results_data = {
    "Icy Taro Ball Signature": {"image": "static/icy-taro-ball-Signature.png", "link": "https://www.meetfresh.us/icy-taro-ball-signature/"},
    "Icy Grass Jelly Signature": {"image": "static/Signature-Icy-Grass-Jelly.png", "link": "https://www.meetfresh.us/icy-grass-jelly-signature/"},
    "Hot Red Bean Soup Signature": {"image": "static/Hot-Red-Bean-Soup-Signature.png", "link": "https://www.meetfresh.us/hot-red-bean-soup-signature/"},
    "Hot Grass Jelly Soup Signature": {"image": "static/Hot-Grass-Jelly-Signature.png", "link": "https://www.meetfresh.us/hot-grass-jelly-soup-signature/"},
    "Hot Almond Soup Signature": {"image": "static/Hot-Almond-Soup-Signature.png", "link": "https://www.meetfresh.us/hot-almond-soup-signature/"},
}
data = pd.read_csv("menu_items.csv")
data['Image'] = "static/" + data['Image'].apply(lambda x: x.split("/")[-1])
results_data = data.set_index('Name').to_dict(orient='index')

def save_response(responses):
    df = pd.DataFrame([responses], columns=['ingred','sweet','temp','size','people','wait','newcustomer'])
    try:
        existing_df = pd.read_csv("survey_results.csv")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_csv("survey_results.csv", index=False)

    
@app.route('/', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
         # Handling multiple ingredients
        ingred_list = request.form.getlist('What ingredients you prefer (e.g. grass jelly, mini taro…)主料')
        ingred_str = ", ".join(ingred_list)  # Convert list to a comma-separated string
        responses = {
            'ingred': ingred_str,
            'sweet': request.form['What taste you prefer (e.g. how much sweetness)甜度'],
            'temp': request.form['Cold or Hot冷热'],
            'size': request.form['Preferred size大小'],
            'people': request.form['How many people (so we can recommend combo)人数'],
            'wait': request.form['How long you can wait (take into consider both product making and peak hour)等待时长'],
            'newcustomer': request.form['Is this your first time trying a Meet Fresh product(check first time trying)是否是新顾客']
        }
        save_response(responses)
        df = pd.DataFrame([responses])
        temp_choice =  responses['temp']
        ingred = set(ingred_list)
        sweet_choice = responses['sweet']
        waittime = responses['wait']
        filtered_results = {
            key: value for key, value in results_data.items()
            if ((temp_choice == "Cold" and "Icy" in value['Temp']) or (temp_choice == "Hot" and "Hot" in value['Temp']))
            and (ingred & set(value['Ingredients'].split(', ')))  # Check if any user ingredient matches
            and (sweet_choice in value['Sweetness']) and ((waittime =="Less than 5 min" and "1 - 3 min" in value['PrepTime']) or (waittime =="Greater than 5 min" and "4 - 6 min" in value['PrepTime']))
        }
        return render_template('result.html', responses=responses, results=filtered_results)
    return render_template('survey.html', questions=questions)


#@app.route('/download/<filename>')
#def download_file(filename):
    # Replace with the correct directory where your file is located
 #   directory = os.path.join(app.root_path, 'static')
  #  return send_from_directory(directory, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)





# PEG 2.0 (Process & Export to Google Sheet)

import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split

pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client


# read csv file from google sheet using published url
csv_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1_fFP0quWhpbhwiFbPIHh_ul8VPai3QINPi1tC0gXIutJuiDHhDkmGEtsw_sSFuoPdaHLDlKy9Yte/pub?gid=2112842415&single=true&output=csv'
df = pd.read_csv(csv_url)

# write a code to use sklearn binarizer to convert all words in 'Ingredients' columns to binary values
# and drop 'Link','Image','Calories' columns
mlb = MultiLabelBinarizer()
df1 = df.drop(['Category','Calories','Size','Link','Image'], axis=1)
# Convert 'Sweetness' column to numerical values
sweetness_mapping = {'Low': 1, 'Med': 2, 'High': 3}
df1['Sweetness'] = df1['Sweetness'].map(sweetness_mapping)
# Convert 'PrepTime' column to numerical values
df1['Preparation_Time'] = df1['Preparation_Time'].str.extract('(\d+)').astype(float)
#if df1[preparation_time] <5 then 4, else if >=5 then 5 as new df1[preparation_time]
df1['Preparation_Time'] = df1['Preparation_Time'].apply(lambda x: 4 if x < 5 else 5)
# Convert 'Temp' to numerical values
temp_mapping = {'Icy': 1, 'Hot': 2}
df1['Temperature'] = df1['Temperature'].map(temp_mapping)
# Convert 'Size' to numerical values
#size_mapping = {'One Size': 1, 'M': 2, 'L': 3}
#df1['Size'] = df1['Size'].map(size_mapping)

# # write a code to do one hot encoding for 'Sweetness','Temp','size' columns together with above
# df2 = pd.get_dummies(df1, columns=['Sweetness','Temp','Size'])
# print(df2.head())
df1['Ingredients'] = df1['Ingredients'].fillna('')
ingredient_encoded = pd.DataFrame(mlb.fit_transform(df1['Ingredients'].str.split(',')),
                                  columns=mlb.classes_,
                                  index=df1.index)

# Merge one-hot encoded ingredient columns back
df1 = df1.join(ingredient_encoded).drop(columns=['Ingredients'])
#df1= df1.drop(columns=[' Boba',' Grass Jelly',' Melon Jelly', ' Mini Q',' Red Beans', ' Rice Balls', ' Strawberry', ' Taro Paste',' Taro','Taro Ball',' Taro Balls',' ', ' Sago'])
df1.rename(columns = {'Sago' : 'Coco Sago'}, inplace = True)
df1.drop(columns = [''], inplace = True)

# For later comparison between product ingred and survey ingred and filter=creation
df1_ingred = df1.copy(deep = True)
df1_ingred = df1.drop(columns = ['Name','NameCH','Sweetness','Temperature','Preparation_Time'])

# Read survey response
survey_response = pd.read_csv('/content/sample_data/survey_results.csv') # add survey response from customers 
#survey_response = survey_response.iloc[4:5]
survey_response.rename(columns = {'ingred':'Ingredients', 'sweet' : 'Sweetness', 'temp' : 'Temperature', 'size' : 'Size', 'people' : 'People', 'wait' : 'Preparation_Time', 'newcustomer' : 'New_Customer'}, inplace = True)
survey_matrix = survey_response.copy(deep = True)

survey_matrix.drop(columns=['Size','People','New_Customer'], inplace=True)
survey_matrix['Sweetness']= survey_matrix['Sweetness'].map({'Low': 1, 'Medium': 2, 'High': 3})
survey_matrix['Temperature']= survey_matrix['Temperature'].map({'Cold': 1, 'Hot': 2})
survey_matrix['Preparation_Time']= survey_matrix['Preparation_Time'].map({'1 - 3 min': 4, '4 - 6 min': 5, 'Less than 5 min': 4, 'Greater than 5 min': 5})
# Convert the Ingredients column into list
survey_matrix['Ingredients'] = survey_matrix['Ingredients'].apply(lambda x: x.split(','))


# Create new columns (one hot encoded) based on df1's columns
survey_matrix_new = survey_matrix.copy(deep = True)
for col in df1_ingred.columns:
    survey_matrix_new[col] = survey_matrix_new["Ingredients"].apply(lambda values: 1 if col in values else 0)

#survey_input = survey_matrix_new.iloc[:1]
#survey_input = survey_matrix.iloc[47:48]
#survey_input = survey_matrix_new.iloc[49:50]
#survey_input = survey_matrix.sample(n=1)
survey_input = survey_matrix_new

#List columns by ingredients
#survey_ingred = survey_matrix.iloc[49:50]
survey_ingred = survey_matrix

#flatten list
survey_ingred = survey_ingred.explode('Ingredients')
for value in survey_ingred['Ingredients']:
    survey_ingred[value] = 1


# Remove non-numeric columns for cosine similarity and filter cold/hot products
product_features = df1[df1['Temperature'].isin(survey_input['Temperature'])].drop(columns=['Name','NameCH'])
# Find the common columns between df1 and survey_input
common_columns = df1.iloc[:,4:].columns.intersection(survey_ingred.iloc[:,4:].columns)

# Filter product_features where at least one value in common columns exists in df2
product_features = product_features[product_features[common_columns].isin(survey_ingred.to_dict('list')).any(axis=1)]

survey_input_features = survey_input.drop(columns=['Ingredients'])

# similarity score

from sklearn.metrics.pairwise import cosine_similarity
similarity_matrix_survey = cosine_similarity(product_features, survey_input_features)
# Get top 5 products for each customer
top_5_products = []
#get index of similarity_matrics_survey
similarity_df = pd.DataFrame(
    similarity_matrix_survey,  # The similarity matrix
    index=product_features.index,  # Use df1's index (product features index)
    columns=survey_input_features.index  # Use survey_input_features index (customer index)
)

# Get indices of top 5 most similar products with the highest score for the customer

similarity_df = similarity_df.sort_values(by=similarity_df.columns[0], ascending=False)

similarity_df = similarity_df[:5]

#similarity_df = similarity_df.rename(columns={similarity_df.columns[0]: "Similarity Score"})

# prompt: join similarity_df with df on index 

recommendation_df = df.merge(similarity_df, left_index=True, right_index=True, how='inner')
recommendation_df = recommendation_df.sort_values(by=similarity_df.columns[0], ascending=False)
recommendation_df_new = recommendation_df.copy(deep=True)
recommendation_df_new.rename(columns = {recommendation_df_new.columns[-1]: "Similarity Score"}, inplace = True)
recommendation_df_new # Please use this dataframe to show users results



# Get the last column name dynamically
last_column = recommendation_df.columns[-1]

# round 2 decimals for last column in 
recommendation_df[last_column] = recommendation_df[last_column].round(2)
# Create a dictionary where:
# - Key: Last column name
# - Value: List of tuples (Name, Last Column Value)

recommendation_dict = {
    last_column: list(zip(recommendation_df["Name"], recommendation_df[last_column]))
}

# Convert to DataFrame format
df_list = []
for key, product_list in recommendation_dict.items():
    row = {"CustomerID": key}  # Use key as identifier
    for i, (product, score) in enumerate(product_list, start=1):
        row[f"Top{i} Product"] = product
        row[f"Similarity Score Top{i}"] = score
    df_list.append(row)

# Create DataFrame
df_result = pd.DataFrame(df_list)

# Set the key as the index
df_result.set_index("CustomerID", inplace=True)

#survey_other_input = survey_response[['People','New_Customer']].iloc[:1]
#survey_other_input = survey_response[['People','New_Customer']].iloc[10:11]
#survey_other_input = survey_response[['People','New_Customer']].iloc[49:50]
survey_other_input = survey_response[['People','New_Customer']]
merged_df_response = pd.concat([survey_input, df_result, survey_other_input], axis=1)
# add Dalas time as created time
from datetime import datetime
from zoneinfo import ZoneInfo
dallas_time = datetime.now(ZoneInfo("America/Chicago"))
merged_df_response['created_time'] = dallas_time
#merged_df_response['created_time'] = pd.to_datetime('now')


# Append new records to Googlesheet
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd

# Embed the JSON key directly in your code as a string
json_key = '''
{
  "type": "service_account",
  "project_id": "meetfresh-data-migration",
  "private_key_id": "1d1dbef38e7044f2280cbc2838a70351228a7f7c",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCp71HrAwmm+qAh\\nvA4AsRNM14Y2zCVE26AAdjw7YJfbYQ0z22eG90Sbu3hyqrAmH4LFNkLebs9s2D0l\\nraFcAS+LeJvaGTHOKwPWoTZ2Qgt/GQS16pQawNjEYS1X952moIuwGSvenc3fIdYm\\nw7Fn2pQyuRf8kBAKVkVC/+O9aadWm5z2Q01R+WNOCcb1JQUSbcfEfcBGfDV9UtLL\\npvobFnJTH4hQXNitoZHweaSu6ZMqnFeMrOvFkMfr63OiuQhIVJ35zZaK0BGqycU/\\nwflXmD6Yumj708hRFy1uZsrOZaWFs+C4MsRv8tb6DJw0Qx+XhS1l7HDHm+tQGZDH\\niosCfXm3AgMBAAECggEAGSt8W63QgS4AB98dx9ZygGAv3e/w2TkagtcAZt8Qvwqp\\n9PNbay82t0ZWOc20V4E1UlaOIvoQuRNyQyFrlAAM9cCAfRZcPSg74k9wjKWNpF6l\\nRviexTOpJ7UpDS186VBAQG4KBGglNRaC7KzxmutSJg0qU1tXNODAU4MpTUXX5kja\\ndBc9epBtHUAKZ4q7cqDLpugDZI/yVDBSJ+td1lGx/YzZbheRnxpzcAoyXzKSy+Yn\\n6CoT9oHCyp4YK/Qb7iazM2OYIY6olN+T+/By/MlBlYiA1Cxen/qSVRfDKuyzam/c\\naDYfL/zaSus50CcdOs+c3r+hhfsBqFeCe4cz7T/gaQKBgQDUJ+YItptL70YCmgXM\\nElT1bxczwWRe/2Ie5R8ZZvaKEAlAS4KojTR/qVDubpQ1qDxJIU1O5wzOTOcmfLwv\\nhkxjdjot9GaDzMbl+1sd2evPGuY1S4SNr4RhHy3ZYifk7sdFgMQGXUQgJyJWJrha\\nM59xBZWf0cvmKHE8OA0AnLGlowKBgQDNDbg9JgmuQc2qeAyakefCztRUpbUMa6xV\\n5tweXw7+g6AUTbhb/j6/I2GCBd3YIUWpj8trzO6lFiv4s6DPGUGouSTrZGpJ+EY0\\nmH4y/UjlJVHbvoTnIDyGUzqEv8RgRdIh2OzYp17t5WpEfKb60sXBD6bZrGdAOHqa\\nykHSHphU3QKBgDl0+MrBUbu1+Jr5xbon+NRjmsAMjzdfKN6/JLYHeZuYjjjYenFV\\nlLNCUsXQMtl5T6Jqn3pP/trcXvnAbGLel0+UlFsfxqfJTNC6S0oBW+jCGzix1Btf\\nPpXjENK/z5gjxtoe7nfeyHWAw77bS7A6LOM6JPScqAEUUN6DO5o/1ajLAoGBAKp5\\nToOf3Qp/cJHZrnjO9oQx2brp7OP/nE3qWXPyiY+1NF/M4YmxjM7xhj5HzFDEEJtQ\\njcj4niqnjTT9eaLTl4/DJNuCJw+KFivh34Faq8C9zxlGgk14snjmNs9ocsWrJnC3\\nXOkd9MEJKtj3XQdINdo0vf1X5JsymVOY9THP98sNAoGBANNYhg82LPfwJtu8RWW5\\nXRJeDSSm6AENlP+93PCgLDlYNXfqWlmvZlnuRFltcobGEQYj/TSYwEPRQ3Y83lXs\\n5W+m7bla9OA+OEaxXg48hzAl2JcpGTTH/9EpJSlorcK7vjUlb+PG+SLb6Z3lOhSb\\ng5etrkqM7jLBrb5qgf0osFCi\\n-----END PRIVATE KEY-----\\n",
  "client_email": "meetfresh-data-migration@meetfresh-data-migration.iam.gserviceaccount.com",
  "client_id": "114713800073444959941",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/meetfresh-data-migration%40meetfresh-data-migration.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
'''

# Load the JSON key from the string
service_account_info = json.loads(json_key)

# Authenticate using the service account
credentials = service_account.Credentials.from_service_account_info(service_account_info)

# ID of the Google Sheet where you want to export the data
SPREADSHEET_ID = '1dN3quMHzOj33XM3Jdbz5vK82JnZebWJX9UEdVPjAvXU'

# Authenticate with Google Sheets API
def authenticate_google_sheets():
    service = build('sheets', 'v4', credentials=credentials)
    return service

# Function to export headers to Google Sheets
def export_headers_to_sheet(df):
    """
    Exports the header row (column names) to Google Sheets.
    :param df: DataFrame containing survey data.
    """
    service = authenticate_google_sheets()
    header_data = [df.columns.tolist()]  # Extract column names as list

    range_ = "Sheet1!A1"  # Assuming headers start from A1
    body = {"values": header_data}

    sheet = service.spreadsheets()
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_,
        valueInputOption="RAW",
        body=body
    ).execute()
    print("Headers exported to Google Sheets")

# Function to append survey responses to Google Sheets
def append_survey_response(response_data):
    """
    Appends a single survey response to the next available row in Google Sheets.
    :param response_data: List containing survey response data, e.g., ["Alice", 90, "2025-03-26 10:00:00"]
    """
    service = authenticate_google_sheets()

    range_ = "Sheet1!A2"  # Data starts from the second row (below the headers)
    body = {"values": [response_data]}

    sheet = service.spreadsheets()
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_,
        valueInputOption="RAW",
        body=body
    ).execute()

    print(f"New survey response added: {response_data}")


# Test the whole process (clear and export)
merged_df = merged_df_response.copy(deep=True)
export_headers_to_sheet(merged_df)
def test_export():
    # Convert 'Recommendation' column to string (if it exists)
    # if 'Recommendation' in merged_df.columns:
    #     merged_df['Recommendation'] = merged_df['Recommendation'].astype(str)
    # Convert 'Ingredients' column to string (if it exists)
    if 'Ingredients' in merged_df.columns:
        merged_df['Ingredients'] = merged_df['Ingredients'].astype(str)

        merged_df['created_time'] = merged_df['created_time'].astype(str)

    # Loop through each row in the DataFrame and append to Google Sheets
    for index, row in merged_df.iterrows():
        response_data = row.tolist()  # Convert the row to a list
        append_survey_response(response_data)  # Append each row to Google Sheets
# Run the test export
test_export()

