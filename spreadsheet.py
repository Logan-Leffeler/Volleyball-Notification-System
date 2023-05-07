import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('virtual-equator-386019-aa4e9efb6c66.json', scope)
client = gspread.authorize(creds)

sheet = client.open('Volleyball').sheet1

volley_data = sheet.get_all_records()

print(volley_data)