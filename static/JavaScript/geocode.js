const days = ['', 'Monday', 'Tuesday', 'Wednesday',
                          'Thursday', 'Friday', 'Saturday',
                          'Sunday'];
const daysShort = ['M', 'T', 'W', 'Th', 'F'];

$(document).ready(function() {

    // Center map on the University of Washington's 'Red Square', considered by many to
    // be the center of the Seattle Campus
    var mymap = L.map('mapid').setView([47.65587781988791, -122.30949282646179], 17);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}.png', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom, 2012'
    }).addTo(mymap)

    var chosen = ['CSE351', 'EE233', 'CLAS320', 'MATH308'];

    $.ajax({
        url: '/get_geocode/',
        type: 'POST',
    }).done(function(response) {
        var coords = response.data;
        Object.keys(coords).forEach(function(key) {
            
            try {
                latitude = parseFloat(response.data[key]['Latitude']);
                longitude = parseFloat(response.data[key]['Longitude']);
                L.marker([latitude, longitude]).addTo(mymap)
            } catch (error) {
            }
            
        });

        // Create table with courses
        var table = document.getElementById('table');
        var daysOfWeek = table.insertRow();
        for (var i = 0; i < days.length; i++) {
            var cell = table.rows[0].insertCell();
            cell.innerHTML = '<strong>' + days[i] + '</strong>';
        }
        for (var i = 0; i < 20; i++) {
            var row = table.insertRow();
            for (var j = 0; j < days.length; j++) {
                row.insertCell();
            }
        }
        /*
        for (var i = 13; i < 46; i++) {
            var row = table.insertRow();
            var cell = row.insertCell();
            cell.innerHTML = '<strong>' + getTime(i / 2) + '</strong>';
            for (var j = 1; j < days.length; j++) {
                row.insertCell();
            }
        }*/

        var rowIndex = 1;
        var courseMap = {};
        // Fill in table with chosen courses
        var course = response.courses;
        for (var i = 0; i < chosen.length; i++) {
            // Find department from course name
            var pattern = /[A-Z&]+/g;
            var result = pattern.exec(chosen[i]);
            var courseList = course[result][chosen[i]];
            
            var building = courseList[0].Building;
            var latitude = parseFloat(coords[building]['Latitude']);
            var longitude = parseFloat(coords[building]['Longitude']);
            if (latitude != '' && longitude != '') {
                L.marker([latitude, longitude]).addTo(mymap) 
            }
            
            var sectionMap = {};
            for (var j = 0; j < courseList.length; j++) {
                sectionType = courseList[j]['Type'];
                switch (sectionType) {
                case 'LECT':
                case 'VAR':       
                    var courseSections = {
                        CourseInformation: courseList[j],
                        QZ: [], 
                        LB: [], 
                        ST: []
                    };
                    sectionMap['Lecture ' + courseList[j]['Section']] = courseSections;
                    break;
                default:
                    courseSections[sectionType].push(courseList[j]);
                }
            }
            //document.getElementById("table").rows[Math.floor(time)].cells[daysOffered[j]].innerHTML = chosen[i];
            
            courseMap[chosen[i]] = sectionMap;
            daysOffered = getDays(chosen[i], 'A', course[result]);
            for (var j = 0; j < daysOffered.length; j++) {
                table.rows[rowIndex].cells[daysShort.indexOf(daysOffered[j]) + 1].innerHTML = chosen[i] + '<br/>'
                    + courseList[0].Type + ' ' + courseList[0].Section + '<br/>' + courseList[0].Building + '<br/>' + 
                    courseList[0].Time;
            }
            rowIndex++;
            quiz = sectionMap['Lecture A']['QZ'];
            if (quiz.length > 0) {
                quizDays = getDays(chosen[i], quiz[0].Section, course[result]);
                for (var j = 0; j < quizDays.length; j++) {
                    table.rows[rowIndex].cells[daysShort.indexOf(quizDays[j]) + 1].innerHTML = chosen[i] + '<br/>'
                    + quiz[0].Type + ' ' + quiz[0].Section + '<br/>' + quiz[0].Building + '<br/>' + 
                    quiz[0].Time;
                }
            }
            lab = sectionMap['Lecture A']['LB'];
            if (lab.length > 0) {
                labDays = getDays(chosen[i], lab[0].Section, course[result]);
                for (var j = 0; j < labDays.length; j++) {
                    table.rows[rowIndex].cells[daysShort.indexOf(quizDays[j]) + 1].innerHTML = chosen[i] + '<br/>'
                    + lab[0].Type + ' ' + lab[0].Section + '<br/>' + lab[0].Building + '<br/>' + 
                    lab[0].Time;
                }
            }
            rowIndex ++;
        }
        console.log(courseMap);
        
    });

});



// Returns an Array of Strings representing the days (full names) the
// given course is offered
function getDays (course, section, courseMap) {
    var courseInformation = courseMap[course];
    var daysOn = null;
    for (var i = 0; i < courseInformation.length; i++) {
        if (courseInformation[i]['Section'] == section) {
            daysOn = courseInformation[i]['Days'];
            break;
        }
    }
    var daysOffered = new Array();
    for (var j = 0; j < daysShort.length; j++) {
        if (daysOn.startsWith('Th')) {
            daysOffered.push('Th');
            daysOn = daysOn.replace('Th', '');
            console.log(course, daysOn);
            continue;
        }
        if (daysOn.startsWith(daysShort[j])) {
            daysOffered.push(daysShort[j]);
            daysOn = daysOn.replace(daysShort[j], '');
        }
    }
    return daysOffered;
}

// Returns the time as a String on a 12-hour clock
function getTime (time) {
    if (time > 12) {
    time -= 12; 
    }
    if (time == 0.5) {
        time = 12.5;
    }
    if (time % 1 === 0) {
        return (time) + ':00';
    } else {
        return Math.floor(time) + ':30';
    }
}

// Returns the Distance in meters between two buildings
function getDistance (building1, building2) {
    if (coords[building1]['Latitude'] == '' ||
        coords[building1]['Longitude'] == '') {
        alert('Could not find Coordinates for ' + building1 + ' hall');
        return null;
    } else if (coords[building2]['Latitude'] == '' ||
        coords[building2]['Longitude'] == '') {
        alert('Could not find Coordinates for ' + building2 + ' hall');
        return null;
    } else {
        var latitude1 = parseFloat(coords[building1]['Latitude']);
        var longitude1 = parseFloat(coords[building1]['Longitude']);
        var latitude2 = parseFloat(coords[building2]['Latitude']);
        var longitude2 = parseFloat(coords[building2]['Longitude']);
        var coord1 = latitude1 - latitude2;
        var coord2 = longitude1 - longitude2;
        return Math.sqrt(Math.pow(coord1, 2) + Math.pow(coord2, 2)) * 100000;
    }
}