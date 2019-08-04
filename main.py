"""Creates/Updates TSV/JSON Files based on user input and creates a prerequisite
tree in the console or as a PNG file. 
"""

import csv
import os
import re
import json
import logging
import requests
from datetime import datetime
from parse_courses import gather, CAMPUSES, COLUMN_NAMES, course_files_dir, course_dir, read_file
from create_tree import create_tree, console_tree

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s -- %(asctime)s -- %(levelname)s : %(message)s')
handler = logging.FileHandler('Log.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_files():
    """Creates a directory called 'course_dir' in the current directory if it does
    not already exist. Initializes this directory with all missing campus files
    if the directory had just been created. If the directory was already present,
    the user can choose to update it.
    """
    try:
        os.mkdir(course_dir)
        message = f'Created Directory {course_dir} in {os.getcwd()}'
        print(message)
        logger.info(message)
        try: 
            os.mkdir(f'{course_files_dir}\\JSON')
        except Exception: 
            logger.info(f'JSON Directory created in {course_dir}')
        try: 
            os.mkdir(f'{course_files_dir}\\TSV')
        except Exception: 
            logger.info(f'TSV Directory created in {course_dir}')
    except Exception:
        last_updated = str(datetime.fromtimestamp(os.stat(course_files_dir).st_mtime)).split('.')[0]
        print(f'Course catalogs were last updated on {last_updated}')
        update = input('Would you like to update the Course Catalogs? (y/n): ')
    else:
        update = 'y'
    finally:
        if 'y' in update.lower():
            print(f"Creating TSV/JSON docs for {', '.join(list(CAMPUSES.keys()))} UW Campuses...")
            gather(course_files_dir)
            print('Check the Log for any departments that may not have been parsed')


def scan_transcript(course_dict, webapp=False):
    """Asks the user if their transcript should be scanned in to remove classes from the class
       tree that they've already taken.
    @params 
        'course_dict': The dictionary of courses scanned in from the campus selected by the user
    Returns
        List of courses taken from the transcript given
    """
    if not webapp:
        print('If you would like to scan in your transcript to eliminate searching courses you have')
        print("already taken, go to MyUW under 'Unofficial Transcript' and press CTRL+A and paste")
        print('your transcript into a text file in the same directory as this script.')
        transcript = input('Scan in Transcript? (y/n): ')
        file_name = ''
        if 'y' in transcript.lower():
            check = False
            while not check:
                file_name = input('Transcript file name: ')
                check = file_name in os.listdir(os.getcwd())
        else:
            return []
    else:
        try:
            open('Transcript.txt')
        except Exception:
            return []
        else:
            file_name = 'Transcript.txt'
    courses_taken = []
    with open(file_name, mode='r') as transcript:
        for line in transcript:
            if 'CUMULATIVE CREDIT SUMMARY' in line:
                break
            match = re.search(r'([A-Z& ]+\s?\d{3})', line)
            if match:
                dropped = re.search(r'\d\.\d\s+W\d\s', line)
                line_data = match.group(0).replace(' ', '')
                if line_data in course_dict and not dropped:
                    courses_taken.append(line_data)
    return courses_taken


def check_connection(url='https://www.google.com/'):
    """Checks for a connection to the internet
    Returns
        True if internet is connected, False otherwise
    """
    try:
        requests.get(url)
    except Exception:
        return False
    else:
        return True


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


def keyword_search(all_courses, courses_taken, more='y'):
    """Prints all courses that include the given keyword in their course description.
       (Case-insensitive)
    @params
        'all_courses': Course dictionary
        'courses_taken': Courses already taken from the user, scanned in from transcript
    """
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
        logger.critical("No Internet Connection")
        print('Could not connect to the Internet')
