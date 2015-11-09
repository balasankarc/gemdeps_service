from gemdeps import app
from flask import render_template, request, Markup
import json
import os


@app.route('/', methods=['GET', 'POST'])
def index():
    completedeplist = {}
    gemnames = "["
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    for app in ['diaspora', 'gitlab', 'asciinema']:
        appname = app + "_debian_status.json"
        filepath = os.path.join(SITE_ROOT, "static", appname)
        inputfile = open(filepath)
        filecontent = inputfile.read()
        inputfile.close()
        deps = json.loads(filecontent)
        completedeplist[app] = deps
        gemnames += ", ".join([str('"' + x['name'] + '"') for x in deps])
        gemnames += ", "
    gemnames += "]"
    gemnames = Markup(gemnames)
    print completedeplist
    if request.method == 'GET':
        return render_template('index.html', gemnames=gemnames)
    else:
        apps = request.form.getlist('appname')
        gemname = request.form.get('gemname')
        gems = {}
        flag = 0
        for app in apps:
            gem = [x for x in completedeplist[app] if x['name'] == gemname]
            if gem:
                flag = 1
            gems[app] = gem
        return render_template('index.html',
                               gemnames=gemnames,
                               gemname=gemname,
                               gemlist=gems,
                               flag=flag)
