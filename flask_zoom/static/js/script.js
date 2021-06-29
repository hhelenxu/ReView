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