import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import pickle

def get_service():
    creds = None
    if os.path.exists('send_email_token.pickle'):
        with open('send_email_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # creds.refresh()
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'send_email_creds.json', ['https://www.googleapis.com/auth/gmail.send'])
            creds = flow.run_local_server(port=8080)
        with open('send_email_token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

def send_email(SENDER, RECIPIENT, SUBJECT, MESSAGE_TEXT,user_id = "me"):
    service = get_service()
    message = create_message(SENDER, RECIPIENT, SUBJECT, MESSAGE_TEXT)
    message = service.users().messages().send(userId=user_id, body=message).execute()
    return message



if __name__ == "__main__":
    SENDER = 'your_email@gmail.com'
    RECIPIENT = 'your_email@gmail.com'
    SUBJECT = 'TEST'
    MESSAGE_TEXT = 'Hello, this is a test email.'
    send_email(SENDER, RECIPIENT, SUBJECT, MESSAGE_TEXT)








