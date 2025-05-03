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
CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1_fFP0quWhpbhwiFbPIHh_ul8VPai3QINPi1tC0gXIutJuiDHhDkmGEtsw_sSFuoPdaHLDlKy9Yte/pub?gid=2112842415&single=true&output=csv'
# Alt: read a local file:
# CSV_URL = 'menu_items_w_og_onehot_ingredients.csv'

df1 = memorize_products(CSV_URL)
# print(df1.columns[10:])
product_features = df1.drop(columns=['Category', 'Name', 'NameCH', 'Calories','Ingredients', 'Size', 'Link', 'Image'])

# Get the concatenated bilingual version here
from src.questions import QUESTIONS_BI as QUESTIONS
from src.questions import OPTIONS_BI as OPTIONS
from src.questions import NUMERIZED_OPTIONS

Questions = {QUESTIONS[key]: OPTIONS[key] for key in
             ['newcustomer', 'ingred', 'sweet', 'temp', 'size', 'people', 'wait']}

from src.funcs import parse_survey_response, map_survey_responses, clean_feature_matrices, calculate_similarity, generate_recommendations, format_output_df

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

        # Apply temperature mask and shrink the candidate pool
        # Kept `survey_input` bc it's needed for output (to Google Sheets)
        survey_input, filtered_product_features, survey_input_features = clean_feature_matrices(survey_matrix, product_features)

        # Calculate similarity
        try:
            similarity_matrix_survey = calculate_similarity(filtered_product_features, survey_input_features)
        except Exception as e:
            print("Similarity matrix could not be calculated. No recommendations to display.")
            error_message=f"Error when calculating similarity: {e}\nYour response: {survey_response}"
            print(error_message)
            return render_template('error.html', error_message=error_message)


        # Convert the similarity matrix to a DataFrame
        similarity_df = pd.DataFrame(
                similarity_matrix_survey,
                index=filtered_product_features.index,
                columns=survey_input_features.index)

        # Rank products by score and take top 5
        recommendation_df = generate_recommendations(
            info_df=df1[['Name', 'NameCH', 'Image', 'Link']],
            similarity_df=similarity_df)

        # Generate df to be written out
        output_df = format_output_df(input_df=survey_input,
                                     response_df=survey_response,
                                     recommendation_df=recommendation_df)
        # print('output_df.shape = ', output_df.shape)
        # Sanity check
        if output_df.empty:
            error_message = "Error: DataFrame is empty, nothing to export."
            print(error_message)
            return render_template('error.html', error_message=error_message)

        # Append new records to Google Sheets
        from src.google_utils import export_to_google_sheets

        # Write down the header
        export_to_google_sheets(output_df, line=1)
        # Write the body
        export_to_google_sheets(output_df, line=2)

        # Show results
        results_data = recommendation_df.to_dict(orient='records')
        print(results_data)

        if not results_data:
            return render_template('result.html', error_message="No recommendations found based on your input.")
        else:
            return render_template('result.html', responses=survey_response, results=results_data)

    return render_template('survey.html', questions=Questions, question_list=QUESTIONS)


# @app.route('/download/<filename>')
# def download_file(filename):
# Replace with the correct directory where your file is located
#   directory = os.path.join(app.root_path, 'static')
#  return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    # app.debug = True # Enable debug mode
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)












