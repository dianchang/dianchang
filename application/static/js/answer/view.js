// 继续阅读
$('.btn-continue-reading').click(function () {
    var $answer = $(this).parents('.more-answer');

    $answer.addClass('full');
});

// 高亮评论
//var hash = window.location.hash;
//if (startsWith(hash, '#comment')) {
//    var commentId = hash.split('#comment')[1];
//    var $comment = $(".answer-comment[data-id='" + commentId + "']");
//
//    $comment.css('backgroundColor', '#E6F9F2');
//    $(window).scrollTo($comment, {
//        offset: {
//            top: -200
//        }
//    });
//
//    setTimeout(function () {
//        $comment.animate({
//            'backgroundColor': '#f5f5f5'
//        }, 2000);
//    });
//}

// 跳转回答
$('.more-answer').click(function (e) {
    var href = $(this).data('href');

    if (e.target.targetName === 'A' || $(e.target).parents('a').length !== 0) {
        return true;
    }

    window.location = href;
});
