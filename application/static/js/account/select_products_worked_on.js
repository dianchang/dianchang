var $mainWap = $('#main-wap');
var $topicInput = $mainWap.find("input[name='topic']");

// 话题自动完成
initTopicTypeahead($topicInput, function (e, topic) {
    var data = null;

    if (typeof topic.create !== 'undefined') {
        data = {name: topic.name};
    } else {
        data = {topic_id: topic.id}
    }

    $.ajax({
        url: urlFor('account.submit_product_worked_on'),
        method: 'post',
        dataType: 'json',
        data: data
    }).done(function (response) {
        if (response.result) {
            if (response.html !== '') {
                $mainWap.find('.products-wap').removeClass('empty');
                $mainWap.find('.products-wap .inner-wap').append(response.html);
            }
        }

        $topicInput.typeahead('val', '');
    });
});

// 设为当前在职
$mainWap.on('click', '.btn-set-current-working-on', function () {
    var id = $(this).data('id');
    var _this = $(this);

    $.ajax({
        url: urlFor('account.set_product_current_working_on', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            $mainWap.find('.product-worked-on').removeClass('current');
            _this.parents('.product-worked-on').addClass('current');
        }
    });
});

// 取消设为当前在职
$mainWap.on('click', '.btn-cancel-current-working-on', function () {
    var id = $(this).data('id');
    var _this = $(this);

    $.ajax({
        url: urlFor('account.cancel_set_product_current_working_on', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            _this.parents('.product-worked-on').removeClass('current');
        }
    });
});

// 移除产品
$mainWap.on('click', '.btn-remove-product', function () {
    var id = $(this).data('id');
    var _this = $(this);

    $.ajax({
        url: urlFor('account.remove_product', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            _this.parents('.product-worked-on').detach();
        }
    });
});

var uploader = simple.uploader({
    url: 'http://upload.qiniu.com',
    fileKey: 'file',
    connectionCount: 1,
});

// 上传话题图标
$mainWap.on('click', '.btn-upload-topic-avatar', function () {
    $(this).parents('.product-worked-on').find('input').click();
});

$mainWap.on('change', "input[name='avatar']", function (e) {
    uploader.upload(this.files, {
        params: {
            token: $(this).data('token')
        }
    });
});

uploader.on('uploadsuccess', function (e, file, response) {
    if (response.result) {
        var $product = $(".product-worked-on[data-id='" + response.id + "']");

        $product.find('img.topic-avatar').attr('src', response.url);
        $product.find('.btn-upload-topic-avatar').detach();
        $product.find('input').detach();
    }
});
