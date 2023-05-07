import gspread
from oauth2client.service_account import ServiceAccountCredentials
import boto3
from botocore.exceptions import ClientError


scope = ['https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('virtual-equator-386019-aa4e9efb6c66.json', scope)
client = gspread.authorize(creds)
# aws_sns_client = boto3.client('sns', region_name='us-east-1')
aws_ses_client = boto3.client('ses', region_name = 'us-east-1')

sheet_name = 'Volleyball'
worksheet_name = 'Summer 1'

sheet = client.open(sheet_name)
worksheet = sheet.worksheet(worksheet_name)

volley_data = worksheet.get_all_records()

player_data = sheet.worksheet('Player_db').get_all_records()

needs_to_respond = []

for record in volley_data:
    if record['Week 1:'] == '':
        playername = record['Players']
        needs_to_respond.append(playername.rstrip())

for player in player_data:
    if player['Name'] in needs_to_respond:
        print(f"text {player['Name']} at {player['Phone']}")
        sender = 'leffeler@gmail.com'
        recepient = player['Email']
        subject = 'Missing Volleyball Info'
        body = 'Volleyball is tomorrow. Please respond on this spreadsheet if you can make it or not: https://docs.google.com/spreadsheets/d/1QlyMbAXxbiUrmJ0TH6HtAPaSJOrArEYKkrKtU2sWUb4/edit#gid=1402272001'

        message = {
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text':{
                    'Data': body
                }
            }
        }

        try:
            response = aws_ses_client.send_email(
                Source = sender,
                Destination = {
                    'ToAddresses': [
                        recepient
                    ]
                },
                Message = message
            )
            print(f"Email sent! Message ID: {response['MessageId']}")
        except ClientError as e:
            print(e.response['Error']['Message'])













        # response = aws_sns_client.publish(
        #     PhoneNumber = str(player['Phone']),
        #     Message = f"{player['Name']} sign up for vball nerd"
        # )
