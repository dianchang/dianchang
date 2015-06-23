var timerForTopicTypeahead = null;
var $expertTopics = $('.expert-topics');
var $topicInput = $("input[name='topic']");

// 去除擅长话题
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

// 取消添加擅长话题
$('.btn-finish-expert-topic').click(function () {
    var $wap = $(this).parents('.add-expert-topic-wap');

    $wap.removeClass('edit');
});

// 拖拽排序
var sortable = new Sortable($expertTopics[0], {
    onEnd: function (evt) {
        evt.oldIndex;
        evt.newIndex;
    }
});

// Topic input 启用 Typeahead 自动完成
$topicInput.typeahead({
    minLength: 1,
    highlight: true,
    hint: false
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
                    ancestor_topic_id: g.topicId
                }
            }).done(function (matchs) {
                cb(matchs);
            });
        }, 300);
    },
    templates: {
        'suggestion': function (data) {
            return '<p>' + data.name + '</p>';
        }
    }
});

// 通过选择 autocomplete 菜单项添加擅长话题
$topicInput.on('typeahead:selected', function (e, topic) {
    var _this = $(this);

    $.ajax({
        url: urlFor('topic.add_expert', {uid: topic.id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            $('.expert-topics').append(response.html);
        }

        _this.parents('.add-expert-topic-wap').removeClass('edit');
        $topicInput.typeahead('val', '');
    });
});