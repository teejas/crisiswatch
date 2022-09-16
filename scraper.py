import requests
import os
import sys
from bs4 import BeautifulSoup
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID of the spreadsheet.
SPREADSHEET_ID = os.environ['SPREADSHEET_DB_ID']

# connect to google sheets api
creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

try:
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()

    pgidx = 1 # page index
    values = []
    while pgidx > 0:
        # URL to scrape
        url = "https://www.amnesty.org/en/latest/news/page/" + str(pgidx) + "/?qtopic=2066"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
        print(url)
        # Get the page
        page = requests.get(url, headers=headers)
        # Parse the page
        soup = BeautifulSoup(page.content, 'html.parser')

        post_list = soup.find(class_='postlist')
        if post_list is None:
            pgidx = -1
            break

        posts = post_list.find_all("article")
        if posts is None:
            pgidx = -1
            break

        for post in posts:
            print(post['aria-label'])
            print(post.find('a')['href'])
            for metadata in post.find_all('span', class_='post-meta'):
                if metadata['aria-label'] == "Post published date":
                    print(metadata.text)
                    dt_obj = datetime.strptime(metadata.text, '%B %d, %Y') # May 31, 2022
                    print(dt_obj)

            values.append([dt_obj.strftime('%Y-%m-%d'), post['aria-label'], post.find('a')['href']])

        pgidx += 1 # increment page index

    body = {
        'values': values
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, 
        range="A1:D" + str(len(values)+100),
        valueInputOption="USER_ENTERED",
        body=body).execute()
    print(f"{(result.get('updates').get('updatedCells'))} cells appended.")

except HttpError as err:
    print(err)