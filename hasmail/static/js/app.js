$(function() {
  $.fn.editable.defaults.mode = 'inline';
  $.fn.editable.defaults.emptytext = '…';
  $.fn.editableform.buttons =
    '<button type="submit" class="btn btn-primary btn-sm editable-submit">'+
      '<i class="icon-ok"></i>'+
    '</button>'+
    '<button type="button" class="btn btn-default btn-sm editable-cancel">'+
      '<i class="icon-remove"></i>'+
    '</button>';

  $('.editable').editable();
});
