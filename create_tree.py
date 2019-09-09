"""Creates a Prerequisite tree for a given course either as a PNG or in the console"""


import os    
import re
from utility import logger, scan_transcript, Prerequisite_Trees
try:
    from graphviz import Digraph
except Exception:
    raise Exception('Graphviz not installed. Try installing with "pip install graphviz"')
    

# Change PATH setup for Graphviz folder here:
# --------------------------GRAPHVIZ PATH SETUP------------------------- #
os.environ["PATH"] += os.pathsep + 'C:\\Graphviz\\bin'
# ---------------------------------------------------------------------- #

level_counter = None
width_counter = None
total = []

def create_tree(course_df, courses_taken, course, indent, webapp=False):
    """Starts the tree by adding the selected course as the top element
    @params
        'course_df': The dictionary of courses
        'courses_taken': Courses already taken from the user, scanned in from transcript
        'course': The course in question
        UNUSED: 'indent': The indentation level for each prerequisite course
    Returns
        The number of levels in the tree
    """
    # Tree used to draw the course prerequisite tree
    tree = Digraph(
        comment='Prerequisites',
        graph_attr = {'rankdir':'TB', 'splines':'ortho', 'overlap':'scale'},
        edge_attr = {'arrowhead': 'dot'}
    )
    global level_counter, width_counter
    level_counter = set()
    width_counter = set()
    if course in course_df.index and course not in courses_taken:
        if course_df.loc[course]['Prerequisites'] or course_df.loc[course]['Co-Requisites']:
            tree.node(course, course)
            tree.attr('node', shape='invtrapezium', style='rounded,filled', color='gray30')
            global total
            total = []
            # Recursively build up tree
            create_tree_helper(course_df, course, 0, courses_taken, tree)
            levels = max(level_counter)
            if levels:
                tree.render(os.path.normpath(f'{Prerequisite_Trees}/{course}'), view=not webapp, format='png')
            logger.info(f"Prerequisite Tree created for {course} in 'static/Prerequisite_Trees'")
            return min(list((levels, max(width_counter))))
    return -1


arrowheads = ['box', 'dot', 'normal', 'diamond', 'inv', 'tee', 'crow',
              'icurve', 'curve', 'vee', 'none']
split_course = re.compile(r'/|,|&&')
def create_tree_helper(course_df, course, level, courses_taken, tree):
    """Builds up the prerequisite tree
    @params
        'course_df': The dictionary of courses
        'course': The course in question
        'level': The current level of the tree
        'courses_taken': Courses already taken from the user, scanned in from transcript
        'tree': The tree being built
    """
    level_counter.add(level)
    if course in course_df.index and course:
        if course not in total:
            total.append(course)
            for i, requisite_type in enumerate(['Prerequisites', 'Co-Requisites']):
                for index, crs in enumerate(course_df.loc[course][requisite_type].split(';')):
                    split_crs = split_course.split(crs)
                    width_counter.add(len(split_crs))
                    if set(split_crs).isdisjoint(courses_taken):
                        for option in split_course.split(crs):
                            if option:
                                tree.attr('edge', arrowhead=arrowheads[index] if not i else f'o{arrowheads[index]}', arrowsize='1.1')
                                tree.attr('node', fillcolor=f'grey{str(99 - (level * 3))}' if not i else 'cyan')
                                tree.edge(course, option)
                                create_tree_helper(course_df, option, level + 1, courses_taken, tree)


def console_tree(course_df, courses_taken, course, indent):
    """Recursively prints all the prerequisite courses for the given 'course'
    @params
        'course_df': The dictionary of courses
        'courses_taken': Courses already taken from the user, scanned in from transcript
        'course': The course in question
        NOT USED 'indent': The indentation level for each prerequisite course
    """

    def search_for(req, char):
        for course in req:
            if char in course:
                return course
        return ''

    if course and course in course_df.index and course not in courses_taken:  
        check = course_df.loc[course]['Prerequisites'].split(';')
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
                        console_tree(course_df, courses_taken, reqcourse, indent + '|   ')
                if len(check) > 1 and len(list_reqs) > 1:
                    print(indent.replace('|   ', '', 1))
