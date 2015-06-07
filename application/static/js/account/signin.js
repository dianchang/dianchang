var $signinEmail = $(".signin-wap input[name='email']");
var $signinPwd = $(".signin-wap input[name='password']");
var $signinRemember = $(".signin-wap input[name='remember']");
var $signupEmail = $(".signup-wap input[name='email']");
var $signupName = $(".signup-wap input[name='email']");
var $signupCode = $(".signup-wap input[name='code']");
var $signupPwd = $(".signup-wap input[name='password']");

// 切换到注册
$('.btn-go-to-signup').click(function () {
    $('.signup-wap').show();
    $('.signin-wap').hide();
    $signinEmail.val('');
    $signinPwd.val('');
    hideTip($('.wap input'));
});

// 切换到登录
$('.btn-go-to-signin').click(function () {
    $('.signin-wap').show();
    $('.signup-wap').hide();
    $signupCode.val('');
    $signupEmail.val('');
    $signupName.val('');
    $signupPwd.val('');
    hideTip($('.wap input'));
});

// 登录
$('.btn-signin').click(function () {
    var email = $.trim($signinEmail.val());
    var password = $.trim($signinPwd.val());
    var remember = $signinRemember.is(':checked');

    if (email === "") {
        showTip($signinEmail, '邮箱不能为空');
    }

    if (password === "") {
        showTip($signinPwd, '密码不能为空');
    }

    $.ajax({
        url: urlFor('account.signin'),
        method: 'post',
        dataType: 'json',
        data: {
            'email': email,
            'password': password,
            'remember': remember
        }
    }).done(function (response) {
        if (response.result) {
            window.location = urlFor('site.index');
        } else {
            if (response.email !== "") {
                showTip($signinEmail, response.email);
            } else {
                hideTip($signinEmail);

                if (response.password !== "") {
                    showTip($signinPwd, response.password);
                } else {
                    hideTip($signinPwd);
                }
            }
        }
    });
});

// 输入字符时，隐藏tooltip
$(".wap input").on('keyup', function () {
    hideTip($(this));
});

/**
 * 显示tip
 * @param $element
 * @param tip
 */
function showTip($element, tip) {
    $element
        .attr('data-original-title', tip)
        .tooltip({
            title: tip,
            trigger: 'manual',
            placement: 'right'
        }).tooltip('show');
}

/**
 * 隐藏tip
 * @param $element
 */
function hideTip($element) {
    if ($element.length === 1) {
        $element.tooltip('hide');
    } else {
        $.each($element, function () {
            $(this).tooltip('hide');
        });
    }
}
