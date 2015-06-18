// Flash message
setTimeout(showFlash, 200);
setTimeout(hideFlash, 2000);

// 搜索框
$('.navbar-form input').focus(function () {
    $('.navbar-form .help-text').show();
}).blur(function () {
    $('.navbar-form .help-text').hide();
});

$('#nav-notification').click(function () {
    if ($(this).hasClass('on') && $(this).hasClass('more')) {
        $(this).removeClass('on').removeClass('more');
    } else if ($(this).hasClass('on')) {
        $(this).addClass('more');
        $(this).find('.notifications-count').text(23);
    } else {
        $(this).addClass('on');
        $(this).find('.notifications-count').text(2);
    }
});

// 调整modal高度
$('.modal-adjust-position').on('show.bs.modal', function () {
    var _this = $(this);

    setTimeout(function () {
        var $dialog = _this.find(".modal-dialog");
        var offset;

        _this.css('display', 'block');
        offset = ($(window).height() - $dialog.height()) * 0.3;

        if (offset > 0) {
            $dialog.css('margin-top', offset);
        }
    }, 50);
});

var timerForTopicTypeahead = null;
var timerForQuestion = null;
var $askQuestionBg = $('.ask-question-bg');
var $askQuestionWap = $askQuestionBg.find('.ask-question-wap');
var $topicInput = $askQuestionBg.find("input[name='search-topic']");
var $questionInput = $askQuestionBg.find("input[name='question']");
var $toSecondBtn = $askQuestionBg.find('.btn-to-second');
var $toFirstBtn = $askQuestionBg.find('.btn-to-first');
var $questionTitle = $askQuestionBg.find(".question-title");
var $questionTitleInput = $askQuestionBg.find("input[name='title']");
var $firstAnonymousCheckbox = $askQuestionBg.find(".first-form input[name='anonymous']");
var $secoundAnonymousCheckbox = $askQuestionBg.find(".second-form input[name='anonymous']");
var $btnCloseBg = $askQuestionBg.find('.btn-close-bg');
var $descTextarea = $askQuestionBg.find('textarea');
var $secondForm = $askQuestionBg.find('.second-form');
var descEditor = null;

// 显示提问框
$('.btn-ask-question').click(function () {
    if (!$askQuestionBg.hasClass('open')) {
        $askQuestionBg.show('slow').addClass('open');
    }
});

// 隐藏提问框
$btnCloseBg.click(function () {
    $askQuestionBg.hide('slow').removeClass('open');
});

// 添加补充描述
$('.btn-add-desc').click(function () {
    descEditor = new Simditor({
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

    $(this).detach();
});

// 输入问题，返回类似问题
$questionInput.on('keyup', function () {
    var title = $.trim($(this).val());

    if (timerForQuestion) {
        clearTimeout(timerForQuestion);
    }

    if (title === "") {
        $('.similar-questions').hide().empty();
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
                $('.similar-questions').show().html("<p class='text-light tip'>类似问题：</p>" + response.html);
                $toSecondBtn.text('我的问题是新的，下一步');
            } else {

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

    $askQuestionWap.removeClass('first').addClass('second');
    $questionTitle.text(title);
    $questionTitleInput.val(title);
    $secoundAnonymousCheckbox.prop('checked', $firstAnonymousCheckbox.is(':checked'));
});

// 删除话题
$(document).onOnce('click', '.btn-delete-topic', function () {
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
        if (timerForTopicTypeahead) {
            clearTimeout(timerForTopicTypeahead);
        }

        timerForTopicTypeahead = setTimeout(function () {
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

// 通过选择autocomplete菜单项添加话题
$topicInput.on('typeahead:selected', function (e, topic) {
    addTopic(topic);
});

// 通过回车添加话题
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

// 选中该话题
$askQuestionBg.on('change', '.topic-selector', function () {
    var id = $(this).data('id');
    var $topicWap = $(this).parents('.topic-wap');

    if ($(this).is(':checked')) {
        $topicWap.append("<input type='hidden' name='topic' value='" + id + "'>");
    } else {
        $topicWap.find("input[name='topic']").detach();
    }
});

// 提交问题
$('.btn-submit-question').click(function () {
    $secondForm.ajaxSubmit({
        url: urlFor('question.add'),
        method: 'POST',
        dataType: 'json',
        success: function (response) {
            if (response.result) {
                window.location = urlFor('question.view', {uid: response.id});
            }
        }
    });
});

// 退回到提问的第一阶段
$toFirstBtn.click(function () {
    $askQuestionWap.removeClass('second').addClass('first');
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
            + "<input type='checkbox' class='topic-selector' data-id='" + topic.id + "' checked=checked>"
            + "<a class='dc-topic' href='" + urlFor('topic.view', {uid: topic.id}) + "' target='_blank'>" + topic.name + "</a>"
            + "<span class='followers-count'>" + topic.followers_count + " 人关注</span>"
            + "<input type='hidden' name='topic' value='" + topic.id + "'>"
            + "</div>"
        );
    }
    $topicInput.typeahead('val', '');
}

/**
 * Show flash message.
 */
function showFlash() {
    $('.flash-message').slideDown('fast');
}

/**
 * Hide flash message.
 */
function hideFlash() {
    $('.flash-message').slideUp('fast');
}
