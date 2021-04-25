# -*- coding: utf-8 -*-
"""
    :author: Grey Li <withlihui@gmail.com>, Laszlo Starost
    :copyright: (c) 2017 by Grey Li.
    :license: MIT, see LICENSE for more details.
"""
import os
import shutil
import ntpath
import urllib

from flask import Flask, render_template, request, make_response, redirect, url_for, send_file
from flask_dropzone import Dropzone
from flask_wtf.csrf import CSRFProtect, CSRFError


if not os.getenv('BASEDIR'):
    raise RuntimeError('BASEDIR is not set as environment variable.')
if not os.getenv('SECRET_KEY'):
    raise RuntimeError('SECRET_KEY is not set as environment variable.')
basedir = os.getenv('BASEDIR')
print()
print('basedir')
print(basedir)
print()

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
)

dropzone = Dropzone(app)
csrf = CSRFProtect(app)  # initialize CSRFProtect


def get_sub_dir_and_files(path):
    sub_dir_and_files = {}
    sub_dir_and_files['sub_dir'] = []
    sub_dir_and_files['files'] = []
    with os.scandir(path) as it:
        for entry in it:
            name = os.sep + entry.name
            if entry.is_file():
                sub_dir_and_files['files'].append(name)
            else:
                sub_dir_and_files['sub_dir'].append(name)
    return sub_dir_and_files


def url_to_path(path):
    """unquotes url and adds the directory seperator of operating system at the beggining of path"""
    path = urllib.parse.unquote(path)   # unquote special caracters from url like %20 --> white space
    return os.sep + path


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
@app.route('/media/')
def show_main_directory():
    print()
    print('show_main')
    print(basedir)
    print()
    sub_dir_and_files = get_sub_dir_and_files(basedir)
    return render_template('media.html', sub_directories=sub_dir_and_files['sub_dir'], files=sub_dir_and_files['files'], path=basedir)
        

@app.route('/media/<path:path>')
def show_directory(path):
    """Shows current directory structur (sub directories and files)"""
    path = url_to_path(path)
    if os.path.exists(path):
        if os.path.isfile(path):
            return send_file(path, attachment_filename=ntpath.basename(path))   # ntpath.basename(path) returns the file name
        sub_dir_and_files = get_sub_dir_and_files(path)
        return render_template('media.html', sub_directories=sub_dir_and_files['sub_dir'], files=sub_dir_and_files['files'], path=path)
    return make_response(render_template('400.html', path=path), 400)


@app.route('/media/new-folder/<path:path>')
def render_new_folder_form(path):
    return render_template('folderform.html', path=path)


@app.route('/create-new-folder/<path:path>', methods = ['POST'])
def create_new_folder(path):
    path = url_to_path(path)
    folder = request.form.get('folder_name')
    new_path = os.path.join(path, folder)
    os.mkdir(new_path)
    return redirect(url_for('show_directory', path=path))
#    try:
#        os.mkdir(path)
#    except OSError:
#        return make_response(render_template('400.html', path=path, 400)
#    else:
#        return redirect(url_for('show_directory', path))


@app.route('/confirm-delete-folder/<path:path>')
def confirm_delete_folder(path):
    parent_path = os.path.dirname(path)
    return render_template('confirmdelete.html', path=path, parent_path=parent_path)


@app.route('/delete-folder/<path:path>')
def delete_folder(path):
    path = url_to_path(path)
    if os.path.isfile(path):
        os.remove(path)
    else:
        shutil.rmtree(path)
    parent_path = os.path.dirname(path)
    return redirect(url_for('show_directory', path=parent_path))
    

@app.route('/upload/<path:path>', methods=['POST', 'GET'])
def upload(path):
    """upload files in global_temp_path"""
    path = url_to_path(path)
    if os.path.exists(path):
        if request.method == 'POST':
            for key, f in request.files.items():
                if key.startswith('file'):
                    f.save(os.path.join(path, f.filename))
        return render_template('upload.html', path=path)
    return make_response(render_template('400.html', path=path), 400)


@app.route('/completed/<path:path>')
def completed(path):
    path = url_to_path(path)
    return render_template('complete.html', path=path)
