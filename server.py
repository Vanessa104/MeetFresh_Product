
# PEG 2.0 (Process & Export to Google Sheet)

from flask import Flask, render_template, request
from flask import send_from_directory
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity

# ##----Hard-coding the questions and save as constants----##
# ### As reference, colnames later used for user inputs are:
# ### ['ingred','sweet','temp','size','people','wait','newcustomer'] ###
QUESTIONS_ENG = {'ingred': 'What ingredients do you prefer (e.g., grass jelly, taro balls…)?',
                 'sweet': 'Which level of sweetness do you prefer?',
                 'temp': 'Do you prefer hot or cold?',
                 'size': 'Which size do you prefer？',
                 'people': 'How many people are there in your party?',
                 'wait': 'How long can you wait?',
                 'newcustomer': 'Is this your first time trying a Meet Fresh product?'}

INGREDIENTS_ENG = ['Almond Flakes', 'Almond Pudding', 'Almond Soup', 'Black Sugar Boba',
                   'Boba', 'Caramel Pudding', 'Caramel Sauce', 'Chocolate Chip Egg Waffle',
                   'Chocolate Chips', 'Chocolate Egg Waffle', 'Chocolate Syrup',
                   'Chocolate Wafer Rolls', 'Coconut Flakes', 'Coconut Milk',
                   'Coconut Soup', 'Creamer', 'Crystal Mochi', 'Egg Waffle', 'Fluffy',
                   'Grass Jelly', 'Grass Jelly Shaved Ice', 'Grass Jelly Soup',
                   'Hot Red Beans Soup', 'Ice Cream', 'Mango', 'Matcha Egg Waffle',
                   'Matcha Red Beans Egg Waffle', 'Melon Jelly', 'Milk', 'Milk Tea Sauce',
                   'Mini Q', 'Mixed Nuts', 'Mung Bean Cakes', 'Peanuts', 'Potaro Ball',
                   'Purple Rice', 'Purple Rice Soup', 'Q Mochi', 'Red Beans',
                   'Red Beans Soup', 'Rice Balls', 'Coco Sago', 'Sesame Rice Balls',
                   'Shaved Ice', 'Strawberry', 'Taro', 'Taro Balls', 'Taro Paste',
                   'Taro Paste Sauce', 'Tofu Pudding', 'Ube Milk Shaved Ice', 'Ube Paste']
OPTIONS_ENG = {'ingred': INGREDIENTS_ENG,
               'sweet': ['High', 'Medium', 'Low'],
               'temp': ["Cold", "Hot"],
               'size': ['M', 'L'],
               'people': ["Single", "2 -- 3", "4 -- 5", "6 or more"],
               'wait': ["Less than 5 min", "More than 5 min"],
               'newcustomer': ['Yes','No']}

QUESTIONS_CHN = {'ingred': '请选择您想加的原料',
                 'sweet': '请选择甜度',
                 'temp': '请选择甜品温度',
                 'size': '请选择甜品分量',
                 'people': '请选择就餐人数',
                 'wait': '请选择等待时长',
                 'newcustomer': ' 请问您是第一次来鲜芋仙吗？'}
INGREDIENTS_CHN = ['杏仁碎', '杏仁布丁', '杏仁粥', '黑糖珍珠',
                   '珍珠', '焦糖布丁', '焦糖浆', '巧克力碎鸡蛋仔',
                   '巧克力碎', '巧克力蛋仔', '巧克力糖浆',
                   '巧克力华夫卷', 'Coconut Flakes', '椰奶',
                   'Coconut Soup', 'Creamer', 'Crystal Mochi', 'Egg Waffle', 'Fluffy',
                   '仙草', '仙草冰沙', 'Grass Jelly Soup',
                   '热红豆汤', '冰淇淋', '芒果', 'Matcha Egg Waffle',
                   'Matcha Red Beans Egg Waffle', 'Melon Jelly', '牛奶', '奶茶糖浆',
                   'Mini Q', 'Mixed Nuts', '绿豆糕', '花生', '芋薯圆',
                   '紫米', '紫米粥', 'Q Mochi', '红豆',
                   '红豆汤', '汤圆', '椰汁西米', '芝麻汤圆',
                   '冰沙', '草莓', '芋头', '芋圆', '芋泥',
                   'Taro Paste Sauce', '豆花', '紫薯牛奶冰', '紫薯泥']
