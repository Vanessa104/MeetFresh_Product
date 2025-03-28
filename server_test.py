
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





# I will change the code according to the finalized similarity scores once they are completed （Roman）
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split

#read menu_items.csv
df = pd.read_csv('/content/sample_data/menu_items v1 - menu_items_v2.csv') # will be replaced by the new menu dataset
print(df.head())

# If Temp contains'Icy and Hot' Then break it into two rows 'Icy' and 'Hot' for each Name and If Size contains'M and L' Then break it into two rows 'M' and 'L' for each Name



# Create a list to store the new rows
new_rows = []

for index, row in df.iterrows():
    temp_values = row['Temp'].split(' and ') if ' and ' in str(row['Temp']) else [row['Temp']]
    size_values = row['Size'].split(' and ') if ' and ' in str(row['Size']) else [row['Size']]

    for temp in temp_values:
        for size in size_values:
            new_row = row.copy()
            new_row['Temp'] = temp
            new_row['Size'] = size
            new_rows.append(new_row)

# Create a new DataFrame from the list of new rows
new_df = pd.DataFrame(new_rows).reset_index(drop=True)

# If Name contains 'Icy', 'Cold' or 'Hot' then use the Name, else add Temp with Name as a new name
new_df['Name']=np.where(new_df['Name'].str.contains('Icy|Cold|Hot'), new_df['Name'] + ' ' + new_df['Size'], new_df['Temp'] + ' ' + new_df['Name'] + ' ' + new_df['Size'])

df = new_df

# write a code to use sklearn binarizer to convert all words in 'Ingredients' columns to binary values
# and drop 'Link','Image','Calories' columns
mlb = MultiLabelBinarizer()
df1 = df.drop(['Link','Image','Calories','Size'], axis=1)
# Convert 'Sweetness' column to numerical values
sweetness_mapping = {'Low': 1, 'Medium': 2, 'High': 3}
df1['Sweetness'] = df1['Sweetness'].map(sweetness_mapping)
# Convert 'PrepTime' column to numerical values
df1['PrepTime'] = df1['PrepTime'].str.extract('(\d+)').astype(float)
# Convert 'Temp' to numerical values
temp_mapping = {'Icy': 1, 'Hot': 2}
df1['Temp'] = df1['Temp'].map(temp_mapping)
# Convert 'Size' to numerical values
#size_mapping = {'One Size': 1, 'M': 2, 'L': 3}
#df1['Size'] = df1['Size'].map(size_mapping)

# # write a code to do one hot encoding for 'Sweetness','Temp','size' columns together with above
# df2 = pd.get_dummies(df1, columns=['Sweetness','Temp','Size'])
# print(df2.head())

ingredient_encoded = pd.DataFrame(mlb.fit_transform(df1['Ingredients'].str.split(',')),
                                  columns=mlb.classes_,
                                  index=df1.index)

# Merge one-hot encoded ingredient columns back
df1 = df1.join(ingredient_encoded).drop(columns=['Ingredients'])
df1= df1.drop(columns=[' Boba',' Grass Jelly',' Melon Jelly', ' Mini Q',' Red Beans', ' Rice Balls', ' Strawberry', ' Taro Paste',' Taro'])
df1

# replace df1['name'] with df1['name'] + ' ' + df1['nameCH']
df1['Name'] = df1['Name'] + ' ' + df1['NameCH']
# drop df1['nameCH']
df1= df1.drop(['NameCH'], axis=1)
df1

# generate a mock dataframe with same columns as df1, but replace first columns with random letters
df_mock = df1.copy()
df_mock['Name'] = [chr(np.random.randint(65, 91)) for i in range(len(df_mock))]
df_mock

# randomly select 5 rows from df_mock

# Sample 5 random rows from df_mock
sampled_mock = df_mock.sample(n=5)

# Display the sampled DataFrame
sampled_mock

# Remove non-numeric columns for cosine similarity
product_features = df1.drop(columns=['Name'])
sampled_features = sampled_mock.drop(columns=['Name'])
#customer_features = df_mock.drop(columns=['Name'])
sampled_features = sampled_features.iloc[[0]]

# calculate the similarity between product_features and customer_features and provide a list of top 5 Name with the highest similarity score for each row of customer_features

from sklearn.metrics.pairwise import cosine_similarity

# Calculate cosine similarity between product and customer features
similarity_matrix_sampled = cosine_similarity(product_features, sampled_features)

# Get top 5 products for each customer
top_5_products = []
for i in range(sampled_features.shape[0]):
    # Get similarity scores for the current customer
    customer_similarities = similarity_matrix_sampled [:, i]

    # Get indices of top 5 most similar products
    top_5_indices = np.argsort(customer_similarities)[-5:][::-1]  # Get indices of top 5

    # Get names of top 5 products
    # Concat Name with Size as Name in df1
    top_5_names = df1.iloc[top_5_indices]['Name'].tolist()

    top_5_products.append(top_5_names)

# add similarity score for each name in the result
for i, customer_products in enumerate(top_5_products):
    for j, product_name in enumerate(customer_products):
        similarity_score = similarity_matrix_sampled[df1[df1['Name'] == product_name].index[0], i]
        customer_products[j] = f"{product_name} ({similarity_score:.2f})"
# print the results with similarity score
for i, customer_products in enumerate(top_5_products):
    print(f"Top 5 products for Customer {sampled_features.index[i]}: {customer_products}")

# change the print result as df with column 'Recommendation' with index from sampled_mock
df_result = pd.DataFrame({'Recommendation': top_5_products})
df_result.index = sampled_features.index



# save the result as 'recommendation' and merge the 'recommendation' with the first record in df_mock


#add logic append new record

# prompt: save top 5 result as 'recommendation' and merge the 'recommendation' with the first record in df_mock

# Save the top 5 products as 'recommendation'
#recommendation = pd.DataFrame({'recommendation': [top_5_products]})


# Merge 'recommendation' with the first record in df_mock
merged_df = pd.concat([sampled_features, df_result], axis=1)



pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pandas

# Append new records
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

export_headers_to_sheet(merged_df)
def test_export():

    # Convert 'Recommendation' column to string (if it exists)
    if 'Recommendation' in merged_df.columns:
        merged_df['Recommendation'] = merged_df['Recommendation'].astype(str)

    # Loop through each row in the DataFrame and append to Google Sheets
    for index, row in merged_df.iterrows():
        response_data = row.tolist()  # Convert the row to a list
        append_survey_response(response_data)  # Append each row to Google Sheets


# Run the test export
test_export()
