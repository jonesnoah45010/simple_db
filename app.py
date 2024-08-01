from fastapi import FastAPI, HTTPException, Response, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import json
from sql_connection import sql_db
from datetime import datetime, timezone, timedelta
from send_email import send_email
from password_manager import hash_password, check_password, generate_password
import os
from jose import JWTError, jwt
import traceback

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/get_session_token")
app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # Allows all origins
	allow_credentials=True,
	allow_methods=["*"],  # Allows all methods
	allow_headers=["*"],  # Allows all headers
)


templates = Jinja2Templates(directory="templates")



class ForgotUsernameItem(BaseModel):
	email: str
class ForgotPasswordItem(BaseModel):
	email: str
class ValidateAccountItem(BaseModel):
	username: str
	temp_password: str
	new_password: str
class CreateAccountItem(BaseModel):
	username: str
	email: str
class InsertItem(BaseModel):
	search_key: str = Field(..., example="your_search_key")
	data: str = Field(..., example="{'key1':'value1','key2':'value2'}")
class SelectItem(BaseModel):
	search_key: str = Field(..., example="your_search_key")
class DeleteEntryItem(BaseModel):
	search_key: str = Field(..., example="your_search_key")
class UpdateEntryItem(BaseModel):
	search_key: str = Field(..., example="your_search_key")
	new_entry: str = Field(..., example="{'key1':'new_value1','key2':'new_value2'}")
class Token(BaseModel):
	access_token: str
	token_type: str
class TokenData(BaseModel):
	username: Optional[str] = None
class User(BaseModel):
	username: str
	email: Optional[str] = None
	is_validated: Optional[bool] = None
class UserInDB(User):
	hashed_password: str

def get_user(username: str, db = None):
	if db is None:
		db = sql_db()
	user_data = db.select("simple_db_users",("username = %s", (username,)))
	db.close()
	if len(user_data) > 0:
		user_data = user_data[0]
		return user_data
	else:
		return None

def authenticate_user(username: str, password: str, db = None):
	if db is None:
		user = get_user(username)
	else:
		user = get_user(username,db)
	if not user:
		return False
	if not check_password(user["password"], password):
		return False
	return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
	to_encode = data.copy()
	if expires_delta:
		expire = datetime.utcnow() + expires_delta
	else:
		expire = datetime.utcnow() + timedelta(minutes=15)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username: str = payload.get("sub")
		if username is None:
			raise credentials_exception
		token_data = TokenData(username=username)
	except JWTError:
		raise credentials_exception
	user = get_user(username=token_data.username)
	if user is None:
		raise credentials_exception
	return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
	if str(current_user["is_validated"]) == "0":
		raise HTTPException(status_code=400, detail="Inactive user")
	return current_user

def current_utc_date():
	now_utc = datetime.now(timezone.utc)
	formatted_date = now_utc.strftime("%Y-%m-%d")
	return formatted_date










@app.post("/create_account")
def create_account(item: CreateAccountItem, response: Response):
	d = item.dict()
	db = sql_db()
	where_statement = ("username = %s", (d["username"],))
	existing = db.select("simple_db_users",where_statement)
	if len(existing) > 0:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="username is already in use"
		)
	temp_password = generate_password()
	SENDER = os.getenv("GMAIL_ACCOUNT")
	RECIPIENT = d["email"]
	SUBJECT = 'simple_db account created'
	activation_page_link = str(os.getenv("SERVICE_URL")) + '/activate_user_form?username=' + str(d["username"])
	MESSAGE_TEXT = (
	'Thank you for creating a simple_db account under the username ' + d["username"] + 
	'. Your temporary password is ' + temp_password + 
	'\n You must set a new perminent password in order to activate your account. ' 
	'Please activate your account using the link below...' + '\n' + activation_page_link
	)
	send_email(SENDER, RECIPIENT, SUBJECT, MESSAGE_TEXT)
	to_insert = eval(repr(d))
	to_insert["password"] = hash_password(temp_password)
	to_insert["is_validated"] = 0
	db.insert("simple_db_users",[to_insert])
	db.insert("simple_db_temp_passwords",[{"username":to_insert["username"],"password":to_insert["password"]}])
	db.close()
	response.status_code = status.HTTP_200_OK
	return {"message":"successfully created account " + to_insert["username"] + ", check your email for temporary password"}




