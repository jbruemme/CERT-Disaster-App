import datetime as dt
import os
import sqlite3
import pandas as pd
import re

"""
Global Variables
"""
# Database connection
db_connection = None

# Column headers for import/export files and SQL households table
CSV_COLUMNS = [
    "address",
    "adults",
    "children",
    "pets",
    "dogs",
    "critical_meds",
    "meds_need_refrigerated",
    "has_special_needs",
    "has_propane_tank",
    "has_natural_gas",
    "phone",
    "email",
    "has_medical_training",
    "know_neighbors",
    "has_neighbors_key",
    "wants_newsletter",
    "can_cert_contact",
]

#=======================================================================================================================

"""
Helper Functions
"""

# Address formatting using regex
ADDRESS_REGEX = re.compile(
    r"^\d+\s+.+,\s*[A-Za-z .]+,\s*[A-Z]{2}\s+\d{5}$"
)

# Phone formatting using regex
PHONE_REGEX = re.compile(
    r"^\s*(\(\d{3}\)|\d{3})[-\s.]?\d{3}[-\s.]?\d{4}\s*$"
)

# Email formatting using regex
EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

"""
Helper function to validate address
1. Validates that the given address matches the regex formatting
2. Validates digits only for house number.
3. Validates any characters until comma for street name.
4. Validates letters, spaces, dots until comma for city.
5. Validates exactly 2 uppercase letters for state
6. validates exactly 5 digits for zip.
7. Validates number street, city, state zip order
"""
def validate_address(address):
    return bool(ADDRESS_REGEX.match(address))


"""
Helper function to validate phone number
1. Validates '3 digits - 3 digits - 4 digits'
"""
def validate_phone(phone):
    if pd.isna(phone) or str(phone).strip() == "":
        return True
    return bool(PHONE_REGEX.match(phone))

"""
Helper function to validate email address
1. Validates '@' and '.domain'
"""
def validate_email(email):
    if pd.isna(email) or str(email).strip() == "":
        return True
    return bool(EMAIL_REGEX.match(email))

"""
Helper function to convert all boolean data inputs to binary boolean (1 = true, 0 = false) so they can properly be saved
to the database.
"""
def boolean_converter(csv_boolean_data):
    return csv_boolean_data.astype(str).str.strip().str.lower().map({
        "yes": 1, "y": 1, "true": 1, "1": 1,
        "no": 0, "n": 0, "false": 0, "0": 0,
        "": None, "nan": None
    })

"""
Helper function to setup the database.
"""
def db_setup():
    global db_connection
    db_connection = sqlite3.connect('cert_disaster.db')
    init_db(db_connection)

"""
Helper function for prompting/validating user input for updating a record
1. Checks for value type to perform validation for boolean, integer and string data
2. Creates the user prompt and validates their input
3. Returns the user input once validated
"""
def edit_prompt_and_validation(prompt, current_value, value_type, mandatory=False):

    # Convert boolean values to yes/no for prompting user, blank if current_prompt is none
    if value_type == "bool":
        if current_value is None:
            current_prompt = ""
        elif current_value == 1:
            current_prompt = "yes"
        elif current_value == 0:
            current_prompt = "no"
        else:
            current_prompt = ""
    else:
        current_prompt = "" if current_value is None else current_value

    while True:
        # Prompt user for new value while showing current value
        if value_type == "bool":
            input_value = input(f"{prompt} = {current_prompt} (yes/no): ").strip().lower()
        else:
            input_value = input(f"{prompt} = {current_prompt}: ").strip()

        # If no input keep the current value, if input is mandatory make sure user enters input
        if input_value == "":
            if mandatory:
                print(f"{prompt} is mandatory. Please enter a value.")
                continue
            return current_value

        # Validating user input for boolean fields
        if value_type == "bool":
            if input_value in ["yes", "y", "true", "1"]:
                return 1
            if input_value in ["no", "n", "false", "0"]:
                return 0
            print("Please enter yes/no.")
            continue

        # Validating user input for integer fields
        if value_type == "int":
            if input_value.isdigit():
                return int(input_value)
            print("Please enter an integer.")
            continue

        # Validating user input for address
        if value_type == "str":
            if prompt.lower() == "address":
                if not validate_address(input_value):
                    print("Invalid address format, try again, must be this format: <number> <street name>, <City>, <ST> <zip code>")
                    continue

            # Validating user input for phone
            if prompt.lower() == "phone number":
                if not validate_phone(input_value):
                    print("Invalid phone format, try again, must be this format: 123-123-1234")
                    continue

            # Validating user input for email
            if prompt.lower() == "email address":
                if not validate_email(input_value):
                    print("Invalid email format, try again, must be this format: test@test.domain")
                    continue

            return input_value

