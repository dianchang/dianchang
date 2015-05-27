var timerForTypeahead = null;
var $topicInput = $("input[name='search-topic']");

// 删除话题
$('.btn-delete-topic').click(function () {
    var topicId = parseInt($(this).data('id'));

    $(this).parent().detach();
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
    addTopic(topic);
});

// 通过回车添加句集
$topicInput.on('keypress', function (e) {
    var name = $.trim($(this).val());

    if (e.which === 13) {
        e.preventDefault();

        if (name === "") {
            return;
        }

        $.ajax({
            url: urlFor('topic.get_by_name', {name: name}),
            method: 'post',
            dataType: 'json'
        }).done(function (topic) {
                addTopic(topic);
            }
        );
    }
});

/**
 * Add topic.
 * @param {Object} topic
 */
function addTopic(topic) {
    if (!$(".topic-wap[data-id='" + topic.id + "']").length) {
        $(".topics-inner-wap").append(
            "<div class='topic-wap'>"
            + "<a class='label label-default topic' href='" + urlFor('topic.view', {uid: topic.id}) + "'"
            + "data-id='{{ topic.id }}'>" + topic.name + "</a>"
            + "<a href='javascript: void(0)' class='btn-delete-topic' data-id='" + topic.id + "'>"
            + "<span class='fa fa-close'></span>"
            + "</a>"
            + "<input type='hidden' name='topic' value='" + topic.id + "'>"
            + "</div>"
        );
    }
    $topicInput.typeahead('val', '');
}
