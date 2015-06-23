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
