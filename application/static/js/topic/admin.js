var timerForParentTopicTypeahead = null;
var $nameWap = $('.name-wap');
var $parentTopicInput = $("input[name='parent-topic']");
var timerForTopicTypeahead = null;
var $childTopicInput = $("input[name='child-topic']");
var $synonymInput = $("input[name='synonym']");

// 进入名称编辑模式
$('.btn-edit-name').click(function () {
    var name = $.trim($nameWap.find('.name').text());

    $nameWap.addClass('edit').find('input').val(name).focus();
});

// 保存名称
$('.btn-save-name').click(function () {
    var id = $(this).data('id');
    var name = $.trim($(this).parents('.name-wap').find('input').val());

    $.ajax({
        url: urlFor('topic.update_name', {uid: id}),
        method: 'post',
        dataType: 'json',
        data: {
            name: name
        }
    }).done(function (response) {
        if (response.result) {
            $nameWap.find('.name').text(name);
        }

        $nameWap.removeClass('edit');
    });
});

// parentTopicInput启用Typeahead自动完成
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
                    q: q,
                    descendant_topic_id: g.topicId
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
    addParentTopic(g.topicId, parentTopic.id);
});

// 删除直接父话题
$(document).on('click', '.btn-remove-parent-topic', function () {
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

// childTopicInput启用Typeahead自动完成
$childTopicInput.typeahead({
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

// 通过选择autocomplete菜单项添加句集
$childTopicInput.on('typeahead:selected', function (e, childTopic) {
    addChildTopic(g.topicId, childTopic.id);
});

// 删除直接子话题
$(document).on('click', '.btn-remove-child-topic', function () {
    var childTopicId = parseInt($(this).data('child-topic-id'));
    var _this = $(this);

    $.ajax({
        url: urlFor('topic.remove_child_topic', {uid: g.topicId, child_topic_id: childTopicId}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            _this.parent().detach();
        }
    });
});

// 添加话题同义词
$synonymInput.on('keypress', function (e) {
    var name = $.trim($(this).val());
    var _this = $(this);

    if (e.which === 13) {
        e.preventDefault();

        $.ajax({
            url: urlFor('topic.add_synonym', {uid: g.topicId}),
            method: 'post',
            dataType: 'json',
            data: {
                synonym: name
            }
        }).done(function (response) {
            if (response.result) {
                $('.synonyms').append(response.html);
                _this.val('').focus();
            }
        });
    }
});

// 删除话题同义词
$(document).on('click', '.btn-remove-topic-synonym', function () {
    var id = $(this).data('id');
    var _this = $(this);

    $.ajax({
        url: urlFor('topic.remove_synonym', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            _this.parent().detach();
        }
    });
});

// 上传话题图片
var uploader = simple.uploader({
    url: 'http://upload.qiniu.com',
    fileKey: 'file',
    connectionCount: 1,
    'params': {
        token: g.uptoken
    }
});

$('.btn-upload-topic-avatar').click(function () {
    $("input[name='avatar']").click();
});

$("input[name='avatar']").on('change', function () {
    uploader.upload(this.files);
});

uploader.on('uploadsuccess', function (e, file, response) {
    if (response.result) {
        $('img.topic-avatar').attr('src', response.url);
    }
});

// 申请删除话题
$('.btn-apply-for-deletion').click(function () {
    var id = $(this).data('id');
    var _this = $(this);
    var applied = $(this).hasClass('applied');

    if (applied) {
        return false;
    }

    $.ajax({
        url: urlFor('topic.apply_for_deletion', {uid: id}),
        dataType: 'json',
        method: 'post'
    }).done(function (response) {
        if (response.result) {
            _this.addClass('applied').text('申请已提交');
        }
    });
});


// 锁定话题
$('.lock-wap input').change(function () {
    var lockTarget = $(this).val();
    var id = g.topicId;

    $.ajax({
        url: urlFor('topic.lock', {uid: id}),
        method: 'post',
        dataType: 'json',
        data: {
            target: lockTarget
        }
    }).done(function (response) {
        if (response.result) {
            if (lockTarget === 'all') {
                if (response.locked) {
                    $('.lock-wap input').prop('checked', true);
                } else {
                    $('.lock-wap input').prop('checked', false);
                }
            }
        }
    });
});

/**
 * 添加直接父话题
 * @param {int} topicId - 问题id
 * @param {int} parentTopicId - 问题id
 */
function addParentTopic(topicId, parentTopicId) {
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

/**
 * 添加直接子话题
 * @param {int} topicId - 话题id
 * @param {int} childTopicId - 子话题id
 */
function addChildTopic(topicId, childTopicId) {
    $.ajax({
        url: urlFor('topic.add_child_topic', {uid: topicId, child_topic_id: childTopicId}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            if (!$(".child-topic-wap[data-id='" + response.id + "']").length) {
                $(".child-topics").append(response.html);
            }
            $childTopicInput.typeahead('val', '');
        }
    });
}
