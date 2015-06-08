// Flash message
setTimeout(showFlash, 200);
setTimeout(hideFlash, 2000);

$('.navbar-form input').focus(function () {
    $('.navbar-form .help-text').show();
}).blur(function () {
    $('.navbar-form .help-text').hide();
});

$('#nav-notification').click(function () {
    if ($(this).hasClass('on') && $(this).hasClass('more')) {
        $(this).removeClass('on').removeClass('more');
    } else if ($(this).hasClass('on')) {
        $(this).addClass('more');
        $(this).find('.notifications-count').text(23);
    } else {
        $(this).addClass('on');
        $(this).find('.notifications-count').text(2);
    }
});

/**
 * Show flash message.
 */
function showFlash() {
    $('.flash-message').slideDown('fast');
}

/**
 * Hide flash message.
 */
function hideFlash() {
    $('.flash-message').slideUp('fast');
}
