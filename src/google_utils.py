import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Embed the JSON key directly in your code as a string
JSON_KEY = '''
{
"type": "service_account",
"project_id": "meetfresh-data-migration",
"private_key_id": "1d1dbef38e7044f2280cbc2838a70351228a7f7c",
"private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCp71HrAwmm+qAh\\nvA4AsRNM14Y2zCVE26AAdjw7YJfbYQ0z22eG90Sbu3hyqrAmH4LFNkLebs9s2D0l\\nraFcAS...==",
"client_email": "meetfresh-data-migration@meetfresh-data-migration.iam.gserviceaccount.com",
"client_id": "114713800073444959941",
"auth_uri": "https://accounts.google.com/o/oauth2/auth",
"token_uri": "https://oauth2.googleapis.com/token",
"auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
"client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/meetfresh-data-migration%40meetfresh-data-migration.iam.gserviceaccount.com",
"universe_domain": "googleapis.com"
}
'''

# ID of the Google Sheet where you want to export the data
SPREADSHEET_ID = '1dN3quMHzOj33XM3Jdbz5vK82JnZebWJX9UEdVPjAvXU'

def authenticate_google_sheets():
    """
    Authenticates with Google Sheets API using the service account credentials.
    """
    service_account_info = json.loads(JSON_KEY)
    # print(type(service_account_info), service_account_info)
    print(service_account_info["private_key"])
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    print(service_account_info["private_key"])
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('sheets', 'v4', credentials=credentials)
    return service


def export_to_google_sheets(df, sheet_name="Sheet1", line:int=1):
    """
    Exports a DataFrame to Google Sheets.
    :param df: The DataFrame to export.
    :param sheet_name: The name of the sheet (default is "Sheet1").
    :param line: The line index (starting at 1) in the sheet to write data in. Default is 1. Any other int values would indicate writing at the end.
    """
    # Open the file
    service = authenticate_google_sheets()
    sheet = service.spreadsheets()

    # Write the header on the first line
    if line == 1:
        # Extract column names as list
        values = [df.columns.tolist()] # + df.values.tolist()
        body = {"values": values}
        # Define range (i.e., 'Sheet1!A1', 1st cell of 1st line in 1st sheet)
        range_ = f"{sheet_name}!A1"
        # Write header to sheet
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_,
            valueInputOption="RAW",
            body=body
        ).execute()
        print("Header written to Google Sheets.")
    else:
        # Count the existing number of lines by only fetching a single column
        first_column = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                          range=f"{sheet_name}!A:A")
        line_num = len(first_column.get('values', []))

        # Assume multiple lines (downward-compatible with a single line)
        # Make sure to export content by line
        for i, df_row in df.iterrows():
            # Define content body
            values = {"values": [df_row]}
            body = {"values": values}
            # Define range to be the next line
            range_ = f"{sheet_name}!A{line_num+1+i}"
            # Write line to sheet
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_,
                valueInputOption="RAW",
                body=body
            ).execute()
        print("Data written to Google Sheets.")

    # Clear existing sheet data
    # sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=sheet_name).execute()
