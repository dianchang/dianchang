// 继续阅读
$('.btn-continue-reading').click(function () {
    var $answer = $(this).parents('.more-answer');

    $answer.addClass('full');
});

// 高亮评论
var hash = window.location.hash;
if (startsWith(hash, '#comment')) {
    var commentId = hash.split('#comment')[1];
    var $comment = $(".answer-comment[data-id='" + commentId + "']");

    $comment.css('backgroundColor', '#E6F9F2');
    $(window).scrollTo($comment, {
        offset: {
            top: -200
        }
    });

    setTimeout(function () {
        $comment.animate({
            'backgroundColor': '#f5f5f5'
        }, 2000);
    });
}
