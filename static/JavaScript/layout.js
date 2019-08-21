$(document).ready(function() {
    $('button#searchBtn').on('click', function() {
        var course = $('#courseSearch').val();
        course += ' SearchCourse';
        $.ajax({
            url: '/_get_tree/',
            type: 'POST',
            data: {
                name: course
            }
        }).done(function(resp) {
            if (resp.data.includes(' ') && (resp.data.startsWith('NA'))) {
                alert(resp.data.split(' ')[1] + ' is not a course offered at UW');
            } else if (resp.data.includes(' ') && resp.data.startsWith('ND')) {
                alert(resp.data.split(' ')[1] + ' is not a department at UW');
            } else if (resp.data.length > 0) {
                var searched = resp.data
                if (resp.data.includes(' ')) {
                    searched = searched.split(' ')[1];
                }
                var root = window.location.protocol + '//' + window.location.host + '/' + searched;
                window.open(root, '_top');
            }
        });
    });
});