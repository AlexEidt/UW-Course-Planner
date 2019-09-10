"""Common methods and Directory Names used by the other scripts"""

import logging, re, json, os

# -----------------------Directories----------------------- #
UW_Time_Schedules = os.path.normpath(f'{os.getcwd()}/static/UW_Time_Schedules')
Organized_Time_Schedules = os.path.normpath(f'{UW_Time_Schedules}/Organized_Time_Schedules')
Prerequisite_Trees = os.path.normpath(f'{os.getcwd()}/static/Prerequisite_Trees')
# --------------------------------------------------------- #


# -----------------------Logger----------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s -- %(asctime)s -- %(levelname)s : %(message)s')
handler = logging.FileHandler('Log.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)
# ---------------------------------------------------- #


# -----------------------Methods----------------------- #
def scan_transcript(course_df, webapp=False):
    """Asks the user if their transcript should be scanned in to remove classes from the class
       tree that they've already taken.
    @params 
        'course_df': The dictionary of courses scanned in from the campus selected by the user
    Returns
        List of courses taken from the transcript given
    """
    if not webapp:
        print('If you would like to scan in your transcript to eliminate searching courses you have')
        print("already taken, go to MyUW under 'Unofficial Transcript' and press CTRL+A and paste")
        print('your transcript into a text file in the same directory as this script.')
        transcript = input('Scan in Transcript? (y/n): ').lower()
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
                if line_data in course_df.index and not dropped:
                    courses_taken.append(line_data)
    return courses_taken

