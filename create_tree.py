"""
Alex Eidt

Creates a Prerequisite Tree Graph for any course at the University of Washington.
Creates Department course graphs showing connections between all courses in that department.
"""


import os
import re
from graphviz import Digraph

# Change PATH setup for Graphviz folder here:
# --------------------------GRAPHVIZ PATH SETUP------------------------- #
os.environ['PATH'] += os.pathsep + 'C:\\Graphviz\\bin'
# ---------------------------------------------------------------------- #

total = set()
REQUISITE_TYPES = ['Prerequisites', 'Co-Requisites']
PATH = os.path.join(os.getcwd(), 'static', 'Prerequisite_Trees')
SPLIT_COURSE = re.compile(r'/|,|&&')
ARROWHEADS = [
    'box', 'dot', 'normal', 'diamond', 'inv', 'tee', 'crow',
    'icurve', 'curve', 'vee', 'none'
]


def create_tree(course_df, course, url):
    """Starts the tree by adding the selected course as the top element
    @params
        'course_df': The DataFrame of courses
        'course': The course in question
        'url': URL of current webpage
    """
    file_path = os.path.join('..', 'static', 'Prerequisite_Trees', f'{course}.svg')
    if f'{course}.svg' in os.listdir(PATH):
        return file_path
    # Tree used to draw the course prerequisite tree
    tree = Digraph(
        comment=f'{course} Prerequisites',
        graph_attr={'rankdir': 'TB', 'splines': 'ortho', 'overlap': 'scale'},
        edge_attr={'arrowhead': 'dot', 'arrowsize': '0.8'},
    )
    course_df = course_df[course_df['Campus'] == course_df.loc[course, 'Campus']]
    prereqs = set(course_df.loc[course, REQUISITE_TYPES])
    splitted = list(filter(
        lambda x: x in course_df.index and x != 'POI',
        re.compile(r'/|,|&&|;').split(','.join(prereqs))
    ))
    if any(prereqs) and splitted and course in course_df.index:
        del splitted
        global total
        total.clear()
        tree.node(course, course, fontname='helvetica')
        tree.attr('node', shape='rectangle', style='filled', color='gray30', fontname='helvetica')
        # Recursively build up tree
        create_tree_helper(course_df, course, 0, tree, url)
        path = os.path.join(PATH, course)
        tree.render(path, view=False, format='svg')
        os.remove(path)
        return file_path
    return None


def create_tree_helper(course_df, course, level, tree, url):
    """Builds up the prerequisite tree
    @params
        'course_df': The DataFrame of courses
        'course': The course in question
        'level': The current level of the tree
        'tree': The tree being built
        'url': URL of the current webpage
    """
    if course not in total:
        total.add(course)
        for i, requisite_type in enumerate(REQUISITE_TYPES):
            for index, crs in enumerate(course_df.loc[course.replace('&amp;', '&'), requisite_type].split(';')):
                for option in SPLIT_COURSE.split(crs):
                    if option and option != 'POI' and option in course_df.index:
                        option = option.replace('&', '&amp;')
                        tree.attr(
                            'edge',
                            arrowhead=ARROWHEADS[index] if not i else f'o{ARROWHEADS[index]}',
                        )
                        tree.attr(
                            'node',
                            fillcolor=f'grey{99 - (level * 3)}' if not i else 'cyan',
                            URL=f'{url}{option}',
                            target="_blank"
                        )
                        tree.edge(course, option)
                        create_tree_helper(course_df, option, level + 1, tree, url)


def post_requisites(course_df, course, url):
    """Starts the tree by adding the selected course as the top element
    @params
        'course_df': The DataFrame of courses
        'course': The course in question
        'url': URL of current webpage
    """
    postreqs = {}
    post_requisites_helper(course_df, course, postreqs)

    # Tree used to draw the postrequisite tree
    tree = Digraph(
        comment=f'{course} Course Post Requisites',
        graph_attr={'rankdir': 'BT', 'splines': 'ortho', 'overlap': 'false'},
        edge_attr={'arrowhead': 'normal', 'arrowsize': '0.8'},
    )
    tree.attr('node', shape='rectangle', fontname='helvetica')

    for crs, postreq in postreqs.items():
        crs = crs.replace('&', '&amp;')
        tree.attr('node', URL=f'{url}{crs}', target="_blank")
        tree.node(crs)
        for post in postreq:
            post = post.replace('&', '&amp;')
            tree.attr('node', URL=f'{url}{post}', target="_blank")
            tree.edge(crs, post)

    path = os.path.join(PATH, f'{course}_POST')
    tree.render(path, view=False, format='svg')
    os.remove(path)
    return None

    
def post_requisites_helper(course_df, course, postreqs):
    # Get post-requisites
    mask = (course_df['Prerequisites'] != '') & (course_df['Prerequisites'] != 'POI')
    campus_mask = course_df['Campus'] == course_df.loc[course, 'Campus']
    postreqs_df = course_df[mask & campus_mask]['Prerequisites'].str.split(r'/|,|&&|;')
    postreqs_df = postreqs_df.apply(lambda x: set(filter(lambda y: y != 'POI', x)))
    post_requisites = postreqs_df[postreqs_df.apply(lambda x: course in x)].index

    if post_requisites.empty:
        return
    if course not in postreqs:
        postreqs[course] = set()
    postreqs[course].update(post_requisites)
    for postreq in post_requisites:
        post_requisites_helper(course_df, postreq, postreqs)


def graph_department(department_df, department, url):
    """Builds up the department prerequisite tree
    @params
        'department_df': The DataFrame of courses in the department
        'department': The department in question
        'url': URL of the current webpage
    """
    file_path = os.path.join('..', 'static', 'Prerequisite_Trees', f'{department}.svg')
    if f'{department}.svg' in os.listdir(PATH):
        return file_path

    course_prereqs = {}
    split_prereqs = re.compile(r'/|,|&&|;')
    for course in department_df.index:
        if course not in course_prereqs:
            course_prereqs[course] = set()
        for requisite_type in REQUISITE_TYPES:
            for prereq in split_prereqs.split(department_df.loc[course, requisite_type]):
                if ''.join(filter(lambda x: not x.isdigit() or x == '&', prereq)) == department and \
                    prereq in department_df.index:
                    course_prereqs[course].add(prereq)
        if not course_prereqs[course]:
            del course_prereqs[course]

    if not course_prereqs:
        return None

    # Tree used to draw the department tree
    tree = Digraph(
        comment=f'{department} Course Connections by Pre/Co-Requisites',
        graph_attr={'layout': 'dot', 'rankdir': 'LR', 'splines': 'true', 'overlap': 'false'},
        edge_attr={'arrowhead': 'normal', 'arrowsize': '0.6'},
    )
    tree.attr('node', shape='rectangle', fontname='helvetica')

    for course, prereqs in course_prereqs.items():
        course = course.replace('&', '&amp;')
        tree.attr('node', URL=f'{url}{course}', target='_blank')
        tree.node(course)
        for prereq in prereqs:
            if prereq in department_df.index:
                prereq = prereq.replace('&', '&amp;')
                tree.attr('node', URL=f'{url}{prereq}', target='_blank')
                tree.node(prereq)
                tree.edge(course, prereq)

    path = os.path.join(PATH, department)
    tree.render(path, view=False, format='svg')
    os.remove(path)
    return file_path