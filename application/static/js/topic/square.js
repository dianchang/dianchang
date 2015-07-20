var active = 'product';
var $mainWap = $('#main-wap');

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

// 切换话题大类
$mainWap.on('click', '.list-group-item', function () {
    var target = $(this).data('target');
    var targetClass = '.' + target + '-topics-wap';

    $('.list-group-item').not(this).removeClass('active');
    $(this).addClass('active');

    $mainWap.find('.topics-wap').not(targetClass).removeClass('active');
    $mainWap.find(targetClass).addClass('active');
});
