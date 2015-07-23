(function () {
    // Add csrf token header for Ajax request
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", g.csrfToken);
            }
        }
    });

    // Find out params in routing rules
    var pattern = new RegExp("<[^:]*:?([^>]+)>", "g");
    var result = null;

    $.each(g.rules, function (endpoint, rules) {
        $.each(rules, function (index, rule) {
            rule.params = [];
            while ((result = pattern.exec(rule.rule)) !== null) {
                rule.params.push(result[1]);
            }
        });
    });

    /**
     * Generate url for the endpoint.
     * urlFor(endpoint [, parameters] [, external])
     * @param endpoint
     * @param parameters
     * @param external
     * @returns url for the endpoint.
     */
    function urlFor(endpoint, parameters, external) {
        var url = null,
            params = [],
            maxMatchDegree = 0.0,
            keys;

        if ($.type(parameters) === "boolean") {
            external = parameters
        }

        parameters = ($.type(parameters) !== 'undefined') ? parameters : {};
        external = ($.type(external) !== 'undefined') ? external : false;

        if (g.rules[endpoint] === undefined) {
            throw new Error("Uncorrect endpoint in " + "urlFor(\"" + endpoint + "\", " +
                JSON.stringify(parameters) + ")");
        }

        keys = $.map(parameters, function (value, key) {
            return key;
        });

        // Find the first matched rule among rules in this endpoint.
        $.each(g.rules[endpoint], function (index, rule) {
            var match = true,
                currentMatchDegree = 0.0;

            $.each(rule.params, function (index, param) {
                if ($.inArray(param, keys) === -1) {
                    match = false;
                    return false;
                }
            });

            if (match) {
                currentMatchDegree = parseFloat(rule.params.length) / keys.length;
                if (currentMatchDegree > maxMatchDegree || url === null) {
                    maxMatchDegree = currentMatchDegree;
                    url = rule.rule;
                    params = rule.params;
                }
            }
        });

        if (url) {
            $.each(keys, function (index, key) {
                // Build in params
                if ($.inArray(key, params) > -1) {
                    url = url.replace(new RegExp("<[^:]*:?" + key + ">"), parameters[key]);
                } else {
                    // Query string params
                    if (url.indexOf("?") === -1) {
                        url += "?";
                    }
                    if (!endsWith(url, '?')) {
                        url += "&";
                    }
                    url += key + "=" + parameters[key];
                }
            });
        } else {
            throw new Error("Uncorrect parameters in " + "urlFor(\"" + endpoint + "\", " +
                JSON.stringify(parameters) + ")");
        }

        if (external) {
            url = g.domain + url
        }

        return url;
    }

    /**
     * Register context into global variable g.
     * @param context
     */
    function registerContext(context) {
        if (typeof g === 'undefined') {
            throw new Error("Global variable g is not defined.");
        }

        $.each(context, function (key, value) {
            if (g.hasOwnProperty(key)) {
                throw new Error("The key '" + key + "' already exists in the global variable g.");
            }
            g[key] = value;
        });
    }

    // Unbind events before bind.
    $.fn.onOnce = function (events, selector, handle) {
        if ($.isFunction(selector)) {
            handle = selector;
            this.off(events).on(events, handle);
        } else {
            this.off(events, selector).on(events, selector, handle);
        }
        return this;
    };

    /**
     * 显示tip
     * @param $element
     * @param tip
     */
    function showTip($element, tip) {
        var placement;

        if (typeof $element.attr('data-placement') === 'undefined') {
            placement = 'right'
        } else {
            placement = $element.attr('data-placement');
        }

        $element
            .attr('data-original-title', tip)
            .tooltip({
                title: tip,
                trigger: 'manual',
                placement: placement,
                container: 'body',
                template: '<div class="tooltip tooltip-white" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
            }).tooltip('show');
    }

    /**
     * 隐藏tip
     * @param $element
     */
    function hideTip($element) {
        if ($element.length === 1) {
            $element.tooltip('hide');
        } else {
            $.each($element, function () {
                $(this).tooltip('hide');
            });
        }
    }

    /**
     * Check whether str starts with prefix.
     * @param str
     * @param prefix
     * @returns {boolean}
     */
    function startsWith(str, prefix) {
        return str.slice(0, prefix.length) === prefix;
    }

    /**
     * Check whether str ends with suffix.
     * @param str
     * @param su
     * 从url中以json的形式获取params
     * @returns {}ffix
     * @returns {boolean}
     */
    function endsWith(str, suffix) {
        return str.slice(-suffix.length) === suffix;
    }

    /**
     * 禁止窗口滚动
     */
    function disableScroll() {
        $('body').addClass('modal-open');
    }

    /**
     * 使能窗口滚动
     */
    function enableScroll() {
        $('body').removeClass('modal-open');
    }

    /**
     */
    function getJsonFromUrl() {
        var query = location.search.substr(1);
        var result = {};
        query.split("&").forEach(function (part) {
            var item = part.split("=");
            result[item[0]] = decodeURIComponent(item[1]);
        });
        return result;
    }

    /**
     * 初始化 topic 自动完成
     * @param {Object} options
     */
    $.fn.initTopicTypeahead = function (options) {
        var $topicInput = this;
        var params = options.params;
        var block = (typeof options.block === 'undefined') ? false : options.block;
        var small = (typeof options.small === 'undefined') ? false : options.small;
        var callback = options.callback;
        var timerForTopicTypeahead = null;
        var inputMarginRight = parseInt($topicInput.css("margin-right"));
        var $twitterTypeahead;

        $topicInput.typeahead({
            hint: true,
            highlight: true,
            minLength: 1
        }, {
            displayKey: 'name',
            source: function (q, cb) {
                var data = {
                    q: q,
                    create: true
                };

                if (typeof params === 'object') {
                    $.extend(data, params);
                }

                if (timerForTopicTypeahead) {
                    clearTimeout(timerForTopicTypeahead);
                }

                timerForTopicTypeahead = setTimeout(function () {
                    $.ajax({
                        url: urlFor('topic.query'),
                        method: 'post',
                        dataType: 'json',
                        data: data
                    }).done(function (matchs) {
                        var event = $.Event('keydown');

                        if (matchs.length !== 0) {
                            cb(matchs);
                            event.which = event.keyCode = 40;
                            $topicInput.trigger(event);
                        } else {
                            $topicInput.typeahead('close');
                        }
                    });
                }, 300);
            },
            templates: {
                'suggestion': function (data) {
                    if (typeof data.create === 'undefined') {
                        return "<p class='typeahead-suggestion typeahead-topic-suggestion " + (small ? 'sm' : '') + "' data-name='" + data.name + "'><img src='" + data.avatar_url + "' class='topic-avatar img-rounded'>" + data.name + "</p>";
                    } else {
                        return "<p class='typeahead-suggestion typeahead-topic-suggestion " + (small ? 'sm' : '') + "' data-name='" + data.name + "'><span class='color'>+ 添加：</span>" + data.name + "</p>";
                    }
                }
            }
        });

        $topicInput.on('typeahead:selected', function (e, topic) {
            callback(e, topic);
            $topicInput.typeahead('val', '');
        });

        $topicInput.css('verticalAlign', 'middle');
        $twitterTypeahead = $topicInput.parents('.twitter-typeahead');
        $topicInput.css('marginRight', 0);
        $twitterTypeahead.css('marginRight', inputMarginRight);
        if (block) {
            $twitterTypeahead.css('display', 'block');
        }
    };

    /**
     * 获取用户数据
     * @param id
     * @returns {Object}
     */
    function getUserData(id) {
        id = parseInt(id);

        if (typeof g.users === 'undefined') {
            g.users = {};
        }
        return g.users[id];
    }

    /**
     * 设置用户数据
     * @param id
     * @param data
     */
    function setUserData(id, data) {
        id = parseInt(id);

        var currentData = getUserData(id);

        if (typeof currentData === 'undefined') {
            g.users[id] = {};
        }

        $.extend(g.users[id], data);
    }

    /**
     * 获取话题数据
     * @param id
     * @returns {Object}
     */
    function getTopicData(id) {
        id = parseInt(id);

        if (typeof g.topics === 'undefined') {
            g.topics = {};
        }
        return g.topics[id];
    }

    /**
     * 设置话题数据
     * @param id
     * @param data
     */
    function setTopicData(id, data) {
        id = parseInt(id);

        var currentData = getTopicData(id);

        if (typeof currentData === 'undefined') {
            g.topics[id] = {};
        }

        $.extend(g.topics[id], data);
    }

    window.showTip = showTip;
    window.hideTip = hideTip;
    window.urlFor = urlFor;
    window.registerContext = registerContext;
    window.startsWith = startsWith;
    window.endsWith = endsWith;
    window.disableScroll = disableScroll;
    window.enableScroll = enableScroll;
    window.getJsonFromUrl = getJsonFromUrl;
    window.getUserData = getUserData;
    window.setUserData = setUserData;
    window.getTopicData = getTopicData;
    window.setTopicData = setTopicData;
})();
