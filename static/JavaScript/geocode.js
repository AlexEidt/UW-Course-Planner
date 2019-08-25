function deleteRow(btn) {
    var row = btn.parentNode.parentNode;
    row.parentNode.removeChild(row);
}
var mymap = L.map('mapid').setView([47.65587781988791, -122.30949282646179], 15);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}.png', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom, 2012'
}).addTo(mymap);
$('#mapped').hide()
var index = 0;
var campus = new Array();
var layers = new Array();
$(document).ready(function() {
    var table = document.getElementById('chosen');
    $('a#campus').on('click', function() {
        campus = [];
        campus.push(this.innerHTML);
        var campus_for = 'Seattle';
        if (campus.length > 0) {
            campus_for = campus[0];
        }
        var campus_coords = {
            'Bothell': [47.758937, -122.190688],
            'Seattle': [47.65587781988791, -122.30949282646179],
            'Tacoma': [47.244562, -122.437562]
        }
        // Center map on the University of Washington's 'Red Square', considered by many to
        // be the center of the Seattle Campus
        mymap.setView(campus_coords[this.innerHTML], 15, {animate: true});
    });
    $('button#btn').on('click', function() {
        if ($('#course').val() != '') {
            var courses = ''
            for (var i = 0; i < table.rows.length; i++) {
                courses += table.rows[i].cells[0].innerHTML + ',';
            }
            check_course = $('#course').val().toUpperCase();
            while (check_course.includes(' ')) {
                check_course = check_course.replace(' ', '');
            }
            if ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'.includes(check_course.charAt(check_course.length - 1))) {
                check_course = check_course.substring(0, check_course.length - 2);
            }
            if (!courses.includes(check_course)) {
                $.ajax({
                    url: '/check_course/',
                    type: 'POST',
                    data: {
                        course: $('#course').val()
                    },
                    beforeSend: function() {
                        $('#btn').attr('disabled', true);
                        $('span#select').addClass('spinner-border spinner-border-sm');
                    },
                }).done(function(resp) {
                    if (resp.data) {
                        var row = table.insertRow();
                        row.insertCell().innerHTML = resp['name'];
                        row.insertCell().innerHTML = '<button class="btn btn-primary" id="remove" onclick="deleteRow(this)">Remove</button>';
                    } else {
                        alert($('#course').val() + ' is not a course at UW or may not be offered this quarter');
                    }
                    $('#btn').attr('disabled', false);
                    $('span#select').removeClass('spinner-border spinner-border-sm');
                });
            } else {
                alert($('#course').val().toUpperCase() + ' has already been entered');
            }
        }
    });
    $('button#schedule').on('click', function() {
        var courses = ''
        for (var i = 0; i < table.rows.length; i++) {
            courses += table.rows[i].cells[0].innerHTML + ',';
        }
        if (courses.trim().length > 0) {
            $.ajax({
                url: '/create_schedule/',
                type: 'POST',
                data: {
                    course: courses
                },
                beforeSend: function() {
                    $('#schedule').attr('disabled', true);
                    $('span#sch').addClass('spinner-border spinner-border-sm');
                },
            }).done(function(resp) {
                if (resp.option != null) {
                    $('#inputs').hide();
                    $('btn#remove').attr('disabled', true);
                    $('span#sch').removeClass('spinner-border spinner-border-sm');
                    table.innerHTML = '';

                    $('#mapped').show();
                    show_schedule(resp);
                    
                } else {
                    $('#schedule').attr('disabled', false);
                    $('span#sch').removeClass('spinner-border spinner-border-sm');
                    alert('No Course Combinations Found');
                }
            });
        }
    });
    $('#prev').on('click', function() {
        if (index > 0) {
            index--;
            mymap.removeLayer(layers[index + 1][0]);
            layers[index][0].addTo(mymap);
            document.getElementById('sectionsTitle').innerHTML = layers[index][1];
        } else {
            $('#prev').attr('disabled', true);
        }
        $('#next').attr('disabled', false);
    });
    $('#next').on('click', function() {
        index++;
        if (index < layers.length) {
            mymap.removeLayer(layers[index - 1][0]);
            layers[index][0].addTo(mymap);
            document.getElementById('sectionsTitle').innerHTML = layers[index][1];
            $('#prev').attr('disabled', false);
        } else {
            $.ajax({
                url: '/get_schedules/',
                type: 'POST',
                beforeSend: function() {
                        $('#next').attr('disabled', true);
                        $('span#nextSpan').addClass('spinner-border spinner-border-sm');
                } 
            }).done(function(resp) {
                $('#next').attr('disabled', false);
                $('span#nextSpan').removeClass('spinner-border spinner-border-sm');
                if (resp.option == null) {
                    alert('No more combinations');
                    $('#next').attr('disabled', true);
                } else {
                    show_schedule(resp);
                    mymap.removeLayer(layers[index - 1][0]);
                }
                $('#prev').attr('disabled', false);
            });
        }
    });
});
function show_schedule(resp) {
    var headerText = '';

    var building_map = {}
    for (var i = 0; i < resp.option.length; i++) {
        for (var j = 0; j < resp.option[i].length; j++) {
            for (var k = 0; k < resp.option[i][j].Building.length; k++) {
                var building = resp.option[i][j].Building[k];
                var o = resp.option[i][j];
                if (building_map.hasOwnProperty(building)) {
                    building_map[building].push('<strong>' + o.Course + '</strong>' 
                                                + ' ' + o.Type + ' ' + o.Section + 
                                                '<br>' + o.Days[k] + ' ' + o.Time[k] 
                                                + ' ' + building + ' ' + o['Room Number'][k]);
                } else {
                    building_map[building] = ['<strong>' + o.Course + '</strong>' 
                                            + ' ' + o.Type + ' ' + o.Section + 
                                            '<br>' + o.Days[k] + ' ' + o.Time[k] + 
                                            ' ' + building + ' ' + o['Room Number'][k]];
                }
                if (!headerText.includes(o.Course)) {
                    headerText += o.Course + ' ' + o.Section + ', ';
                } else {
                    headerText += o.Section + ', ';
                }
            }
        }
    }
    var courseMarkers = new Array();
    Object.keys(building_map).forEach(function(building) {
        var latitude = parseFloat(resp.coords[building]['Latitude']);
        var longitude = parseFloat(resp.coords[building]['Longitude']);
        var text = '';
        for (var i = 0; i < building_map[building].length; i++) {
            //L.marker([latitude, longitude]).addTo(mymap);
            text += '<br>' + building_map[building][i];
        }
        if (text.startsWith('<br>')) {
            text = text.substring(4);
        }
        courseMarkers.push(L.marker([latitude, longitude]).bindPopup(text));
    });
    var header = headerText.trim().substring(0, headerText.length - 2);
    document.getElementById('sectionsTitle').innerHTML = header;
    var layer = L.layerGroup(courseMarkers);
    layer.addTo(mymap);
    layers.push([layer, header]);
}