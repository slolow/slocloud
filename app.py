# -*- coding: utf-8 -*-
"""
    :author: Grey Li <withlihui@gmail.com>, Laszlo Starost
    :copyright: (c) 2017 by Grey Li.
    :license: MIT, see LICENSE for more details.
"""
import os

from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_dropzone import Dropzone
from flask_wtf.csrf import CSRFProtect, CSRFError


if not os.getenv('BASEDIR'):
    raise RuntimeError('BASEDIR is not set as environment variable.')
if not os.getenv('SECRET_KEY'):
    raise RuntimeError('SECRET_KEY is not set as environment variable.')
basedir = os.getenv('BASEDIR')

app = Flask(__name__)

app.config.update(
    # Flask-Dropzone config:
    SECRET_KEY=os.getenv('SECRET_KEY'),  # the secret key used to generate CSRF token
    DROPZONE_ALLOWED_FILE_CUSTOM=True,
    DROPZONE_ALLOWED_FILE_TYPE='image/*, .txt, .pdf, .docx, .html, .py',
    DROPZONE_MAX_FILE_SIZE=3,
    DROPZONE_MAX_FILES=30,
    DROPZONE_PARALLEL_UPLOADS=3,  # set parallel amount
    DROPZONE_UPLOAD_MULTIPLE=True,  # enable upload multiple
    DROPZONE_ENABLE_CSRF=True,  # enable CSRF protection
    DROPZONE_REDIRECT_VIEW='completed'
)

dropzone = Dropzone(app)
csrf = CSRFProtect(app)  # initialize CSRFProtect


def get_sub_dir_and_files(path):
    sub_dir_and_files = {}
    sub_dir_and_files['sub_dir'] = []
    sub_dir_and_files['files'] = []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                sub_dir_and_files['files'].append(entry.name)
            else:
                sub_dir_and_files['sub_dir'].append(entry.name)
    return sub_dir_and_files


@app.errorhandler(404)
def page_not_found(e):
    return make_response(render_template('404.html'), 404)


@app.errorhandler(CSRFError)
def csrf_error(e):
    return e.description, 400


# can be used to check if user is loged in but better check this out:
#https://flask-login.readthedocs.io/en/latest/ with @login_required
#@app.before_request()
#def check_log_in():
#    return "correct password"



@app.route('/')
@app.route('/index')
@app.route('/home')
def log_in():
    return "Hey"


@app.route('/media')
def show_main_directory():
    sub_dir_and_files = get_sub_dir_and_files(basedir)
    return render_template('media.html', sub_directories=sub_dir_and_files['sub_dir'], files=sub_dir_and_files['files'], relative_path='')
        

@app.route('/media/<path:path>')
def show_directory(path):
    """Shows current directory structur (sub directories and files) and sets the temp_path in global space"""
    if os.path.exists(os.path.join(basedir, path)):
        global temp_path
        temp_path = os.path.join(basedir, path)
        sub_dir_and_files = get_sub_dir_and_files(temp_path)
        return render_template('media.html', sub_directories=sub_dir_and_files['sub_dir'], files=sub_dir_and_files['files'], relative_path=path + '/')
    return make_response(render_template('400.html', path=os.path.join(basedir, path)), 400)


@app.route('/media/new-folder')
def render_new_folder_form():
    return render_template('folderform.html')


@app.route('/create-new-folder', methods = ['POST'])
def create_new_folder():
    folder = request.form.get('folder_name')
    path = os.path.join(temp_path, folder)
    os.mkdir(path)
    rel_path = os.path.relpath(path, start=basedir)
    return redirect(url_for('show_directory', path=rel_path))
#    try:
#        os.mkdir(path)
#    except OSError:
#        return make_response(render_template('400.html', path=path, 400)
#    else:
#        return redirect(url_for('show_directory', path))
    


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    """upload files in temp_path"""
    if request.method == 'POST':
        for key, f in request.files.items():
            if key.startswith('file'):
                f.save(os.path.join(temp_path, f.filename))
    return render_template('upload.html')


@app.route('/completed')
def completed():
    return render_template('complete.html', path=temp_path)