@app.get("/activate_user_form", response_class=HTMLResponse)
async def activate_user_form(request: Request, username: Optional[str] = None):
    return templates.TemplateResponse("index.html", {"request": request, "username": username})




@app.post("/validate_and_create_password")
def validate_and_create_password(item: ValidateAccountItem, response: Response):
	d = item.dict()
	# print("validate_and_create_password " + str(d))
	db = sql_db()
	user_data = db.select("simple_db_users",("username = %s", (d["username"],)))
	user_temp_password = db.select("simple_db_temp_passwords",("username = %s", (d["username"],)))

	# print("validate_and_create_password user_data " + str(user_data))
	# print("validate_and_create_password user_temp_password " + str(user_temp_password))

	if len(user_data) > 0:
		user_data = user_data[0]
	else:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Username not found"
		)
	if len(user_temp_password) > 0:
		user_temp_password = user_temp_password[0]
	else:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Username temporary password not found"
		)
	# print("validate_and_create_password check_password " + str(check_password(hashed_password = user_temp_password["password"], user_password = d["temp_password"])))
	if not check_password(hashed_password = user_temp_password["password"], user_password = d["temp_password"]):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect temp_password"
		)
	update_data = {
	"is_validated": 1,
	"password": hash_password(d["new_password"])
	}
	where_condition = ("username = %s", (d["username"],))
	db.update("simple_db_users", update_data, where_condition)
	db.delete("simple_db_temp_passwords",where_condition)
	db.close()
	response.status_code = status.HTTP_200_OK
	return {"message":"your accound has been activated and your password reset"}

@app.post("/forgot_username")
def forgot_username(item: ForgotUsernameItem, response: Response):
	d = item.dict()
	db = sql_db()
	user_data = db.select("simple_db_users",("email = %s", (d["email"],)))
	if len(user_data) > 0:
		user_data = user_data[0]
	else:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Username not found"
		)
	SENDER = os.getenv("GMAIL_ACCOUNT")
	RECIPIENT = d["email"]
	SUBJECT = 'simple_db forgot username'
	MESSAGE_TEXT = 'Thank you for using simple_db, your username is ' + str(user_data["username"])
	send_email(SENDER, RECIPIENT, SUBJECT, MESSAGE_TEXT)
	db.close()
	response.status_code = status.HTTP_200_OK
	return {"message":"email with your username was sent to " + str(d["email"])}

@app.post("/forgot_password")
def forgot_password(item: ForgotPasswordItem, response: Response):
	d = item.dict()
	db = sql_db()
	user_data = db.select("simple_db_users",("email = %s", (d["email"],)))
	if len(user_data) > 0:
		user_data = user_data[0]
	else:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Username not found"
		)
	temp_password = generate_password()
	SENDER = os.getenv("GMAIL_ACCOUNT")
	RECIPIENT = d["email"]
	SUBJECT = 'simple_db forgot password'
	MESSAGE_TEXT = (
	'Thank you for using simple_db account under the username ' + user_data["username"] + 
	'. Your new temporary password is ' + temp_password + 
	'\nYou must set a new perminent password in order to re-activate your account. ' 
	'You should send the HTTP POST request JSON \n'
	'{"username":"' + user_data["username"] + '","temp_password":"' + temp_password + '","new_password":"YOUR_NEW_PASSWORD"}' 
	' \nto the /validate_and_create_password endpoint of the simple_db API'
	)
	send_email(SENDER, RECIPIENT, SUBJECT, MESSAGE_TEXT)
	data_to_update = {}
	data_to_update["password"] = hash_password(temp_password)
	data_to_update["is_validated"] = 0
	where_condition = ("username = %s", (user_data["username"],)) 
	db.delete("simple_db_temp_passwords",where_condition)
	db.insert("simple_db_temp_passwords",[{"username":user_data["username"],"password":data_to_update["password"]}])
	db.close()
	response.status_code = status.HTTP_200_OK
	return {"message":"email with your new temporary password was sent to " + str(d["email"])}


