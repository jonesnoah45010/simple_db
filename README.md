# Simple DB API
This API behaves like a simple, easy to use, JSON based database service.  
Users can save and later extract saved JSON data.  The MySQL database 
table in use is partitioned by the user_id and kept up to date on new users
via daily scheduled partition altering events.

# Initial Setup...
1. Open the example_env.txt file
2. Add your personal MySQL server credentials to example_env.txt
3. Rename example_env.txt to .env
4. Create python3.11 virtual environment
5. pip install -r requirements.txt
6. Open true_database.sql
7. Replace "YOUR_DATABASE_NAME" in true_database.sql with the database name you defined under SQL_NAME in .env
8. Create the simple_db and simple_db_users tables in your database by executing true_database.sql with your MySQL client
9. You will need to setup a google cloud console project to use the automated emails for account creation feature. Follow instructions below...


### Step 1: Create a Project in Google Cloud Console

1.  **Go to Google Cloud Console**: Visit the Google Cloud Console.
2.  **Create a New Project**:
    -   Click on the project dropdown at the top of the page.
    -   Click on "New Project".
    -   Enter a name for your project and, optionally, set a billing account.
    -   Click "Create".

### Step 2: Enable the Gmail API

1.  **Go to the API Library**:
    -   In the Google Cloud Console, navigate to the “APIs & Services” > “Library”.
2.  **Enable Gmail API**:
    -   In the API Library, search for "Gmail API".
    -   Click on "Gmail API" and then click on the "Enable" button.

### Step 3: Create OAuth 2.0 Credentials

1.  **Go to Credentials**:
    -   Navigate to “APIs & Services” > “Credentials”.
2.  **Create Credentials**:
    -   Click on "Create Credentials" and select "OAuth client ID".
3.  **Configure the OAuth Consent Screen**:
    -   If this is your first time setting up OAuth, you’ll be prompted to configure the consent screen.
    -   Select "External" and click "Create".
    -   Fill in the necessary details (application name, support email, etc.) and save.
4.  **Set up OAuth Client ID**:
    -   After configuring the consent screen, you’ll be directed back to the "Create OAuth client ID" page.
    -   Choose "Desktop app" as the application type.
    -   Click "Create".
    -   Download the `client_secret.json` file and save it as `send_email_creds.json` in the same directory as send_email.py


# Run Locally Using...
```sh
uvicorn app:app --reload
```

# To create an account...
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/create_account' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"username": "YOUR_USER_NAME","email": "YOUR_EMAIL@EMAIL.COM"}'
```

# To validate account and create perminent password...
You only have to do this once
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/validate_and_create_password' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"username":"YOUR_USER_NAME","temp_password":"YOUR_TEMP_PASSWORD","new_password":"YOUR_NEW_PASSWORD"}'
```

# If you forget your username...
You will recieve an email after POST with your username
```sh
curl -X POST 
  "http://localhost:8000/forgot_username" \
  -H "Content-Type: application/json" \
  -d '{"email": "YOUR_EMAIL@EMAIL.COM"}'

```

# If you forget your password...
You will recieve an email after POST with your temporary password
You will then need to go back through the /validate_and_create_password process
```sh
curl -X POST 
  "http://localhost:8000/forgot_password" \
  -H "Content-Type: application/json" \
  -d '{"email": "YOUR_EMAIL@EMAIL.COM"}'

```

# To generate a 24 hour access token...
You can generate as many as you want but they will always expire after 24 hours
```sh
curl -X 'GET' \
  'http://127.0.0.1:8000/get_session_token?username=<YOUR_USER_NAME>&password=<YOUR_PASSWORD_HERE>' \
  -H 'accept: application/json'
```

# Insert data using...
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/insert_data' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token_here>' \
  -H 'Content-Type: application/json' \
  -d '{"search_key": "key77","data": "{\"key_name\":\"value_name\"}"}'
```
... or ...
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/insert_data' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token_here>' \
  -H 'Content-Type: application/json' \
  -d '{"search_key": "key2","data": "{\"key_name\":1}"}'
```
... etc ...

# To insert data using Python...
```python
import requests
import json
url = "http://127.0.0.1:8000/insert_data"
my_dict = {"key_name": 2} # can be any dict structure
data = {"search_key": "search_key_name","data": json.dumps(my_dict)}
response = requests.post(url, json=data)
```


# Select data using...

if you know the exact day the entry was inserted..
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/select_data' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token_here>' \
  -H 'Content-Type: application/json' \
  -d '{"search_key": "key1","created_date":"2024-05-27"}'
```
... or if you just want to do a search of all entries...
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/select_data' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token_here>' \
  -H 'Content-Type: application/json' \
  -d '{"search_key": "key2"}'
```
... or if you know that the entry was inserted after a certain day...
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/select_data' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token_here>' \
  -H 'Content-Type: application/json' \
  -d '{"search_key": "key100","created_date_is_after":"2024-05-27"}'
```
... or if you know that the entry was inserted before a certain day ...
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/select_data' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token_here>' \
  -H 'Content-Type: application/json' \
  -d '{"search_key": "key100","created_date_is_before":"2024-06-03"}'
```
... or if you know that the entry was inserted within a range of days...
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/select_data' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token_here>' \
  -H 'Content-Type: application/json' \
  -d '{"search_key": "key100","created_date_is_after":"2024-05-27","created_date_is_before":"2024-06-03"}'
```

# To select data using Python...
```python
import requests
url = "http://127.0.0.1:8000/select_data"
data = {"search_key": "key3","created_date": "2023-05-27"}  
# created_date is optional but improves speed
response = requests.post(url, json=data)
selected_data = response.json()
```