OPTIONS_CHN = {'ingred': INGREDIENTS_CHN,
               'sweet': ['高糖', '中糖', '低糖'],
               'temp': ["冷", "热"],
               'size': ['中份', '大份'],
               'people': ["单人", "2 -- 3", "4 -- 5", "6人或以上"],
               'wait': ["少于5分钟", "超过5分钟"],
               'newcustomer': ['是', '否']}
# save the mapping of options to numbers here (for later use)
NUMERIZED_OPTIONS = {'sweet': [3, 2, 1],
                     'temp': [1, 2],
                     # 'size': [2, 3],
                     # 'people': ["单人", "2 -- 3", "4 -- 5", "6人或以上"],
                     'wait': [4, 5],
                     'newcustomer': [1, 0]}

# #----End of block----##
# Make a concatenated bilingual version for temporary use:
QUESTIONS_BI = {key: f'{QUESTIONS_ENG[key]}\n{QUESTIONS_CHN[key]}'
                for key in QUESTIONS_ENG}
OPTIONS_BI = {key: f'{OPTIONS_ENG[key]} {OPTIONS_CHN[key]}'
              for key in OPTIONS_ENG}
# ##----Actual End of block----###

app = Flask(__name__)

# I'll use all English as an example for now.
# ## To concatenate eng+chn, do
# ### f'{QUESTIONS_ENG[key]}\n{QUESTIONS_CHN[key]}':
#       [f'{OPTIONS_ENG[key][opt_idx]} {OPTIONS_CHN[key][opt_idx]}'
#        for opt_idx in range(len(OPTIONS_ENG[key]))]
questions = {QUESTIONS_BI[key]: OPTIONS_BI[key] for key in
             ['newcustomer', 'ingred', 'sweet', 'temp', 'size', 'people', 'wait']}

# read csv file from google sheet using published url
csv_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1_fFP0quWhpbhwiFbPIHh_ul8VPai3QINPi1tC0gXIutJuiDHhDkmGEtsw_sSFuoPdaHLDlKy9Yte/pub?gid=2112842415&single=true&output=csv'
df = pd.read_csv(csv_url)
df['Image'] = "static/" + df['Image'].fillna("").apply(lambda x: x.split("/")[-1])
# data = df
# data['Image'] = "static/" + data['Image'].apply(lambda x: x.split("/")[-1])
# results_data = data.set_index('Name').to_dict(orient='index')

# write a code to use sklearn binarizer to convert all words in 'Ingredients' columns to binary values
# and drop 'Link','Image','Calories' columns
mlb = MultiLabelBinarizer()
df1 = df.drop(['Category', 'Calories', 'Size', 'Link', 'Image'], axis=1)
# Convert 'Sweetness' column to numerical values
df1['Sweetness'] = df1['Sweetness'].map({'Low': 1, 'Med': 2, 'High': 3})
# {OPTIONS_ENG['sweet'][idx]: NUMERIZED_OPTIONS['sweet'][idx]
#  for idx in range(len(OPTIONS_ENG['sweet']))})

# Convert 'PrepTime' column to numerical values
df1['Preparation_Time'] = df1['Preparation_Time'].str.extract('(\d+)').astype(float)
# if df1[preparation_time] <5 then 4, else if >=5 then 5 as new df1[preparation_time]
df1['Preparation_Time'] = df1['Preparation_Time'].apply(lambda x: 4 if x < 5 else 5)

# Convert 'Temp' to numerical values
temp_mapping = {'Icy': 1, 'Hot': 2}
df1['Temperature'] = df1['Temperature'].map(temp_mapping)
# Convert 'Size' to numerical values
# size_mapping = {'One Size': 1, 'M': 2, 'L': 3}
# df1['Size'] = df1['Size'].map(size_mapping)

# # write a code to do one hot encoding for 'Sweetness','Temp','size' columns together with above
# df2 = pd.get_dummies(df1, columns=['Sweetness','Temp','Size'])
# print(df2.head())
df1['Ingredients'] = df1['Ingredients'].fillna('')
ingredient_encoded = pd.DataFrame(mlb.fit_transform(df1['Ingredients'].str.split(',')),
                                  columns=mlb.classes_,
                                  index=df1.index)

