var $mainWap = $('#main-wap');
var selectedTopicsCount = 0;
var $btnNext = $('.btn-next');

// 选择话题
$(document).on('click', '#main-wap .topic', function () {
    var active = $(this).hasClass('active');
    var id = $(this).data('id');

    if (active) {
        selectedTopicsCount -= 1;
        $(this).removeClass('active').find('input').detach();
    } else {
        selectedTopicsCount += 1;
        $(this).addClass('active').append("<input type='hidden' name='topic_id' value='" + id + "'>");
    }

    if (selectedTopicsCount < 0) {
        selectedTopicsCount = 0;
    }

    if (selectedTopicsCount >= 10) {
        $btnNext.removeClass('not-finish');
    } else {
        $btnNext.addClass('not-finish');
    }

    $btnNext.find('.left-topics-count').text(10 - selectedTopicsCount);
});

// 切换话题面板
$mainWap.find('.selector').click(function () {
    var targetClass = $(this).data('target');

    $(this).addClass('active').siblings().removeClass('active');
    $mainWap.find('.topics-wap').removeClass('active');
    $mainWap.find('.' + targetClass).addClass('active');
});

// 提交结果
$btnNext.click(function () {
    if (selectedTopicsCount < 10) {
        return;
    }

    $('.form-select-topics').ajaxSubmit({
        url: urlFor('account.submit_interesting_topics'),
        method: 'post',
        dataType: 'json',
        success: function (response) {
            if (response.result) {
                window.location = urlFor('account.select_products_worked_on');
            }
        }
    });
});
