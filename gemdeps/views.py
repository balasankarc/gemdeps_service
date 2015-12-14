import json
import os

from flask import Markup, render_template, request

from gemdeps import app


@app.route('/', methods=['GET', 'POST'])
def index():
    completedeplist = {}
    gemnames = []
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    for app in ['diaspora', 'gitlab', 'asciinema']:
        appname = app + "_debian_status.json"
        filepath = os.path.join(SITE_ROOT, "static", appname)
        inputfile = open(filepath)
        filecontent = inputfile.read()
        inputfile.close()
        deps = json.loads(filecontent)
        completedeplist[app] = deps
        gemnames += [str(x['name']) for x in deps]
    gemnames = list(set(gemnames))
    gemnames.sort()
    gemnames = Markup(gemnames)
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


@app.route('/status/<appname>')
def status(appname):
    ignore_list = ['mini_portile2', 'newrelic_rpm',
                   'newrelic-grape']
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    appfilename = appname + "_debian_status.json"
    filepath = os.path.join(SITE_ROOT, "static", appfilename)
    inputfile = open(filepath)
    filecontent = inputfile.read()
    inputfile.close()
    deps = json.loads(filecontent)
    packaged_count = 0
    unpackaged_count = 0
    itp_count = 0
    total = 0
    mismatch = 0
    final_list = []
    for i in deps:
        if i['name'] in ignore_list:
            continue
        else:
            final_list.append(i)
            if i['status'] == 'Packaged' or i['status'] == 'NEW':
                packaged_count += 1
            elif i['status'] == 'ITP':
                itp_count += 1
            else:
                unpackaged_count += 1
            if i['satisfied'] == False:
                mismatch += 1
    total = len(final_list)
    print total
    percent_complete = (packaged_count * 100) / total
    return render_template('status.html',
                           appname=appname.title(),
                           deps=final_list,
                           packaged_count=packaged_count,
                           unpackaged_count=unpackaged_count,
                           itp_count=itp_count,
                           mismatch_count=mismatch,
                           total=total,
                           percent_complete=percent_complete
                           )


@app.route('/about')
def about():
    return render_template('about.html')
