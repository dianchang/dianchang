// 显示desc编辑框
$('.btn-edit-desc').click(function () {
    var desc = $.trim($('.desc').text());

    $(this).parents('.desc-wap').addClass('edit');
    $('.input-desc').val(desc).focus();
});

// 更新desc
$('.btn-submit-desc').click(function () {
    var $input = $(this).prev();
    var desc = $.trim($input.val());

    $.ajax({
        url: urlFor('user.update_desc'),
        method: 'post',
        dataType: 'json',
        data: {
            desc: desc
        }
    }).done(function (response) {
        if (response.result) {
            $('.desc').text(desc);

            $('.desc-wap').removeClass('edit');
        }
    });
});

// 显示desc编辑框
$('.btn-edit-meta').click(function () {
    var location, organization, position;

    if ($('.location').length !== 0) {
        location = $.trim($('.location').text());
    } else {
        location = "";
    }

    console.log(location);

    if ($('.organization').length !== 0) {
        organization = $.trim($('.organization').text());
    } else {
        organization = "";
    }

    if ($('.position').length !== 0) {
        position = $.trim($('.position').text());
    } else {
        position = "";
    }

    $(this).parents('.user-meta-wap').addClass('edit');

    $('.input-location').val(location).focus();
    $('.input-organization').val(organization);
    $('.input-position').val(position);
});

// 更新desc
$('.btn-submit-meta').click(function () {
    var location = $.trim($('.input-location').val());
    var organization = $.trim($('.input-organization').val());
    var position = $.trim($('.input-position').val());

    $.ajax({
        url: urlFor('user.update_meta_info'),
        method: 'post',
        dataType: 'json',
        data: {
            location: location,
            organization: organization,
            position: position
        }
    }).done(function (response) {
        var html = "";

        if (response.result) {
            if (location) {
                html += "<span class='location'>" + location + "</span> <span class='divider'>·</span>";
            }
            if (organization) {
                html += " <span class='organization'>" + organization + "</span> <span class='divider'>·</span>";
            }
            if (position) {
                html += " <span class='position'>" + position + "</span> <span class='divider'>·</span>";
            }

            $('.user-meta').html(html);
            $('.user-meta-wap').removeClass('edit');
        }
    });
});

