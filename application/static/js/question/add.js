var timerForTypeahead = null;
var $topicInput = $("input[name='search-topic']");
var $questionInput = $("input[name='question']");
var $addQuestionWap = $('.add-question-wap');
var $toSecondBtn = $('.btn-to-second');
var $toFirstBtn = $('.btn-to-first');
var $questionTitleInput = $("input[name='title']");
var $firstAnonymousCheckbox = $("form.first input[name='anonymous']");
var $secoundAnonymousCheckbox = $("form.second input[name='anonymous']");

var timerForQuestion = null;

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
$topicInput.on('typeahead:selected', function (e, topic) {
    addTopic(topic);
});

// 通过回车添加句集
$topicInput.on('keyup', function (e) {
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

// 输入问题，返回类似问题
$questionInput.on('keyup', function () {
    var title = $.trim($(this).val());

    if (timerForQuestion) {
        clearTimeout(timerForQuestion);
    }

    if (title === "") {
        return;
    }

    timerForQuestion = setTimeout(function () {
        $.ajax({
            url: urlFor('question.similar'),
            method: 'post',
            dataType: 'json',
            data: {
                title: title
            }
        }).done(function (response) {
            if (response.count !== 0) {
                $('.similar-questions').html("<p>类似问题：</p>" + response.html);
                $toSecondBtn.text('我的问题是新的，下一步');
            } else {
                $('.similar-questions').empty();
                $toSecondBtn.text('下一步');
            }
        });
    }, 500);
});

// 进入提问的第二阶段
$toSecondBtn.click(function () {
    var title = $.trim($questionInput.val());

    if (title === "") {
        return;
    }

    $addQuestionWap.removeClass('first').addClass('second');
    $questionTitleInput.val($.trim($questionInput.val()));
    $secoundAnonymousCheckbox.prop('checked', $firstAnonymousCheckbox.is(':checked'));
});

// 退回到提问的第一阶段
$toFirstBtn.click(function () {
    $addQuestionWap.removeClass('second').addClass('first');
    $firstAnonymousCheckbox.prop('checked', $secoundAnonymousCheckbox.is(':checked'));
    $('.topics-inner-wap').empty();
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
