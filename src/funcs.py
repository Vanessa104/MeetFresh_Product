# This script records all helper functions
import pandas as pd
import numpy as np

# read csv file from google sheet using published url
# columns in this file: Category	Name	NameCH	Sweetness	Preparation_Time	Calories	Ingredients	Temperature	Size	Link	Image
CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1_fFP0quWhpbhwiFbPIHh_ul8VPai3QINPi1tC0gXIutJuiDHhDkmGEtsw_sSFuoPdaHLDlKy9Yte/pub?gid=2112842415&single=true&output=csv'


def onehot_ingredients(df_row):
    """
    Helper function to be applied on each row of data frame
    to expand 'Ingredients' column into one-hot coded columns
    Args:
        df_row: one row in a pd.DataFrame that has an 'Ingredients' column
    Returns:

    """
    ing_list_str = df_row['Ingredients']
    if type(ing_list_str) is not str:
        return df_row
    ings = [ing.strip() for ing in ing_list_str.split(',') if ing != '']
    for ing in ings:
        # if ing.startswith('Grass Jelly'):
        #     df_row['Grass Jelly'] = 1
        # elif ing.startswith('Pota'):
        #     df_row['Potaro Balls'] = 1
        # else:
        df_row[ing] = 1
    return df_row


def memorize_products(url:str):
    """
    Read in all menu items.
    Args:
        url: url to the menu items (without teas) with one-hot coded ingredients

    Returns:
        product_info: pd.dataframe of menu items with features to be displayed
                            in the survey results
        product_features: pd.dataframe of menu items with
    """
    # Read the list of products from
    df = pd.read_csv(CSV_URL)
    df['Image'] = "static/" + df['Image'].fillna("").apply(lambda x: x.split("/")[-1])
    # for reference, the header: Category,Name,NameCH,Sweetness,Preparation_Time,Calories,Ingredients,Temperature,Size,Link,Image

    # Get product info for display:
    # product_info = df[['Category', 'Name', 'NameCH', 'Sweetness', 'Preparation_Time', 'Calories', 'Temperature', 'Size', 'Link', 'Image']]
    product_info = df.copy(deep=True)
    # Map values to numerical for other columns
    product_info['Sweetness'] = product_info['Sweetness'].map(
        {'Low': 1, 'Med': 2, 'High': 3})
    product_info['Preparation_Time'] = product_info['Preparation_Time'].map(
        {'1-3 min': 4, '4-6 min': 5})
    product_info['Temperature'] = product_info['Temperature'].map(
        {'Icy': 1, 'Hot': 2})

    # Just in case it's not one-hot coded yet
    if len(df.columns) < 12:
        product_ingred = df[['Ingredients']].apply(onehot_ingredients, axis=1).drop(columns=['Ingredients'])
        product_ingred = product_ingred.fillna(0).astype(int)
    else:
        irrelevant_colnames = ['Category', 'Name', 'NameCH', 'Calories','Sweetness', 'Temperature', 'Preparation_Time', 'Size', 'Link', 'Image']
        kept_colnames = [colname for colname in df.columns if colname not in irrelevant_colnames]
        product_ingred = df[kept_colnames]

    # merge the two
    df1 = pd.concat([product_info, product_ingred], axis=1)

    return df1


def parse_survey_response(request_form, question_dict):
    """
    Process survey responses into a DataFrame suitable for similarity calculations.
    """
    # Normalize form keys just in case Windows change line endings
    # If no line-ending changes happens, these two lines doesn't affect anything
    normalized_form = {key.replace('\r\n', '\n'): value
                       for key, value in request_form.items()}
    normalized_form_lists = {key.replace('\r\n', '\n'): request_form.getlist(key)
                             for key in request_form.keys()}
    # Handling multiple ingredients
    # Sanity check
    try:
        ingred_list = normalized_form_lists[question_dict['ingred']]
        assert len(ingred_list) > 1, 'Please select at least one ingredient.'
    except KeyError:
        error_message = 'Please select at least one ingredient.'
        return error_message
    except AssertionError as e:
        return str(e)
    except Exception as e:
        error_message = f'{e.__class__}: {e}\n'
        return error_message

    # Convert list to a comma-separated string
    ingred_str = ", ".join(ingred_list)
    # Save/read survey response
    # Use the same column names as the input menu
    responses = {
        'Ingredients': ingred_str,
        # 'ingred': request.form[question_dict['ingred']],
        'Sweetness': normalized_form[question_dict['sweet']],
        'Temperature': normalized_form[question_dict['temp']],
        'Size': normalized_form[question_dict['size']],
        'People': normalized_form[question_dict['people']],
        'Preparation_Time': normalized_form[question_dict['wait']],
        'New_Customer': normalized_form[question_dict['newcustomer']]
    }

    survey_response = pd.DataFrame([responses],
                                   columns=['Ingredients', 'Sweetness',
                                            'Temperature', 'Size',
                                            'People', 'Preparation_Time',
                                            'New_Customer'],
                                   dtype=object)
    return survey_response


