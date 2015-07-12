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

var $expertTopics = $('.expert-topics');
var $topicInput = $("input[name='topic']");

// 移除擅长话题
$expertTopics.on('click', '.btn-remove-topic', function () {
    var id = $(this).data('id');
    var $topic = $(this).parents('.expert-topic');

    $.ajax({
        url: urlFor('topic.remove_expert', {uid: id}),
        dataType: 'json',
        method: 'post'
    }).done(function (response) {
        if (response.result) {
            $topic.detach();
        }
    });
});

// 添加话题经验
$expertTopics.on('click', '.btn-add-experience', function () {
    var $expertTopicWap = $(this).parents('.expert-topic');
    var $textarea = $expertTopicWap.find('textarea');

    $expertTopicWap.addClass('edit');
    $textarea.focus();
});

// 编辑话题经验
$expertTopics.on('click', '.btn-edit-experience', function () {
    var $expertTopicWap = $(this).parents('.expert-topic');
    var $experience = $expertTopicWap.find('.experience');
    var experience = $.trim($experience.text());
    var $textarea = $expertTopicWap.find('textarea');

    $expertTopicWap.addClass('edit');
    $textarea.val(experience).focus();
});

// 取消编辑话题经验
$('.btn-cancel-edit-experience').click(function () {
    var $expertTopicWap = $(this).parents('.expert-topic');

    $expertTopicWap.removeClass('edit');
});

// 提交话题经验
$('.btn-submit-experience').click(function () {
    var $expertTopicWap = $(this).parents('.expert-topic');
    var $experience = $expertTopicWap.find('.experience');
    var $textarea = $expertTopicWap.find('textarea');
    var experience = $.trim($textarea.val());
    var topicId = $(this).data('topic-id');

    $.ajax({
        url: urlFor('topic.update_experience', {uid: topicId, compose: 1}),
        method: 'post',
        dataType: 'json',
        data: {
            experience: experience
        }
    }).done(function (response) {
        if (response.result) {
            $expertTopicWap.removeClass('edit');
            $experience.text(experience);

            if (experience === "") {
                $expertTopicWap.addClass('empty');
            } else {
                $expertTopicWap.removeClass('empty');
            }
        }
    });
});

// 添加擅长话题
$('.btn-add-expert-topic').tooltip().click(function () {
    var $wap = $(this).parents('.add-expert-topic-wap');

    $wap.addClass('edit');
    $topicInput.focus();
});

// 完成添加擅长话题
$('.btn-finish-expert-topic').click(function () {
    var $wap = $(this).parents('.add-expert-topic-wap');

    $wap.removeClass('edit');
});

// 拖拽排序
var sortable = new Sortable($expertTopics.first()[0], {
    onEnd: function (evt) {
        var show_orders = [];

        $('.expert-topic').each(function (index, element) {
            var originalShowOrder = parseInt($(element).data('show-order'));
            var id = parseInt($(element).data('id'));

            if (index !== originalShowOrder) {
                console.log(id + ", " + index);
                show_orders.push({
                    'id': id,
                    'show_order': index
                });
            }
        });

        if (show_orders.length !== 0) {
            $.ajax({
                url: urlFor('topic.update_show_order'),
                method: 'post',
                dataType: 'json',
                data: {
                    show_orders: JSON.stringify(show_orders)
                }
            }).done(function (response) {
                if (response.result) {
                    $('.expert-topic').each(function (index, element) {
                        $(element).data('show-order', index);
                    });
                }
            });
        }
    }
});

// $topicInput 启用 Typeahead 自动完成
$topicInput.initTopicTypeahead({
    block: true,
    small: true,
    params: {
        limit: 6
    },
    callback: function (e, topic) {
        var _this = $(this);
        var $outerWap = $(this).parents('.expert-topics-outer-wap');
        var data;

        if (typeof topic.create === 'undefined') {
            data = {id: topic.id};
        } else {
            data = {name: topic.name};
        }

        $.ajax({
            url: urlFor('topic.add_expert'),
            method: 'post',
            dataType: 'json',
            data: data
        }).done(function (response) {
            if (response.result) {
                $('.expert-topics').append(response.html);

                if (response.full) {
                    $outerWap.addClass('full');
                    _this.parents('.add-expert-topic-wap').removeClass('edit');
                } else {
                    $outerWap.removeClass('full');
                }
            }

            $topicInput.typeahead('val', '');
        });
    }
});
