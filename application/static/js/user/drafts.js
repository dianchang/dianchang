// 删除草稿
$('.btn-remove-draft').click(function () {
    var id = parseInt($(this).data('id'));
    var $draftWap = $(this).parents('.draft').first();

    $.ajax({
        url: urlFor('answer.remove_draft', {uid: id}),
        method: 'post',
        dataType: 'json'
    }).done(function (response) {
        if (response.result) {
            $draftWap.hide('fast', function () {
                $draftWap.detach();
            });
        }
    });
});
