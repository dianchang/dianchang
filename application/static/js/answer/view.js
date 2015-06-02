// 赞评论
$(document).onOnce('click', '.btn-like-comment', function () {
    var $likeCommentWap = $(this).parents('.like-comment-wap').first();
    var $likesCount = $(this).find('.likes-count');
    var id = parseInt($(this).data('id'));

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
