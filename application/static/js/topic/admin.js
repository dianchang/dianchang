var $nameWap = $('.name-wap');
var $parentTopicInput = $("input[name='parent-topic']");
var $childTopicInput = $("input[name='child-topic']");
var $synonymInput = $("input[name='synonym']");
var $mergeTopic = $("input[name='merge-topic']");

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
    var locked = $(this).hasClass('locked');

    if (!locked) {
        $("input[name='avatar']").click();
    }
});

$("input[name='avatar']").on('change', function () {
    uploader.upload(this.files);
});

uploader.on('uploadsuccess', function (e, file, response) {
    if (response.result) {
        $('img.topic-avatar').attr('src', response.url);
    }
});

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

// 取消编辑名称
$('.btn-cancel-edit-name').click(function () {
    $nameWap.removeClass('edit');
});

// 所属话题启用 Typeahead
$parentTopicInput.initTopicTypeahead({
    params: {
        descendant_topic_id: g.topicId
    },
    callback: function (e, parentTopic) {
        if (typeof parentTopic.create === 'undefined') {
            addParentTopic(g.topicId, {parent_topic_id: parentTopic.id});
        } else {
            addParentTopic(g.topicId, {name: parentTopic.name});
        }
    }
});

// 通过点击按钮添加所属话题
$('.btn-add-parent-topic').click(function () {
    var name = $.trim($parentTopicInput.typeahead('val'));

    if (name !== '') {
        addParentTopic(g.topicId, {name: name});
    }
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

// 下属话题启用 Typeahead
$childTopicInput.initTopicTypeahead({
    params: {
        ancestor_topic_id: g.topicId
    }, callback: function (e, childTopic) {
        if (typeof childTopic.create === 'undefined') {
            addChildTopic(g.topicId, {child_topic_id: childTopic.id});
        } else {
            addChildTopic(g.topicId, {name: childTopic.name});
        }
    }
});

// 通过点击按钮添加下属话题
$('.btn-add-child-topic').click(function () {
    var name = $.trim($childTopicInput.typeahead('val'));

    if (name !== '') {
        addChildTopic(g.topicId, {name: name});
    }
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
    if (e.which === 13) {
        e.preventDefault();
        addSynonym();
    }
});

$('.btn-add-synonym').click(function () {
    addSynonym();
});

// 合并话题启用 Typeahead
// TODO
$mergeTopic.initTopicTypeahead({
    callback: function (e, parentTopic) {
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

// 设置话题类型
$('.topics-kind-wap input').click(function () {
    var id = g.topicId;
    var kind = $(this).val();

    $.ajax({
        url: urlFor('topic.update_kind', {uid: id}),
        method: 'post',
        dataType: 'json',
        data: {
            kind: kind
        }
    }).done(function (response) {

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
 * 添加话题同义词
 */
function addSynonym() {
    var synonym = $.trim($synonymInput.val());

    if (synonym === '') {
        return;
    }

    $.ajax({
        url: urlFor('topic.add_synonym', {uid: g.topicId}),
        method: 'post',
        dataType: 'json',
        data: {
            synonym: synonym
        }
    }).done(function (response) {
        if (response.result) {
            $('.synonyms').append(response.html);
        }

        $synonymInput.val('').focus();
    });
}

/**
 * 添加直接父话题
 * @param {int} topicId - 问题id
 * @param {Object} data
 */
function addParentTopic(topicId, data) {
    $.ajax({
        url: urlFor('topic.add_parent_topic', {uid: topicId}),
        method: 'post',
        dataType: 'json',
        data: data
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
 * @param {Object} data
 */
function addChildTopic(topicId, data) {
    $.ajax({
        url: urlFor('topic.add_child_topic', {uid: topicId}),
        method: 'post',
        dataType: 'json',
        data: data
    }).done(function (response) {
        if (response.result) {
            if (!$(".child-topic-wap[data-id='" + response.id + "']").length) {
                $(".child-topics").append(response.html);
            }
            $childTopicInput.typeahead('val', '');
        }
    });
}
