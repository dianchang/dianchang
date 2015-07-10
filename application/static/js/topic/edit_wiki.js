var $mainWap = $('#main-wap');

// 初始化wiki富文本编辑框
var wikiEditor = new Simditor({
    textarea: $("textarea[name='wiki']"),
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

// 当窗口往下滚动时，按钮固定
$(window).scroll(function () {
    if ($(window).scrollTop() >= 124) {
        $mainWap.find('.btns-wap').addClass('stick');
    } else {
        $mainWap.find('.btns-wap').removeClass('stick');
    }
});

// 浏览
$mainWap.on('click', '.btn-preview', function () {
    var wiki = wikiEditor.getValue();

    $('.preview-wap').fadeIn('fast').find('.wiki').html(wiki);
});

// 退出浏览
$mainWap.on('click', '.btn-close-preview', function () {
    $('.preview-wap').fadeOut('fast');
});
