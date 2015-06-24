# coding: utf-8
from fabric.api import local, run, env, cd, prefix, shell_env
from config import load_config

config = load_config()
host_string = config.HOST_STRING


def deploy():
    """部署"""
    # 编译并上传静态文件
    env.host_string = "localhost"
    with cd('/var/www/dianchang'):
        with prefix('source venv/bin/activate'):
            local('python manage.py build')
            local('python manage.py upload')
    # 远程部署
    env.host_string = config.HOST_STRING
    with cd('/var/www/dianchang'):
        with shell_env(MODE='PRODUCTION'):
            run('git reset --hard HEAD')
            run('git pull')
            with prefix('source venv/bin/activate'):
                run('pip install -r requirements.txt')
                run('python manage.py db upgrade')
                run('python manage.py build')
            run('supervisorctl restart dianchang')


def restart():
    """重启"""
    env.host_string = config.HOST_STRING
    run('supervisorctl restart dianchang')