# Merge one-hot encoded ingredient columns back
df1 = df1.join(ingredient_encoded).drop(columns=['Ingredients'])
# df1= df1.drop(columns=[' Boba',' Grass Jelly',' Melon Jelly',
# ' Mini Q',' Red Beans', ' Rice Balls', ' Strawberry', ' Taro Paste',
# ' Taro','Taro Ball',' Taro Balls',' ', ' Sago'])
df1.rename(columns = {'Sago': 'Coco Sago'}, inplace=True)
df1.drop(columns=[''], inplace=True)

# For later comparison between product ingred and survey ingred and filter=creation
df1_ingred = df1.copy(deep=True).drop(columns=['Name', 'NameCH', 'Sweetness', 'Temperature', 'Preparation_Time'])


def save_response(responses):
    df = pd.DataFrame([responses], columns=['ingred', 'sweet', 'temp', 'size', 'people','wait', 'newcustomer'])
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
        ingred_list = request.form.getlist(QUESTIONS_BI['ingred'])
        ingred_str = ", ".join(ingred_list)  # Convert list to a comma-separated string
        responses = {
            'ingred': ingred_str,
            'sweet': request.form[QUESTIONS_BI['sweet']],
            'temp': request.form[QUESTIONS_BI['temp']],
            'size': request.form[QUESTIONS_BI['size']],
            'people': request.form[QUESTIONS_BI['people']],
            'wait': request.form[QUESTIONS_BI['wait']],
            'newcustomer': request.form[QUESTIONS_BI['newcustomer']]
        }

        import pandas as pd
        # Read survey response
        survey_response = pd.DataFrame([responses],
                                       columns=['ingred', 'sweet', 'temp', 'size', 'people', 'wait', 'newcustomer'])

        # survey_response = survey_response.iloc[4:5]
        survey_response.rename(columns={'ingred':'Ingredients',
                                        'sweet': 'Sweetness',
                                        'temp': 'Temperature',
                                        'size': 'Size',
                                        'people': 'People',
                                        'wait': 'Preparation_Time',
                                        'newcustomer': 'New_Customer'},
                               inplace=True)
        survey_matrix = survey_response.copy(deep=True)

        survey_matrix.drop(columns=['Size', 'People', 'New_Customer'], inplace=True)
        survey_matrix['Sweetness']= survey_matrix['Sweetness'].map(
            {OPTIONS_BI['sweet'][idx]: NUMERIZED_OPTIONS['sweet'][idx]
             for idx in range(len(OPTIONS_ENG['sweet']))})
        survey_matrix['Temperature']= survey_matrix['Temperature'].map(
            {OPTIONS_BI['temp'][idx]: NUMERIZED_OPTIONS['temp'][idx]
             for idx in range(len(OPTIONS_ENG['temp']))})
        survey_matrix['Preparation_Time']= survey_matrix['Preparation_Time'].map(
            {OPTIONS_BI['wait'][idx]: NUMERIZED_OPTIONS['wait'][idx]
             for idx in range(len(OPTIONS_ENG['wait']))})
        # Convert the Ingredients column into list
        survey_matrix['Ingredients'] = survey_matrix['Ingredients'].apply(lambda x: x.split(','))

        # Create new columns (one hot encoded) based on df1's columns
        survey_matrix_new = survey_matrix.copy(deep=True)
        for col in df1_ingred.columns:
            survey_matrix_new[col] = survey_matrix_new["Ingredients"].apply(lambda values: 1 if col in values else 0)

        survey_input = survey_matrix_new

        # List columns by ingredients
        survey_ingred = survey_matrix

        # flatten list
        survey_ingred = survey_ingred.explode('Ingredients')
        for value in survey_ingred['Ingredients']:
            survey_ingred[value] = 1
        # Find common columns
        product_features = df1[df1['Temperature'].isin(survey_input['Temperature'])].drop(columns=['Name', 'NameCH'])
        # Find the common columns between df1 and survey_input
        common_columns = df1.iloc[:, 4:].columns.intersection(survey_ingred.iloc[:, 4:].columns)

        # Filter product_features where at least one value in common columns exists in df2
        filtered_columns = product_features[common_columns].isin(survey_ingred.to_dict('list')).any(axis=1)
        product_features = product_features[filtered_columns]
        # Filter survey input features (ensure numeric and without missing values)
        survey_input_features = survey_input.drop(columns=['Ingredients']).select_dtypes(include=[np.number]).dropna()

        # Debug print for shapes
        print("Product Features Shape:", product_features.shape)
        print("Survey Input Features Shape:", survey_input_features.shape)

        # Calculate cosine similarity
        def calculate_similarity(product_features, survey_input_features):
            if product_features.shape[0] == 0 or survey_input_features.shape[0] == 0:
                raise ValueError("Input arrays must contain at least one sample.")
            similarity_matrix = cosine_similarity(product_features, survey_input_features)
            return similarity_matrix

        try:
            similarity_matrix_survey = calculate_similarity(product_features, survey_input_features)
        except ValueError as e:
            print(f"Error: {e}")
            similarity_matrix_survey = None
        if similarity_matrix_survey is not None:
            # Convert the similarity matrix to a DataFrame
            similarity_df = pd.DataFrame(
                similarity_matrix_survey,
                index=product_features.index,
                columns=survey_input_features.index
            )

            # Get top 5 products
            similarity_df = similarity_df.sort_values(by=similarity_df.columns[0], ascending=False)
            similarity_df = similarity_df.head(5)

            # Merge with original data for recommendations
            recommendation_df = df.merge(similarity_df, left_index=True, right_index=True, how='inner')
            recommendation_df = recommendation_df.sort_values(by=similarity_df.columns[0], ascending=False)

            # Rename the similarity column
            recommendation_df_new = recommendation_df.copy(deep=True)
            recommendation_df_new.rename(columns={recommendation_df_new.columns[-1]: "Similarity Score"}, inplace=True)

            # Convert to dictionary for the output
            recommendation_df_new = recommendation_df_new.drop_duplicates(subset=['Name'])
            results_data = recommendation_df_new.set_index('Name').to_dict(orient='index')
            # Show results
            print(results_data)
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

                # Generate concatenated recommendation string dynamically
                recommendations = [
                    f"{row.get(f'Top{i} Product', 'NA')},{row.get(f'Similarity Score Top{i}', 'NA')}"
                    for i in range(1, 6)
                ]
                row["Recommendation"] = ",".join(recommendations)

                df_list.append(row)

            # Create DataFrame
            df_result = pd.DataFrame.from_records(df_list)

            # Set CustomerID as index
            df_result.set_index("CustomerID", inplace=True)

        # Drop Top Product and Score columns efficiently
            df_result.drop(columns=[col for col in df_result.columns if "Top" in col or "Similarity Score" in col], inplace=True)
            # survey_other_input = survey_response[['People','New_Customer']].iloc[:1]
            # survey_other_input = survey_response[['People','New_Customer']].iloc[10:11]
            # survey_other_input = survey_response[['People','New_Customer']].iloc[49:50]
            survey_other_input = survey_response[['People','New_Customer']]
            merged_df_response = pd.concat([survey_input, df_result, survey_other_input], axis=1)
            # add Dallas time as created time
            from datetime import datetime
            from zoneinfo import ZoneInfo
            dallas_time = datetime.now(ZoneInfo("America/Chicago"))
            merged_df_response['created_time'] = dallas_time
            # merged_df_response['created_time'] = pd.to_datetime('now')

        else:
            print("Similarity matrix could not be calculated. No recommendations to display.")
            merged_df_response = pd.DataFrame()
            results_data = {}

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

        if merged_df_response.empty:
            print("Error: DataFrame is empty, nothing to export.")
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
        if not results_data:
            return render_template('result.html', error_message="No recommendations found based on your input.")
        else:
            return render_template('result.html', responses=responses, results=results_data)
    return render_template('survey.html', questions=questions)


# @app.route('/download/<filename>')
# def download_file(filename):
# Replace with the correct directory where your file is located
#   directory = os.path.join(app.root_path, 'static')
#  return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)












