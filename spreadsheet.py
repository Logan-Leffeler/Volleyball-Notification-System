import gspread
from oauth2client.service_account import ServiceAccountCredentials
import boto3
from botocore.exceptions import ClientError

# Connect to google spreadsheet API and establish E-Mail service

scope = ['https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('virtual-equator-386019-aa4e9efb6c66.json', scope)
client = gspread.authorize(creds)
# aws_sns_client = boto3.client('sns', region_name='us-east-1')
aws_ses_client = boto3.client('ses', region_name = 'us-east-1')

# Figure out Current session and establish datasets

with open("current_session.txt", "r") as file:
    current_session = int(file.read())

sheet_name = 'Volleyball'
worksheet_name = f'Session {current_session}'

sheet = client.open(sheet_name)
worksheet = sheet.worksheet(worksheet_name)

volley_data = worksheet.get_all_records()

player_data = sheet.worksheet('Player_db').get_all_records()

# Figure out what the current week is

with open("current_week.txt", "r") as file:
    current_week = int(file.read())
    current_week += 1

# Loop through players and create a list of players that have not responded

needs_to_respond = []

for record in volley_data:
    if record[f'Week {current_week}:'] == '':
        playername = record['Players']
        needs_to_respond.append(playername.rstrip())

# Loop through players and send emails to ones who have not responded

for player in player_data:
    if player['Name'] in needs_to_respond:
        sender = 'leffeler@gmail.com'
        recepient = player['Email']
        subject = 'Missing Volleyball Info'
        body = f'Tomorrow is week {current_week} of volleyball. Please respond on this spreadsheet if you can make it or not: https://docs.google.com/spreadsheets/d/1QlyMbAXxbiUrmJ0TH6HtAPaSJOrArEYKkrKtU2sWUb4/edit#gid=1402272001'

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


# Update week for next week and potentially update session for next session

with open("current_week.txt", "w") as file:
    file.write('')
    if current_week == 5:
        current_week = 0
        with open("current_session.txt", "w") as file2:
            file2.write('')
            current_session += 1
            if current_session == 5:
                current_session = 0
            file2.write(str(current_session))
    file.write(str(current_week))














        # response = aws_sns_client.publish(
        #     PhoneNumber = str(player['Phone']),
        #     Message = f"{player['Name']} sign up for vball nerd"
        # )
