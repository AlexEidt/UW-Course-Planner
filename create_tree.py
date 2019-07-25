"""Creates a Prerequisite tree for a given course"""


import os    
import re
from graphviz import Digraph


# Change PATH setup for Graphviz folder here:
# --------------------------GRAPHVIZ PATH SETUP------------------------- #
os.environ["PATH"] += os.pathsep + 'C:\\Graphviz\\bin'
# ---------------------------------------------------------------------- #


def create_tree(course_dict, courses_taken, course, indent):
    """Starts the tree by adding the selected course as the top element
    @params
        'course_dict': The dictionary of courses
        'courses_taken': Courses already taken from the user, scanned in from transcript
        'course': The course in question
        UNUSED: 'indent': The indentation level for each prerequisite course
    """
    # Tree used to draw the course prerequisite tree
    tree = Digraph(
        comment='{} Prerequisites'.format(course),
        graph_attr = {'rankdir':'TB', 'splines':'ortho', 'overlap':'scale'},
        edge_attr = {'arrowhead': 'dot'}
    )
    tree.node(course, course)
    tree.attr('node', shape='invtrapezium', style='rounded,filled', color='gray30')
    # Recursively build up tree
    create_tree_helper(course_dict, course, 0, courses_taken, [], tree)
    tree.render('{}\\{}'.format('Prereq Trees', course), view=True, format='png')


arrowheads = ['box', 'dot', 'normal', 'diamond', 'tee', 'crow',
              'icurve', 'curve', 'inv', 'vee', 'none']
split_course = re.compile(r'&&|/|,')
def create_tree_helper(course_dict, course, level, courses_taken, total, tree):
    """Builds up the prerequisite tree
    @params
        'course_dict': The dictionary of courses
        'course': The course in question
        'level': The current level of the tree
        'courses_taken': Courses already taken from the user, scanned in from transcript
        'total': All the courses currently in the tree
        'tree': The tree being built
    """
    if course in course_dict and course:
        if course not in total:
            total.append(course)
            for index, crs in enumerate(course_dict[course]['Prerequisites'].split(';')):
                if set(split_course.split(crs)).isdisjoint(courses_taken):
                    for option in split_course.split(crs):
                        if option:
                            tree.attr('edge', arrowhead=arrowheads[index], arrowsize='1.1')
                            tree.attr('node', fillcolor='grey{}'.format(str(99 - (level * 3))))
                            tree.edge(course, option)
                            create_tree_helper(course_dict, option, level + 1, courses_taken, total, tree)


def console_tree(course_dict, courses_taken, course, indent):
    """Recursively prints all the prerequisite courses for the given 'course'
    @params
        'course_dict': The dictionary of courses
        'courses_taken': Courses already taken from the user, scanned in from transcript
        'course': The course in question
        NOT USED 'indent': The indentation level for each prerequisite course
    """
    def search_for(req, char):
        for course in req:
            if char in course:
                return course
        return ''

    if course and course in course_dict and course not in courses_taken:  
        check = course_dict[course]['Prerequisites'].split(';')
        for req in check:
            list_reqs = re.compile(r',|&&|/').split(req)
            if set(list_reqs).isdisjoint(courses_taken):
                for reqcourse in list_reqs:
                    if reqcourse:
                        branch = '{}{}'.format(indent, reqcourse)
                        if len(branch.strip()) is not 1 and branch.strip().replace('|', ''):
                            if len(list_reqs) <= 1 and '&&' not in req and '/' not in req:
                                print(branch) 
                            elif reqcourse in search_for(req.split(','), '&&').split('&&'):
                                print('{}&'.format(branch))
                            elif reqcourse in search_for(req.split(','), '/').split('/'):
                                print('{}#'.format(branch))
                            else:
                                print('{}*'.format(branch))
                        console_tree(course_dict, courses_taken, reqcourse, indent + '|   ')
                if len(check) > 1 and len(list_reqs) > 1:
                    print(indent.replace('|   ', '', 1))