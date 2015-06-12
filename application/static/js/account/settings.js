// url token联动
$("input[name='url_token']").on('keyup', function () {
    $('.url-token').text($(this).val());
});
