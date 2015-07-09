var $mainWap = $('#main-wap');

// 完成关注，进入主页
$mainWap.on('click', '.btn-finish', function () {
    $.ajax({
        url: urlFor('account.generate_home_feeds'),
        method: 'POST',
        dataType: 'json'
    }).always(function () {
        window.location = urlFor('site.index');
    });
});
