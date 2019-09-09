"""Runs the Flask Application"""

import re, json, os
from datetime import datetime
import uwtools
from create_tree import create_tree
from geocode import get_combinations
from geocode import main as check_schedules
from utility import check_connection, scan_transcript, Organized_Time_Schedules
from flask import Flask, redirect, url_for, render_template, jsonify, request


app = Flask(__name__)
app.config['SECRET_KEY'] = '\xfaz\xc3\xa8\xd6\xb8\xa0>\x89\x80b'

catalogs = uwtools.course_catalogs()


@app.route('/')
@app.route('/home/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def get_transcript():
    if request.method == 'POST':
        transcript = request.files['transcript']
        transcript.save('Transcript.txt')
    found_transcript = 'Transcript.txt' in os.listdir(os.getcwd()) 
    return render_template('requirements.html', url=request.url_root, transcript=found_transcript)


@app.route('/search/', methods=['POST'])
def search():
    course = request.form['name'].upper().replace(' ', '')
    if course in catalogs.index:
        levels = create_tree(catalogs, scan_transcript(catalogs, webapp=True), 
                            course, None, webapp=True)
        return render_template('course.html', course=course, course_data=catalogs.loc[course].to_dict(), 
                                levels=levels)
    return redirect(url_for('index'))


@app.route('/_get_tree/', methods=['POST'])
def _get_tree():
    course = request.form['name'].upper().replace(' ', '')
    search_course = course.endswith('SEARCHCOURSE')
    course = course.replace('SEARCHCOURSE', '', 1)
    levels = -1
    if re.search(r'[A-Z]+', course) and not re.search(r'\d{3}', course) and search_course:
        if course in {c: d for _, v in uwtools.departments().items() for c, d in v.items()}:
            img = course
        else:
            img = f'ND {course}'
    else:
        courses_taken = scan_transcript(catalogs, webapp=True)
        if course in courses_taken:
            img = f'AT {course}'
        else:
            if course in catalogs.index:
                if catalogs.loc[course]['Prerequisites'] or catalogs.loc[course]['Co-Requisites']:
                    if not search_course:
                        levels = create_tree(catalogs, courses_taken, course, None, webapp=True)
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
    matches = {}
    courses = catalogs[catalogs['Description'].str.contains(f'(?i){keyword}')].to_dict(orient='records')
    for course in courses:
        matches['{}{}'.format(course['Department Name'], course['Course Number'])] = course
    return jsonify({'matches': matches})


@app.route('/get_geocode/', methods=['POST'])
def get_geocode():
    return jsonify({'coords': uwtools.geocode()}) 


@app.route('/check_course/', methods=['POST'])
def check_course():
    with open(os.path.normpath(f'{Organized_Time_Schedules}/Total.json'), mode='r') as file:
        current_courses = json.loads(file.read())
    course = request.form['course'].upper().replace(' ', '')
    planned_course = None
    if re.search(r'[A-Z& ]+\d+ ?[A-Z]?', course):
        check_in = course if not course[-1].isalpha() else course[:-1]
        if check_in in current_courses.keys():
            planned_course = course
            check = True
            if course[-1].isalpha():
                planned_course = f'{course[:-1]} {course[-1]}'
                if course[:-1] in catalogs.index:
                    if course[:-1] in current_courses.keys():
                        check = f'Lecture {course[-1]}' in current_courses[course[:-1]].keys()
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
    courses = request.form['course'].strip(',').split(',')
    global course_options
    course_options = get_combinations(courses)
    try:
        next_option = next(course_options)
    except StopIteration:
        next_option = None
    return jsonify({'option': next_option, 'coords': uwtools.geocode()})


@app.route('/get_schedules/', methods=['POST'])
def get_schedules():
    try:
        next_option = next(course_options)
    except StopIteration:
        next_option = None
    return jsonify({'option': next_option, 'coords': uwtools.geocode()})


@app.route('/keyword/')
def keyword():
    return render_template('keyword.html')


@app.route('/requirements/')
def requirements():
    found_transcript = 'Transcript.txt' in os.listdir(os.getcwd()) 
    return render_template('requirements.html', url=request.url_root, transcript=found_transcript)


@app.route('/departments/', methods=['GET', 'POST'])
def departments():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('departments.html', department_dict=uwtools.departments(),
        url=request.url_root)


@app.route('/geocode/')
def geocode():
    check_schedules()
    return render_template('geocode.html')


@app.route('/<department>/')
def department(department):
    if request.method == 'POST':
        return redirect(url_for('index'))
    if not re.search(r'[A-Z]+\d+', department):
        department_chosen = {}
        department_dict = {c: d for _, v in uwtools.departments().items() for c, d in v.items()}
        for dict_ in catalogs[catalogs['Department Name'] == department].to_dict(orient='records'):
            department_chosen['{}{}'.format(dict_['Department Name'], dict_['Course Number'])] = dict_
        return render_template('department.html', course_dict=department_chosen,
            department_dict=department_dict, url=request.url_root, department=department,
            in_dict=department in department_dict)
    else:
        levels = create_tree(catalogs, scan_transcript(catalogs, webapp=True), department, None, webapp=True)
        return render_template('course.html', course=department, 
            course_data=catalogs.loc[department].to_dict(), levels=levels,
            in_dict=department in catalogs.index, url=request.url_root)
    

@app.route('/generate/')
def generate():
    return render_template('generate.html')


if __name__ == '__main__':
    app.run(debug=False)
