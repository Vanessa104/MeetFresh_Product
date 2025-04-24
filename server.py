#!/usr/bin/env python3
from flask import Flask, render_template, request
# import logging
# logging.basicConfig(filename='app.log', level=logging.DEBUG)
import pandas as pd


app = Flask(__name__)

from src.funcs import memorize_products
from src.questions import INGREDIENTS_ENG as all_ingredients

# temporary
all_ingredients[all_ingredients.index('Coco Sago')] = 'Sago'


# read csv file from google sheet using published url
# CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1_fFP0quWhpbhwiFbPIHh_ul8VPai3QINPi1tC0gXIutJuiDHhDkmGEtsw_sSFuoPdaHLDlKy9Yte/pub?gid=2112842415&single=true&output=csv'
# Alt: read a local file:
CSV_URL = 'menu_items_w_og_onehot_ingredients.csv'

df1 = memorize_products(CSV_URL)
# print(df1.columns[10:])
product_features = df1.drop(columns=['Category', 'Name', 'NameCH', 'Calories','Ingredients', 'Size', 'Link', 'Image'])

# Get the concatenated bilingual version here
from src.questions import QUESTIONS_BI as QUESTIONS
from src.questions import OPTIONS_BI as OPTIONS
from src.questions import NUMERIZED_OPTIONS

Questions = {QUESTIONS[key]: OPTIONS[key] for key in
             ['newcustomer', 'ingred', 'sweet', 'temp', 'size', 'people', 'wait']}

from src.funcs import parse_survey_response, map_survey_responses, clean_feature_matrices, calculate_similarity, generate_recommendations

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
        # print(f'survey_matrix={survey_matrix}')

        # Apply temperature mask and shrink the candidate pool
        # Kept `survey_input` bc it's needed for output (to Google Sheets)
        survey_input, filtered_product_features, survey_input_features = clean_feature_matrices(survey_matrix, product_features)

        # Calculate cosine similarity
        try:
            similarity_matrix_survey = calculate_similarity(filtered_product_features, survey_input_features)
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
                index=filtered_product_features.index,
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
        from src.google_utils import export_to_google_sheets

        if merged_df_response.empty:
            print("Error: DataFrame is empty, nothing to export.")
        # Test the whole process (clear and export)
        merged_df = merged_df_response.copy(deep=True)
        print('merged_df columns:', merged_df.columns)
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












