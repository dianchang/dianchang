var $mainWap = $('#main-wap');
var $topicInput = $mainWap.find("input[name='topic']");
var timerForTopicTypeahead = null;

$topicInput.typeahead({
    minLength: 1,
    highlight: true,
    hint: true
}, {
    displayKey: 'name',
    source: function (q, cb) {
        if (timerForTopicTypeahead) {
            clearTimeout(timerForTopicTypeahead);
        }

        timerForTopicTypeahead = setTimeout(function () {
            $.ajax({
                url: urlFor('topic.query'),
                method: 'post',
                dataType: 'json',
                data: {
                    q: q,
                    create: true
                }
            }).done(function (matchs) {
                cb(matchs);
            });
        }, 300);
    },
    templates: {
        'suggestion': function (data) {
            if (typeof data.create === 'undefined') {
                return "<p class='typeahead-suggestion' data-name='" + data.name + "'><img src='" + data.avatar_url + "' class='topic-avatar img-rounded'>" + data.name + "</p>";
            } else {
                return "<p class='typeahead-suggestion' data-name='" + data.name + "'><span class='color'>+ 添加：</span>" + data.name + "</p>";
            }
        }
    }
});

$('.twitter-typeahead').css('display', 'block');

// 通过选择autocomplete菜单项添加句集
$topicInput.on('typeahead:selected', function (e, topic) {
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

        $product.find('.btn-upload-topic-avatar').detach()
            .find('img.topic-avatar').attr('src', response.url);
    }
});
