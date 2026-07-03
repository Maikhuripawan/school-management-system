from flask import Flask, render_template, redirect, url_for, request, flash, send_file, abort, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from functools import wraps

app = Flask(__name__)
app.secret_key = "super_secret_school_key"

# --- DATABASE CONNECTION (PostgreSQL) ---
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        # RealDictCursor se data bilkul SQLite Row ki tarah column names ke sath milta hai
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    raise Exception("DATABASE_URL Environment Variable nahi mila! Render Environment check karein.")

# --- AUTO INITIALIZE DATABASE ---
try:
    import database
    print("Zabardasti Database Initialize kar rahe hain... - app.py:29")
    database.init_db()  # Yeh line aapki users table ko force create karegi
    print("Database Initialization Successful! - app.py:31")
except Exception as e:
    print(f"Database initialization info/error: {str(e)} - app.py:33")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Nayi CSV file ko safely load karne ka helper function
def load_schools_csv():
    csv_path = os.path.join(BASE_DIR, "schools (1).csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = df.replace({np.nan: None})
        if 'Phone' in df.columns:
            df['Phone'] = df['Phone'].apply(lambda x: str(int(x)) if x is not None else '')
        return df
    return pd.DataFrame()

# --- SECURITY WALL (Login Required Decorators) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Kripya pehle login karein!", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Yeh page dekhne ki ijaazat sirf Admin ko hai!", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# --- LOGIN / LOGOUT ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Galat Username ya Password!", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Aap kamyabi se logout ho gaye hain.", "info")
    return redirect(url_for('login'))


# --- USER MANAGEMENT ROUTE (Naye Users Banane Aur Dekhne Ke Liye) ---
@app.route('/users', methods=['GET', 'POST'])
@login_required
@admin_only
def manage_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('password')
        new_role = request.form.get('role')
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (new_username, new_password, new_role)
            )
            conn.commit()
            flash(f"User '{new_username}' kamyabi se ban gaya!", "success")
        except Exception as e:
            conn.rollback()
            flash("Error: Yeh Username pehle se maujood hai!", "danger")
            
    cursor.execute("SELECT id, username, role FROM users ORDER BY id DESC")
    all_users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('users.html', users=all_users)


# --- HOME / DASHBOARD ROUTE ---
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM students')
    student_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) FROM staff')
    staff_count = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    df_schools = load_schools_csv()
    schools_list = []
    if not df_schools.empty:
        schools_list = df_schools[['Name', 'UDISE', 'District', 'Type']].to_dict(orient='records')
        
    return render_template('index.html', 
                           student_count=student_count, 
                           staff_count=staff_count, 
                           schools=schools_list)

# --- SINGLE SCHOOL DETAIL ROUTE ---
@app.route('/school/<int:udise_code>')
@login_required
def school_detail(udise_code):
    df_schools = load_schools_csv()
    if df_schools.empty:
        return "Schools data file not found.", 404
        
    school_data = df_schools[df_schools['UDISE'] == udise_code].to_dict(orient='records')
    if school_data:
        return render_template('school.html', school=school_data[0])
    
    abort(404)

