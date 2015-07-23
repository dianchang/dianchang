$mainWap = $('#main-wap');

var index = 1;

// 换一批用户
$mainWap.on('click', '.btn-refresh', function () {
    if ($('.recommend-user-wap-' + (index + 1)).length !== 0) {
        index = index + 1;
    } else {
        index = 1;
    }

    $('.recommend-user-wap-' + index).show();
    $('.recommend-user-wap').not('.recommend-user-wap-' + index).hide();
});
