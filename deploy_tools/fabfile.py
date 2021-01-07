import random
from fabric.contrib.files import append, exists
from fabric.api import cd, env, local, run

REPO_URL = 'https://github.com/WorldWideDev/TDD-Python-Django-Course.git'
env.key_filename = ['/home/xdevx/XFiles/Deployment/t420.pem']
env.hosts = ['ec2-34-222-246-51.us-west-2.compute.amazonaws.com']

def deploy():
    site_folder = f'/home/{env.user}/sites/{env.host}'
    run(f'mkdir -p {site_folder}')
    _download_dependancies()
    with cd(site_folder):
        _get_latest_source()
        _update_virtualenv()
        _create_or_update_dotenv()
        _update_static_files()
        _update_database()
        _provision_nginx()
        _provision_gunicorn()
        _initialize_services()

def _download_dependancies():
    run('sudo apt update')
    run('sudo apt install python3 python3-venv nginx')

def _get_latest_source():
    if exists('.git'):
        run('git fetch')
    else:
        run(f'git clone {REPO_URL} .')
    current_commit = local("git log -n 1 -- format=%H", capture=True)
    run(f'git reset --hard {current_commit}')

def _update_virtualenv():
    if not exists('virtualenv/bin/pip'):
        run(f'python3 -m venv virtualenv')
    run('./virtualenv/bin/pip install -r requirements.txt')

def _create_or_update_dotenv():
    append('.env', 'DJANGO_DEBUG_FALSE=y')
    append('.env', f'SITENAME={env.host}')
    current_contents = run('cat .env')
    if 'DJANGO_SECRET_KEY' not in current_contents:
        new_secret = ''.join(random.SystemRandom().choices(
            'abcdefghijklmnopqrstuvwxyz1234567890', k=50
        ))
        append('.env', f'DJANGO_SECRET_KEY={new_secret}')

def _update_static_files():
    run('./virtualenv/bin/python manage.py collectstatic --noinput')

def _update_database():
    run(f'./virtualenv/bin/python manage.py migrate --noinput')


def _provision_nginx():
    run(f'cat ./deploy_tools/nginx.template.conf \
            | sed "s/DOMAIN/{env.host}/g" \
            | sudo tee /etc/nginx/sites-available/{env.host}')
    run(f'sudo ln -s /etc/nginx/sites-available/{env.host} \
            /etc/nginx/sites-enabled')

def _provision_gunicorn():
    run(f'cat ./deploy_tools/gunicorn-systemd.template.service \
            | sed "s/DOMAIN/{env.host}/g" \
            | sudo tee /etc/systemd/system/gunicorn-{env.host}.service')

def _initialize_services():
    run('sudo systemctl daemon-reload')
    run('sudo systemctl reload nginx')
    run(f'sudo systemctl enable gunicorn-{env.host}')
    run(f'sudo systemctl start gunicorn-{env.host}')
