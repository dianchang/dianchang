var timerForParentTopicTypeahead = null;
var $parentTopicInput = $("input[name='parent-topic']");

// 启动Typeahead自动完成
$parentTopicInput.typeahead({
    minLength: 1,
    highlight: true,
    hint: false
}, {
    displayKey: 'name',
    source: function (q, cb) {
        if (timerForParentTopicTypeahead) {
            clearTimeout(timerForParentTopicTypeahead);
        }

        timerForParentTopicTypeahead = setTimeout(function () {
            $.ajax({
                url: urlFor('topic.query'),
                method: 'post',
                dataType: 'json',
                data: {
                    q: q
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
$parentTopicInput.on('typeahead:selected', function (e, parentTopic) {
    addToTopic(g.topicId, parentTopic.id);
});

// 删除直接父话题
$('.btn-remove-parent-topic').click(function () {
    var parentTopicId = parseInt($(this).data('parent-topic-id'));
    var _this = $(this);

    $.ajax({
        url: urlFor('topic.remove_parent_topic', {uid: g.topicId, parent_topic_id: parentTopicId}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            _this.parent().detach();
        }
    });
});

/**
 * 添加直接父话题
 * @param {int} topicId - 问题id
 * @param {int} parentTopicId - 问题id
 */
function addToTopic(topicId, parentTopicId) {
    $.ajax({
        url: urlFor('topic.add_parent_topic', {uid: topicId, parent_topic_id: parentTopicId}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            if (!$(".parent-topic-wap[data-id='" + response.id + "']").length) {
                $(".parent-topics").append(response.html);
            }
            $parentTopicInput.typeahead('val', '');
        }
    });
}
