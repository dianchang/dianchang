var $accountWap = $('.dc-signin-signup-forgot-pwd-wap');

adjustWidth();

$(window).resize(function () {
    adjustWidth();
});

// 切换到登录框
$('.btn-go-to-signin-signup').click(function () {
    $accountWap.css({
        'left': '-280px'
    }).show().animate({
        'left': '30px'
    }, 180, function () {
        $('.logo-wap').hide();
    });
});

/**
 * 调整 leftWap 和 rightWap 的宽度
 */
function adjustWidth() {
    var $leftWap = $('.left-wap');
    var $rightWap = $('.right-wap');

    if ($(window).width() > 1020) {
        $leftWap.css('width', $(window).width() / 2.0 - 170);
        $('body').css('paddingLeft', $(window).width() / 2.0 - 170);
        $('.answers').show();
    } else {
        $leftWap.css('width', $(window).width() / 3.0);
        $('body').css('paddingLeft', $(window).width() / 3.0);
        $('.answers').show();
    }
}