def map_survey_responses(response_df, option_dict, target_dict):
    """
    Map the dataframe with OG survey responses into
    numerical values and one-hot coded ingredients.
    Args:
        response_df: pd.DataFrame that records the survey response in 7 columns:
                    ['Ingredients', 'Sweetness', 'Temperature', 'Size',
                    'People', 'Preparation_Time', New_Customer'].
        option_dict: Dictionary with all options used in the survey,
                    i.e., `OPTIONS` used in the main script. Keys are
                    ['newcustomer', 'ingred', 'sweet', 'temp', 'size', 'people', 'wait']
        target_dict: Dictionary with values to be used in subsequent analyses,
                    i.e., `NUMERIZED_OPTIONS` used in the main script. Keys are
                    ['newcustomer', 'ingred', 'sweet', 'temp', 'wait']

    Returns:
        df: equivalent to `survey_matrix` in v0 codes, with relevant columns only
    """
    df = response_df.copy(deep=True)
    df.drop(columns=['Size', 'People', 'New_Customer'], inplace=True)
    # print(df.shape, df.columns)
    # Map stuff
    df['Sweetness'] = df['Sweetness'].map(
        {option_dict['sweet'][idx]: target_dict['sweet'][idx]
         for idx in range(len(option_dict['sweet']))})
    df['Temperature'] = df['Temperature'].map(
        {option_dict['temp'][idx]: target_dict['temp'][idx]
         for idx in range(len(option_dict['temp']))})
    df['Preparation_Time'] = df['Preparation_Time'].map(
        {option_dict['wait'][idx]: target_dict['wait'][idx]
         for idx in range(len(option_dict['wait']))})
    # Convert the Ingredients column into list
    # helper func to be applied by row:
    Ingred_mapping_dict = {option_dict['ingred'][idx]: target_dict['ingred'][idx] for idx in range(len(option_dict['ingred']))}
    def map_ingredients(ingred_list_str:str):
        ingred_list_here = ingred_list_str.split(',')
        ingred_list_here = [Ingred_mapping_dict[item.strip()] for item in ingred_list_here if item != '']
        return ingred_list_here
    # apply mapping by row
    df['Ingredients'] = df['Ingredients'].apply(map_ingredients)
    return df


def clean_feature_matrices(survey_matrix, product_features):
    # Create new columns (one hot encoded) based on df1's columns
    survey_input = survey_matrix.copy(deep=True)
    for col in product_features.columns.tolist()[3:]:
        survey_input[col] = survey_input["Ingredients"].apply(lambda values: 1 if col in values else 0)
    # Apply temperature mask
    temp_mask = product_features['Temperature'].isin(
        survey_input['Temperature'].unique())
    filtered_product_features = product_features[temp_mask]
    # Get common columns (aka selected ingredients)
    common_columns = survey_matrix['Ingredients'].tolist()[0]
    # print(f'common_columns={common_columns}')

    # Only keep the products that have at least one of the selected ingredients
    filtered_rows = filtered_product_features[common_columns].eq(
        [1] * len(common_columns)).any(axis=1)
    # print(f'filtered_rows={filtered_rows}')
    filtered_product_features = filtered_product_features[filtered_rows]

    # # Filter survey input features (ensure numeric and without missing values)
    survey_input_features = survey_input.drop(columns=['Ingredients']).select_dtypes(include=[np.number]).dropna()

    # sanity check
    assert filtered_product_features.shape[1] == survey_input_features.shape[1]

    return survey_input, filtered_product_features, survey_input_features


from sklearn.metrics.pairwise import cosine_similarity


def calculate_similarity(filtered_df, survey_input_features):
    """
    Calculate cosine similarity between survey input and product features.
    """
    #to-do: double-check here
    # product_features = filtered_df.drop(columns=['Name', 'Category', 'Link', 'Image'])
    # survey_features = survey_input_features.drop(columns=['Ingredients'])

    if filtered_df.empty or survey_input_features.empty:
        raise ValueError("No data for similarity calculation.")

    similarity_matrix = cosine_similarity(filtered_df, survey_input_features)

    return similarity_matrix


def generate_recommendations(info_df, similarity_df):
    """
    Generate top recommendations based on similarity scores.
    """
    top_recommendations = similarity_df.sort_values(by=0, ascending=False).head(5)

    recommendations = info_df.loc[top_recommendations.index]
    recommendations['Similarity Score'] = top_recommendations[0]
    recommendations['Rank'] = np.arange(1, 6)
    return recommendations


def format_output_df(input_df, response_df, recommendation_df):
    """
    Incorporate all info into the format expected in the output Google Sheet
    """
    # Format the DF to be written to Google Sheets
    output_df = input_df.copy(deep=True)

    # Format column 'Recommendation': turn rec_df to string
    recommendations = [f'{i}. {row["Name"]}, {row["Similarity Score"]}'
                       for i, row in recommendation_df.iterrows()]
    output_df['Recommendation'] = "; ".join(recommendations)

    # Add back other survey input:
    output_df = pd.concat([output_df,
                           response_df[['People', 'New_Customer']]],
                          axis=1)

    # Add Dallas time as created time
    from datetime import datetime
    from zoneinfo import ZoneInfo
    dallas_time = datetime.now(ZoneInfo("America/Chicago"))
    output_df['created_time'] = dallas_time

    # # Make customer ID
    # import re, random
    # # Replace all non-digit characters with an empty string
    # id_num = re.sub(r'\D', '', str(dallas_time))
    # # Add another random two digits
    # id_num = id_num + str(random.randint(10,99))
    # output_df = pd.concat([pd.DataFrame({"CustomerID": [id_num]}),
    #                        output_df], axis=1)

    # Convert content to strings
    if 'Ingredients' in output_df.columns:
        output_df['Ingredients'] = output_df['Ingredients'].astype(str)
        output_df['created_time'] = output_df['created_time'].astype(str)

    return output_df
