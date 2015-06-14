var $titleWap = $('.title-wap');
var $titleInput = $('.title-wap input');
var $title = $('.title-wap .title');
var timerForTypeahead = null;
var $topicInput = $("input[name='topic']");
var $answerTextarea = $("textarea[name='']");
var timerForAnswer = null;
var $draftTip = $('.tip-save-draft');

// 编辑标题
$('.btn-edit-title').click(function () {
    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $titleWap.addClass('edit');
    $titleInput.val($.trim($title.text())).focus();
});

// 保存标题
$('.btn-save-title').click(function () {
    var title = $.trim($titleInput.val());

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

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

var $descWap = $('.desc-wap');
var $descTextarea = $('.desc-wap textarea');
var $desc = $('.desc-wap .desc');

// 初始化描述富文本编辑器
var descEditor = new Simditor({
    textarea: $descTextarea,
    toolbarFloat: false,
    toolbar: ['bold', 'italic', 'underline', 'ol', 'ul', 'blockquote', 'code', 'link', 'image', 'markdown'],
    upload: {
        url: urlFor('site.upload_image'),
        fileKey: 'file',
        connectionCount: 1,
        leaveConfirm: '正在上传文件，如果离开上传会自动取消'
    }
});

// 添加问题描述
$('.btn-add-desc').click(function () {
    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $descWap.addClass('edit');
    descEditor.focus();
});

// 编辑问题描述
$('.btn-edit-desc').click(function () {
    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $descWap.addClass('edit');
    descEditor.setValue($.trim($desc.html())).focus();
});

// 保存问题描述
$('.btn-save-desc').click(function () {
    var desc = $.trim($descTextarea.val());

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $.ajax({
        url: urlFor('question.update', {uid: g.questionId}),
        method: 'post',
        dataType: 'json',
        data: {
            desc: desc
        }
    }).done(function (response) {
        if (response.result) {
            $descWap.removeClass('edit');
            $desc.html(response.desc);

            if (response.desc === "") {
                $descWap.addClass('empty');
            } else {
                $descWap.removeClass('empty');
            }
        }
    });
});

// 添加话题
$('.btn-add-topic').click(function () {
    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $('.topics-wap').addClass('edit');
});

// 编辑话题
$('.btn-edit-topic').click(function () {
    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $('.topics-wap').addClass('edit');
    $("input[name='topic']").focus();
});

// 完成话题编辑
$('.btn-finish-add-topic').click(function () {
    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $('.topics-wap').removeClass('edit');
});

// 删除话题
$(document).on('click', '.btn-delete-topic', function () {
    var topicId = parseInt($(this).data('id'));
    var _this = $(this);

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return false;
    }

    if ($('.topics .topic-wap').length <= 1) {
        alert('请至少绑定一个话题');
        return false;
    }

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

// 通过选择autocomplete菜单项添加话题
$topicInput.on('typeahead:selected', function (e, topic) {
    addToTopic(g.questionId, {topic_id: topic.id});
});

// 通过回车添加话题
// 这里似乎只能用 keypress，而不能用 keydown 或 keyup，
// 否则在触发 typeahead:selected 时也会触发 keydown 与 keyup，
// 造成话题的重复添加
$topicInput.on('keypress', function (e) {
    if (e.which === 13) {
        addToTopic(g.questionId, {name: $(this).val()});
    }
});

// 切换content tabs
$('.content-tabs a').click(function () {
    $('.content-tabs a').not(this)
        .removeClass('active')
        .each(function (index, element) {
            $("." + $(element).data('target')).hide();
        });

    $(this).addClass('active');
    $("." + $(this).data('target')).show();
});

// 初始化回答富文本编辑器
if (!g.answered) {
    var answerEditor = new Simditor({
        textarea: $("textarea[name='answer']"),
        toolbar: ['bold', 'italic', 'underline', 'ol', 'ul', 'blockquote', 'code', 'link', 'image', 'markdown'],
        upload: {
            url: urlFor('site.upload_image'),
            fileKey: 'file',
            connectionCount: 1,
            leaveConfirm: '正在上传文件，如果离开上传会自动取消'
        }
    });

    if (window.location.hash === "#answer") {
        answerEditor.focus();
    }

    // 自动保存草稿
    answerEditor.on('valuechanged', function () {
        var content = answerEditor.getValue();

        if (timerForAnswer) {
            clearTimeout(timerForAnswer);
        }

        $draftTip.text('保存中...');

        timerForAnswer = setTimeout(function () {
            $.ajax({
                url: urlFor('question.save_answer_draft', {uid: g.questionId}),
                method: 'post',
                dataType: 'json',
                data: {
                    content: content
                }
            }).done(function (response) {
                if (response.result) {
                    $draftTip.text('已保存');
                } else {
                    $draftTip.text('系统繁忙');
                }
            });
        }, 4000);
    });

    // 提交回答
    $('.btn-submit-answer').click(function () {
        var answer_content = answerEditor.getValue();

        clearTimeout(timerForAnswer);

        $.ajax({
            url: urlFor('question.answer', {uid: g.questionId}),
            dataType: 'json',
            method: 'post',
            data: {
                answer: answer_content
            }
        }).done(function (response) {
            if (response.result) {
                var answersCount = parseInt($('.answers-count').text());

                $('.answers-tab-item').click();
                $(response.html).hide().appendTo($('.showed-answers')).fadeIn('slow');
                $('.answers-count').text(answersCount + 1);
                $('.new-answer-wap').detach();
            }
        });
    });
}

// 显示 & 隐藏被折叠的回答
$('.btn-toggle-hided-answers').click(function () {
    $('.hided-answers').toggle();
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
