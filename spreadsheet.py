import sys
sys.path.append('./dependencies')
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import boto3
from botocore.exceptions import ClientError
import os


def run(event, context):
    # Connect to google spreadsheet API and establish E-Mail service

    scope = ['https://www.googleapis.com/auth/drive']
    creds_file = os.path.join('/tmp', 'virtual-equator-386019-d1063402b3b1.json')
    s3 = boto3.resource('s3')
    bucket_name = 'weekly-volleyball'
    object_key = 'virtual-equator-386019-d1063402b3b1.json'

    try:
        s3.Bucket(bucket_name).download_file(object_key, creds_file)
    except ClientError as e:
        print(e.response['Error']['Message'])

    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    # aws_sns_client = boto3.client('sns', region_name='us-east-1')
    aws_ses_client = boto3.client('ses', region_name = 'us-east-1')

    # Figure out what the current week is

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('volleyball_tracker')


    response = table.get_item(Key={'id': 'week_counter'})
    current_week = int(response['Item']['current_week'])
    if current_week >= 5:
        new_session = True
        current_week = 0
    else:
        new_session = False
    current_week += 1

    table.update_item(
        Key={'id': 'week_counter'},
        UpdateExpression='SET current_week = :val1',
        ExpressionAttributeValues={':val1': current_week}
        )
    
    # End update week function
    
    # Figure out what the current session is

    response = table.get_item(Key={'id': 'week_counter'})
    current_session = int(response['Item']['current_session'])

    if new_session:
        current_session += 1
    if current_session >= 5:
        current_session = 1

    table.update_item(
        Key={'id': 'week_counter'},
        UpdateExpression='SET current_session = :val1',
        ExpressionAttributeValues={':val1': current_session}
        )
    
    # Establish datasets

    sheet_name = 'Volleyball'
    worksheet_name = 'Early Summer'

    sheet = client.open(sheet_name)
    worksheet = sheet.worksheet(worksheet_name)

    volley_data = worksheet.get_all_records()

    player_data = sheet.worksheet('Player_db').get_all_records()

    # Figure out what the current week and date is



    current_date = volley_data[0][f'Week {current_week}:']

    # Loop through players and create a list of players that have not responded

    needs_to_respond = []

    for record in volley_data:
        if record[f'Week {current_week}:'] == '':
            playername = record['Players']
            needs_to_respond.append(playername.rstrip())


    # Loop through players and create a list of players that have responded yes

    yes_players = []

    for record in volley_data:
        if record[f'Week {current_week}:'] == 'Yes ':
            playername = record['Players']
            yes_players.append(playername.rstrip())

    # Loop through players and create a list of players that have responded no

    no_players = []

    for record in volley_data:
        if record[f'Week {current_week}:'] == 'No ':
            playername = record['Players']
            no_players.append(playername.rstrip())

    # Loop through players and send emails based on response status 

    # TODO: Make function get subject/body
    # Potentially make Email Service class
    for player in player_data:
        if player['Name'] in needs_to_respond:
            subject = 'Missing Volleyball Info'
            body = f'Tomorrow is {current_date}, week {current_week} of volleyball. Please respond on this spreadsheet if you can make it or not: https://docs.google.com/spreadsheets/d/1QlyMbAXxbiUrmJ0TH6HtAPaSJOrArEYKkrKtU2sWUb4/edit#gid=1402272001'
        elif player['Name'] in yes_players:
            subject = 'You signed up for Voleyball'
            body = f'Tomorrow is {current_date}, week {current_week} of volleyball. You are currently signed up as YES. Please respond on this spreadsheet if you can not make it, otherwise ignore this message :)   https://docs.google.com/spreadsheets/d/1QlyMbAXxbiUrmJ0TH6HtAPaSJOrArEYKkrKtU2sWUb4/edit#gid=1402272001'
        elif player['Name'] in no_players:
            subject = 'You are signed up as "No" for Volleyball'
            body = f'Tomorrow is {current_date}, week {current_week} of volleyball. You are currently signed up as NO. Please respond on this spreadsheet if you would like to change to YES, otherwise ignore this message :)    https://docs.google.com/spreadsheets/d/1QlyMbAXxbiUrmJ0TH6HtAPaSJOrArEYKkrKtU2sWUb4/edit#gid=1402272001'

        sender = 'leffeler@gmail.com'
        recepient = player['Email']
        
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
