$(function() {
  $.fn.editable.defaults.mode = 'inline';
  $.fn.editable.defaults.emptytext = '…';
  $.fn.editableform.buttons =
    '<button type="submit" class="btn btn-primary btn-sm editable-submit">'+
      '<i class="fa fa-check"></i>'+
    '</button>'+
    '<button type="button" class="btn btn-default btn-sm editable-cancel">'+
      '<i class="fa fa-times"></i>'+
    '</button>';

  $('.editable').editable();
});
