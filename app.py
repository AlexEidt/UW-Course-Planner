"""Runs the Flask Application"""

import re
import json
import os
import uwtools
import pandas as pd
from datetime import datetime
from create_tree import create_tree
from schedule import get_combinations
from schedule import main as check_schedules
from flask import Flask, redirect, url_for, render_template, jsonify, request


app = Flask(__name__)
app.config['SECRET_KEY'] = '\xfaz\xc3\xa8\xd6\xb8\xa0>\x89\x80b'

catalogs = pd.read_csv(os.path.join(os.getcwd(), 'static', 'Course_Catalogs.csv'), index_col=0).fillna('')
uw_departments = uwtools.departments(struct='dict', flatten='campus')
with open(os.path.join(os.getcwd(), 'static', 'geocode.json'), mode='r') as f:
    geocode_ = json.loads(f.read())


@app.route('/')
@app.route('/home/')
def index():
    return render_template('index.html')

"""
@app.route('/upload', methods=['GET', 'POST'])
def get_transcript():
    # Download Transcript from user and save as 'Transcript.txt'
    if request.method == 'POST':
        transcript = request.files['transcript']
        transcript.save('Transcript.txt')
    found_transcript = 'Transcript.txt' in os.listdir() 
    return render_template('requirements.html', url=request.url_root, transcript=found_transcript)
"""


@app.route('/search/', methods=['POST'])
def search():
    # Search used for the Search Bar in right corner of the Nav Bar
    course = request.form['name'].upper().replace(' ', '')
    if course in catalogs.index:
        # Create the Prerequisite Tree if necessary for the course page
        levels = create_tree(catalogs, course)
        return render_template('course.html', course=course, course_data=catalogs.loc[course].to_dict(), 
                                levels=levels)
    return redirect(url_for('index'))


@app.route('/_get_tree/', methods=['POST'])
def _get_tree():
    # Used to generate trees for the 'Create Tree' page
    course = request.form['name'].upper().replace(' ', '')
    search_course = course.endswith('SEARCHCOURSE')
    course = course.replace('SEARCHCOURSE', '', 1)
    levels = -1
    if re.search(r'[A-Z]+', course) and not re.search(r'\d{3}', course) and search_course:
        if course in {c for _, v in uw_departments.items() for c in v}:
            img = course
        else:
            # ND -> Not a Department
            img = f'ND {course}'
    elif course in catalogs.index:
        if catalogs.loc[course]['Prerequisites'] or catalogs.loc[course]['Co-Requisites']:
            if not search_course:
                levels = create_tree(catalogs, course)
                img = f'{course}.png'
            else:
                img = course
        else:
            # NP -> No Prerequisites
            img = f'NP {course}'
    else:
        # NA -> Not Available
        img = f'NA {course}' if course else ''
    return jsonify({'data': img, 'levels': levels if levels > 0 else 0})


@app.route('/_keyword_search/', methods=['POST'])
def _keyword_search():
    # Used for the case-insensitive keyword search 
    keyword = request.form['keyword'].lower()
    lower = catalogs['Description'].str.lower()
    courses = catalogs[lower.str.contains(keyword, regex=False)].to_dict(orient='index')
    return jsonify({'matches': courses})


@app.route('/get_geocode/', methods=['POST'])
def get_geocode():
    return jsonify({'coords': geocode_}) 


@app.route('/check_course/', methods=['POST'])
def check_course():
    # Checks course entered in MyMap to verify they are actually offered that quarter
    with open(os.path.join(os.getcwd(), 'static', 'Time_Schedules.json'), mode='r') as f:
        current_courses = json.loads(f.read())
    course = request.form['course'].upper().replace(' ', '')
    planned_course = None
    if re.search(r'[A-Z& ]+\d+ ?[A-Z]?', course):
        check_in = course if not course[-1].isalpha() else course[:-1]
        if check_in in current_courses:
            planned_course = course
            check = True
            if course[-1].isalpha():
                planned_course = f'{course[:-1]} {course[-1]}'
                if course[:-1] in catalogs.index:
                    if course[:-1] in current_courses:
                        check = f'Lecture {course[-1]}' in current_courses[course[:-1]]
                    else:
                        check = False
                else:
                    check = False
            else:
                check = course in catalogs.index
        else:
            check = False
    else:
        check = False
    return jsonify({'data': check, 'name': planned_course})


course_options = None
@app.route('/create_schedule/', methods=['POST'])
def create_schedule():
    # Creates all possible schedules based on the courses entered by the user
    courses = request.form['course'].strip(',').split(',')
    global course_options
    course_options = get_combinations(courses)
    try:
        next_option = next(course_options)
    except StopIteration:
        next_option = None
    return jsonify({'option': next_option, 'coords': geocode_})


@app.route('/get_schedules/', methods=['POST'])
def get_schedules():
    # Cycles through course options
    global course_options
    try:
        next_option = next(course_options)
    except StopIteration:
        next_option = None
    return jsonify({'option': next_option, 'coords': geocode_})


@app.route('/keyword/')
def keyword():
    return render_template('keyword.html')


@app.route('/departments/', methods=['GET', 'POST'])
def departments():
    # Displays all departments at every UW Campus
    if request.method == 'POST':
        return redirect(url_for('index'))
    total = {}
    for campus in sorted(uw_departments):
        total[campus] = {d: uw_departments[campus][d] for d in sorted(uw_departments[campus])}
    return render_template('departments.html', department_dict=total,
        url=request.url_root)


@app.route('/geocode/')
def geocode():
    if 'Time_Schedules.json' not in os.listdir(os.path.join(os.getcwd(), 'static')):
        check_schedules()
    return render_template('geocode.html')


@app.route('/<department>/')
def department(department):
    if request.method == 'POST':
        return redirect(url_for('index'))
    if not re.search(r'[A-Z]+\d+', department):
        department_chosen = {}
        department_dict = {c: d for _, v in uw_departments.items() for c, d in v.items()}
        for dict_ in catalogs[catalogs['Department Name'] == department].to_dict(orient='records'):
            department_chosen['{}{}'.format(dict_['Department Name'], dict_['Course Number'])] = dict_
        return render_template('department.html', course_dict=department_chosen,
            department_dict=department_dict, url=request.url_root, department=department,
            in_dict=department in department_dict)
    else:
        levels = create_tree(catalogs, department)
        return render_template('course.html', course=department, 
            course_data=catalogs.loc[department].to_dict(), levels=levels,
            in_dict=department in catalogs.index, url=request.url_root)
    

@app.route('/generate/')
def generate():
    return render_template('generate.html')


@app.route('/update_course_catalog/')
def update_course_catalog():
    uwtools.course_catalogs().to_csv(os.path.join(os.getcwd(), 'static', 'Course_Catalogs.csv'))
    return redirect(url_for('index'))


@app.route('/update_time_schedules/')
def update_time_schedules():
    check_schedules()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=False)