# This script records all helper functions
import pandas as pd
import numpy as np

# read csv file from google sheet using published url
CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1_fFP0quWhpbhwiFbPIHh_ul8VPai3QINPi1tC0gXIutJuiDHhDkmGEtsw_sSFuoPdaHLDlKy9Yte/pub?gid=2112842415&single=true&output=csv'

def memorize_products(url:str):
    # Read the list of products from
    # Logic from line 13 -- 52
    df = pd.read_csv(CSV_URL)
    pass


def process_survey_response(responses):
    """
    Process survey responses into a DataFrame suitable for similarity calculations.
    """
    # Processing survey data into a DataFrame
    # Logic from lines 175–204
    survey_response = pd.DataFrame([responses])
    survey_response.rename(columns={
        'ingred': 'Ingredients',
        'sweet': 'Sweetness',
        'temp': 'Temperature',
        'size': 'Size',
        'people': 'People',
        'wait': 'Preparation_Time',
        'newcustomer': 'New_Customer'
    }, inplace=True)

    # One-hot encode ingredients
    #to-do: double-check here. (below are copilot codes)
    survey_input_features = survey_response.copy()
    survey_input_features['Ingredients'] = survey_input_features['Ingredients'].apply(lambda x: x.split(','))
    return survey_response, survey_input_features


from sklearn.metrics.pairwise import cosine_similarity


def calculate_similarity(df, survey_input_features):
    """
    Calculate cosine similarity between survey input and product features.
    """
    # Logic from lines 233–244
    #to-do: double-check here
    product_features = df.drop(columns=['Name', 'Category', 'Link', 'Image'])
    survey_features = survey_input_features.drop(columns=['Ingredients'])

    if product_features.empty or survey_features.empty:
        raise ValueError("No data for similarity calculation.")

    similarity_matrix = cosine_similarity(product_features, survey_features)
    return similarity_matrix



def generate_recommendations(df, similarity_matrix):
    """
    Generate top recommendations based on similarity scores.
    """
    # Logic from lines 245–305
    similarity_df = pd.DataFrame(similarity_matrix, index=df.index)
    top_recommendations = similarity_df.sort_values(by=0, ascending=False).head(5)

    recommendations = df.loc[top_recommendations.index]
    recommendations['Similarity Score'] = top_recommendations[0]
    return recommendations.to_dict(orient='index')

