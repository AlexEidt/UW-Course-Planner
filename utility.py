"""Common methods and Directory Names used by the other scripts"""

import re, json, os

# -----------------------Directories----------------------- #
UW_Time_Schedules = os.path.normpath(f'{os.getcwd()}/static/UW_Time_Schedules')
Organized_Time_Schedules = os.path.normpath(f'{UW_Time_Schedules}/Organized_Time_Schedules')
Prerequisite_Trees = os.path.normpath(f'{os.getcwd()}/static/Prerequisite_Trees')
# --------------------------------------------------------- #

# -----------------------Methods----------------------- #
def scan_transcript(course_df):
    """Asks the user if their transcript should be scanned in to remove classes from the class
       tree that they've already taken.
    @params 
        'course_df': The dictionary of courses scanned in from the campus selected by the user
    Returns
        List of courses taken from the transcript given
    """
    try:
        open('Transcript.txt')
    except FileNotFoundError:
        return []
    else:
        courses_taken = []
        with open('Transcript.txt', mode='r') as transcript:
            for line in transcript:
                if 'CUMULATIVE CREDIT SUMMARY' in line:
                    break
                match = re.search(r'([A-Z& ]+\s?\d{3})', line)
                if match:
                    dropped = re.search(r'\d\.\d\s+W\d\s', line)
                    line_data = match.group(0).replace(' ', '')
                    if line_data in course_df.index and not dropped:
                        courses_taken.append(line_data)
        return courses_taken