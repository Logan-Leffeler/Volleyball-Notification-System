import sys
sys.path.append('./dependencies')
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import boto3
from botocore.exceptions import ClientError
import os


def get_google_creds():
    scope = ['https://www.googleapis.com/auth/drive']
    creds_file = os.path.join('/tmp', 'virtual-equator-386019-d1063402b3b1.json')
    s3 = boto3.resource('s3')
    bucket_name = 'weekly-volleyball'
    object_key = 'virtual-equator-386019-d1063402b3b1.json'

    try:
        s3.Bucket(bucket_name).download_file(object_key, creds_file)
    except ClientError as e:
        print(e.response['Error']['Message'])

    return ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)


def get_worksheet_data(client, sheet_name, worksheet_name):
    sheet = client.open(sheet_name)
    worksheet = sheet.worksheet(worksheet_name)

    return worksheet.get_all_records()


def get_date(volley_data, current_week):
    current_date = volley_data[0][f'Week {current_week}:']
    return current_date


def get_player_responses(volley_data, current_week):
    needs_to_respond = []
    yes_players = []
    no_players = []

    for record in volley_data:
        if record[f'Week {current_week}:'] == '':
            playername = record['Players']
            needs_to_respond.append(playername.rstrip())
        elif record[f'Week {current_week}:'] == 'Yes ':
            playername = record['Players']
            yes_players.append(playername.rstrip())
        elif record[f'Week {current_week}:'] == 'No ':
            playername = record['Players']
            no_players.append(playername.rstrip())

    return needs_to_respond, yes_players, no_players


def send_email(aws_ses_client, player_data, needs_to_respond, yes_players, no_players, current_date, current_week):
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
        message={
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text': {
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
  

def update_week(dynamodb):
    table = dynamodb.Table('volleyball_tracker')

    response = table.get_item(Key={'id': 'week_counter'})
    current_week = int(response['Item']['current_week'])

    if current_week >= 5:
        current_week = 0

    current_week += 1
    table.update_item(
        Key={'id': 'week_counter'},
        UpdateExpression='SET current_week = :val1',
        ExpressionAttributeValues={':val1': current_week}
    )
    return current_week


def run(event, context):
    print("Pancakes")
    creds = get_google_creds()
    client = gspread.authorize(creds)
    aws_ses_client = boto3.client('ses', region_name = 'us-east-1')
    dynamodb = boto3.resource('dynamodb')
    current_week = update_week(dynamodb)
    sheet_name = 'Volleyball'
    worksheet_name = 'Early Summer'
    player_sheet = "Player_db"
    volley_data = get_worksheet_data(client, sheet_name, worksheet_name)
    player_data = get_worksheet_data(client, sheet_name, player_sheet)
    current_date = get_date(volley_data, current_week)
    needs_to_respond, yes_players, no_players = get_player_responses(volley_data, current_week)
    send_email(aws_ses_client, player_data, needs_to_respond, yes_players, no_players, current_date, current_week)