@app.post("/get_session_token", response_model=Token)
async def get_session_token(form_data: OAuth2PasswordRequestForm = Depends()):
	user = authenticate_user(form_data.username, form_data.password)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"},
		)
	access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	access_token = create_access_token(
		data={"sub": user["username"]}, expires_delta=access_token_expires
	)
	return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
	return current_user

@app.post("/delete_account")
def delete_account(response: Response, current_user: User = Depends(get_current_active_user)):
	db = sql_db()
	username = current_user["username"]
	where_condition = ("username = %s", (current_user["username"],)) 
	db.delete("simple_db_temp_passwords",where_condition)
	db.delete("simple_db_users",where_condition)
	where_condition = ("user_id = %s", (current_user["username"],))
	db.delete("simple_db",where_condition)
	db.close()
	response.status_code = status.HTTP_200_OK
	return {"message":"successful deleted account " + str(username)}

@app.post("/insert_data")
def insert_data(item: InsertItem, response: Response, current_user: User = Depends(get_current_active_user)):
	try:
		db = sql_db()
		d = item.dict()
		print("INSERTING DATA " + str(d))
		d["data"] = d["data"].replace("'",'"')
		d["user_id"] = current_user["username"]
		db.insert("simple_db",[d])
		db.close()
		response.status_code = status.HTTP_200_OK
		return {"message":"successful insert"}
	except:
		stack_trace = traceback.format_exc()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=stack_trace
		)

@app.post("/select_data")
def select_data(item: SelectItem, response: Response, current_user: User = Depends(get_current_active_user)):
	try:
		db = sql_db()
		d = item.dict()
		d["user_id"] = current_user["username"]
		using_created_date = False
		where_statement = ("user_id = %s and search_key = %s", (current_user["username"],d["search_key"]))
		data = db.select("simple_db",where=where_statement)
		send_back = []
		for item in data:
			new_item = {}
			new_item["created_at"] = item["created_at"]
			new_item["data"] = json.loads(item["data"])
			send_back.append(new_item)
		db.close()
		response.status_code = status.HTTP_200_OK
		return {"results":send_back}
	except:
		stack_trace = traceback.format_exc()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=stack_trace
		)

@app.post("/delete_entry")
def delete_entry(item: DeleteEntryItem, response: Response, current_user: User = Depends(get_current_active_user)):
	db = sql_db()
	d = item.dict()
	where_statement = ("user_id = %s and search_key = %s", (current_user["username"],d["search_key"]))
	data = db.select("simple_db",where=where_statement)
	if len(data) > 0:
		where_condition = ("search_key = %s", (d["search_key"],)) 
		db.delete("simple_db",where_condition)
		db.close()
		return {"message":"entry was deleted with search_key " + str(d["search_key"])}
	else:
		response.status_code = status.HTTP_200_OK
		db.close()
		return {"message":"no data was deleted for search_key " + str(d["search_key"])}

@app.post("/update_entry")
def update_entry(item: UpdateEntryItem, response: Response, current_user: User = Depends(get_current_active_user)):
	db = sql_db()
	d = item.dict()
	where_statement = ("user_id = %s and search_key = %s", (current_user["username"],d["search_key"]))
	data = db.select("simple_db",where=where_statement)
	if len(data) > 0:
		update_data = {
		"search_key": d["search_key"],
		"data": d["new_entry"]
		}
		where_condition = ("username = %s and search_key = %s", (current_user["username"],d["search_key"]))
		db.update("simple_db", update_data, where_condition)
		db.close()
		return {"message":"entry was updated for search_key " + str(d["search_key"])}
	else:
		response.status_code = status.HTTP_200_OK
		db.close()
		return {"message":"no data was updated for search_key " + str(d["search_key"])}





if __name__ == "__main__":
	uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv('PORT', 8080)))

























