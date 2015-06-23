// 去除擅长话题
$('.btn-remove-topic').click(function () {
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
$('.btn-add-experience').click(function () {
    var $expertTopicWap = $(this).parents('.expert-topic');
    var $textarea = $expertTopicWap.find('textarea');

    $expertTopicWap.addClass('edit');
    $textarea.focus();
});

// 编辑话题经验
$('.btn-edit-experience').click(function () {
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
