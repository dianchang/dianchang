// 赞评论
$(document).onOnce('click', '.btn-like-comment', function () {
    var $likeCommentWap = $(this).parents('.like-comment-wap').first();
    var $likesCount = $(this).find('.likes-count');
    var id = parseInt($(this).data('id'));

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $.ajax({
        url: urlFor('answer.like_comment', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            if (response.liked) {
                $likeCommentWap.addClass('liked').removeClass('zero');
            } else {
                $likeCommentWap.removeClass('liked');

                if (response.count == 0) {
                    $likeCommentWap.addClass('zero');
                } else {
                    $likeCommentWap.removeClass('zero');
                }
            }

            $likesCount.text(response.count);
        }
    });
});

// 回复评论
$(document).onOnce('click', '.btn-reply-comment', function () {
    var id = parseInt($(this).data('id'));
    var $commentBody = $(this).parents('.media-body');

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    $commentBody.append(
        "<div class='comment-form-wap'>"
        + "<div class='comment-edit-area' contenteditable='true'></div>"
        + "<div class='commands'>"
        + "<a href='javascript: void(0)' class='btn-cancel-reply'>取消</a>"
        + "<button type='button' class='btn btn-primary btn-submit-reply' data-parent-id=" + id + ">评论</button>"
        + "</div>"
        + "</div>"
    );

    $commentBody.find('.comment-edit-area').focus();
});

// 取消回复
$(document).onOnce('click', '.btn-cancel-reply', function () {
    $(this).parents('.comment-form-wap').first().detach();
});

// 提交回复
$(document).onOnce('click', '.btn-submit-reply', function () {
    var parentCommentId = parseInt($(this).data('parent-id'));
    var $commentWap = $(this).parents('.answer-comment');
    var $replyWap = $(this).parents('.comment-form-wap').first();
    var comment = $.trim($(this).parent().prev().html());

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    if (comment === '') {
        return;
    }

    $.ajax({
        url: urlFor('answer.reply_comment', {uid: parentCommentId}),
        method: 'post',
        dataType: 'json',
        data: {
            content: comment
        }
    }).done(function (response) {
        if (response.result) {
            $commentWap.after(response.html);
            $replyWap.detach();
        }
    });
});

// 评论区
$('.comment-edit-area').focus(function () {
    $(this).html('');
    $(this).next().show();
});

// 取消评论
$('.btn-cancel-comment').click(function () {
    $(this).parent().hide();
    $(this).parent().prev().html("<p class='text-light'>写下你的评论...</p>");
});

// 提交评论
$(document).onOnce('click', '.btn-submit-comment', function () {
    var $comments = $('.comments');
    var comment = $.trim($(this).parent().prev().html());
    var _this = $(this);

    if (!g.signin) {
        window.location = urlFor('account.signin');
        return;
    }

    if (comment === '') {
        return;
    }

    $.ajax({
        url: urlFor('answer.comment', {uid: g.answerId}),
        method: 'post',
        dataType: 'json',
        data: {
            content: comment
        }
    }).done(function (response) {
        if (response.result) {
            $comments.after(response.html);
            _this.parent().hide();
            _this.parent().prev().html("<p class='text-light'>写下你的评论...</p>");
        }
    });
});
