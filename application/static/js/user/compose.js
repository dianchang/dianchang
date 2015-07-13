// 关注 & 取消关注问题
$('.question .btn-follow-question').click(function () {
    var id = $(this).data('id');
    var _this = $(this);

    $.ajax({
        url: urlFor('question.follow', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            if (response.followed) {
                _this.addClass('followed');
            } else {
                _this.removeClass('followed');
            }

            _this.find('.followers-count').text(response.followers_count);
        }
    });
});

// 忽略问题
$('.question .btn-ignore-feed').click(function () {
    var id = $(this).data('id');
    var $questionWap = $(this).parents('.question-wap');

    $.ajax({
        url: urlFor('user.ignore_compose_feed', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            $questionWap.addClass('ignored');
        }
    });
});

// 撤销忽略问题
$('.question-wap .btn-recover-feed').click(function () {
    var id = $(this).data('id');
    var $questionWap = $(this).parents('.question-wap');

    $.ajax({
        url: urlFor('user.recover_compose_feed', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            $questionWap.removeClass('ignored');
        }
    });
});
