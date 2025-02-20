from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import PyPDF2
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resumes.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    skills = db.Column(db.Text, nullable=True)
    experience_level = db.Column(db.String(50), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'resume' not in request.files:
        return redirect(url_for('index'))

    file = request.files['resume']
    if file.filename == '':
        return redirect(url_for('index'))

    if file and file.filename.endswith('.pdf'):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']

        experience_level, skills = parse_resume(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        resume = Resume(name=name, email=email, contact=contact, filename=filename, skills=skills, experience_level=experience_level)
        db.session.add(resume)
        db.session.commit()
        return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    resumes = Resume.query.all()
    return render_template('admin.html', resumes=resumes)

@app.route('/clear_data')
def clear_data():
    db.drop_all()
    db.create_all()
    return redirect(url_for('admin'))

def parse_resume(filepath):
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()

            skills = extract_skills(text)
            experience_level = classify_experience_level(skills)
            return experience_level, skills
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return None, None

def extract_skills(text):
    skills = []
    skill_keywords = ['Python', 'JavaScript', 'Java', 'C++', 'SQL', 'HTML', 'CSS']
    for keyword in skill_keywords:
        if keyword.lower() in text.lower():
            skills.append(keyword)
    return ', '.join(skills)

def classify_experience_level(skills):
    if 'Python' in skills and 'JavaScript' in skills:
        return 'Advanced'
    elif 'Python' in skills or 'JavaScript' in skills:
        return 'Intermediate'
    else:
        return 'Beginner'

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/clear_data', methods=['POST'])
@login_required
def clear_data():
    if not current_user.is_admin:
        flash('Access denied. Admins only.')
        return redirect(url_for('index'))
    db.drop_all()
    db.create_all()
    flash('Data cleared successfully.')
    return redirect(url_for('admin'))
