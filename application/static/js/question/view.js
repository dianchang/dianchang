var $titleWap = $('.title-wap');
var $titleInput = $('.title-wap input');
var $title = $('.title-wap .title');

// 编辑标题
$('.btn-edit-title').click(function () {
    $titleWap.addClass('edit');
    $titleInput.val($.trim($title.text()));
});

// 保存标题
$('.btn-save-title').click(function () {
    var title = $.trim($titleInput.val());

    if (title === "") {
        return;
    }

    $.ajax({
        url: urlFor('question.update', {uid: g.questionId}),
        method: 'post',
        dataType: 'json',
        data: {
            title: title
        }
    }).done(function () {
        $titleWap.removeClass('edit');
        $title.text(title);
    });
});


var timerForTypeahead = null;
var $topicInput = $("input[name='topic']");

// 添加话题
$('.btn-add-topic').click(function () {
    $('.topics-wap').addClass('edit');
});

// 编辑话题
$('.btn-edit-topic').click(function () {
    $('.topics-wap').addClass('edit');
});

// 完成话题编辑
$('.btn-finish-add-topic').click(function () {
    $('.topics-wap').removeClass('edit');
});

// 删除话题
$('.btn-delete-topic').click(function () {
    var topicId = parseInt($(this).data('id'));
    var _this = $(this);

    $.ajax({
        url: urlFor('question.remove_topic', {uid: g.questionId, topic_id: topicId}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            _this.parent().detach();
            checkTopicsCount();
        }
    });
});


// 启动Typeahead自动完成
$topicInput.typeahead({
    minLength: 1,
    highlight: true,
    hint: false
}, {
    displayKey: 'name',
    source: function (q, cb) {
        if (timerForTypeahead) {
            clearTimeout(timerForTypeahead);
        }

        timerForTypeahead = setTimeout(function () {
            $.ajax({
                url: urlFor('topic.query'),
                method: 'post',
                dataType: 'json',
                data: {
                    q: q,
                    question_id: g.questionId
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

// 通过选择autocomplete菜单项添加句集
$topicInput.on('typeahead:selected', function (e, topic) {
    addToTopic(g.questionId, {topic_id: topic.id});
});

// 通过回车添加句集
$topicInput.on('keypress', function (e) {
    if (e.which === 13) {
        addToTopic(g.questionId, {name: $(this).val()});
    }
});

/**
 * 为问题添加话题
 * @param {int|string} questionId - 问题id
 * @param {Object} data - Ajax请求的data部分，key为title或collection_id
 */
function addToTopic(questionId, data) {
    $.ajax({
        url: urlFor('question.add_topic', {uid: questionId}),
        method: 'post',
        dataType: 'json',
        data: data
    }).done(function (response) {
        if (response.result) {
            if (!$(".topic-wap[data-id='" + response.id + "']").length) {
                $(".topics-inner-wap").append(response.html);
            }
            $topicInput.typeahead('val', '');
            checkTopicsCount();
        }
    });
}

/**
 * Check if there is no topics, and update elements status.
 */
function checkTopicsCount() {
    if ($('.topic-wap').length === 0) {
        $('.topics-wap').addClass('empty');
    } else {
        $('.topics-wap').removeClass('empty');
    }
}
