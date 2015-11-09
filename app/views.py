from app import app
from flask import render_template, request
import json
import os


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        apps = request.form.getlist('appname')
        gemname = request.form.get('gemname')
        gems = {}
        flag = 0
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        for app in apps:
            appname = app + "_debian_status.json"
            filepath = os.path.join(SITE_ROOT, "static", appname)
            inputfile = open(filepath)
            filecontent = inputfile.read()
            inputfile.close()
            deps = json.loads(filecontent)
            gem = [x for x in deps if x['name'] == gemname]
            if gem:
                flag = 1
            gems[app] = gem
        return render_template('index.html',
                               gemname=gemname,
                               gemlist=gems,
                               flag=flag)
