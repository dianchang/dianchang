// 初始化回答富文本编辑器
var answerEditor = new Simditor({
    textarea: $("textarea[name='wiki']"),
    toolbar: ['bold', 'italic', 'underline', 'ol', 'ul', 'blockquote', 'code', 'link', 'image', 'markdown'],
    upload: {
        url: urlFor('site.upload_image'),
        fileKey: 'file',
        connectionCount: 1,
        leaveConfirm: '正在上传文件，如果离开上传会自动取消'
    }
});
