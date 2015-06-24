fis.config.set('project.include', ['templates/**', 'static/**']);
fis.config.set('project.exclude', ['static/bower_components/**', 'static/**.less']);
fis.config.set('modules.postpackager', 'simple');
fis.config.set('pack', {
    '/pkg/lib.js': [
        'static/js/libs/*.js',
        'static/js/init.js'
    ],
    '/pkg/lib.css': [
        'static/css/libs/*.css'
    ],
    '/pkg/layout.css': [
        'static/css/bootstrap.theme.css',
        'static/css/common.css',
        'static/css/macros/*.css',
        'static/css/layout.css'
    ]
});