# --- STUDENTS ROUTES ---
@app.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.form
        try:
            cursor.execute('''
                INSERT INTO students (full_name, gender, grade_class, section, roll_no, admission_no, dob, aadhaar_no, father_name, father_phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (
                    data.get('full_name'), data.get('gender'), data.get('grade_class'), 
                    data.get('section'), data.get('roll_no'), data.get('admission_no'), 
                    data.get('dob'), data.get('aadhaar_no'), data.get('father_name'), 
                    data.get('father_phone')
                )
            )
            conn.commit()
            flash("Student added successfully!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error: {str(e)}", "danger")
            
    cursor.execute('SELECT * FROM students')
    students_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('students.html', students=students_list)

# --- EDIT STUDENT ROUTE ---
@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM students WHERE id = %s', (student_id,))
    student = cursor.fetchone()
    
    if student is None:
        cursor.close()
        conn.close()
        abort(404)
        
    if request.method == 'POST':
        data = request.form
        try:
            cursor.execute('''
                UPDATE students 
                SET full_name = %s, gender = %s, grade_class = %s, section = %s, roll_no = %s, 
                    admission_no = %s, dob = %s, aadhaar_no = %s, father_name = %s, father_phone = %s
                WHERE id = %s''',
                (
                    data.get('full_name'), data.get('gender'), data.get('grade_class'), 
                    data.get('section'), data.get('roll_no'), data.get('admission_no'), 
                    data.get('dob'), data.get('aadhaar_no'), data.get('father_name'), 
                    data.get('father_phone'), student_id
                )
            )
            conn.commit()
            flash("Student record updated successfully!", "success")
            return redirect(url_for('students'))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating record: {str(e)}", "danger")
            
    cursor.close()
    conn.close()
    return render_template('edit_student.html', student=student)

# --- DELETE STUDENT ROUTE ---
@app.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM students WHERE id = %s', (student_id,))
        conn.commit()
        flash("Student record deleted successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting record: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('students'))

@app.route('/students/upload', methods=['POST'])
@login_required
def upload_students():
    if 'file' not in request.files:
        return redirect(url_for('students'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('students'))
        
    if file:
        df = pd.read_excel(file)
        conn = get_db_connection()
        cursor = conn.cursor()
        for _, row in df.iterrows():
            try:
                cursor.execute('''
                    INSERT INTO students (full_name, gender, grade_class, section, roll_no, admission_no, dob, aadhaar_no, father_name, father_phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (admission_no) DO NOTHING''',
                    (
                        str(row.get('Full Name*')), str(row.get('Gender* (M/F)')), str(row.get('Grade/Class* (6-12)')), 
                        str(row.get('Section')), str(row.get('Roll No')), str(row.get('Admission No')), 
                        str(row.get('Date of Birth (YYYY-MM-DD)')), str(row.get('Aadhaar No')), str(row.get("Father's Name")), 
                        str(row.get("Father's Phone"))
                    )
                )
            except:
                conn.rollback()
        conn.commit()
        cursor.close()
        conn.close()
        flash("Bulk Students Uploaded successfully!", "success")
    return redirect(url_for('students'))

# --- STAFF ROUTES ---
@app.route('/staff', methods=['GET', 'POST'])
@login_required
def staff():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.form
        try:
            cursor.execute('''
                INSERT INTO staff (full_name, gender, staff_type, designation, department, employee_id, phone, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (
                    data.get('full_name'), data.get('gender'), data.get('staff_type'), 
                    data.get('designation'), data.get('department'), data.get('employee_id'), 
                    data.get('phone'), data.get('email')
                )
            )
            conn.commit()
            flash("Staff member added successfully!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error: {str(e)}", "danger")
            
    cursor.execute('SELECT * FROM staff')
    staff_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('staff.html', staff=staff_list)

# --- EDIT STAFF ROUTE ---
@app.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
@login_required
def edit_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM staff WHERE id = %s', (staff_id,))
    staff_member = cursor.fetchone()
    
    if staff_member is None:
        cursor.close()
        conn.close()
        abort(404)
        
    if request.method == 'POST':
        data = request.form
        try:
            cursor.execute('''
                UPDATE staff 
                SET full_name = %s, gender = %s, staff_type = %s, designation = %s, 
                    department = %s, employee_id = %s, phone = %s, email = %s
                WHERE id = %s''',
                (
                    data.get('full_name'), data.get('gender'), data.get('staff_type'), 
                    data.get('designation'), data.get('department'), data.get('employee_id'), 
                    data.get('phone'), data.get('email'), staff_id
                )
            )
            conn.commit()
            flash("Staff record updated successfully!", "success")
            return redirect(url_for('staff'))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating staff record: {str(e)}", "danger")
            
    cursor.close()
    conn.close()
    return render_template('edit_staff.html', staff=staff_member)

# --- DELETE STAFF ROUTE ---
@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
@login_required
def delete_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM staff WHERE id = %s', (staff_id,))
        conn.commit()
        flash("Staff record deleted successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting staff record: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('staff'))

@app.route('/staff/upload', methods=['POST'])
@login_required
def upload_staff():
    if 'file' not in request.files:
        return redirect(url_for('staff'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('staff'))
        
    if file:
        df = pd.read_excel(file)
        conn = get_db_connection()
        cursor = conn.cursor()
        for _, row in df.iterrows():
            try:
                cursor.execute('''
                    INSERT INTO staff (full_name, gender, staff_type, designation, department, employee_id, phone, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (employee_id) DO NOTHING''',
                    (
                        str(row.get('Full Name*')), str(row.get('Gender*')), str(row.get('Staff Type*')), 
                        str(row.get('Designation')), str(row.get('Department')), str(row.get('Employee ID')), 
                        str(row.get('Phone')), str(row.get('Email'))
                    )
                )
            except:
                conn.rollback()
        conn.commit()
        cursor.close()
        conn.close()
        flash("Bulk Staff Uploaded successfully!", "success")
    return redirect(url_for('staff'))

# --- EXPORT EXCEL ---
@app.route('/export/excel/<type>')
@login_required
def export_excel(type):
    conn = get_db_connection()
    if type == 'students':
        df = pd.read_sql_query("SELECT * FROM students", conn)
        filename = "Students_Export.xlsx"
    else:
        df = pd.read_sql_query("SELECT * FROM staff", conn)
        filename = "Staff_Export.xlsx"
    conn.close()
    
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    out.seek(0)
    
    return send_file(out, as_attachment=True, download_name=filename)

# --- EXPORT PDF ---
@app.route('/export/pdf/<type>')
@login_required
def export_pdf(type):
    conn = get_db_connection()
    cursor = conn.cursor()
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    if type == 'students':
        data = [["ID", "Name", "Gender", "Class", "Sec", "Roll No", "Admission No", "Father Name"]]
        cursor.execute("SELECT id, full_name, gender, grade_class, section, roll_no, admission_no, father_name FROM students")
        rows = cursor.fetchall()
        title = "Student Directory Report"
    else:
        data = [["ID", "Name", "Gender", "Type", "Designation", "Emp ID", "Phone", "Email"]]
        cursor.execute("SELECT id, full_name, gender, staff_type, designation, employee_id, phone, email FROM staff")
        rows = cursor.fetchall()
        title = "Staff Directory Report"
    
    cursor.close()
    conn.close()
    
    for row in rows:
        data.append([str(row[key]) for key in row.keys()])
        
    elements.append(Paragraph(f"<h1>{title}</h1>", styles['Title']))
    elements.append(Spacer(1, 20))
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(t)
    doc.build(elements)
    out.seek(0)
    
    return send_file(out, as_attachment=True, download_name=f"{type}_report.pdf")

if __name__ == '__main__':
    app.run(debug=True)