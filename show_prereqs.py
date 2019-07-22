import csv
import os
import re
import json
from datetime import datetime
from parse_courses import gather, CAMPUSES


course_dir = 'UW_Campus_Catalogs' # Name of Folder with Campus tsv/json files
course_files_dir = '{}\\{}'.format(os.getcwd(), course_dir) # course_dir file path


# Creates a directory called 'course_dir' in the current directory if it does
# not already exist. Initializes this directory with all missing campus files
# if the directory had just been created. If the directory was already present,
# the user can choose to update it.
def check_files():
    try:
        os.mkdir(course_dir)
        print('Created Directory {} in {}'.format(course_dir, os.getcwd()))
        try: os.mkdir('{}\\{}'.format(course_files_dir, 'JSON'))
        except Exception: pass
        try: os.mkdir('{}\\{}'.format(course_files_dir, 'TSV'))
        except Exception: pass
    except Exception:
        last_updated = str(datetime.fromtimestamp(os.stat(course_files_dir).st_mtime)).split('.')[0]
        print('Course catalogs were last updated on {}'.format(last_updated))
        update = input('Would you like to update the Course Catalogs? (y/n): ')
    else:
        update = 'y'
    finally:
        if 'y' in update.lower():
            try: os.remove('{}\\{}\\{}'.format(course_files_dir, 'JSON', 'Total.json'))
            except (FileExistsError, FileNotFoundError) as e: pass
            try: os.remove('{}\\{}\\{}'.format(course_files_dir, 'TSV', 'Total.tsv'))
            except (FileExistsError, FileNotFoundError) as e: pass
            print('Creating TSV/JSON docs for {} UW Campuses...'.format(str(list(CAMPUSES.keys()))[1:-1].replace("'", '')))
            gather(course_files_dir)
            for campus in CAMPUSES.keys():
                courses_dict = read_file(campus)
                write_json(courses_dict, 'w', campus)
                write_json(courses_dict, 'a', 'Total')
                with open('{}\\{}\\{}.tsv'.format(course_files_dir, 'TSV', campus)) as campus_file:
                    with open('{}\\{}\\{}.tsv'.format(course_files_dir, 'TSV', 'Total'), mode='a') as total:
                        for line in campus_file:
                            total.write(line)


# Scans the tsv file for the given 'campus'
# 'campus': The campus to search courses from
# Returns a dictionary of all course ID's with their information
def read_file(campus):
    all_courses = {}
    try:
        with open('{}\\{}\\{}.tsv'.format(course_files_dir, 'TSV', campus), mode='r') as file:
            reader = csv.reader(file, delimiter='\t')
            column_names = next(reader)
            for course in reader: 
                    all_courses['{0[1]}{0[2]}'.format(course)] = {
                        column_names[i]: course[i] for i in range(len(column_names))
                    }
    except (FileExistsError, FileNotFoundError) as e:
        print(e)
        return {}
    else:
        return all_courses


# Recursively prints all the prerequisite courses for the given 'course'
# 'course_dict': The dictionary of courses
# 'course': The course in question
# 'indent': The indentation level for each prerequisite course
def show_prerequisites(course_dict, courses_taken, course, indent):

    def search_for(req, char):
        for course in req:
            if char in course:
                return course
        return ''

    if course is not '' and course in course_dict and course not in courses_taken:  
        check = course_dict[course]['Prerequisites'].split(';')
        for req in check:
            list_reqs = re.compile(r',|&&|/').split(req)
            #list_reqs = req.split(',')
            if set(list_reqs).isdisjoint(courses_taken):
                for reqcourse in list_reqs:
                    if reqcourse is not '':
                        branch = '{}{}'.format(indent, reqcourse)
                        if len(branch.strip()) is not 1 and len(branch.strip().replace('|', '')) is not 0:
                            if len(list_reqs) <= 1 and '&&' not in req and '/' not in req:
                                print(branch) 
                            elif reqcourse in search_for(req.split(','), '&&').split('&&'):
                                print('{}&'.format(branch))
                            elif reqcourse in search_for(req.split(','), '/').split('/'):
                                print('{}#'.format(branch))
                            else:
                                print('{}*'.format(branch))
                        show_prerequisites(course_dict, courses_taken, reqcourse, indent + '|   ')
                if len(check) > 1 and len(list_reqs) > 1:
                    print(indent.replace('|   ', '', 1))


# Asks the user if their transcript should be scanned in to remove classes from the class
# tree that they've already taken. 
# 'course_dict': The dictionary of courses scanned in from the campus selected by the user
# Returns a list of courses taken from the transcript given
def scan_transcript(course_dict):
    print('If you would like to scan in your transcript to eliminate searching courses you have')
    print("already taken, go to MyUW under 'Unofficial Transcript' and press CTRL+A and paste")
    print('your transcript into a text file in the same directory as this script.')
    transcript = input('Scan in Transcript? (y/n): ')
    file_name = ''
    if 'y' in transcript:
        check = False
        while not check:
            file_name = input('Transcript file name: ')
            check = file_name in os.listdir(os.getcwd())
    else:
        return []
    courses_taken = []
    try:
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
    except (FileExistsError, FileNotFoundError) as e:
        print(e)
        return []
    else:
        return courses_taken


# Writes the complete course dictionary for a UW Campus to a JSON file
# 'all_courses': Course dictionary
# 'campus': The campus the courses are from
def write_json(all_courses, mode_type, campus):
    file_name = '{}\\{}\\{}.json'.format(course_files_dir, 'JSON', campus)
    with open(file_name, mode=mode_type) as json_file:
        json.dump(all_courses, json_file, indent=4, sort_keys=True)


# Creates the campus tsv files if necessary and prompts the user for a UW
# Campus and the course they would like to search for
def start():
    check_files()
    for num, campus in enumerate(CAMPUSES.keys(), start=1):
        print(campus)
    campus = ''
    while campus not in CAMPUSES.keys():
        campus = input('Choose a UW Campus: ')
    all_courses = read_file(campus)
    courses_taken = scan_transcript(all_courses)
    more = 'y'
    while 'y' in more:
        course = input('Enter a Course: ')
        print('****************************************************')
        show_prerequisites(all_courses, courses_taken, course, '')
        more = input('Continue? (y/n): ').lower()


start()

with open('Prereqs.txt', mode='w') as prereq:
    for key, course in read_file('Total').items():
        if course['Prerequisites'] is not '':
            prereq.write('{}{}: {}{}'.format(course['Department Name'], course['Course Number'], course['Prerequisites'], '\n'))
