var $titleDescWap = $('.title-desc-wap');
var $titleWap = $('.title-wap');
var $titleInput = $titleWap.find('input');
var $descInTitleTextarea = $titleWap.find('textarea');
var $title = $('.title-wap .title');
var timerForTopicTypeahead = null;
var $topicInput = $("input[name='topic']");
var timerForAnswer = null;
var $draftTip = $('.tip-save-draft');

var params = getJsonFromUrl();
// 跳转并高亮评论
if (typeof params.answer_id !== 'undefined' && typeof params.comment_id !== 'undefined') {
    var answerId = params.answer_id;
    var $answer = $(".answer[data-id='" + answerId + "']");
    var $commentsOuterWap = $answer.find('.comments-outer-wap');

    if ($commentsOuterWap.hasClass('empty')) {
        $.ajax({
            url: urlFor('answer.load_comments_wap', {uid: answerId}),
            dataType: 'json',
            method: 'post'
        }).done(function (response) {
            if (response.result) {
                var $comment = null;

                $commentsOuterWap.removeClass('empty').removeClass('hide').html(response.html);
                $comment = $(".answer-comment[data-id='" + params.comment_id + "']");
                $comment.css('backgroundColor', '#E6F9F2');
                $(window).scrollTo($comment, {
                    offset: {
                        'top': -100
                    }
                });
                setTimeout(function () {
                    $comment.animate({'backgroundColor': '#F5F6F5'});
                }, 2000);
            }
        });
    }
} else if (typeof params.answer_id !== 'undefined') {
    // 跳转回答
    $(window).scrollTo($(".answer[data-id='" + params.answer_id + "']"), {
        'offset': {
            'top': -100
        }
    });
}

// 编辑标题
$('.btn-edit-title').click(function () {
    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $titleWap.addClass('edit');
    $titleInput.val($.trim($title.text())).focus();
});

// 初始化位于标题内部的描述富文本编辑器
var descInTitleEditor = new Simditor({
    textarea: $descInTitleTextarea,
    toolbarFloat: false,
    toolbar: ['bold', 'italic', 'underline', 'ol', 'ul', 'blockquote', 'code', 'link', 'image', 'markdown'],
    upload: {
        url: 'http://upload.qiniu.com',
        fileKey: 'file',
        connectionCount: 1,
        leaveConfirm: '正在上传文件，如果离开上传会自动取消',
        params: {
            token: g.editorUptoken
        }
    }
});

// 添加问题描述
$('.btn-add-desc').click(function () {
    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $titleWap.addClass('add-desc');
    descInTitleEditor.focus();
});

// 退出标题编辑模式
$('.btn-cancel-edit-title').click(function () {
    $titleWap.removeClass('edit').removeClass('add-desc');
});

// 保存标题
$('.btn-save-title').click(function () {
    var title = $.trim($titleInput.val());
    var withDesc = $titleWap.hasClass('add-desc');
    var data = {title: title};

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    if (title === "") {
        return;
    }

    if (withDesc) {
        data.desc = descInTitleEditor.getValue();
    }

    $.ajax({
        url: urlFor('question.update', {uid: g.questionId}),
        method: 'post',
        dataType: 'json',
        data: data
    }).done(function (response) {
        $titleWap.removeClass('edit').removeClass('add-desc');
        $title.text(response.title);

        $desc.html(response.desc);

        if (response.desc === "") {
            $titleDescWap.addClass('empty-desc');
        } else {
            $titleDescWap.removeClass('empty-desc');
        }
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
        url: 'http://upload.qiniu.com',
        fileKey: 'file',
        connectionCount: 1,
        leaveConfirm: '正在上传文件，如果离开上传会自动取消',
        params: {
            token: g.editorUptoken
        }
    }
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
                $titleDescWap.addClass('empty-desc');
            } else {
                $titleDescWap.removeClass('empty-desc');
            }
        }
    });
});

