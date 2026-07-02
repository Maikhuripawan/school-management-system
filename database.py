import sqlite3

def init_db():
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    
    # 1. Students Table (According to your template)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            grade_class TEXT NOT NULL,
            section TEXT,
            roll_no TEXT,
            admission_no TEXT UNIQUE,
            dob TEXT,
            aadhaar_no TEXT,
            blood_group TEXT,
            nationality TEXT,
            mother_tongue TEXT,
            category TEXT,
            religion TEXT,
            rte TEXT,
            admission_date TEXT,
            house TEXT,
            father_name TEXT,
            father_phone TEXT,
            father_occupation TEXT,
            father_education TEXT,
            mother_name TEXT,
            mother_phone TEXT,
            mother_occupation TEXT,
            mother_education TEXT,
            guardian_name TEXT,
            guardian_phone TEXT,
            guardian_relation TEXT,
            annual_income TEXT,
            state TEXT,
            district TEXT,
            block TEXT,
            village_town TEXT,
            pin_code TEXT,
            permanent_address TEXT,
            correspondence_address TEXT,
            previous_school TEXT,
            medium_of_instruction TEXT,
            subjects_opted TEXT,
            height TEXT,
            weight TEXT,
            vaccination_status TEXT,
            hostel_required TEXT
        )
    ''')
    
    # 2. Staff Table (According to your template)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            staff_type TEXT NOT NULL,
            designation TEXT,
            qualification TEXT,
            subjects TEXT,
            department TEXT,
            employee_id TEXT UNIQUE,
            phone TEXT,
            email TEXT,
            aadhaar_no TEXT,
            dob TEXT,
            joining_date TEXT,
            salary_group TEXT,
            contract_type TEXT,
            class_teacher TEXT,
            class_teacher_of TEXT,
            address TEXT,
            bank_account_no TEXT,
            ifsc_code TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database and Tables created successfully!")