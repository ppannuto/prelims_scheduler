/* Global jQuery options */

/* setup bootstrap-editable for inline edits */
$.fn.editable.defaults.mode = 'inline';

$(document).ready(function() {
  /* Make default faculty selection blank */
  $(".schedule_faculty").prop('selectedIndex', -1);

  /* Setup AJAX form for adding new prelims */
  var add_prelim_form_options = {
    success:    add_prelim_form_success,
    clearForm:  true,
    dataType:   'json'
  };
  $(".add_prelim_form").ajaxForm(add_prelim_form_options);

  add_delete_form_hooks();

  /* Setup editable fields for prelims */
  $('.prelim_title').editable({
    success: function(response, newValue) {
      if (response.status == 'error') return response.msg;
    },
    error: function(response, newValue) {
      if (response.status === 500) {
        return 'Temporary server error. Please try again later.';
      } else {
        return response.responseText;
      }
    }
  });
});

function add_delete_form_hooks() {
  var delete_unscheduled_prelim_form_options = {
    success:    delete_unscheduled_prelim_form_success,
    dataType:   'json'
  };
  $(".delete_unscheduled_prelim_form").ajaxForm(delete_unscheduled_prelim_form_options);
}

function add_prelim_form_success(data, statusText, xhr, $form) {
  var p = $("#event_"+data['event_id']+"_add_prelim_error_text");
  if (data['success']) {
    $("#event_"+data['event_id']+"_unscheduled_entries").append(data['html']);
    add_delete_form_hooks();
    p.html("<strong>Success:</strong> Added " + data['student'])
    p.parent().toggleClass('alert-danger', false);
    p.parent().toggleClass('alert-success', true);
  } else {
    p.html("<strong>Error:</strong> " + data['msg']);
    p.parent().toggleClass('alert-success', false);
    p.parent().toggleClass('alert-danger', true);
    console.log(data['msg']);
  }
  p.parent().show();
  p.parent().delay(10000).fadeOut(1000);
}

function delete_unscheduled_prelim_form_success(data) {
  $("#event_"+data['event_id']+"_unscheduled_"+data['student']).remove();
  console.log('delete unscheduled');
  console.log(data);
  console.log("#event_"+data['event_id']+"_unscheduled_"+data['student']);
}
