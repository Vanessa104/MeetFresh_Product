import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Embed the JSON key directly in your code as a string
JSON_KEY = '''
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

# ID of the Google Sheet where you want to export the data
SPREADSHEET_ID = '1dN3quMHzOj33XM3Jdbz5vK82JnZebWJX9UEdVPjAvXU'

def authenticate_google_sheets():
    """
    Authenticates with Google Sheets API using the service account credentials.
    """
    service_account_info = json.loads(JSON_KEY)
    # print(type(service_account_info), service_account_info)
    # print(service_account_info["private_key"])
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    # print(service_account_info["private_key"])
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
                                          range=f"{sheet_name}!A:A").execute()
        line_num = len(first_column.get('values', []))

        # Assume multiple lines (downward-compatible with a single line)
        # Make sure to export content by line
        for i, df_row in df.iterrows():
            # Define content body
            body = {"values": [df_row.tolist()]}
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
