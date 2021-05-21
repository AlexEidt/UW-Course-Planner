"""
Alex Eidt

Runs the Flask Application for the UW Course Planner Web App.
"""


import re
import json
import os
import uwtools
import pandas as pd
from create_tree import create_tree, graph_department
from schedule import get_combinations
from schedule import main as check_schedules
from flask import Flask, redirect, url_for, render_template, jsonify, request


app = Flask(__name__)
app.config['SECRET_KEY'] = '\xfaz\xc3\xa8\xd6\xb8\xa0>\x89\x80b'

PATH = os.path.join(os.getcwd(), 'static')

CATALOGS = pd.read_csv(os.path.join(PATH, 'Course_Catalogs.csv'), dtype=str, index_col=0).fillna('')
with open(os.path.join(PATH, 'departments.json'), mode='r') as f:
    UW_DEPARTMENTS = json.loads(f.read())
with open(os.path.join(PATH, 'geocode.json'), mode='r') as f:
    GEOCODED = json.loads(f.read())
# Used to check courses entered in MyMap to verify they are actually offered that quarter
with open(os.path.join(PATH, 'Time_Schedules.json'), mode='r') as f:
    TIME_SCHEDULE = json.loads(f.read())


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
    if course in CATALOGS.index:
        # Create the Prerequisite Tree if necessary for the course page
        svg = create_tree(CATALOGS, course, request.url_root)
        return render_template(
            'course.html',
            svg=svg,
            course=course,
            course_data=CATALOGS.loc[course].to_dict()
        )
    return redirect(url_for('index'))


@app.route('/_get_tree/', methods=['POST'])
def _get_tree():
    # Used to generate trees for the 'Create Tree' page
    course = request.form['name'].upper().replace(' ', '')
    # SEARCHCOURSE is a flag indicating this request came from the search bar
    search_course = course.endswith('SEARCHCOURSE')
    course = course.replace('SEARCHCOURSE', '', 1)
    if re.search(r'[A-Z]+', course) and not re.search(r'\d{3}', course):
        if course in {c for v in UW_DEPARTMENTS.values() for c in v}:
            img = graph_department(
                CATALOGS[CATALOGS['Department Name'] == course],
                course,
                request.url_root
            ) if not search_course else course
        else:
            # ND -> Not a Department
            img = f'ND {course}'
    elif course in CATALOGS.index:
        if CATALOGS.loc[course, 'Prerequisites'] or CATALOGS.loc[course, 'Co-Requisites']:
            img = create_tree(CATALOGS, course, request.url_root) if not search_course else course
        else:
            # NP -> No Prerequisites
            img = f'NP {course}'
    else:
        # NA -> Not Available
        img = f'NA {course}' if course else ''
    return jsonify({'data': img})


@app.route('/_keyword_search/', methods=['POST'])
def _keyword_search():
    # Used for the case-insensitive keyword search 
    keyword = request.form['keyword'].lower()
    lower = CATALOGS['Description'].str.lower()
    courses = CATALOGS[lower.str.contains(keyword, regex=False)].to_dict(orient='index')
    return jsonify({'matches': courses})


@app.route('/get_geocode/', methods=['POST'])
def get_geocode():
    return jsonify({'coords': GEOCODED}) 


@app.route('/check_course/', methods=['POST'])
def check_course():
    course = request.form['course'].upper().replace(' ', '')
    planned_course = None
    if re.search(r'[A-Z& ]+\d+ ?[A-Z]?', course):
        check_in = course if not course[-1].isalpha() else course[:-1]
        if check_in in TIME_SCHEDULE:
            planned_course = course
            check = True
            if course[-1].isalpha():
                planned_course = f'{course[:-1]} {course[-1]}'
                if course[:-1] in CATALOGS.index:
                    if course[:-1] in TIME_SCHEDULE:
                        check = f'Lecture {course[-1]}' in TIME_SCHEDULE[course[:-1]]
                    else:
                        check = False
                else:
                    check = False
            else:
                check = course in CATALOGS.index
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
    return jsonify({'option': next_option, 'coords': GEOCODED})


@app.route('/get_schedules/', methods=['POST'])
def get_schedules():
    # Cycles through course options
    global course_options
    try:
        next_option = next(course_options)
    except StopIteration:
        next_option = None
    return jsonify({'option': next_option, 'coords': GEOCODED})


@app.route('/keyword/')
def keyword():
    return render_template('keyword.html')


@app.route('/departments/', methods=['GET', 'POST'])
def departments():
    # Displays all departments at every UW Campus
    if request.method == 'POST':
        return redirect(url_for('index'))
    total = {}
    for campus in sorted(UW_DEPARTMENTS):
        total[campus] = {
            d: UW_DEPARTMENTS[campus][d] for d in sorted(UW_DEPARTMENTS[campus])
        }
    return render_template(
        'departments.html',
        department_dict=total,
        url=request.url_root
    )


@app.route('/geocode/')
def geocode():
    if 'Time_Schedules.json' not in os.listdir(PATH):
        check_schedules()
    return render_template('geocode.html')


@app.route('/<department>/')
def department(department):
    if request.method == 'POST':
        return redirect(url_for('index'))
    department = department.upper()
    if not re.search(r'[A-Z]+\d+', department):
        department_chosen = {}
        department = department.replace('&amp;', '&')
        department_df = CATALOGS[CATALOGS['Department Name'] == department]
        svg = graph_department(department_df, department, request.url_root)
        if not department_df.empty:
            for dict_ in department_df.to_dict(orient='records'):
                department_chosen[f"{dict_['Department Name']}{dict_['Course Number']}"] = dict_
        return render_template(
            'department.html',
            course_dict=department_chosen,
            department_dict={c: d for v in UW_DEPARTMENTS.values() for c, d in v.items()},
            url=request.url_root,
            department=department,
            in_dict=bool(department_chosen),
            svg=svg
        )
    else:
        svg = create_tree(CATALOGS, department, request.url_root)
        in_dict = department in CATALOGS.index
        if in_dict:
            course_data = CATALOGS.loc[department].to_dict()
            split_course = re.compile(r'/|,|&&|;')
            for data in ['Prerequisites', 'Co-Requisites', 'Offered with']:
                course_data[data] = list(filter(
                    lambda x: x in CATALOGS.index and x != 'POI',
                    split_course.split(course_data[data])
                ))
        else:
            course_data = None
        return render_template(
            'course.html',
            svg=svg,
            course=department, 
            course_data=course_data,
            in_dict=in_dict,
            url=request.url_root
        )
    

@app.route('/generate/')
def generate():
    return render_template('generate.html')


@app.route('/update_course_catalog/')
def update_course_catalog():
    uwtools.course_catalogs().to_csv(os.path.join(PATH, 'Course_Catalogs.csv'))
    return redirect(url_for('index'))


@app.route('/update_time_schedules/<quarter>/')
def update_time_schedules(quarter):
    year, q = quarter.split('#', 1)
    check_schedules(int(year), q.upper())
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=False)