"""Creates/Updates TSV/JSON Files based on user input and creates a prerequisite
tree in the console or as a PNG file. 
"""

import csv
import os
import re
import json
import logging
from datetime import datetime
from parse_courses import gather, CAMPUSES, COLUMN_NAMES
from create_tree import create_tree, console_tree

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s -- %(asctime)s -- %(levelname)s : %(message)s')
handler = logging.FileHandler('Log.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

course_dir = 'UW_Campus_Catalogs' # Name of Folder with Campus tsv/json files
course_files_dir = f'{os.getcwd()}\\{course_dir}' # course_dir file path


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
            try: 
                os.remove(f'{course_files_dir}\\JSON\\Total.json')
            except (FileExistsError, FileNotFoundError) as e: 
                pass
            try: 
                os.remove(f'{course_files_dir}\\JSON\\Total.tsv')
            except (FileExistsError, FileNotFoundError) as e: 
                pass
            print(f"Creating TSV/JSON docs for {', '.join(list(CAMPUSES.keys()))} UW Campuses...")
            check_parse = gather(course_files_dir)
            total = open(f'{course_files_dir}\\TSV\\Total.tsv', mode='a')
            csv.writer(total, delimiter='\t').writerow(COLUMN_NAMES)
            for campus in CAMPUSES.keys():
                courses_dict = read_file(campus)
                write_json(courses_dict, 'w', campus)
                logger.info(f'JSON File for UW {campus} created under {course_files_dir}\\JSON')
                with open(f'{course_files_dir}\\TSV\\{campus}.tsv') as campus_file: 
                    next(campus_file)
                    for line in campus_file:
                        total.write(line)
            write_json(read_file('Total'), 'w', 'Total')
            logger.info(f'JSON File for All UW Campuses created under {course_files_dir}\\JSON')
            total.close()
            if not check_parse:
                print('There has been an error parsing courses from the UW Course Catalogs. Check ParseUW.log')
                print(f'Courses from the following deparment(s) were not scanned: {str(check_parse)}')


def read_file(campus):
    """Scans the tsv file for the given 'campus'
    @params
        'campus': The campus to search courses from
    Returns:
        Dictionary of all course ID's with their information
    """
    all_courses = {}
    with open(f'{course_files_dir}\\TSV\\{campus}.tsv', mode='r') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)
        for course in reader: 
            if course:
                all_courses['{0[1]}{0[2]}'.format(course)] = {
                    COLUMN_NAMES[i]: course[i] for i in range(len(COLUMN_NAMES))
                }
    return all_courses


def scan_transcript(course_dict):
    """Asks the user if their transcript should be scanned in to remove classes from the class
       tree that they've already taken.
    @params 
        'course_dict': The dictionary of courses scanned in from the campus selected by the user
    Returns
        List of courses taken from the transcript given
    """
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


def write_json(all_courses, mode_type, campus):
    """Writes the complete course dictionary for a UW Campus to a JSON file
    @params
        'all_courses': Course dictionary
        'mode_type': Write or append to file
        'campus': The campus the courses are from
    """
    file_name = f'{course_files_dir}\\JSON\\{campus}.json'
    with open(file_name, mode=mode_type) as json_file:
        json.dump(all_courses, json_file, indent=4, sort_keys=True)


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


def main():
    """Creates the campus tsv files if necessary and prompts the user for a UW
       Campus and the course they would like to search for"""
    check_files()
    campus = select_option(CAMPUSES.keys(), 'Choose a UW Campus: ')
    all_courses = read_file(campus)
    courses_taken = scan_transcript(all_courses)
    enter_courses(all_courses, courses_taken)


if __name__ == '__main__':
    main()
