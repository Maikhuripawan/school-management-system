from flask import Flask, render_template, redirect, url_for, request, flash, send_file
import sqlite3
import pandas as pd
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

app = Flask(__name__)
app.secret_key = "super_secret_school_key"

def get_db_connection():
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    student_count = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    staff_count = conn.execute('SELECT COUNT(*) FROM staff').fetchone()[0]
    conn.close()
    return render_template('index.html', student_count=student_count, staff_count=staff_count)

# --- STUDENTS ROUTES ---
@app.route('/students', methods=['GET', 'POST'])
def students():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.form
        try:
            conn.execute('''
                INSERT INTO students (full_name, gender, grade_class, section, roll_no, admission_no, dob, aadhaar_no, father_name, father_phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
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
            flash(f"Error: {str(e)}", "danger")
            
    students_list = conn.execute('SELECT * FROM students').fetchall()
    conn.close()
    return render_template('students.html', students=students_list)

@app.route('/students/upload', methods=['POST'])
def upload_students():
    if 'file' not in request.files:
        return redirect(url_for('students'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('students'))
        
    if file:
        df = pd.read_excel(file)
        conn = get_db_connection()
        for _, row in df.iterrows():
            conn.execute('''
                INSERT OR IGNORE INTO students (full_name, gender, grade_class, section, roll_no, admission_no, dob, aadhaar_no, father_name, father_phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    str(row.get('Full Name*')), str(row.get('Gender* (M/F)')), str(row.get('Grade/Class* (6-12)')), 
                    str(row.get('Section')), str(row.get('Roll No')), str(row.get('Admission No')), 
                    str(row.get('Date of Birth (YYYY-MM-DD)')), str(row.get('Aadhaar No')), str(row.get("Father's Name")), 
                    str(row.get("Father's Phone"))
                )
            )
        conn.commit()
        conn.close()
        flash("Bulk Students Uploaded successfully!", "success")
    return redirect(url_for('students'))

# --- STAFF ROUTES ---
@app.route('/staff', methods=['GET', 'POST'])
def staff():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.form
        try:
            conn.execute('''
                INSERT INTO staff (full_name, gender, staff_type, designation, department, employee_id, phone, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    data.get('full_name'), data.get('gender'), data.get('staff_type'), 
                    data.get('designation'), data.get('department'), data.get('employee_id'), 
                    data.get('phone'), data.get('email')
                )
            )
            conn.commit()
            flash("Staff member added successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            
    staff_list = conn.execute('SELECT * FROM staff').fetchall()
    conn.close()
    return render_template('staff.html', staff=staff_list)

@app.route('/staff/upload', methods=['POST'])
def upload_staff():
    if 'file' not in request.files:
        return redirect(url_for('staff'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('staff'))
        
    if file:
        df = pd.read_excel(file)
        conn = get_db_connection()
        for _, row in df.iterrows():
            conn.execute('''
                INSERT OR IGNORE INTO staff (full_name, gender, staff_type, designation, department, employee_id, phone, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    str(row.get('Full Name*')), str(row.get('Gender*')), str(row.get('Staff Type*')), 
                    str(row.get('Designation')), str(row.get('Department')), str(row.get('Employee ID')), 
                    str(row.get('Phone')), str(row.get('Email'))
                )
            )
        conn.commit()
        conn.close()
        flash("Bulk Staff Uploaded successfully!", "success")
    return redirect(url_for('staff'))

# --- EXPORT EXCEL ---
@app.route('/export/excel/<type>')
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
def export_pdf(type):
    conn = get_db_connection()
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    if type == 'students':
        data = [["ID", "Name", "Gender", "Class", "Sec", "Roll No", "Admission No", "Father Name"]]
        rows = conn.execute("SELECT id, full_name, gender, grade_class, section, roll_no, admission_no, father_name FROM students").fetchall()
        title = "Student Directory Report"
    else:
        data = [["ID", "Name", "Gender", "Type", "Designation", "Emp ID", "Phone", "Email"]]
        rows = conn.execute("SELECT id, full_name, gender, staff_type, designation, employee_id, phone, email FROM staff").fetchall()
        title = "Staff Directory Report"
    
    conn.close()
    
    for row in rows:
        data.append([str(item) for item in row])
        
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
    from database import init_db
    init_db() 
    app.run(debug=True)