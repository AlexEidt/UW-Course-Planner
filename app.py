"""Runs the Flask Application"""

import re
import json
from flask import Flask, redirect, url_for, render_template, jsonify, request
from create_tree import create_tree
from main import read_file, course_files_dir

app = Flask(__name__)


with open(f'{course_files_dir}\\JSON\\Departments.json', mode='r') as file:
    department_dict = json.loads(file.read())


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


@app.route('/')
@app.route('/home/')
def index():
    return render_template('index.html')


@app.route('/_get_tree/', methods=['POST'])
def _get_tree():
    course = request.form['name'].upper().replace(' ', '')
    errorMsg = 'None'
    img = None
    course_dict = get_course_dict('Total')
    if course in course_dict:
        if course_dict[course]['Prerequisites']:
            create_tree(course_dict, [], course, None)
            img = f'{course}.png'
        else:
            errorMsg = f'Error: {course} has no prerequisites'
    else:
        errorMsg = f'Error: {course} is not a course at UW'
    return jsonify({'data': render_template('response.html', img=img),
                    'errorMsg': errorMsg})


@app.route('/departments/', methods=['GET', 'POST'])
def departments():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('departments.html', department_dict=department_dict,
        url=request.url_root)


@app.route('/<campus>/<department>/')
def department(campus, department):
    if request.method == 'POST':
        return redirect(url_for('index'))
    course_dict = get_course_dict(campus)
    if not re.search(r'[A-Z]+\d+', department):
        department_chosen = {}
        for course, data in course_dict.items():
            if re.sub(r'\d+', '', course) == department:
                department_chosen[course] = data
        return render_template('department.html', course_dict=department_chosen,
            department_dict=department_dict, url=request.url_root, campus=campus, department=department)
    else:
        levels = create_tree(course_dict, [], department, None)
        return render_template('course.html', course=department, course_data=course_dict[department], levels=levels)
    

if __name__ == '__main__':
    app.run(debug=True)