// 取消编辑描述
$('.btn-cancel-edit-desc').click(function () {
    $descWap.removeClass('edit');
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

// 显示/隐藏邀请
$('.btn-toggle-invitation').click(function () {
    var active = $(this).hasClass('active');

    $(this).toggleClass('active');

    if (active) {
        $('.invitation-wap').hide('fast');
    } else {
        $('.invitation-wap').show('fast');
    }
});

var $invitationInput = $('.invitation-wap input');
var timerForInvitationTypeahead = null;

// 启用邀请回答者的 autocomplete
$invitationInput.typeahead({
    minLength: 1,
    highlight: true,
    hint: false
}, {
    displayKey: 'name',
    source: function (q, cb) {
        var data = {q: q};

        if (timerForInvitationTypeahead) {
            clearTimeout(timerForInvitationTypeahead);
        }

        if (g.signin) {
            data.exclude_id = g.userId;
        }

        timerForInvitationTypeahead = setTimeout(function () {
            $.ajax({
                url: urlFor('user.query'),
                method: 'post',
                dataType: 'json',
                data: data
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

$('.invitation-wap .header .twitter-typeahead').css('display', 'block');

// 通过选择 typeahead 邀请用户
$invitationInput.on('typeahead:selected', function (e, user) {
    $.ajax({
        url: urlFor('question.invite', {uid: g.questionId, user_id: user.id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            var html = "";
            var $invitedUsersWap = $('.invited-users-wap');

            if (!$invitedUsersWap.hasClass('empty')) {
                html += "、";
            }
            html += response.html;

            $invitedUsersWap.removeClass('empty');
            $('.invited-users').append(html);
        }

        $invitationInput.val('');
    });
});

// 邀请回答
$('.btn-invite').click(function () {
    var user_id = $(this).data('id');
    var _this = $(this);

    $.ajax({
        url: urlFor('question.invite', {uid: g.questionId, user_id: user_id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            if (response.invited) {
                _this.addClass('invited');
            } else {
                _this.removeClass('invited');
            }
        }
    });
});

// 取消邀请回答
$(document).on('click', '.btn-un-invite', function () {
    var user_id = $(this).data('id');
    var _this = $(this);

    $.ajax({
        url: urlFor('question.invite', {uid: g.questionId, user_id: user_id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result && !response.invited) {
            _this.parents('.dc-invited-user-wap').detach();
        }
    });
});

// 初始化回答富文本编辑器
if (!g.answered && g.signin) {
    var answerEditor = new Simditor({
        textarea: $("textarea[name='answer']"),
        toolbar: ['bold', 'italic', 'underline', 'ol', 'ul', 'blockquote', 'code', 'link', 'image', 'markdown'],
        upload: {
            url: 'http://upload.qiniu.com',
            fileKey: 'file',
            connectionCount: 1,
            leaveConfirm: '正在上传文件，如果离开上传会自动取消',
            params: {
                token: g.editorUptoken
            }
        }
    });

    if (window.location.hash === "#answer" || window.location.hash === "#draft") {
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
        var $identityInput = $("input[name='identity']");
        var identity = $.trim($identityInput.val());
        var $experienceInput = $("input[name='experience']");
        var experience = $.trim($experienceInput.val());

        clearTimeout(timerForAnswer);

        $.ajax({
            url: urlFor('question.answer', {uid: g.questionId}),
            dataType: 'json',
            method: 'post',
            data: {
                answer: answer_content,
                identity: identity,
                experience: experience
            }
        }).done(function (response) {
            if (response.result) {
                $('.answers-tab-item').click();
                $(response.html).hide().appendTo($('.showed-answers')).fadeIn('slow');
                $('.new-answer-wap').detach();
            }
        });
    });
}

// 显示 & 隐藏被折叠的回答
$('.btn-toggle-hided-answers').click(function () {
    $('.hided-answers').toggle();
});

// 跳转到我的回答
$('.btn-go-to-my-answer').click(function () {
    var myAnswerId = $(this).data('my-answer-id');

    var $targetAnswer = $(".answer[data-id='" + myAnswerId + "']");

    $('.answers-tab-item').click();

    $(window).scrollTo($targetAnswer);
    $targetAnswer.css({
        backgroundColor: 'rgb(221, 245, 245)'
    }).animate({
        backgroundColor: '#ffffff'
    }, 1200);
});

// 跳转到邀请回答
$('.btn-go-to-invitation-wap').click(function () {
    $('.invitation-tab-item').click();
    $(window).scrollTo("0%");
});

// 修改显示身份
$('.identity-selector label').click(function () {
    var identity = $.trim($(this).data('identity'));
    var identityName = $.trim($(this).text());

    $("input[name='identity']").val(identity);
    $('.identity').text(identityName);
});

// 添加话题经验
$('.btn-add-experience').click(function () {
    var $experienceWap = $(this).parents('.experience-wap');
    var $textarea = $experienceWap.find('textarea');

    $experienceWap.addClass('edit');
    $textarea.focus();
});

// 编辑话题经验
$('.btn-edit-experience').click(function () {
    var $experienceWap = $(this).parents('.experience-wap');
    var experience = $.trim($experienceWap.find('.experience').text());
    var $textarea = $experienceWap.find('textarea');

    $experienceWap.addClass('edit');
    $textarea.val(experience);
    $textarea.focus();
});

// 提交话题经验
$('.btn-submit-experience').click(function () {
    var topicId = parseInt($(this).data('topic-id'));
    var $experienceWap = $(this).parents('.experience-wap');
    var $btnApply = $experienceWap.next();
    var $textarea = $experienceWap.find('textarea');
    var experience = $.trim($textarea.val());
    var $experience = $experienceWap.find('.experience');
    var $myselfInfo = $('.myself-info');

    $.ajax({
        url: urlFor('topic.update_experience', {uid: topicId}),
        method: 'post',
        dataType: 'json',
        data: {
            experience: experience
        }
    }).done(function (response) {
        if (response.result) {
            $experience.text(experience);
            $experienceWap.removeClass('edit');

            if ($btnApply.hasClass('applied')) {
                $myselfInfo.find('.experience').text("，" + experience);
                $("input[name='experience']").val(experience);
            }

            if (experience === "") {
                $experienceWap.addClass('empty')
            } else {
                $experienceWap.removeClass('empty')
            }
        }
    });
});

// 取消编辑话题经验
$('.btn-cancel-edit-experience').click(function () {
    var $experienceWap = $(this).parents('.experience-wap');

    $experienceWap.removeClass('edit');
});

// 采用话题经验
$('.btn-apply-experience').click(function () {
    var $experienceWap = $(this).parent().find('.experience-wap');
    var experience = $.trim($experienceWap.find('.experience').text());
    var applied = $(this).hasClass('applied');
    var $myselfInfo = $('.myself-info');

    // 取消采纳
    if (applied) {
        // 取消选中该按钮
        $(this).removeClass('applied').removeClass('btn-primary').addClass('btn-default');

        $myselfInfo.find('.experience').empty();
        $("input[name='experience']").val('');
        $myselfInfo.find('.desc').show();
    } else {
        // 采纳
        if ($experienceWap.hasClass('empty')) {
            return;
        }

        $myselfInfo.find('.experience').text("，" + experience);
        $("input[name='experience']").val(experience);
        $myselfInfo.find('.desc').hide();
        // 选中该按钮
        $(this).addClass('applied').addClass('btn-primary').removeClass('btn-default');
        // 取消其他按钮的选中状态
        $('.btn-apply-experience').not(this).removeClass('applied').removeClass('btn-primary').addClass('btn-default');
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
