var $mainWap = $('#main-wap');
var $rightWap = $mainWap.find('.right-wap');
var $upvoteWap = $mainWap.find('.upvote-wap');
var $btnAskQuestion = $('.btn-ask-question');

// 添加提醒点
if ($rightWap.hasClass('at-guide-step-3')) {
    $upvoteWap.addClass('bubble-notice');
} else if ($rightWap.hasClass('at-guide-step-6')) {
    $btnAskQuestion.addClass('bubble-notice').addClass('bubble-notice-top');
}

$upvoteWap.click(function () {
    $(this).removeClass('bubble-notice');
});

$btnAskQuestion.click(function () {
    $(this).removeClass('bubble-notice').removeClass('bubble-notice-top');
});

$mainWap.on('click', '.btn-next-step', function () {
    var currentStep = parseInt($(this).data('step'));
    var nextStep = currentStep + 1;

    if (currentStep < 1 || currentStep > 6) {
        return false;
    }

    $.ajax({
        url: urlFor('account.finish_guide'),
        dataType: 'json',
        method: 'post',
        data: {
            'step': currentStep
        }
    }).done(function (response) {
        if (response.result) {
            if (currentStep < 6) {
                $rightWap.removeClass('at-guide-step-' + currentStep).addClass('at-guide-step-' + nextStep);
            } else if (currentStep == 6) {
                $rightWap.removeClass('at-guide-step-' + currentStep).removeClass('need-guide');
            }

            if (currentStep === 2) {
                $upvoteWap.addClass('bubble-notice');
            } else {
                $upvoteWap.removeClass('bubble-notice');
            }

            if (currentStep === 5) {
                $btnAskQuestion.addClass('bubble-notice').addClass('bubble-notice-top');
            } else {
                $btnAskQuestion.removeClass('bubble-notice').removeClass('bubble-notice-top');
            }
        }
    });
});
