$(document).ready(function() {
    $('button#gather').on('click', function(event) {
        event.preventDefault();
        if ("{{ connected() }}".includes('True')) {
            $.ajax({
                url: '/gather',
                type: 'POST',
                beforeSend: function() {
                    $('#gather').attr('disabled', true);
                    $('span').addClass('spinner-border spinner-border-sm');
                },
            }).done(function() {
                $('span').removeClass('spinner-border spinner-border-sm');
                if ("{{ gather()|safe }}".includes('True')) {
                    $('#gatherImg').attr('src', "{{ url_for('static', filename='Images/check.png') }}");
                    alert('All required files created')
                } else {
                    $('#gatherImg').attr('src', "{{ url_for('static', filename='Images/x.png') }}");
                    $('#gather').attr('disabled', false);
                }
            });
        } else {
            alert("No Internet Connection Available")
        }
    });
});