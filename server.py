#!/usr/bin/env python3
from flask import Flask, render_template, request
# import logging
# logging.basicConfig(filename='app.log', level=logging.DEBUG)
import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)

from src.funcs import memorize_products
from src.questions import INGREDIENTS_ENG as all_ingredients

# temporary
all_ingredients[all_ingredients.index('Coco Sago')] = 'Sago'


# read csv file from google sheet using published url
CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1_fFP0quWhpbhwiFbPIHh_ul8VPai3QINPi1tC0gXIutJuiDHhDkmGEtsw_sSFuoPdaHLDlKy9Yte/pub?gid=2112842415&single=true&output=csv'
# df = pd.read_csv(CSV_URL)
# df['Image'] = "static/" + df['Image'].fillna("").apply(lambda x: x.split("/")[-1])

df1, df1_ingred = memorize_products(CSV_URL)

# just sanity check
try:
    assert sorted(df1_ingred.columns.tolist()) == sorted(all_ingredients)
except Exception as e:
    print(e)
    for i in range(min(len(df1_ingred.columns), len(all_ingredients))):
        print(df1_ingred.columns[i], all_ingredients[i])
    exit(1)


# Get the concatenated bilingual version here
from src.questions import QUESTIONS_BI as QUESTIONS
from src.questions import OPTIONS_BI as OPTIONS
from src.questions import NUMERIZED_OPTIONS

Questions = {QUESTIONS[key]: OPTIONS[key] for key in
             ['newcustomer', 'ingred', 'sweet', 'temp', 'size', 'people', 'wait']}

from src.funcs import parse_survey_response, map_survey_responses, calculate_similarity, generate_recommendations

@app.route('/', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        survey_response = parse_survey_response(request_form=request.form,
                                                question_dict=QUESTIONS)
        # Handling error
        if type(survey_response) is str:
            return render_template('error.html', error_message=survey_response)

        survey_matrix = map_survey_responses(survey_response,
                                             option_dict=OPTIONS,
                                             target_dict=NUMERIZED_OPTIONS)
        print(f'survey_matrix={survey_matrix}')
        # Create new columns (one hot encoded) based on df1's columns
        survey_input = survey_matrix.copy(deep=True)
        for col in all_ingredients:
            survey_input[col] = survey_input["Ingredients"].apply(lambda values: 1 if col in values else 0)

        # List columns by ingredients
        survey_ingred = survey_matrix

        # flatten list
        survey_ingred = survey_ingred.explode('Ingredients')
        for value in survey_ingred['Ingredients']:
            survey_ingred[value] = 1
        print(f'survey_ingred={survey_ingred}\nsurvey_input={survey_input}')
        # Find common columns
        product_features = df1.drop(columns=['Category', 'Name', 'NameCH', 'Calories','Ingredients', 'Size', 'Link', 'Image'])


        # Apply temperature mask
        temp_mask = product_features['Temperature'].isin(
                survey_input['Temperature'].unique())
        product_features = product_features[temp_mask]
        # Because ingredients in the survey are identical to column names here, we know for sure:
        # common_columns = survey_ingred.columns[4:]
        common_columns = survey_matrix['Ingredients'].tolist()[0]
        print(f'common_columns={common_columns}')
        # print(f'survey_ingred.to_dict(\'list\')={survey_ingred.to_dict("list")}')

        # Filter product_features where at least one value in common columns exists in df2
        filtered_rows = product_features[common_columns].isin(survey_ingred.iloc[:, 1:].to_dict("list")).any(axis=1)
        # print(f'filtered_rows={filtered_rows}')
        product_features = product_features[filtered_rows]
        # # Filter survey input features (ensure numeric and without missing values)
        survey_input_features = survey_input.drop(columns=['Ingredients']).select_dtypes(include=[np.number]).dropna()
        print(f'survey_input_features={survey_input_features}')

        # Debug print for shapes
        print("Product Features Shape:", product_features.shape)
        print("Survey Input Features Shape:", survey_input_features.shape)

        # Calculate cosine similarity
        try:
            similarity_matrix_survey = calculate_similarity(product_features.dropna(), survey_input_features)
        except Exception as e:
            merged_df_response = pd.DataFrame()
            results_data = {}
            print("Similarity matrix could not be calculated. No recommendations to display.")
            error_massage=f"Error when calculating similarity: {e}"
            print(error_massage)
            return render_template('error.html', error_message=error_massage)


        # Convert the similarity matrix to a DataFrame
        similarity_df = pd.DataFrame(
                similarity_matrix_survey,
                index=product_features.index,
                columns=survey_input_features.index)

        # Get top 5 products
        similarity_df = similarity_df.sort_values(by=similarity_df.columns[0], ascending=False).head(5)

        # Merge with original data for recommendations
        # note-to-self: `df1` should be `product_info` here
        recommendation_df = df1.merge(similarity_df, left_index=True, right_index=True, how='inner')
        recommendation_df = recommendation_df.sort_values(by=similarity_df.columns[0], ascending=False)

        # Rename the similarity column
        recommendation_df_new = recommendation_df.copy(deep=True)
        recommendation_df_new.rename(columns={recommendation_df_new.columns[-1]: "Similarity Score"}, inplace=True)

        # Convert to dictionary for the output
        recommendation_df_new = recommendation_df_new.drop_duplicates(subset=['Name'])
        results_data = recommendation_df_new.set_index('Name').to_dict(orient='index')
        # Show results
        print(results_data.keys())
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

    return render_template('survey.html', questions=Questions, question_list=QUESTIONS)


# @app.route('/download/<filename>')
# def download_file(filename):
# Replace with the correct directory where your file is located
#   directory = os.path.join(app.root_path, 'static')
#  return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    # app.debug = True # Enable debug mode
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)












