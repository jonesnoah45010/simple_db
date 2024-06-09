import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

SQL_HOST = os.getenv("SQL_HOST")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_NAME = os.getenv("SQL_NAME")


class sql_db:

	def __init__(self,host=SQL_HOST,user=SQL_USER,password=SQL_PASSWORD,name=SQL_NAME):
		self.host = host
		self.user = user
		self.password = password
		self.name = name
		self.db = None
		self.cursor = None
		connected = False
		counter = 0
		try:
			self.connect()
			connected = True
		except:
			while not connected:
				try:
					time.sleep(1)
					self.connect()
					connected = True
					print("SQL reconnect successful")
				except Exception as e:
					counter += 1
					if counter < 10:
						print(f"SQL connection failed {counter} times, re-attempting...")
					else:
						print("SQL failed to connect after 10 re-attempts do to issue...")
						print(e)
						return None

	def connect(self):
		# connects to the sql server
		self.db = mysql.connector.connect( 
		host = self.host, 
		user = self.user, 
		passwd = self.password,
		database = self.name
		)
		self.cursor = self.db.cursor(dictionary=True)

	def reset(self):
		# resets connection to the sql server
		self.cursor.close()
		self.db.close()
		self.connect()

	def close(self):
		# closes connection to the sql server
		self.cursor.close()
		self.db.close()

	def show_databases(self):
		# returns a list of all schemas in the database
		self.cursor.execute("SHOW DATABASES")
		result = self.cursor.fetchall()
		formatted = []
		for r in result:
			formatted.append(r[0])
		return formatted

	def query(self,q,commit=True):
		# runs query then commits, nothing returned
		self.cursor.execute(q)
		if commit:
			self.db.commit()

	def query_and_return(self,q):
		# runs query then returns values as list of tuples
		self.cursor.execute(q)
		return self.cursor.fetchall()

	def select_database(self,name):
		# switches to a new database
		self.connect(name)

	def commit(self):
		# commit changes made by queries
		self.db.commit()

	def show_tables(self):
		# returns a list of tables in current schema
		self.cursor.execute("SHOW TABLES")
		return self.cursor.fetchall()


	def select(self, table_name, where=None, columns=None):
		# fetches data from a given table
		# returns data as a list of dicts
		if columns is None:
			columns = "*"
		elif isinstance(columns, (list, tuple)):
			columns = ", ".join(columns)

		q = f"SELECT {columns} FROM {table_name}"
		params = ()
		if where:
			q += f" WHERE {where[0]}"
			params = where[1]

		self.cursor.execute(q, params)
		return self.cursor.fetchall()


	def insert(self, table_name, dicts=None):
		# inserts data into table
		# data to be inserted must be a list of dicts
		try:
			if isinstance(dicts, dict):
				dicts = [dicts]

			for chunk in [dicts[i:i + 10000] for i in range(0, len(dicts), 10000)]:
				header_list = list(chunk[0].keys())
				headers = ", ".join(header_list)
				placeholders = ", ".join(["%s"] * len(header_list))
				values = []

				for d in chunk:
					values.append(tuple(d.get(h) for h in header_list))

				q = f"INSERT INTO {table_name} ({headers}) VALUES ({placeholders})"
				self.cursor.executemany(q, values)
				self.db.commit()
		except Exception as e:
			print("SQL INSERT Error: " + str(e))

	def delete(self, table_name, where=None):
		# deletes from table given sql WHERE condition
		# deletes all data if where left as None
		if where is None:
			q = f"DELETE FROM {table_name} WHERE true"
			params = ()
		else:
			q = f"DELETE FROM {table_name} WHERE {where[0]}"
			params = where[1]

		self.cursor.execute(q, params)
		self.db.commit()



	def update(self, table_name, data, where=None):
		# updates data in a given table based on where condition
		# data should be a dictionary of column-value pairs to be updated
		try:
			set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
			params = list(data.values())

			q = f"UPDATE {table_name} SET {set_clause}"
			if where:
				q += f" WHERE {where[0]}"
				params.extend(where[1])

			self.cursor.execute(q, tuple(params))
			self.db.commit()
		except Exception as e:
			print("SQL UPDATE Error: " + str(e))











if __name__ == "__main__":

	db = sql_db()
	data = db.select("users")
	print("YOU JUST FETCHED THE USERS TABLE...")
	print(data[0])













