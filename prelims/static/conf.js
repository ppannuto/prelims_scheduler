$(document).ready(function() {
  $(".schedule_faculty").prop('selectedIndex', -1);

  var add_prelim_form_options = {
    success:    add_prelim_form_success,
    clearForm:  true,
    dataType:   'json'
  };
  $(".add_prelim_form").ajaxForm(add_prelim_form_options);

  add_delete_form_hooks();
});

function add_delete_form_hooks() {
  var delete_unscheduled_prelim_form_options = {
    success:    delete_unscheduled_prelim_form_success,
    dataType:   'json'
  };
  $(".delete_unscheduled_prelim_form").ajaxForm(delete_unscheduled_prelim_form_options);
}

function add_prelim_form_success(data, statusText, xhr, $form) {
  $("#event_"+data['event_id']+"_unscheduled_entries").append(data['html']);
  add_delete_form_hooks();
}

function delete_unscheduled_prelim_form_success(data) {
  $("#event_"+data['event_id']+"_unscheduled_"+data['student']).remove();
  console.log('delete unscheduled');
  console.log(data);
  console.log("#event_"+data['event_id']+"_unscheduled_"+data['student']);
}
