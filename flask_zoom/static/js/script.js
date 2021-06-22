// $(document).ready( function () {
//     $.noConflict();
//     $('#table_id').DataTable();
// } );

$(document).ready(function() {
    $.noConflict();
    $('#table_id').DataTable({
      "ordering": true,
      columnDefs: [{
        orderable: false,
        targets: "no-sort"
      }]
    });
  });