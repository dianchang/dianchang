$accountWap = $('.dc-signin-signup-forgot-pwd-wap');

// 切换到登录框
$('.btn-go-to-signin-signup').click(function () {
    $accountWap.css({
        'margin-left': '-280px'
    }).show().animate({
        'margin-left': '0'
    }, 180, function () {
        $(this).css({
            position: 'static',
            margin: '50px 0 0 0'
        });
        $('.logo-wap').hide();
    });
});
