"""Finds all combinations of classes given a list of courses to search"""

import json, re, os, itertools, time, uwtools
from datetime import datetime

UW_Time_Schedules = os.path.normpath(f'{os.getcwd()}/static/UW_Time_Schedules')
Organized_Time_Schedules = os.path.normpath(f'{UW_Time_Schedules}/Organized_Time_Schedules')

# --------------------------Time Methods--------------------------#       
get_time = lambda t: [t[0:1], t[1:]] if len(t) == 3 else [t[0:2], t[2:]]
check_pm = lambda t: ' PM' if t else ' AM'
convert = lambda t: time.strftime('%H:%M:%S', time.strptime(t, '%I:%M %p'))
check_convert_pm = lambda t: convert('12:01 AM') < convert(t) < convert('6:30 AM') or convert('10:30 PM') < convert(t) < convert('11:59 PM')
convert_pm = lambda t, pm: f'{pm[0]} {switch_pm(pm[-1])}' if check_convert_pm(t) else t
switch_pm = lambda t: 'AM' if t.strip() == 'PM' else 'PM'
# --------------------------Time Methods--------------------------#    


def has_overlap(time1, time2):
    """Checks if the two times overlap
    @params
        'time1': First time to check
        'time2': Second time to check
    Returns 
        True if there is overlap, otherwise False
    """
    pm1 = 'P' in time1
    pm2 = 'P' in time2
    time1 = time1.replace('P', '', 1)
    time2 = time2.replace('P', '', 1)
    times = list(itertools.chain(time1.split('-', 1), time2.split('-', 1)))
    times = list(map(get_time, times))
    course_times = []
    for i in range(0, len(times), 2):
        pm = pm1 if not i else pm2
        t1 = f'{times[i][0]}:{times[i][1]}{check_pm(pm)}'
        t2 = f'{times[i + 1][0]}:{times[i + 1][1]}{check_pm(pm)}'
        time1 = convert(convert_pm(t1, t1.rsplit(' ', 1)))
        time2 = convert(convert_pm(t2, t2.rsplit(' ', 1)))
        course_times.append((time1, time2))
    t1 = course_times[0]
    return t1[0] <= course_times[1][0] <= t1[1] or t1[0] <= course_times[1][1] <= t1[1]


def get_days(offered):
    """Gets the days a course is offered
    @params
        'offered': String representing the days a course is offered
        Example: 'MWF' -> Monday, Wednesday, Friday
    Returns
        Set of abbreviated days the course is offered
    """
    days = ['Th', 'M', 'T', 'W', 'F', 'S']
    result = set()
    for day in days:
        if day in offered:
            result.add(day)
            offered = offered.replace(day, '', 1)
    return result


def check_overlap(schedule):
    """Checks if the courses in the 'schedule' overlap
    @params
        'schedule': List of dictionaries representing a combination of courses
    Returns
        True if there is overlap between any sections in the 'schedule'.
        False otherwise.
    """
    course_information = {
            'M': [], 'T': [], 'W': [], 'Th': [], 'F': [], 'S':[]
    }
    for course in schedule:
        for course_dict in course:
            for i, d in enumerate(course_dict['Days']):
                for day in get_days(d):
                    course_information[day].append(course_dict['Time'][i])
    for times in course_information.values():
        if len(set(times)) == len(times):
            date_combos = list(itertools.combinations(times, 2))
            dates = [list(set(x)) for x in date_combos if len(set(x)) > 1]
            for date in dates:
                if has_overlap(date[0], date[1]):
                    return True
        else:
            return True
    return False


def get_combinations(planned_courses):
    """Finds all possible combinations of the courses in 'planned_courses'
    such that no sections of any course overlap
    @params
        'planned_courses': List of courses to find combinations from
    Returns
        Generator object with all valid combinations of courses
    """
    with open(os.path.normpath(f'{Organized_Time_Schedules}/Total.json'), mode='r') as file:
        courses_offered = json.loads(file.read())
    total = []
    for course in planned_courses:
        course_sections = []
        lecture = course.rsplit(' ', 1)[-1].strip().upper()
        if re.search(r'[A-Z]\d?', lecture) and ' ' in course:
            search = [courses_offered[course.rsplit(' ', 1)[0]][f'Lecture {lecture}']]
        else:
            search = courses_offered[course].values()
        # Get all Lecture/Quiz/Lab/Studio combinations for the given course
        for section in search:
            products = []
            for section_type in ['QZ', 'LB', 'ST']:
                if section[section_type]:
                    products.append(section[section_type])
            products.append([section['LECT']])
            course_sections.append(list(itertools.product(*products)))
        total.append([y for x in course_sections for y in x])
    # Find all course combinations where there are no course overlaps
    for combo in itertools.filterfalse(lambda x: check_overlap(x), itertools.product(*total)):
        yield combo


