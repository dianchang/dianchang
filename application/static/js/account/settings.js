// url token联动
$("input[name='url_token']").on('keyup', function () {
    $('.url-token').text($(this).val());
});

// 上传头像
var uploader = simple.uploader({
    url: urlFor('account.upload_avatar'),
    fileKey: 'file',
    connectionCount: 1
});

// 上传头像
$('.btn-upload-avatar').click(function () {
    $("input[name='avatar']").click();
});

$("input[name='avatar']").on('change', function (e) {
    uploader.upload(this.files);
});

uploader.on('uploadsuccess', function (e, file, response) {
    response = JSON.parse(response);
    if (response.result) {
        $('img.user-avatar').attr('src', response.image_url);
    }
});
