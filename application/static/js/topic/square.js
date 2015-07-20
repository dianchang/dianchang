$mainWap = $('#main-wap');

// 关注 & 取消关注
$mainWap.on('click', '.btn-follow-topic', function () {
    var topicId = $(this).data('id');
    var followed = $(this).hasClass('followed');
    var _this = $(this);

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $.ajax({
        url: urlFor('topic.follow', {uid: topicId}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            _this.toggleClass('followed');
        }
    });
});
