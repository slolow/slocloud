# slocloud
my own cloud

**Demonstration video** on [Youtube](https://youtu.be/oixHn4sj0GY)

**Install in pipenv:**

  needed:

   - python3, pip, pipx, pipenv, git

    run app from terminal:
      commands:
     1. git clone https://github.com/slolow/slocloud.git
     2. cd slocloud
     3. set environment variables:
        - BASEDIR (your root directory where you want to upload files)
        - [SECRET_KEY](https://flask.palletsprojects.com/en/1.1.x/config/) of flask app 
        - USERNAME
        - PASSWORD (USERNAME and PASSWORD will be the credentials to login to your cloud)
     5. pipenv install -r requirements.txt --> Pipfile and Pipfile.lock should be created
     6. pipenv shell
     7. flask run
