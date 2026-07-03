import os
import psycopg2  # SQLite ki jagah PostgreSQL use karne ke liye

# Render ka database URL uthane ke liye
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    raise Exception("DATABASE_URL Environment Variable nahi mila! Render Environment check karein.")

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Users Table (Multiple Users aur Roles ke liye)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff'
            )
        ''')
        
        # 2. Students Table (Aapke saare columns safe hain)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
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
        
        # 3. Staff Table (Aapke saare columns safe hain)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id SERIAL PRIMARY KEY,
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
        
        # 4. Default Accounts Automatically Create karne ke liye
        # Agar admin pehle se nahi hai tabhi insert hoga (Conflict handle kiya hai)
        cursor.execute('''
            INSERT INTO users (username, password, role) 
            VALUES ('admin', 'school123', 'admin')
            ON CONFLICT (username) DO NOTHING
        ''')
        
        cursor.execute('''
            INSERT INTO users (username, password, role) 
            VALUES ('staff1', 'school123', 'staff')
            ON CONFLICT (username) DO NOTHING
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("PostgreSQL Database, Tables aur Default Users kamyabi se ban gaye hain!")
        
    except Exception as e:
        print(f"Database Initialization me error aaya: {str(e)}")

if __name__ == '__main__':
    init_db()