# ======================================================================================================================

"""
Primary Functions
"""

"""
Function to initialize the application database
1. Initializes connection
2. Creates the households table to store all survey data for a household
"""
def init_db(connection):
    connection.execute('''
        CREATE TABLE IF NOT EXISTS households (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            adults INTEGER NOT NULL,
            children INTEGER NOT NULL,
            pets INTEGER NOT NULL,
            dogs INTEGER,
            critical_meds INTEGER NOT NULL,
            meds_need_refrigerated INTEGER,
            has_special_needs INTEGER NOT NULL,
            has_propane_tank INTEGER NOT NULL,
            has_natural_gas INTEGER NOT NULL,
            phone TEXT,
            email TEXT,
            has_medical_training INTEGER,
            know_neighbors INTEGER,
            has_neighbors_key INTEGER,
            wants_newsletter INTEGER,
            can_cert_contact INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    ''')

"""
Function to import and validate csv files
1. Prompts user for filepath to their csv
2. Validates that all necessary column headers are correctly labeled in the csv
3. Validates that input file address is properly formatted
4. Validates that adult and children values are Integers
5. Validates that all boolean data is of type Integer where 1 = true and 0 = false
"""
def import_csv (connection):

    # Ensure the database was initialized before continuing
    if connection is None:
        print("ERROR: Database not initialized.")
        return

    # Prompt user for import file path
    file_path = input("Please enter path to your CSV file: ").strip()
    if not file_path:
        print("No file path provided, returning to main menu.\n")
        return

    # Read the input file and store as a Panda's dataframe
    try:
        input_df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading file: {e}\n")
        return

    # Validate the imported csv has all necessary data columns
    missing_columns = [column for column in CSV_COLUMNS if column not in input_df.columns]
    if missing_columns:
        print("Missing required columns: ", missing_columns)
        print("\nUnable to import csv file.\n")
        return

    # Validating address formatting
    input_df["valid_address"] = input_df["address"].apply(validate_address)
    invalid = input_df[~input_df["valid_address"]]
    if not invalid.empty:
        print("Address is not properly formatted: ", invalid[["address"]])
        print("\nUnable to import csv file.\n")
        return

    # Validating phone formatting
    input_df["valid_phone"] = input_df["phone"].apply(validate_phone)
    invalid = input_df[~input_df["valid_phone"]]
    if not invalid.empty:
        print("Phone is not properly formatted: ", invalid[["phone"]])
        print("\nUnable to import csv file.\n")
        return

    # Validating email formatting
    input_df["valid_email"] = input_df["email"].apply(validate_email)
    invalid = input_df[~input_df["valid_email"]]
    if not invalid.empty:
        print("Email is not properly formatted: ", invalid[["email"]])
        print("\nUnable to import csv file.\n")
        return

    # Validating and converting adult and children columns to integer values
    try:
        input_df["adults"] = pd.to_numeric(input_df["adults"], errors="raise")
        input_df["children"] = pd.to_numeric(input_df["children"], errors="raise")
    except Exception as e:
        print(f"Adults/Children not properly formatted: {e}")
        print("\nUnable to import csv file.\n")
        return

    # Converting boolean csv data to binary integer values
    boolean_data = [
        "pets", "dogs", "critical_meds", "meds_need_refrigerated", "has_special_needs", "has_propane_tank",
        "has_natural_gas", "has_medical_training", "know_neighbors", "has_neighbors_key", "wants_newsletter",
        "can_cert_contact"
    ]
    for column in boolean_data:
        input_df[column] = boolean_converter(input_df[column])

    # Validating that dogs is blank if pets is 0
    invalid_dogs_input = input_df[(input_df["pets"] == 0) & (input_df["dogs"].notna())]
    if not invalid_dogs_input.empty:
        print("Invalid rows: dogs provided but pets = no:")
        print(invalid_dogs_input[["pets", "dogs"]])
        print("\nUnable to import csv file.\n")
        return

    # Validating that meds_need_refrigerated is blank if critical_meds is 0.
    invalid_refrigerated_meds_input = input_df[(input_df["critical_meds"] == 0) & (input_df["meds_need_refrigerated"].notna())]
    if not invalid_refrigerated_meds_input.empty:
        print("Invalid rows: refrigerated meds given but critical meds = no:")
        print(invalid_refrigerated_meds_input[["critical_meds", "meds_need_refrigerated"]])
        print("\nUnable to import csv file.\n")
        return

    # Updating the created and updated timestamp for the csv file, both should be the current time because this is the
    # initial creation of the file into the database.
    time_stamp = dt.datetime.now().isoformat(timespec="seconds")
    input_df["created_at"] = time_stamp
    input_df["updated_at"] = time_stamp

    # Preparing the csv data to be inserted into the database
    csv_data = input_df[[
        "address", "adults", "children", "pets", "dogs", "critical_meds", "meds_need_refrigerated", "has_special_needs",
        "has_propane_tank", "has_natural_gas", "phone", "email", "has_medical_training", "know_neighbors",
        "has_neighbors_key", "wants_newsletter", "can_cert_contact", "created_at", "updated_at"
    ]].values.tolist()

    # Insert imported csv file data into the database
    connection.executemany("""
        INSERT INTO households (
        address, adults, children, pets, dogs, critical_meds, meds_need_refrigerated, has_special_needs, has_propane_tank,
        has_natural_gas, phone, email, has_medical_training, know_neighbors, has_neighbors_key, wants_newsletter,
        can_cert_contact, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, csv_data)
    connection.commit()

    print("Successfully imported csv file.\n")


"""
Function to export all data from the database as a csv file
1. Saves all data into a pandas dataframe using an SQL query
2. Generates the time stamp, output path, and file name (output/Exported Records - {time_stamp}.csv)
3. Converts the dataframe to csv and exports it to the file path.
"""
def export_csv(connection):

    # Making sure the exported csv is being saved to the output directory
    directory = "output"
    os.makedirs(directory, exist_ok=True)

    # Creating the output file name with a timestamp
    time_stamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"Exported Records - {time_stamp}.csv"

    # Creating full filepath with the directory and file name
    path = os.path.join(directory, file_name)

    try:
        # Saving all data rows into a pandas dataframe and export it as a csv file using the path variable
        output_df = pd.read_sql_query("SELECT * FROM households;", connection)
        output_df.to_csv(path, index=False)
        print("Successfully exported csv file.\n")
    except Exception as e:
        print(f"Error exporting file: {e}\n")

"""
Function to view all records in the database
1. Get all records from database using SQL query and put into pandas dataframe
2. Display the records
3. Prompt user for record id input and send to edit_record function
"""
def view_records(connection):

    # Save all records into a pandas dataframe
    records_df = pd.read_sql_query("SELECT id, address FROM households ORDER BY id;", connection).reset_index(drop=True)

    # Check if the database is empty
    if records_df.empty:
        print("There are no records in the database.\n")
        return

    while True:
        # Display all records in the database
        print("\n==== Cert Disaster Records ====\n")
        for i, row in enumerate(records_df.itertuples(), start = 1):
            print(f"{i}: {row.address}")

        # Get user input and determine next actions
        choice = input("\nSelect a record number to edit or press enter with no input to return to main menu: \n").strip()
        if choice == "":
            return
        if not choice.isdigit():
            print("\nPlease enter a valid record number or press enter with no input to return to the main menu: .\n")
            continue
        choice_int = int(choice)
        if not 1 <= choice_int <= len(records_df):
            print("\nPlease enter a valid record number or press enter with no input to return to the manin menu: .\n")
            continue

        # Valid id entered load the record for editing
        selected_id = int(records_df.at[choice_int - 1, "id"])
        print(f"\nSelected ID: {selected_id}, loading for editing..\n")
        edit_record(connection, selected_id)

"""
Function to edit a specific record
1. Grabs the row data for a record id using SQL query and stores it into a pandas dataframe
2. Checks to make sure the dataframe isn't empty
3. Prompts user to update each piece of data one at a time while displaying the current data
4. Sends user input to the edit_prompt_and_validate function to validate the input before continuing
5. Pushes all updates to the database using an SQL query
"""
def edit_record(connection, record_id):

    # Save the selected record into a pandas dataframe
    edit_df = pd.read_sql_query("SELECT * FROM households WHERE id=?;", connection, params=(record_id,))

    # Check to make sure we actually have the data before performing changes
    if edit_df.empty:
        print("The record you selected was not found.")
        return

    # Getting the series of data from the data frame and saving the updated records as a dictionary (prompts and updated values)
    series = edit_df.iloc[0]
    updated_record = {}

    print(f"\n==== Editing Record: {record_id} ====\n")

    # Mandatory questions
    updated_record["address"] = edit_prompt_and_validation("Address", series["address"], "str")
    updated_record["adults"] = edit_prompt_and_validation("Number of adults", series["adults"], "int")
    updated_record["children"] = edit_prompt_and_validation(
        "Number of children", series["children"], "int")

    # Mandatory pet and followup dog questions
    updated_record["pets"] = edit_prompt_and_validation("Any pets?", series["pets"], "bool")
    if updated_record["pets"] == 1:
        updated_record["dogs"] = edit_prompt_and_validation("Any dogs?", series["dogs"], "bool")
    else:
        updated_record["dogs"] = None

    # Mandatory meds and followup refrigerated questions
    updated_record["critical_meds"] = edit_prompt_and_validation(
        "Any critical meds?", series["critical_meds"], "bool")
    # Followup question
    if updated_record["critical_meds"] == 1:
        updated_record["meds_need_refrigerated"] = edit_prompt_and_validation(
            "Medication needs to be refrigerated?",
            series["meds_need_refrigerated"],
            "bool")
    else:
        updated_record["meds_need_refrigerated"] = None

    # Mandatory questions
    updated_record["has_special_needs"] = edit_prompt_and_validation(
        "Special needs?", series["has_special_needs"], "bool")

    updated_record["has_propane_tank"] = edit_prompt_and_validation(
        "Large propane tank?", series["has_propane_tank"], "bool")

    updated_record["has_natural_gas"] = edit_prompt_and_validation(
        "Natural gas connection?", series["has_natural_gas"], "bool")

    # Optional questions
    updated_record["phone"] = edit_prompt_and_validation("Phone number", series["phone"], "str")
    updated_record["email"] = edit_prompt_and_validation("Email address", series["email"], "str")
    updated_record["has_medical_training"] = edit_prompt_and_validation(
        "Any Medical training?", series["has_medical_training"], "bool")
    updated_record["know_neighbors"] = edit_prompt_and_validation(
        "Know neighbors?", series["know_neighbors"], "bool")
    updated_record["has_neighbors_key"] = edit_prompt_and_validation(
        "Have neighbor's key?", series["has_neighbors_key"], "bool")
    updated_record["wants_newsletter"] = edit_prompt_and_validation(
        "CERT newsletter?", series["wants_newsletter"], "bool")
    updated_record["can_cert_contact"] = edit_prompt_and_validation(
        "Allow CERT non-disaster contact?", series["can_cert_contact"],"bool")

    # Timestamp
    updated_record["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")

    # I was getting blob values in my database converting panda values to native values to fix
    for key, value in updated_record.items():
        if pd.isna(value):
            updated_record[key] = None
            continue
        if hasattr(value, "item"):
            updated_record[key] = value.item()

    # Update the record in the database
    edits = ", ".join(f"{col} = ?" for col in updated_record.keys())
    query = f"UPDATE households SET {edits} WHERE id = ?;"
    connection.execute(query, list(updated_record.values()) + [record_id])
    connection.commit()

    print("Successfully edited record.\n")


def add_record(connection):

    print(f"\n==== Adding Record ====\n")

    new_record = {}

    # Mandatory questions
    new_record["address"] = edit_prompt_and_validation("Address","","str", mandatory=True)
    new_record["adults"] = edit_prompt_and_validation("Number of adults","","int", mandatory=True)
    new_record["children"] = edit_prompt_and_validation("Number of children","","int", mandatory=True)

    # Mandatory pet and followup dog questions
    new_record["pets"] = edit_prompt_and_validation("Any pets?","","bool", mandatory=True)
    if new_record["pets"] == 1:
        new_record["dogs"] = edit_prompt_and_validation("Any dogs?","","bool")
    else:
        new_record["dogs"] = None

    # Mandatory meds and followup refrigerated questions
    new_record["critical_meds"] = edit_prompt_and_validation("Any critical meds?","","bool", mandatory=True)
    if new_record["critical_meds"] == 1:
        new_record["meds_need_refrigerated"] = edit_prompt_and_validation(
            "Medication needs to be refrigerated?",
            "",
            "bool"
        )
    else:
        new_record["meds_need_refrigerated"] = None

    # Mandatory questions
    new_record["has_special_needs"] = edit_prompt_and_validation("Special needs?","","bool", mandatory=True)
    new_record["has_propane_tank"] = edit_prompt_and_validation("Large propane tank?","","bool", mandatory=True)
    new_record["has_natural_gas"] = edit_prompt_and_validation("Natural gas connection?","","bool", mandatory=True)

    # Optional questions
    new_record["phone"] = edit_prompt_and_validation("Phone number","","str")
    new_record["email"] = edit_prompt_and_validation("Email address","","str")
    new_record["has_medical_training"] = edit_prompt_and_validation(
        "Any Medical training?",
        "",
        "bool"
    )
    new_record["know_neighbors"] = edit_prompt_and_validation("Know neighbors?","","bool")
    new_record["has_neighbors_key"] = edit_prompt_and_validation("Have neighbor's key?","","bool")
    new_record["wants_newsletter"] = edit_prompt_and_validation("CERT newsletter?","","bool")
    new_record["can_cert_contact"] = edit_prompt_and_validation(
        "Allow CERT non-disaster contact?",
        "",
        "bool"
    )

    # Timestamps
    timestamp = dt.datetime.now().isoformat(timespec="seconds")
    new_record["created_at"] = timestamp
    new_record["updated_at"] = timestamp

    # Fixing blobs again
    for key, value in new_record.items():
        if pd.isna(value):
            new_record[key] = None
            continue
        if hasattr(value, "item"):
            new_record[key] = value.item()

    # Insert the record into the database
    columns = ", ".join(new_record.keys())
    placeholders = ", ".join("?" for _ in new_record.values())
    connection.execute(
        f"INSERT INTO households ({columns}) VALUES ({placeholders});",
        list(new_record.values())
    )
    connection.commit()

    print("\nRecord successfully added!\n")

"""
Main function, runs the main menu for the application
"""
def main():

    while True:
        print("\n==== Welcome to Cert Disaster App ====\n")
        print("1. Import CSV File\n")
        print("2. Export as CSV File\n")
        print("3. View/Edit Records\n")
        print("4. Add Records\n")
        print("5. Exit Application\n")

        choice = input("Please select an option (1-5): ").strip()

        if choice == "1":
            import_csv(db_connection)
        elif choice == "2":
            export_csv(db_connection)
        elif choice == "3":
            view_records(db_connection)
        elif choice == "4":
            add_record(db_connection)
        elif choice == "5":
            print("Exiting Cert Disaster App\n")
            break
        else:
            print("Invalid option, please choose from 1-5.\n")


if __name__ == "__main__":
    db_setup()
    main()


