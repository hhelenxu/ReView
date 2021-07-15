// $(document).ready( function () {
//     $.noConflict();
//     $('#table_id').DataTable();
// } );

$(document).ready(function() {
    $.noConflict();
    $('#table_id').DataTable({
      "ordering": true,
      "order": [[ 0, "desc" ]], // set default ordering of column 0 to descending
      columnDefs: [{
        orderable: false,
        targets: "no-sort"
      }]
    });
  });

$(document).on('click', '#upvote-btn', function(event) {
  $.ajax({
    url : '/upvote',
    type : "post",
    contentType: 'application/json;charset=UTF-8',
    dataType: "json",
    data : JSON.stringify({'zoomid' : $('#upvote-btn').data('zoomid'), 'tag': $('#upvote-btn').data('tag')}),
    success : function(response) {
      console.log(response);	
    },
    error : function(xhr) {
      console.log(xhr);
    }
  });
  event.preventDefault();
});

$(document).on('click', '#downvote-btn', function(event) {
  $.ajax({
    url : '/downvote',
    type : "post",
    contentType: 'application/json;charset=UTF-8',
    dataType: "json",
    data : JSON.stringify({'zoomid' : $('#downvote-btn').data('zoomid'), 'tag': $('#downvote-btn').data('tag')}),
    success : function(response) {
      console.log(response);	
    },
    error : function(xhr) {
      console.log(xhr);
    }
  });
  event.preventDefault();
});

