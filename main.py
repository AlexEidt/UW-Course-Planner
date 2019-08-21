"""Creates/Updates TSV/JSON Files based on user input and creates a prerequisite
tree in the console or as a PNG file. 
"""

import csv, os, re, json, logging
from datetime import datetime
from parse_courses import gather, CAMPUSES, COLUMN_NAMES, read_file
from create_tree import create_tree, console_tree
from utility import logger, check_connection, scan_transcript, UW_Course_Catalogs
try:
    import requests
except Exception:
    raise Exception('Requests not installed. Try installing with "pip install requests"')


def check_files():
    """Creates a directory called 'course_dir' in the current directory if it does
    not already exist. Initializes this directory with all missing campus files
    if the directory had just been created. If the directory was already present,
    the user can choose to update it.
    """
    try:
        os.mkdir(UW_Course_Catalogs)
        try: 
            os.mkdir(os.path.normpath(f'{UW_Course_Catalogs}/JSON'))
        except Exception: pass
        try: 
            os.mkdir(os.path.normpath(f'{UW_Course_Catalogs}/TSV'))
        except Exception: pass
    except Exception:
        last_updated = str(datetime.fromtimestamp(os.stat(UW_Course_Catalogs).st_mtime)).split('.')[0]
        print(f'Course catalogs were last updated on {last_updated}')
        update = input('Would you like to update the Course Catalogs? (y/n): ')
    else:
        update = 'y'
    finally:
        if 'y' in update.lower():
            print(f"Creating TSV/JSON docs for {', '.join(list(CAMPUSES.keys()))} UW Campuses...")
            gather()
            print('Check the Log for any departments that may not have been parsed')


def select_option(options, prompt, value=None):
    """Prints the enumerated options to the console and allows the user to choose
    @params
        'options': Iterable with the options for the user
        'prompt': The prompt printed to the console
    Returns
        Value selected by user
    """
    dict = {str(c[0]): c[1] for c in list(enumerate(options, start=1))}
    print(str([f'{key}. {value}' for key, value in dict.items()])[1:-1].replace("'", ''))
    while value not in dict.keys() and value not in dict.values():
        value = input(prompt)
    return value if not value.isdigit() else dict[value]


def get_course_data(all_courses, more='y'):
    """Asks user if they want to get any specific data for a course
    @params
        'all_courses': Course dictionary
    """
    get_more = input('Search for more specific course data? (y/n): ').lower()
    if 'y' in get_more:
        while 'y' in more:
            course = input('Select course: ').upper().replace(' ', '')
            option = select_option(COLUMN_NAMES, 'Select course data option: ')
            if course in all_courses:
                print(all_courses[course][option])
            else:
                print(f'{course} is not a course offered at UW.')
            more = input('Continue searching for more specific course data? (y/n): ').lower()


def enter_courses(all_courses, courses_taken, more='y'):
    """Prompts the user for courses to generate PNG or console prerequisite trees
    @params
        'all_courses': Course dictionary
        'courses_taken': Courses already taken from the user, scanned in from transcript
    """
    tree = select_option(['Console', 'PNG', 'Both'], 'Select Prerequisite Tree Type: ')
    tree_dict = {'Console': [console_tree], 'PNG': [create_tree], 'Both': [console_tree, create_tree]}
    while 'y' in more:
        course = input('Enter a Course: ').upper().replace(' ', '')
        print('****************************************************')
        if course in all_courses:
            for function in tree_dict[tree]:
                function(all_courses, courses_taken, course, '')
        else:
            print(f'{course} is not a course offered at UW.')
        more = input('Continue? (y/n): ').lower()


def keyword_search(all_courses, courses_taken):
    """Prints all courses that include the given keyword in their course description.
       (Case-insensitive)
    @params
        'all_courses': Course dictionary
        'courses_taken': Courses already taken from the user, scanned in from transcript
    """
    more = input('Search for keywords in course descriptions? (y/n): ').lower()
    while 'y' in more:
        keyword = input('Enter a Keyword: ').lower()
        courses_taken = scan_transcript(all_courses, webapp=True)
        for course, data in all_courses.items():
            if keyword in data['Description'].lower() and course not in courses_taken:
                print(f'{course}\t{data}')
        more = input('Continue Keyword Search? (y/n) ').lower()


def main(more='y'):
    """Creates the campus tsv files if necessary and prompts the user for a UW
       Campus and the course they would like to search for"""
    check_files()
    campus = select_option(CAMPUSES.keys(), 'Choose a UW Campus: ')
    all_courses = read_file(campus)
    courses_taken = scan_transcript(all_courses)
    while 'y' in more:
        enter_courses(all_courses, courses_taken)
        get_course_data(all_courses)
        keyword_search(all_courses, courses_taken)
        more = input('Continue course searches? (y/n)').lower()


if __name__ == '__main__':
    if check_connection():
        main()
    else:
        logger.critical('No Internet Connection')
        print('No Internet Connection')

