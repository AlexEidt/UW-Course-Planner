"""Creates a Prerequisite tree for a given course using Graphviz"""


import os    
import re
from graphviz import Digraph


# Change PATH setup for Graphviz folder here:
# --------------------------GRAPHVIZ PATH SETUP------------------------- #
os.environ["PATH"] += os.pathsep + 'C:\\Graphviz\\bin'
# ---------------------------------------------------------------------- #


# Tree used the draw the course prerequisite tree
tree = Digraph(
    comment='Course Prerequisites',
    graph_attr = {'rankdir':'TB', 'splines':'ortho', 'overlap':'scale'},
    edge_attr = {'arrowhead': 'dot'}
)


def create_tree(course_dict, courses_taken, course, indent):
    """Starts the tree by adding the selected course as the top element
    @params
        'course_dict': The dictionary of courses
        'courses_taken': Courses already taken from the user, scanned in from transcript
        'course': The course in question
        UNUSED: 'indent': The indentation level for each prerequisite course
    """
    tree.node(course, course)
    tree.attr('node', shape='invhouse', style='rounded,filled', color='lightgrey')
    # Recursively build up tree
    create_tree_helper(course_dict, course, 0, courses_taken)
    tree.render('{}\\{}'.format('Prereq Trees', course), view=True, format='png')


total = []
arrowheads = ['box', 'dot', 'normal', 'diamond', 'tee', 'crow',
              'icurve', 'curve', 'inv', 'vee', 'none']
split_course = re.compile(r'&&|/|,')
def create_tree_helper(course_dict, course, level, courses_taken):
    """Builds up the prerequisite tree
    @params
        'course_dict': The dictionary of courses
        'course': The course in question
        'level': The current level of the tree
        'courses_taken': Courses already taken from the user, scanned in from transcript
    """
    if course in course_dict and course:
        if course not in total:
            total.append(course)
            for index, crs in enumerate(course_dict[course]['Prerequisites'].split(';')):
                if set(split_course.split(crs)).isdisjoint(courses_taken):
                    for option in split_course.split(crs):
                        if option:
                            tree.attr('edge', arrowhead=arrowheads[index], arrowsize='1.1')
                            tree.attr('node', color='grey{}'.format(str(99 - (level * 3))))
                            tree.edge(course, option)
                            create_tree_helper(course_dict, option, level + 1, courses_taken)


