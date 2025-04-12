
# PEG 2.0 (Process & Export to Google Sheet)

from flask import Flask, render_template, request
import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)


# read csv file from google sheet using published url
CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1_fFP0quWhpbhwiFbPIHh_ul8VPai3QINPi1tC0gXIutJuiDHhDkmGEtsw_sSFuoPdaHLDlKy9Yte/pub?gid=2112842415&single=true&output=csv'
df = pd.read_csv(CSV_URL)
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
df1_ingred = df1.copy(deep=True).drop(columns=['Name', 'NameCH', 'Sweetness', 'Temperature', 'PrepTime'])


def save_response(responses):
    df = pd.DataFrame([responses], columns=['ingred', 'sweet', 'temp', 'size', 'people','wait', 'newcustomer'])
    try:
        existing_df = pd.read_csv("survey_results.csv")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_csv("survey_results.csv", index=False)


# Get the concatenated bilingual version here
from src.questions import QUESTIONS_BI as QUESTIONS
from src.questions import OPTIONS_BI as OPTIONS
from src.questions import NUMERIZED_OPTIONS

Questions = {QUESTIONS[key]: OPTIONS[key] for key in
             ['newcustomer', 'ingred', 'sweet', 'temp', 'size', 'people', 'wait']}

@app.route('/', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        # Handling multiple ingredients
        ingred_list = request.form.getlist(QUESTIONS['ingred'])
        ingred_str = ", ".join(ingred_list)  # Convert list to a comma-separated string
        responses = {
            'ingred': ingred_str,
            'sweet': request.form[QUESTIONS['sweet']],
            'temp': request.form[QUESTIONS['temp']],
            'size': request.form[QUESTIONS['size']],
            'people': request.form[QUESTIONS['people']],
            'wait': request.form[QUESTIONS['wait']],
            'newcustomer': request.form[QUESTIONS['newcustomer']]
        }

        # Read survey response
        survey_response = pd.DataFrame([responses],
                                       columns=['ingred', 'sweet', 'temp', 'size', 'people', 'wait', 'newcustomer'])

        # to-do: remove these redundant column name changes
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
            {OPTIONS['sweet'][idx]: NUMERIZED_OPTIONS['sweet'][idx]
             for idx in range(len(OPTIONS['sweet']))})
        survey_matrix['Temperature']= survey_matrix['Temperature'].map(
            {OPTIONS['temp'][idx]: NUMERIZED_OPTIONS['temp'][idx]
             for idx in range(len(OPTIONS['temp']))})
        survey_matrix['Preparation_Time']= survey_matrix['Preparation_Time'].map(
            {OPTIONS['wait'][idx]: NUMERIZED_OPTIONS['wait'][idx]
             for idx in range(len(OPTIONS['wait']))})
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

        # Append new records to Google Sheets
        # from src.google_utils import JSON_KEY, SPREADSHEET_ID
        from src.google_utils import export_to_google_sheets

        if merged_df_response.empty:
            print("Error: DataFrame is empty, nothing to export.")
        # Test the whole process (clear and export)
        merged_df = merged_df_response.copy(deep=True)
        # Write down the header
        export_to_google_sheets(merged_df, line=1)
        # Write the body
        if 'Ingredients' in merged_df.columns:
            merged_df['Ingredients'] = merged_df['Ingredients'].astype(str)
            merged_df['created_time'] = merged_df['created_time'].astype(str)
        export_to_google_sheets(merged_df, line=2)

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












