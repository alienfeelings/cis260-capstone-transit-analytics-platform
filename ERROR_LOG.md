Issues pushing to GitHub
=========================
ERROR:\
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
-----------------
SOLUTION:\
Open PowerShell as Administrator and run:
Get-Service ssh-agent

If it shows Stopped, run:\
Set-Service -Name ssh-agent -StartupType Automatic\
Start-Service ssh-agent

Then verify: Get-Service ssh-agent

You want:

Status   Name
------   ----
Running  ssh-agent

After that, back to PyCharm terminal:\
ssh-add $HOME\.ssh\"your-ssh-key"

Then: ssh-add -l

Test GitHub: ssh -T git@github.com

You're ready to push!


Decimal formatting
==========
two decimal points ==> :.2f\
Ex. ==> print(f"{delayed_percent:.2f}% of vehicles are delayed")



Error running create_schema.py
============
ERROR:\
Traceback (most recent call last):
  File "C:\Users\kahnm\PycharmProjects\cis260-capstone-transit-analytics-platform\database\create_schema.py", line 58, in <module>
    create_schema()\
  File "C:\Users\kahnm\PycharmProjects\cis260-capstone-transit-analytics-platform\database\create_schema.py", line 17, in create_schema
    connection = psycopg.connect(
                 ^^^^^^^^^^^^^^^^ \
  File "C:\Users\kahnm\PycharmProjects\cis260-capstone-transit-analytics-platform\.venv\Lib\site-packages\psycopg\connection.py", line 126, in connect
    raise last_ex.with_traceback(None) \
psycopg.OperationalError: connection failed: connection to server at "localhost" (::1), port 5432 failed: fe_sendauth: no password supplied \

SOLUTION:\
Make sure nomenclature both in .env and files are the same

TIMESTAMPTZ
=======
TIMESTAMPTZ is short for TIMESTAMP WITH TIME ZONE


Issues loading GTFS
======
ERROR:\
Connected to database: mbta_pipeline
Connecting to PostgreSQL...
Connected.
Database: mbta_pipeline
Schema: public

Tables found:

Clearing existing GTFS data...

GTFS load failed. Changes rolled back.
Traceback (most recent call last):
  File "C:\Users\kahnm\PycharmProjects\cis260-capstone-transit-analytics-platform\ingestion\static\load_gtfs.py", line 331, in <module>
    load_gtfs()
  File "C:\Users\kahnm\PycharmProjects\cis260-capstone-transit-analytics-platform\ingestion\static\load_gtfs.py", line 303, in load_gtfs
    cursor.execute("""
  File "C:\Users\kahnm\PycharmProjects\cis260-capstone-transit-analytics-platform\.venv\Lib\site-packages\psycopg\cursor.py", line 117, in execute
    raise ex.with_traceback(None)
psycopg.errors.UndefinedTable: relation "stop_times" does not exist

SOLUTION:\
Check indentation and file structure in create_schema file, run diagnostic print statements,


pgAdmin password issues
=======
If password issues arise, right-click pg server > clear saved password>\
    right-click server again > reconnect > enter password

String indices when cleaning dictionaries
================
ERROR:\
Traceback (most recent call last):
  File "C:\Users\kahnm\PycharmProjects\data-engineering-practice\week_01\day_03_python.py", line 50, in <module>
    if v["vehicle_id"] is not None:
       ~^^^^^^^^^^^^^^
TypeError: string indices must be integers, not 'str'

SOLUTION:\
Check you're calling the entire list, not just the first index 
when reassigning dict/list names. Ex. mv = messy_vehicles[0]
Should be mv = messy_vehicles

Fetching dict values with .get() vs dict["value"]
========
You can use .get() if fetching straight from a dict.
If fetching from a list, you'd need dict[0].get("value"),
because vehicles[0] is the 1st dict in the list.\
Useful structure:\
dict  → .get("key")\
list  → [index] or loop through it\
str   → string methods, not .get()\
None  → cannot use .get()\
----------
Why use {} as the second argument?\
Because .get() can take a default value:\
dictionary.get("key", default_value)\
attributes = vehicle.get("attributes", {}) --> means:\
Get "attributes". If it doesn't exist, give me an empty dictionary instead.
