"""Creates a Prerequisite tree for a given course either as a PNG or in the console"""


import os    
import re
import logging
from graphviz import Digraph

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s -- %(asctime)s -- %(levelname)s : %(message)s')
handler = logging.FileHandler('Log.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    Returns
        The number of levels in the tree
    """
    # Tree used to draw the course prerequisite tree
    tree = Digraph(
        comment=f'{course} Prerequisites',
        graph_attr = {'rankdir':'TB', 'splines':'ortho', 'overlap':'scale'},
        edge_attr = {'arrowhead': 'dot'}
    )
    global level_counter
    level_counter = set()
    tree.node(course, course)
    tree.attr('node', shape='invtrapezium', style='rounded,filled', color='gray30')
    # Recursively build up tree
    global total
    total = []
    create_tree_helper(course_dict, course, 0, courses_taken, tree)
    tree.render('static\\Prerequisite_Trees\\{}'.format(course), view=False, format='png')
    logger.info(f"Prerequisite Tree created for {course} in 'static/Prerequisite_Trees'")
    return max(level_counter)


arrowheads = ['box', 'dot', 'normal', 'diamond', 'tee', 'crow',
              'icurve', 'curve', 'inv', 'vee', 'none']
split_course = re.compile(r'/|,|&&')
def create_tree_helper(course_dict, course, level, courses_taken, tree):
    """Builds up the prerequisite tree
    @params
        'course_dict': The dictionary of courses
        'course': The course in question
        'level': The current level of the tree
        'courses_taken': Courses already taken from the user, scanned in from transcript
        'tree': The tree being built
    """
    level_counter.add(level)
    if course in course_dict and course:
        if course not in total:
            total.append(course)
            for index, crs in enumerate(course_dict[course]['Prerequisites'].split(';')):
                if set(split_course.split(crs)).isdisjoint(courses_taken):
                    for option in split_course.split(crs):
                        if option:
                            tree.attr('edge', arrowhead=arrowheads[index], arrowsize='1.1')
                            tree.attr('node', fillcolor=f'grey{str(99 - (level * 3))}')
                            tree.edge(course, option)
                            create_tree_helper(course_dict, option, level + 1, courses_taken, tree)


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
            list_reqs = split_course.split(req)
            if set(list_reqs).isdisjoint(courses_taken):
                for reqcourse in list_reqs:
                    if reqcourse:
                        branch = f'{indent}{reqcourse}'
                        if len(branch.strip()) is not 1 and branch.strip().replace('|', ''):
                            if len(list_reqs) <= 1 and '&&' not in req and '/' not in req:
                                print(branch) 
                            elif reqcourse in search_for(req.split(','), '&&').split('&&'):
                                print(f'{branch}&')
                            elif reqcourse in search_for(req.split(','), '/').split('/'):
                                print(f'{branch}#')
                            else:
                                print(f'{branch}*')
                        console_tree(course_dict, courses_taken, reqcourse, indent + '|   ')
                if len(check) > 1 and len(list_reqs) > 1:
                    print(indent.replace('|   ', '', 1))

