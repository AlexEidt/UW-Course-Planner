$(document).ready(function() {
    var input = document.getElementById('courseInput');
    input.addEventListener('keyup', function(event) {
        if (event.keyCode === 13) { // Enter Key
            event.preventDefault();
            document.getElementById('btn').click();
        }
    });
    $('img#tree').hide();
    $('button#btn').on('click', function() {
        var course = $('#courseInput').val();
        $.ajax({
            data: {
                name: course,
            },
            url: "/_get_tree/",
            type: "POST",
            beforeSend: function() {
                $('#btn').attr('disabled', true);
                $('span').addClass('spinner-border spinner-border-sm');
            },
        }).done(function(resp) {
            $('#btn').attr('disabled', false);
            var image = resp.data;
            if (!image.includes(' ') && image.length > 0) {
                var time = new Date();
                $('img#tree').attr('src', "../static/Prerequisite_Trees/" + image + '?none=' + time.getTime())
                if (resp.levels > 3) {
                    $('img#tree').attr('style', 
                        "text-align: center; margin-left: auto; margin-right: auto; display: block; width: 80%");
                    $('img#tree').show();
                } else if (resp.levels > 0) {
                    $('img#tree').attr('style', 
                        "text-align: center; margin-left: auto; margin-right: auto; display: block; width: 25%");
                    $('img#tree').show();
                } else {
                    alert('You have completed all necessary Prerequisites for ' + image.split('.')[0] + '. Make sure to check the Course Catalog before registering for any course')
                }
            } else if (image.length > 0) {
                var text = image.split(' ')[1];
                if (image.startsWith('NA')) {
                    alert(text + " is not a course offered at UW");
                } else if (image.startsWith('NP')) {
                    alert(text + " has no Prerequisites");
                } else if (image.startsWith('AT')) {
                    alert('You have already taken ' + text)
                }
            }
            $('span').removeClass('spinner-border spinner-border-sm');
        });
    }); 
});