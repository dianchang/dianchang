$accountWap = $('.dc-signin-signup-forgot-pwd-wap');

// 切换到登录框
$('.btn-go-to-signin-signup').click(function () {
    $accountWap.css({
        'left': '-280px'
    }).show().animate({
        'left': '0'
    }, 180, function () {
        $('.logo-wap').hide();
    });
});
