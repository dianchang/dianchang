(function () {
    // Flash message
    setTimeout(showFlash, 200);
    setTimeout(hideFlash, 2000);

    // 搜索框
    $('.navbar-form input').focus(function () {
        $('.navbar-form .help-text').show();
    }).blur(function () {
        $('.navbar-form .help-text').hide();
    });

    // 消息通知
    $('.dropdown-menu-noti').on('click', function (e) {
        e.stopPropagation();
    });

    // 切换通知面板
    $('.noti-tabs li').click(function () {
        var targetClass = $(this).data('toggle');

        $(this).addClass('active');
        $('.noti-tabs li').not(this).removeClass('active');

        $('.noti-panel').removeClass('active');
        console.log('.noti-panel-' + targetClass);
        $('.noti-panel-' + targetClass).addClass('active');
    });

    // 显示消息类通知
    $('.notifications-count-wap').click(function () {
        var $messageNotiWap = $('.noti-panel-message');

        if (!$messageNotiWap.hasClass('empty')) {
            return true;
        }

        $.ajax({
            url: urlFor('user.get_message_notifications'),
            method: 'post',
            dataType: 'json'
        }).done(function (response) {
            if (response.result) {
                if ($.trim(response.html) !== '') {
                    $messageNotiWap.html(response.html).removeClass('empty');
                } else {
                    $messageNotiWap.addClass('empty');
                }
            }
        });
    });

    $('.noti-tab-message').click(function () {
        $(this).removeClass('new');
    });

    // 显示用户类通知
    $('.noti-tab-user').click(function () {
        var $userNotiWap = $('.noti-panel-user');
        var _this = $(this);

        if (!$userNotiWap.hasClass('empty')) {
            return true;
        }

        $.ajax({
            url: urlFor('user.get_user_notifications'),
            method: 'post',
            dataType: 'json'
        }).done(function (response) {
            if (response.result) {
                if ($.trim(response.html) !== '') {
                    $userNotiWap.html(response.html).removeClass('empty');
                } else {
                    $userNotiWap.addClass('empty');
                }

                _this.removeClass('new');
            }
        });
    });

    // 显示感谢类通知
    $('.noti-tab-thanks').click(function () {
        var $thanksNotiWap = $('.noti-panel-thanks');
        var _this = $(this);

        if (!$thanksNotiWap.hasClass('empty')) {
            return true;
        }

        $.ajax({
            url: urlFor('user.get_thanks_notifications'),
            method: 'post',
            dataType: 'json'
        }).done(function (response) {
            if (response.result) {
                if ($.trim(response.html) !== '') {
                    $thanksNotiWap.html(response.html).removeClass('empty');
                } else {
                    $thanksNotiWap.addClass('empty');
                }

                _this.removeClass('new');
            }
        });
    });

    // 调整modal高度
    $('.modal-adjust-position').on('show.bs.modal', function () {
        var _this = $(this);

        setTimeout(function () {
            var $dialog = _this.find(".modal-dialog");
            var offset;

            _this.css('display', 'block');
            offset = ($(window).height() - $dialog.height()) * 0.3;

            if (offset > 0) {
                $dialog.css('margin-top', offset);
            }
        }, 50);
    });

    // 提问
    var timerForTopicTypeahead = null;
    var timerForQuestion = null;
    var $askQuestionBg = $('.ask-question-bg');
    var $askQuestionWap = $askQuestionBg.find('.ask-question-wap');
    var $topicInput = $askQuestionBg.find("input[name='search-topic']");
    var $questionInput = $askQuestionBg.find("input[name='question']");
    var $similarQuestions = $askQuestionBg.find('.similar-questions');
    var $toSecondBtn = $askQuestionBg.find('.btn-to-second');
    var $toFirstBtn = $askQuestionBg.find('.btn-to-first');
    var $questionHeader = $askQuestionBg.find('.question-header-wap');
    var $questionTitle = $askQuestionBg.find(".question-title");
    var $questionTitleInput = $askQuestionBg.find("input[name='title']");
    var $firstAnonymousCheckbox = $askQuestionBg.find(".first-form input[name='anonymous']");
    var $secoundAnonymousCheckbox = $askQuestionBg.find(".second-form input[name='anonymous']");
    var $btnCloseBg = $askQuestionBg.find('.btn-close-bg');
    var $btnAddDesc = $askQuestionBg.find('.btn-add-question-desc');
    var $btnSubmitQuestion = $askQuestionBg.find('.btn-submit-question');
    var $descTextarea = $askQuestionBg.find('textarea');
    var $firstForm = $askQuestionBg.find('.second-form');
    var $secondForm = $askQuestionBg.find('.second-form');
    var descEditor = null;

    // 显示提问框
    $('.btn-ask-question').click(function () {
        if (!$askQuestionBg.hasClass('open')) {
            $askQuestionBg.show().addClass('open');
        }
    });

    // 隐藏提问框
    $btnCloseBg.click(function () {
        $askQuestionBg.hide().removeClass('open');
        $askQuestionWap.addClass('first').removeClass('second');
        $questionInput.val('');
        $similarQuestions.empty().hide();
        $secondForm.find('.topics').empty();
        $questionHeader.removeClass('edit');

        if (descEditor !== null) {
            descEditor.destroy();
        }
    });

    // 添加补充描述
    $btnAddDesc.click(function () {
        descEditor = new Simditor({
            textarea: $descTextarea,
            toolbarFloat: false,
            toolbar: ['bold', 'italic', 'underline', 'ol', 'ul', 'blockquote', 'code', 'link', 'image', 'markdown'],
            upload: {
                url: 'http://upload.qiniu.com',
                fileKey: 'file',
                connectionCount: 1,
                leaveConfirm: '正在上传文件，如果离开上传会自动取消',
                params: {
                    token: g.editorUptoken
                }
            }
        });

        $questionHeader.addClass('edit');
    });

    // 输入问题，返回类似问题
    $questionInput.on('keyup', function () {
        var title = $.trim($(this).val());

        if (timerForQuestion) {
            clearTimeout(timerForQuestion);
        }

        if (title === "") {
            $similarQuestions.hide().empty();
            return;
        }

        timerForQuestion = setTimeout(function () {
            $.ajax({
                url: urlFor('question.similar'),
                method: 'post',
                dataType: 'json',
                data: {
                    title: title
                }
            }).done(function (response) {
                if (response.count !== 0) {
                    $('.similar-questions').show().html("<p class='text-light tip'>类似问题：</p>" + response.html);
                    $toSecondBtn.text('我的问题是新的，下一步');
                } else {

                    $toSecondBtn.text('下一步');
                }
            });
        }, 500);
    });

    // 进入提问的第二阶段
    $toSecondBtn.click(function () {
        var title = $.trim($questionInput.val());

        if (title === "") {
            return;
        }

        $askQuestionWap.removeClass('first').addClass('second');
        $questionTitle.text(title);
        $questionTitleInput.val(title);
        $secoundAnonymousCheckbox.prop('checked', $firstAnonymousCheckbox.is(':checked'));
    });

    // 启动Typeahead自动完成
    $topicInput.typeahead({
        minLength: 1,
        highlight: true,
        hint: false
    }, {
        displayKey: 'name',
        source: function (q, cb) {
            if (timerForTopicTypeahead) {
                clearTimeout(timerForTopicTypeahead);
            }

            timerForTopicTypeahead = setTimeout(function () {
                $.ajax({
                    url: urlFor('topic.query'),
                    method: 'post',
                    dataType: 'json',
                    data: {
                        q: q
                    }
                }).done(function (matchs) {
                    cb(matchs);
                });
            }, 300);
        },
        templates: {
            'suggestion': function (data) {
                return '<p>' + data.name + '</p>';
            }
        }
    });

    // 通过选择autocomplete菜单项添加话题
    $topicInput.on('typeahead:selected', function (e, topic) {
        addTopic(topic);
    });

    // 通过回车添加话题
    $topicInput.on('keypress', function (e) {
        var name = $.trim($(this).val());

        if (e.which === 13) {
            e.preventDefault();

            if (name === "") {
                return;
            }

            $.ajax({
                url: urlFor('topic.get_by_name', {name: name}),
                method: 'post',
                dataType: 'json'
            }).done(function (topic) {
                    addTopic(topic);
                }
            );
        }
    });

    // 选中该话题
    $askQuestionBg.on('change', '.topic-selector', function () {
        var id = $(this).data('id');
        var $topicWap = $(this).parents('.topic-wap');

        if ($(this).is(':checked')) {
            $topicWap.append("<input type='hidden' name='topic' value='" + id + "'>");
        } else {
            $topicWap.find("input[name='topic']").detach();
        }
    });

    var timerForSubmitQuestion = null;

    // 提交问题
    $btnSubmitQuestion.click(function () {
        $secondForm.ajaxSubmit({
            url: urlFor('question.add'),
            method: 'POST',
            dataType: 'json',
            success: function (response) {
                if (response.result) {
                    window.location = urlFor('question.view', {uid: response.id});
                } else {
                    clearTimeout(timerForSubmitQuestion);

                    if (response.error === 'notopic') {
                        $btnSubmitQuestion.tooltip({
                            title: '请至少添加一个话题',
                            trigger: 'manual'
                        }).tooltip('show');

                        timerForSubmitQuestion = setTimeout(function () {
                            $btnSubmitQuestion.tooltip('hide');
                        }, 3000);
                    }
                }
            }
        });
    });

    // 退回到提问的第一阶段
    $toFirstBtn.click(function () {
        $askQuestionWap.removeClass('second').addClass('first');
        $firstAnonymousCheckbox.prop('checked', $secoundAnonymousCheckbox.is(':checked'));
    });

    // 弹出用户卡片
    $(document).on('mouseenter', '.dc-show-user-card', function () {
        var id = $(this).data('id');
        var html = $(this).data('user');
        var _this = $(this);

        // 隐藏其他的用户卡片
        $('.dc-show-user-card').popover('destroy');

        //if (typeof html === 'undefined') {
        $.ajax({
            url: urlFor('user.get_card', {uid: id}),
            method: 'post',
            dataType: 'json'
        }).done(function (response) {
            if (response.result) {
                //_this.data('user', response.html);
                showUserCard(_this, response.html);
            }
        });
        //} else {
        //    showUserCard(_this, html);
        //}
    });

    // 隐藏用户卡片
    $(document).on('mouseleave', '.dc-show-user-card', function () {
        var _this = $(this);

        setTimeout(function () {
            if (!$(".popover:hover").length) {
                $(_this).popover("destroy");
            }
        }, 200);
    });

    // 弹出话题卡片
    $(document).on('mouseenter', '.dc-show-topic-card', function () {
        var id = $(this).data('id');
        var html = $(this).data('topic');
        var _this = $(this);

        // 隐藏其他的用户卡片
        $('.dc-show-topic-card').popover('destroy');

        //if (typeof html === 'undefined') {
        $.ajax({
            url: urlFor('topic.get_card', {uid: id}),
            method: 'post',
            dataType: 'json'
        }).done(function (response) {
            if (response.result) {
                //_this.data('topic', response.html);
                showTopicCard(_this, response.html);
            }
        });
        //} else {
        //    showUserCard(_this, html);
        //}
    });

    // 隐藏话题卡片
    $(document).on('mouseleave', '.dc-show-topic-card', function () {
        var _this = $(this);

        setTimeout(function () {
            if (!$(".popover:hover").length) {
                $(_this).popover("destroy");
            }
        }, 200);
    });

    var timerForUserCard = null;

    /**
     * 显示用户卡片
     * @param $element
     * @param html
     */
    function showUserCard($element, html) {
        clearTimeout(timerForUserCard);

        $element.popover({
            content: function () {
                return html;
            },
            html: true,
            container: 'body',
            trigger: 'manual',
            placement: 'auto bottom',
            animation: false,
            viewport: {
                selector: 'body',
                padding: 15
            },
            template: '<div class="popover user-popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>',
            selector: '.dc-show-user-card'
        });

        timerForUserCard = setTimeout(function () {
            $element.popover('show');
        }, 500);

        $(document).onOnce("mouseleave", ".user-popover", function () {
            $element.popover('destory');
        });
    }

    var timerForTopicCard = null;

    /**
     * 显示话题卡片
     * @param $element
     * @param html
     */
    function showTopicCard($element, html) {
        clearTimeout(timerForTopicCard);

        $element.popover({
            content: function () {
                return html;
            },
            html: true,
            container: 'body',
            trigger: 'manual',
            placement: 'auto bottom',
            animation: false,
            viewport: {
                selector: 'body',
                padding: 15
            },
            template: '<div class="popover topic-popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>',
            selector: '.dc-show-topic-card'
        });

        timerForTopicCard = setTimeout(function () {
            $element.popover('show');
        }, 500);

        $(document).onOnce("mouseleave", ".topic-popover", function () {
            $element.popover('destroy');
        });
    }

    /**
     * Add topic.
     * @param {Object} topic
     */
    function addTopic(topic) {
        if (!$(".ask-question-bg .topic-wap[data-id='" + topic.id + "']").length) {
            $(".ask-question-bg .topics").append(
                "<div class='topic-wap' data-id='" + topic.id + "'>"
                + "<input type='checkbox' class='topic-selector' data-id='" + topic.id + "' checked=checked>"
                + "<a class='dc-topic' href='" + urlFor('topic.view', {uid: topic.id}) + "' target='_blank'>" + topic.name + "</a>"
                + "<span class='followers-count'>" + topic.followers_count + " 人关注</span>"
                + "<input type='hidden' name='topic' value='" + topic.id + "'>"
                + "</div>"
            );
        }
        $topicInput.typeahead('val', '');
    }

    /**
     * Show flash message.
     */
    function showFlash() {
        $('.flash-message').slideDown('fast');
    }

    /**
     * Hide flash message.
     */
    function hideFlash() {
        $('.flash-message').slideUp('fast');
    }
})();
