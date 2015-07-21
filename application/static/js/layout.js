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

    var $navNotification = $('#nav-notification');

    // 通知
    $('.dropdown-menu-noti').on('click', function (e) {
        e.stopPropagation();
    });

    // 弹出通知面板时，禁止 body 滚动
    // TODO

    // 切换通知面板
    $('.noti-tabs li').click(function () {
        var targetClass = $(this).data('toggle');
        var $currentActiveNotiTab = $('.noti-tabs li.active').not(this);
        var $currentActiveNotiPanel = $('.noti-panel.active').not('.noti-panel-' + targetClass);

        // 标记当前 active 的通知为已读
        $currentActiveNotiTab.removeClass('active').removeClass('new');
        $currentActiveNotiPanel.removeClass('active').find('.noti-in-nav').removeClass('unread');

        // 调整通知数目
        reduceNotificationsCount($currentActiveNotiTab.data('new-count'));
        $currentActiveNotiTab.data('new-count', 0);

        // 设置被点击的通知为 active
        $(this).addClass('active');
        $('.noti-panel-' + targetClass).addClass('active');
    });

    // 显示通知
    $('.notifications-count-wap').click(function () {
        var $notiContent = $navNotification.find('.noti-content');
        var $messageNotiWap = $('.noti-panel-message');
        var $userNotiWap = $('.noti-panel-user');
        var $thanksNotiWap = $('.noti-panel-thanks');

        if (!$notiContent.hasClass('empty')) {
            return true;
        }

        $.ajax({
            url: urlFor('user.get_notifications_html'),
            method: 'post',
            dataType: 'json'
        }).done(function (response) {
            if (response.result) {
                $notiContent.removeClass('empty');

                $messageNotiWap.html(response.message_notifications_html);
                $userNotiWap.html(response.user_notifications_html);
                $thanksNotiWap.html(response.thanks_notifications_html);

                $navNotification.find('.noti-tab.active').click();
            }
        });
    });

    // 显示消息类通知
    $('.noti-tab-message').click(function () {
        $.ajax({
            url: urlFor('user.read_message_notifications'),
            method: 'post',
            dataType: 'json'
        });
    });

    // 显示感谢类通知
    $('.noti-tab-thanks').click(function () {
        $.ajax({
            url: urlFor('user.read_thanks_notifications'),
            method: 'post',
            dataType: 'json'
        });
    });

    // 显示用户类通知
    $('.noti-tab-user').click(function () {
        $.ajax({
            url: urlFor('user.read_user_notifications'),
            method: 'post',
            dataType: 'json'
        });
    });

    // 显示通知面板时，切换到第一个有新消息的面板
    $navNotification.on('show.bs.dropdown', function () {
        if (!$navNotification.find('.noti-content').hasClass('empty')) {
            $navNotification.find('.noti-tab').each(function (index, element) {
                if (parseInt($(element).data('new-count')) !== 0) {
                    $(element).click();
                    return false;
                }
            });
        }
    });

    // 隐藏通知面板时，标记当前 active 的通知为已读
    $navNotification.on('hidden.bs.dropdown', function () {
        var $currentActiveNotiTab = $('.noti-tabs li.active');
        var $currentActiveNotiPanel = $('.noti-panel.active');

        // 标记当前 active 的通知为已读
        $currentActiveNotiTab.removeClass('new');
        $currentActiveNotiPanel.find('.noti-in-nav').removeClass('unread');

        // 调整通知数目
        reduceNotificationsCount($currentActiveNotiTab.data('new-count'));
        $currentActiveNotiTab.data('new-count', 0);
    });

    // 通知跳转
    $('.noti-panel').on('click', '.noti-in-nav', function (e) {
        var href = $(this).data('href');

        if (e.target.tagName === 'A' || $(e.target).parents('a').length !== 0) {
            return true;
        }

        if (typeof href === 'undefined') {
            return false;
        }

        window.location = href;
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

    /**
     * 减少通知数目
     * @param count
     */
    function reduceNotificationsCount(count) {
        var $notiNav = $('#nav-notification');
        var $notiCount = $('.notifications-count-wap .notifications-count');
        var currentCount = parseInt($.trim($notiCount.text()));
        var resultCount = currentCount - count;

        if (!$.isNumeric(resultCount)) {
            return;
        }

        if (resultCount < 0) {
            resultCount = 0;
        }

        if (resultCount === 0) {
            $notiNav.removeClass('new').removeClass('more');
        } else if (resultCount < 10) {
            $notiNav.removeClass('mode');
        }

        $notiCount.text(resultCount);
    }

    // 提问
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
        closeAskQuestionBg();
    });

    $(document).keyup(function (e) {
        if (e.keyCode == 27) {
            closeAskQuestionBg();
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
    $topicInput.initTopicTypeahead({
        params: {
            limit: 6
        },
        small: true,
        callback: function (e, topic) {
            if (typeof topic.create === 'undefined') {
                addTopic(topic);
            } else {
                $.ajax({
                    url: urlFor('topic.get_by_name', {name: topic.name}),
                    method: 'post',
                    dataType: 'json'
                }).done(function (topic) {
                        addTopic(topic);
                    }
                );
            }
        }
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
    $(document).onOnce('mouseenter', '.dc-show-user-card', function () {
        var id = parseInt($(this).data('id'));
        var _this = $(this);
        var userData = getUserData(id);

        // 隐藏其他的用户卡片
        $('.dc-show-user-card').popover('hide').popover('destroy');

        if (typeof userData === 'undefined') {
            $.ajax({
                url: urlFor('user.get_data_for_card', {uid: id}),
                method: 'post',
                dataType: 'json'
            }).done(function (response) {
                if (response.result) {
                    setUserData(id, response.user);
                    showUserCard(_this, response.user);
                }
            });
        } else {
            showUserCard(_this, userData);
        }
    });

    // 隐藏用户卡片
    $(document).onOnce('mouseleave', '.dc-show-user-card', function () {
        var _this = $(this);

        setTimeout(function () {
            if (!$(".popover:hover").length) {
                $(_this).popover("destroy");
            }
        }, 200);
    });

    $(document).onOnce('click', '.dc-user-follow-wap', function () {
        var userId = $(this).data('id');
        var followed = $(this).hasClass('followed');
        var myself = $(this).hasClass('myself');
        var _this = $(this);
        var $count = _this.find('.followers-count');
        var url = urlFor('user.follow', {uid: userId});

        if (!g.signin) {
            window.location = urlFor('account.signin');
            return;
        }

        if (myself) {
            return;
        }

        $.ajax({
            url: url,
            method: 'post',
            dataType: 'json'
        }).done(function (response) {
            if (response.result) {
                if (response.followed) {
                    _this.addClass('followed').addClass('btn-default');
                    if (_this.hasClass('dark')) {
                        _this.removeClass('btn-dark');
                    } else {
                        _this.removeClass('btn-light');
                    }
                } else {
                    _this.removeClass('followed').removeClass('btn-default');

                    if (_this.hasClass('dark')) {
                        _this.addClass('btn-dark');
                    } else {
                        _this.addClass('btn-light');
                    }
                }

                setUserData(userId, {
                    'followed': response.followed,
                    'followers_count': response.followers_count
                });
                $count.text(response.followers_count);
            }
        });
    });

    // 弹出话题卡片
    $(document).onOnce('mouseenter', '.dc-show-topic-card', function () {
        var id = $(this).data('id');
        var _this = $(this);
        var topicData = getTopicData(id);

        // 隐藏其他的用户卡片
        $('.dc-show-topic-card').popover('destroy');

        if (typeof topicData === 'undefined') {
            $.ajax({
                url: urlFor('topic.get_data_for_card', {uid: id}),
                method: 'post',
                dataType: 'json'
            }).done(function (response) {
                if (response.result) {
                    showTopicCard(_this, response.topic);
                    setTopicData(id, response.topic);
                }
            });
        } else {
            showTopicCard(_this, topicData);
        }
    });

    // 隐藏话题卡片
    $(document).onOnce('mouseleave', '.dc-show-topic-card', function () {
        var _this = $(this);

        setTimeout(function () {
            if (!$(".popover:hover").length) {
                $(_this).popover("destroy");
            }
        }, 200);
    });

    // 关注话题
    $(document).onOnce('click', '.dc-topic-follow-wap', function () {
        var topicId = $(this).data('id');
        var followed = $(this).hasClass('followed');
        var _this = $(this);
        var $count = _this.find('.followers-count');
        var url = urlFor('topic.follow', {uid: topicId});

        if (!g.signin) {
            window.location = urlFor('account.signin');
            return;
        }

        $.ajax({
            url: url,
            method: 'post',
            dataType: 'json'
        }).done(function (response) {
            if (response.result) {
                if (response.followed) {
                    if (!_this.hasClass('followed')) {
                        _this.addClass('followed').addClass('btn-default');
                        if (_this.hasClass('dark')) {
                            _this.removeClass('btn-dark');
                        } else {
                            _this.removeClass('btn-light');
                        }
                    }
                } else {
                    _this.removeClass('followed').removeClass('btn-default');

                    if (_this.hasClass('dark')) {
                        _this.addClass('btn-dark');
                    } else {
                        _this.addClass('btn-light');
                    }
                }

                setTopicData(topicId, {
                    'followed': response.followed,
                    'followers_count': response.followers_count
                });
                $count.text(response.followers_count);
            }
        });
    });

    /**
     * 关闭提问框
     */
    function closeAskQuestionBg() {
        $askQuestionBg.hide().removeClass('open');
        $askQuestionWap.addClass('first').removeClass('second');
        $questionInput.val('');
        $similarQuestions.empty().hide();
        $secondForm.find('.topics').empty();
        $questionHeader.removeClass('edit');

        if (descEditor !== null) {
            descEditor.destroy();
        }
    }

    var timerForUserCard = null;

    /**
     * 显示用户卡片
     * @param $element
     * @param userData
     */
    function showUserCard($element, userData) {
        clearTimeout(timerForUserCard);

        $element.popover({
            content: function () {
                if (typeof g.userCardTemplate === 'undefined') {
                    g.userCardTemplate = $('#user-card-template').html();
                }

                return nunjucks.renderString(g.userCardTemplate, userData);
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
            $element.popover('destroy');
        });
    }

    var timerForTopicCard = null;

    /**
     * 显示话题卡片
     * @param $element
     * @param topicData
     */
    function showTopicCard($element, topicData) {
        clearTimeout(timerForTopicCard);

        $element.popover({
            content: function () {
                if (typeof g.topicCardTemplate === 'undefined') {
                    g.topicCardTemplate = $('#topic-card-template').html();
                }

                return nunjucks.renderString(g.topicCardTemplate, topicData);
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
