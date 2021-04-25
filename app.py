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

from flask import Flask, render_template, request, make_response, redirect, url_for, send_file, flash
from flask_dropzone import Dropzone
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.urls import url_parse


if not os.getenv('BASEDIR'):
    raise RuntimeError('BASEDIR is not set as environment variable.')
if not os.getenv('SECRET_KEY'):
    raise RuntimeError('SECRET_KEY is not set as environment variable.')
if not os.getenv('USERNAME'):
    raise RuntimeError('USERNAME is not set as environment variable.')
if not os.getenv('PASSWORD'):
    raise RuntimeError('PASSWORD is not set as environment variable.')
basedir = os.getenv('BASEDIR')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
authenticated_user = False


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


@app.context_processor
def inject_authentication():
    return dict(authenticated_user=authenticated_user)


@app.before_request
def check_login():
    if authenticated_user or request.path == url_for('login'):
        return None
    flash('You need to be login to get access')
    return redirect(url_for('login', next=request.endpoint))


@app.route('/')
@app.route('/index')
@app.route('/home')
def show_main_directory():
    sub_dir_and_files = get_sub_dir_and_files(basedir)
    return render_template('media.html', sub_directories=sub_dir_and_files['sub_dir'], files=sub_dir_and_files['files'], path=basedir)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global authenticated_user
    if authenticated_user:
        return redirect(url_for('show_main_directory'))
    if request.method == 'POST':
        if not username == request.form.get('username') or not password == request.form.get('password'):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        authenticated_user = True
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':    # An attacker could insert a URL to a malicious site in the next argument, 
            next_page = url_for('show_main_directory')            # so the application only redirects when the URL is relative,
        return redirect(next_page)                                # which ensures that the redirect stays within the same site as the application.
    return render_template('login.html')                          # To determine if the URL is relative or absolute, I parse it with Werkzeug's url_parse() 
                                                                  # function and then check if the netloc component is set or not.
                                                                  
@app.route('/logout')
def logout():
    global authenticated_user
    authenticated_user = False
    return redirect(url_for('login'))


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


@app.route('/new-folder/<path:path>')
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
