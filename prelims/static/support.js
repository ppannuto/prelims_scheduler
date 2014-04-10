/* General support routines */

$(".valid-if-any-text").on("change", function() {
    //var valid_div = $(this).parent(".has-success, .has-error");
    var valid_div = $(this).closest('div.has-error, div.has-success')
    console.log('valid_div');
    console.log(valid_div);
    if (this.value.length == 0) {
      console.log('valid-if-any-text -> error');
      valid_div.toggleClass('has-success', false);
      valid_div.toggleClass('has-error', true);
    } else {
      console.log('valid-if-any-text -> success');
      valid_div.toggleClass('has-error', false);
      valid_div.toggleClass('has-success', true);
    }
    console.log(valid_div);
});

$(".cal_watch_check").change(function() {
  /* TODO: This doesn't filter by event_id, but should */

  var fn_to_apply;
  if ($(this).is(":checked")) {
    fn_to_apply = function(val) { return val + 1; }
  } else {
    fn_to_apply = function(val) { return val - 1; }
  }

  $(".fac_busy_"+this.value).each(function(index) {
    if (!("busy_cnt" in this)) {
      this.busy_cnt = 0;
    }
    this.busy_cnt = fn_to_apply(this.busy_cnt);
    if (this.busy_cnt > 0) {
      $(this).addClass("busy_time_slot");
    } else {
      $(this).removeClass("busy_time_slot");
    }
  });
});

$(document).on('change', '.btn-file :file', function() {
  console.log('on change btn file');
  var input = $(this);
  var numFiles = input.get(0).files ? input.get(0).files.length : 1;
  var label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
  console.log(input);
  console.log(numFiles);
  console.log(label);
  input.trigger('fileselect', [numFiles, label]);
});
