"""Geocodes all Building on the UW Seattle Campus
Finds all combinations of classes given a list of courses to search"""

import json, re, os, logging, itertools, time
from datetime import datetime as dttime
import uwtools
from threading import Thread
from utility import logger, UW_Time_Schedules, Organized_Time_Schedules


def get_all_buildings():
    """Creates a dictionary with building abbreviations and their full names
    Returns
        Dictionary with abbreviation, full name pairings for all buildings
    """
    upcoming_quarter = uwtools.get_quarter(type_='upcoming')
    quarter = uwtools.get_quarter()
    year = dttime.now().year
    if upcoming_quarter == 'WIN':
        if dttime.now().month in [9, 10, 11, 12]:
            year += 1
    if quarter != upcoming_quarter and year == dttime.now().year + 1:
        year -= 1

    try:
        os.mkdir(UW_Time_Schedules)
    except Exception: pass
    if f'{upcoming_quarter}{year}.json' not in os.listdir(UW_Time_Schedules):
        df = uwtools.time_schedules(year=year, quarter=upcoming_quarter)
        total = {}
        if df is not None and not df.empty:
            for dict_ in df.to_dict(orient='records'):
                course_name = dict_['Course Name']
                if course_name not in total:
                    total[course_name] = [dict_]
                else:
                    total[course_name].append(dict_)
            with open(os.path.normpath(f'{UW_Time_Schedules}/{upcoming_quarter}{year}.json'), mode='w') as file:
                json.dump(total, file, indent=4, sort_keys=True)
        else:
            upcoming_quarter = quarter


    with open(os.path.normpath(f'{UW_Time_Schedules}/{upcoming_quarter}{year}.json'), mode='r') as file:
        return json.loads(file.read())


# --------------------------Time Methods--------------------------#       
get_time = lambda t: [t[0:1], t[1:]] if len(t) == 3 else [t[0:2], t[2:]]
check_pm = lambda t: ' PM' if t else ' AM'
select_pm = lambda i, pm1, pm2: pm1 if not i else pm2
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
    time1 = time1.replace('P', '')
    time2 = time2.replace('P', '')
    times = list(itertools.chain(time1.split('-', 1), time2.split('-', 1)))
    times = list(map(get_time, times))
    course_times = []
    for i in range(0, len(times), 2):
        pm = select_pm(i, pm1, pm2)
        t1 = f'{times[i][0]}:{times[i][1]}{check_pm(pm)}'
        t2 = f'{times[i + 1][0]}:{times[i + 1][1]}{check_pm(pm)}'
        time1 = convert(convert_pm(t1, t1.rsplit(' ', 1)))
        time2 = convert(convert_pm(t2, t2.rsplit(' ', 1)))
        course_times.append((time1, time2))
    t1 = course_times[0]
    return t1[0] < course_times[1][0] < t1[1] or t1[0] < course_times[1][1] < t1[1]


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
            if section['QZ']:
                products.append(section['QZ'])
            if section['LB']:
                products.append(section['LB'])
            if section['ST']:
                products.append(section['ST'])
            products.append([section['LECT']])
            course_sections.append(list(itertools.product(*products)))
        total.append([y for x in course_sections for y in x])
    # Find all course combinations where there are no course overlaps
    for combo in itertools.filterfalse(lambda x: check_overlap(x), list(itertools.product(*total))):
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

        for section in s_type:
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

    try:
        os.mkdir(UW_Time_Schedules)
    except Exception: 
        pass
    quarter = uwtools.get_quarter()
    upcoming_quarter = uwtools.get_quarter(type_='upcoming')
    year = dttime.now().year
    if upcoming_quarter == 'WIN':
        if dttime.now().month in [9, 10, 11, 12]:
            year += 1
    if quarter != upcoming_quarter and year == dttime.now().year + 1:
        year -= 1
    if f'{upcoming_quarter}{year}.json' not in os.listdir(UW_Time_Schedules):
        courses = get_all_buildings()
        course_map = {}
        for course in courses.keys():
            course_list = courses[course]
            section_map = {}
            for section in course_list:
                section_type = section['Type']
                if section_type in ['LECT', 'VAR']:
                    course_sections = Sections()
                    for section_data in section_times:
                        section[section_data] = [section[section_data]]
                    course_sections.LECT = section
                    section_map['Lecture {}'.format(section['Section'])] = course_sections.__dict__
                else:
                    course_sections.add_section(section_type, section)
            course_map[course] = section_map
        try:
            os.mkdir(Organized_Time_Schedules)
        except Exception: pass
        with open(os.path.normpath(f'{Organized_Time_Schedules}/Total.json'), mode='w') as file:
            json.dump(course_map, file, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()


