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
        "<div class='comment-reply-wap'>"
        + "<textarea name='comment' class='form-control' cols='30' rows='5'></textarea>"
        + "<a class='btn-cancel-reply' href='javascript: void(0)'>取消</a>"
        + "<button class='btn-submit-reply btn btn-primary' type='button' data-parent-id=" + id + ">评论</button>"
        + "</div>"
    );
});

// 取消回复
$(document).onOnce('click', '.btn-cancel-reply', function () {
    $(this).parents('.comment-reply-wap').first().detach()
});

// 提交回复
$(document).onOnce('click', '.btn-submit-reply', function () {
    var parentCommentId = parseInt($(this).data('parent-id'));
    var $commentWap = $(this).parents('.answer-comment');
    var $replyWap = $(this).parents('.comment-reply-wap').first();
    var comment = $.trim($replyWap.find('textarea').val());

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
