"""Runs the Flask Application"""

import re
import json
import os
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, jsonify, request
from create_tree import create_tree
from main import read_file, course_files_dir, course_dir, check_connection, scan_transcript
from parse_courses import CAMPUSES, gather

app = Flask(__name__)
app.config['SECRET_KEY'] = '\xfaz\xc3\xa8\xd6\xb8\xa0>\x89\x80b'


def get_course_dict(campus):
    """Returns the course dictionary for the given campus by reading the .json
       file for that campus
    @params
        'campus': The campus to get the course dictionary from
    Returns
        A course dictionary for the given campus
    """
    with open(f'{course_files_dir}\\JSON\\{campus}.json', mode='r') as file:
        course_dict = json.loads(file.read())
    return course_dict


def check():
    # Create Directories for JSON and TSV Files
    try: 
        os.mkdir(course_dir)
    except Exception: pass
    try: 
        os.mkdir(f'{course_files_dir}\\JSON')
    except Exception: pass
    try: 
        os.mkdir(f'{course_files_dir}\\TSV')
    except Exception: pass
    required_tsv = [f'{c}.tsv' for c in CAMPUSES.keys()] + ['Total.tsv']
    required_json = [f'{c}.json' for c in CAMPUSES.keys()] + ['Departments.json', 'Total.json']
    required_total = required_tsv + required_json
    present_tsv = os.listdir(f'{course_files_dir}\\TSV')
    present_json = os.listdir(f'{course_files_dir}\\JSON')
    present_total = present_tsv + present_json
    check = [c for c in required_total if c not in present_total]
    return not bool(check)


@app.route('/')
@app.route('/home/')
def index():
    return render_template('index.html')


@app.route('/gather', methods=['POST'])
def get_files():
    if check_connection():
        gather(course_files_dir)
    found_transcript = 'Transcript.txt' in os.listdir(os.getcwd()) 
    return render_template('requirements.html', url=request.url_root, transcript=found_transcript, 
        connected=check_connection, gather=check)
 

@app.route('/upload', methods=['GET', 'POST'])
def get_transcript():
    if request.method == 'POST':
        transcript = request.files['transcript']
        transcript.save('Transcript.txt')
    found_transcript = 'Transcript.txt' in os.listdir(os.getcwd()) 
    return render_template('requirements.html', url=request.url_root, transcript=found_transcript, 
        connected=check_connection, gather=check)


@app.route('/search/', methods=['POST'])
def search():
    course = request.form['name'].upper().replace(' ', '')
    total_course_dict = get_course_dict('Total')
    if course in total_course_dict:
        levels = create_tree(total_course_dict, scan_transcript(total_course_dict, webapp=True), course, None, webapp=True)
        return render_template('course.html', course=course, course_data=total_course_dict[course], levels=levels)
    return redirect(url_for('index'))



@app.route('/_get_tree/', methods=['POST'])
def _get_tree():
    course = request.form['name'].upper().replace(' ', '')
    search_course = course.endswith('SEARCHCOURSE')
    course = course.replace('SEARCHCOURSE', '', 1)
    levels = -1
    if re.search(r'[A-Z]+', course) and not re.search(r'\d{3}', course) and search_course:
        department_dict = get_course_dict('Departments')
        if course in department_dict['Total']:
            img = course
        else:
            img = f'ND {course}'
    else:
        course_dict = get_course_dict('Total')
        courses_taken = scan_transcript(course_dict, webapp=True)
        if course in courses_taken:
            img = f'AT {course}'
        else:
            if course in course_dict:
                if course_dict[course]['Prerequisites']:
                    if not search_course:
                        levels = create_tree(course_dict, courses_taken, course, None, webapp=True)
                        img = f'{course}.png'
                    else:
                        img = course
                else:
                    img = f'NP {course}'
            else:
                img = f'NA {course}' if course else ''
    return jsonify({'data': img, 'levels': levels if levels > 0 else 0})


@app.route('/_keyword_search/', methods=['POST'])
def _keyword_search():
    keyword = request.form['keyword'].lower()
    course_dict = get_course_dict('Total')
    matches = {}
    courses_taken = scan_transcript(course_dict, webapp=True)
    for course, data in course_dict.items():
        if keyword in data['Description'].lower() and course not in courses_taken:
            matches[course] = data
    return jsonify({'matches': matches})


@app.route('/keyword/')
def keyword():
    return render_template('keyword.html')


@app.route('/requirements/')
def requirements():
    found_transcript = 'Transcript.txt' in os.listdir(os.getcwd()) 
    return render_template('requirements.html', url=request.url_root, transcript=found_transcript, 
        connected=check_connection, gather=check)


@app.route('/departments/', methods=['GET', 'POST'])
def departments():
    if request.method == 'POST':
        return redirect(url_for('index'))
    department_dict = get_course_dict('Departments')
    return render_template('departments.html', department_dict=department_dict,
        url=request.url_root)


@app.route('/<department>/')
def department(department):
    if request.method == 'POST':
        return redirect(url_for('index'))
    course_dict = get_course_dict('Total')
    if not re.search(r'[A-Z]+\d+', department):
        department_dict = get_course_dict('Departments')
        department_chosen = {}
        for course, data in course_dict.items():
            if re.sub(r'\d+', '', course) == department:
                department_chosen[course] = data
        return render_template('department.html', course_dict=department_chosen,
            department_dict=department_dict, url=request.url_root, department=department,
            in_dict=department in department_dict['Total'])
    else:
        levels = create_tree(course_dict, scan_transcript(course_dict, webapp=True), department, None, webapp=True)
        return render_template('course.html', course=department, 
            course_data=course_dict[department], levels=levels,
            in_dict=department in course_dict, url=request.url_root)
    

@app.route('/generate/')
def generate():
    return render_template('generate.html')


if __name__ == '__main__':
    app.run(debug=False)
