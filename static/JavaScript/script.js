$(document).ready(function() {

  $('button#btn').click(function() {

    $.ajax({

        data: {
          name: $('#courseInput').val(),
        },
        url: "/_get_tree/",
        type: "POST",

    }).done(function(resp) {

      $('div#response').append(resp.data);

    });

  });
  
});
