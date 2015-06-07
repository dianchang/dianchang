var $signinEmail = $(".signin-wap input[name='email']");
var $signinPwd = $(".signin-wap input[name='password']");
var $signinRemember = $(".signin-wap input[name='remember']");
var $signupWap = $('.signup-wap');
var $signupEmail = $(".signup-wap input[name='email']");
var $signupName = $(".signup-wap input[name='name']");
var $signupCode = $(".signup-wap .code");
var $signupPwd = $(".signup-wap input[name='password']");

// 切换到注册
$('.btn-go-to-signup').click(function () {
    $('.signin-wap').hide();
    $('.signup-wap').show();
    hideTip($('.wap input'));
    $signupCode.find('input').first().focus();
});

// 切换到登录
$('.btn-go-to-signin').click(function () {
    $('.signin-wap').show();
    $('.signup-wap').hide();
    $signupCode.val('');
    $signupEmail.val('');
    $signupPwd.val('');
    hideTip($('.wap input'));
});

$('.btn-go-to-forgot-password').click(function () {

});

// 登录
$('.btn-signin').click(function () {
    var email = $.trim($signinEmail.val());
    var password = $.trim($signinPwd.val());
    var remember = $signinRemember.is(':checked');

    if (email === "") {
        showTip($signinEmail, '邮箱不能为空');
        return;
    }
    if (password === "") {
        showTip($signinPwd, '密码不能为空');
        return;
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

// 输入邀请码
$signupCode.find('input').on('keypress', function (e) {
    if (e.which !== 32) {
        forwardCode($(this));
    }
});

// 退格键
// TODO
//$signupCode.find('input').on('keydown', function (e) {
//    var current = $.trim($(this).val());
//
//    console.log($(this));
//    console.log(current);
//
//    if (e.which === 8 && current === "") {
//        backwardCode($(this));
//    }
//});

// 测试邀请码
$signupCode.find('input').on('keyup', function (e) {
    var code = getCodeValue();

    $signupCode.find('input').each(function () {
        var current = $.trim($(this).val()).toString();

        if (current.length > 1) {
            $(this).val(current[0]);
        } else {
            $(this).val(current);
        }
    });

    if (code.length !== 6) {
        return;
    }

    if (code === "") {
        showTip($(this), '邀请码不能为空');
        return;
    }

    $.ajax({
        url: urlFor('account.test_invitation_code'),
        method: 'post',
        dataType: 'json',
        data: {
            code: code
        }
    }).done(function (response) {
        if (response.result) {
            $signupWap.addClass('on');
        } else {
            if (response.code !== "") {
                showTip($signupCode, response.code);
            } else {
                hideTip($signupCode);
            }
        }
    });
});

// 注册
$('.btn-signup').click(function () {
    var code = $.trim($signupCode.val());
    var name = $.trim($signupName.val());
    var email = $.trim($signupEmail.val());
    var password = $.trim($signupPwd.val());

    if (name === "") {
        showTip($signupName, '称谓不能为空');
        return;
    }
    if (email === "") {
        showTip($signupEmail, '邮箱不能为空');
        return;
    }
    if (password === "") {
        showTip($signupPwd, '密码不能为空');
        return;
    }

    $.ajax({
        url: urlFor('account.signup'),
        method: 'post',
        dataType: 'json',
        data: {
            name: name,
            email: email,
            password: password,
            code: code
        }
    }).done(function (response) {
        if (response.result) {
            var messageHtml = "账户激活邮件已发送到你的邮箱，";

            // 显示邮件已发送的提示
            $('.signup-wap').hide();
            $('.signup-success-wap').show();

            if (response.domain !== null) {
                messageHtml += "请 <a href='" + response.domain + "' target='_blank'>登录</a> 激活";
            } else {
                messageHtml += "请登录激活";
            }

            $('.signup-success-wap .message').html(messageHtml);
        } else {
            if (response.name !== "") {
                showTip($signupName, response.name);
            } else {
                hideTip($signupName);
            }

            if (response.email !== "") {
                showTip($signupEmail, response.email);
            } else {
                hideTip($signupEmail);
            }

            if (response.password !== "") {
                showTip($signupPwd, response.password);
            }
        }
    });
});

// 输入字符时，隐藏tooltip
$(".wap input").on('keyup', function () {
    hideTip($(this));
});

/**
 * 获取邀请码的值
 */
function getCodeValue() {
    var code = "";
    var current = "";

    $signupCode.find('input').each(function () {
        current = $.trim($(this).val());
        if (current.length >= 1) {
            code += current[0];
        }
    });

    return code;
}

/**
 * 前进到下一个邀请码输入框
 * @param $input
 */
function forwardCode($input) {
    var $nextInput = $input.next('input');

    if ($nextInput.length > 0) {
        $nextInput.focus();
    }
}

/**
 * 后退到上一个邀请码输入框
 * @param $input
 */
function backwardCode($input) {
    var $previousInput = $input.prev('input');

    if ($previousInput.length > 0) {
        $previousInput.focus();
    }
}

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
