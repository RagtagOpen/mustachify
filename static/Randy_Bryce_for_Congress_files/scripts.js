console.log('begin scripts');

jQuery.noConflict();

function form_input_classes() {
  jQuery('input[type="text"]').addClass('text form-control');
  jQuery('input[type="password"]').addClass('text form-control');
  jQuery('input[type="email"]').addClass('text form-control');
  jQuery('input[type="phone"]').addClass('text form-control');
  jQuery('input[type="tel"]').addClass('text form-control');
  jQuery('select').addClass('form-control');
  jQuery('textarea').addClass('form-control');
  jQuery('input[type="checkbox"]').addClass('checkbox');
  jQuery('input[type="radio"]').addClass('radiobutton');
  jQuery('input[type="submit"]').addClass('btn btn-default');
  jQuery('input[type="image"]').addClass('buttonImage');
}

jQuery(document).ready(function() {
	form_input_classes();
});

jQuery('#SKIN>div.basic').removeClass('container');