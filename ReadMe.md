# CERT Disaster Preparedness App

---

## Overview
Implementation is a command line python app that collects household data for CERT members to help prepare 
for emergency situations as per the project charter.

---

## Imports
These are the imports I used in my application:
- datetime (For timestamps
- os (For path file and output folder)
- sqlite3 (For databse)
- pandas (For handling csv data)
- re (For address, phone, and email formatting/validation)

## Running the application
### Dependencies
- **Python 3.++**
- **pandas**
- **numpy**
```
python -m pip install pandas numpy
```
### Run the app
```
python cert_disaster_app.py
```


## Features & Functionality

### **1. Local SQLite Database**
- Automatically initializes `cert_disaster.db` on startup.
- Stores all household survey records.
- Persisting data not dropping.

---

### **2. CSV Importing**
Imports household records from a CSV file with full validation, including:

- Data column verification  
- Address validation (`1234 Main St, Denver, CO 80222`)  
- Phone number validation (`123-123-1234`)
- Email validation (`test@test.domain`)
- Conversion of yes/no fields to boolean (1/0)  
- Follow-up question validation for pets->dogs and meds->refrigerated
- Timestamps added automatically when file is successfully imported (`created_at`, `updated_at`)

Invalid CSVs are rejected with error messages.

---

### **3. CSV Exporting**
Exports all records from the database into the `/output/` folder:

- Automatically creates output directory  
- Automatically creates output file name with timestamp (`Exported Records - Timestamp`)


---

### **4. Viewing Records**
- Displays a numbered list of all household records.
- User may:
  - Select a *record number* to edit  
  - Press *Enter* with no input to return to the main menu  

---

### **5. Editing Records**
Updates all fields of a selected record:

- Existing values shown to user 
- Press Enter to keep the current value or type in a new value and enter to commit it 
- Validates:
  - Address format  
  - Phone format  
  - Email format  
  - Integer values  
  - Boolean values (yes/no)
- Updates timestamp (`updated_at`)

---

### **6. Adding New Records**
Creates a new record entry:

- Prompts appear in order one at a time until all  
- Required prompts are enforced
- Optional fields allow blank input  
- Booleans structured as (yes/no)  
- Follow-up questions are triggered automatically
- Creates timestamp (`created_at`)
- Updates timestamp (`updated_at`)

---

### **7. Comments**
- Selecting the view records option only displays the record number and address. I thought this would look cleaner than
displaying all the data in the terminal. You can still see the data by selecting a record for editing and going through
each prompt or looking directly in the database.
- After editing/adding a record you may have to go back to the main menu and then view the records again to see the updates.
- I included an import file that I imported into the database using the app, I edited the first record in the file and added
a new record to the end of the file then exported. So the export should show the core functionality of the app.
- I wanted to integrate the edit and add functions together since they share a lot of similar code but just ran out of 
time. All the core functionality should still work though.