# Sections class used for the organized Time Schedule
class Sections:
    def __init__(self):
        self.LECT = ''
        self.QZ = []
        self.LB = []
        self.ST = []
    
    def add_section(self, section_type, data):
        if section_type == 'QZ':
            s_type = self.QZ
        elif section_type == 'LB':
            s_type = self.LB
        elif section_type == 'ST':
            s_type = self.ST
        else:
            return

        # Check if Section is already in the list for that section type.
        # For some courses, such as CHEM142 on the Seattle Campus, the Quiz and Lab Section
        # are grouped in the same section. This is why the 'Building', 'Days', 'Room Number', 
        # 'Seats', and 'Time' sections are represented as lists.
        for section in s_type[::-1]:
            if section['Section'] == data['Section']:
                break
        else:
            for section_data in ['Building', 'Days', 'Room Number', 'Seats', 'Time']:
                data[section_data] = [data[section_data]]
            s_type.append(data)
            return

        for section in s_type:
            if section['Section'] == data['Section']:
                for section_data in ['Building', 'Days', 'Room Number', 'Seats', 'Time']:
                    section[section_data].append(data[section_data])


def main():
    """Creates an Organized Time Schedule as a json file with all courses from
    all UW Campuses included for the current UW Quarter. 
    Organized Time Schedules include the Course as the Key. The associated value to 
    this key are all the lectures for this course with quiz, lab and studio sections
    included as a list
    """
    section_times = ['Building', 'Days', 'Room Number', 'Seats', 'Time']

    # Check if static/UW_Time_Schedules exists and create this directory if necessary
    try:
        os.mkdir(UW_Time_Schedules)
    except Exception: 
        pass
    # Check if static/UW_Time_Schedules/Organized_Time_Schedules exists and create 
    # this directory if necessary
    try:
        os.mkdir(Organized_Time_Schedules)
    except Exception:
        pass

    quarter = uwtools.get_quarter()
    upcoming_quarter = uwtools.get_quarter(type_='upcoming')
    year = datetime.now().year    
    if upcoming_quarter == 'WIN':
        year += 1

    time_schedules_dir = os.listdir(UW_Time_Schedules)
    
    if f'{upcoming_quarter}{year}.json' not in time_schedules_dir:
        df = uwtools.time_schedules(year=year, quarter=upcoming_quarter)
        # If the time schedule for the upcoming quarter is not available, check if
        # the time schedule for the current quarter has already been created. 
        # The time schedule for the current quarter will always be available.
        if df is None or df.empty:
            year = year - 1 if upcoming_quarter == 'WIN' else year
            if f'{quarter}{year}.json' not in time_schedules_dir:
                df = uwtools.time_schedules(year=year, quarter=quarter)
            else:
                return

        # Create a dictionary with Course Names (i.e EE235) as keys and a list of course sections
        # (as dictionaries) as values. 
        total = {}
        for dict_ in df.to_dict(orient='records'):
            course_name = dict_['Course Name']
            if course_name not in total:
                total[course_name] = [dict_]
            else:
                total[course_name].append(dict_)
        # Store the course dictionary in a .json file
        with open(os.path.normpath(f'{UW_Time_Schedules}/{upcoming_quarter}{year}.json'), mode='w') as file:
            json.dump(total, file, indent=4, sort_keys=True)
    
        # Create a dictionary with course names (i.e EE235) as keys.
        # The value for every key is another dictionary with Lectures as keys (i.e Lecture A).
        # These lecture keys have another dictionary with section types as keys (LECT, QZ, LB, ST).
        # The LECT key has the information for the lecture, every other key has a list as a value with
        # dictionaries representing every QZ/LB/ST section for that lecture.
        course_map = {}
        for course in total.keys():
            course_list = total[course]
            section_map = {}
            for section in course_list:
                section_type = section['Type']
                if section_type == 'LECT':
                    course_sections = Sections()
                    for section_data in section_times:
                        section[section_data] = [section[section_data]]
                    course_sections.LECT = section
                    section_map['Lecture {}'.format(section['Section'])] = course_sections.__dict__
                else:
                    course_sections.add_section(section_type, section)
            course_map[course] = section_map
        # Store these Organized Time Schedules as a .json file
        with open(os.path.normpath(f'{Organized_Time_Schedules}/Total.json'), mode='w') as file:
            json.dump(course_map, file, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()