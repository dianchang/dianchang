// 跳转到相关页面
$(document).on('click', '.noti-body', function (e) {
    var href = $(this).data('href');

    if (typeof href === 'undefined') {
        return false;
    }

    if (e.target.tagName == 'A' || $(e.target).parents('a').length !== 0) {
        return;
    }

    window.location = href;
});
