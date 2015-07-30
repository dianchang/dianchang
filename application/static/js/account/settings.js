$('.item input').focus(function () {
    this.value = this.value;
});

// 进入编辑状态
$('.btn-edit').click(function () {
    var $commands = $(this).parents('.commands');
    var $input = $(this).parents('.item').find('input');

    $commands.addClass('edit');
    $input.removeAttr('disabled').focus();
});

// 取消编辑状态
$('.btn-cancel').click(function () {
    var $commands = $(this).parents('.commands');
    var $input = $(this).parents('.item').find('input');

    $input.attr('disabled');
    $commands.removeClass('edit');
    $input.val($input.data('value'));
});

// 修改称呼
$('.btn-submit-name').click(function () {
    var $commands = $(this).parents('.commands');
    var $input = $(this).parents('.item').find('input');
    var name = $.trim($input.val());
    var $nameEditCount = $(this).parents('.item').find('.name-edit-count');

    if (name === "") {
        return false;
    }

    $.ajax({
        url: urlFor('account.update_name'),
        method: 'post',
        dataType: 'json',
        data: {
            name: name
        }
    }).done(function (response) {
        if (response.result) {
            $input.attr('disabled');
            $commands.removeClass('edit');
            $input.val(name).data('value', name);
            $nameEditCount.text(response.name_edit_count);
        }
    });
});

// 修改个人主页网址
$('.btn-submit-url-token').click(function () {
    var $commands = $(this).parents('.commands');
    var $input = $(this).parents('.item').find('input');
    var urlToken = $.trim($input.val());

    if (urlToken === "") {
        return false;
    }

    $.ajax({
        url: urlFor('account.update_url_token'),
        method: 'post',
        dataType: 'json',
        data: {
            url_token: urlToken
        }
    }).done(function (response) {
        if (response.result) {
            $input.attr('disabled');
            $commands.removeClass('edit');
            $input.val(urlToken).data('value', urlToken);
        }
    });
});

// 进入密码编辑状态
$('.btn-edit-password').click(function () {
    var $input = $(this).parents('.item').find('input');

    $input.val('');
});

// 退出密码编辑状态
$('.btn-cancel-password').click(function () {
    var $input = $(this).parents('.item').find('input');

    $input.val('*********');
});

// 修改密码
$('.btn-submit-password').click(function () {
    var $commands = $(this).parents('.commands');
    var $input = $(this).parents('.item').find('input');
    var password = $.trim($input.val());

    if (password === "") {
        return false;
    }

    $.ajax({
        url: urlFor('account.update_password'),
        method: 'post',
        dataType: 'json',
        data: {
            password: password
        }
    }).done(function (response) {
        if (response.result) {
            $input.attr('disabled');
            $commands.removeClass('edit');
            $input.val('*********');
        }
    });
});
