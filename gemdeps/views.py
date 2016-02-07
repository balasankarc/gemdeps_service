#!/usr/bin/env python

import json
import os
import time
import glob

from flask import jsonify, Markup, render_template, request, redirect

from gemdeps import app


def list_apps():
    '''
    Returns the list of available apps by scanning for debian_status.json files
    '''
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    list_of_json = glob.glob(os.path.join(
        SITE_ROOT, 'static', '*_debian_status.json'))
    apps = {}
    for jsonfile in list_of_json:
        pos = len(jsonfile) - jsonfile[::-1].index('/')
        appfilename = jsonfile[pos:]
        appname = appfilename[:appfilename.index('_')]
        apps[appname] = jsonfile
    return apps


@app.route('/')
def index():
    '''
    Displas the home page
    '''
    gemnames = []
    available_apps = list_apps()
    if not available_apps:
        return render_template('no_files.html')
    for app in available_apps:
        filepath = available_apps[app]
        inputfile = open(filepath)
        filecontent = inputfile.read()
        inputfile.close()
        deps = json.loads(filecontent)
        gemnames += [str(x['name']) for x in deps]
    gemnames = list(set(gemnames))
    gemnames.sort()
    gemnames = Markup(gemnames)
    return render_template('index.html', gemnames=gemnames,
                           apps=available_apps)


def infobase(request):
    '''
    Returns the information about a specific gem related to specified apps.
    Used to generate HTML as well as JSON output.
    '''
    apps = request.args.getlist('appname')
    gemname = request.args.get('gemname')
    completedeplist = {}
    gemnames = []
    available_apps = list_apps()
    if not available_apps:
        return render_template('no_files.html')
    for app in available_apps:
        filepath = available_apps[app]
        inputfile = open(filepath)
        filecontent = inputfile.read()
        inputfile.close()
        deps = json.loads(filecontent)
        completedeplist[app] = deps
        gemnames += [str(x['name']) for x in deps]
    gemnames = list(set(gemnames))
    gemnames.sort()
    gemnames = Markup(gemnames)
    if not apps:
        if not gemname:
            flag = 1
            return gemnames, None, None, 1, available_apps, None
        else:
            apps = available_apps
    gems = {}
    flag = 0
    for app in apps:
        if app in available_apps:
            gem = next((x for x in completedeplist[
                       app] if x['name'] == gemname), None)
            if gem:
                flag = 1
                gems[app] = gem
    return gemnames, gemname, gems, flag, available_apps, apps


@app.route('/info')
@app.route('/info/')
def info():
    '''
    Displays the information about a specific gem related to specified apps.
    '''
    gemnames, gemname, gems, flag, available_apps, apps = infobase(request)
    if not gemname:
        flag = 1
        return render_template('info.html', gemnames=gemnames,
                               apps=available_apps, flag=flag)
    return render_template('info.html',
                           gemnames=gemnames,
                           gemname=gemname,
                           gemlist=gems,
                           flag=flag,
                           apps=available_apps)


@app.route('/api/info')
@app.route('/api/info/')
def apiinfo():
    '''
    Displays the information about a specific gem related to specified apps
    in JSON format.
    '''
    gemnames, gemname, gems, flag, available_apps, apps = infobase(request)
    if not gemname:
        return "Specify a gem"
    if not gems:
        return "No results"
    return jsonify(**gems)


def statusbase(appname):
    '''
    Returns the packaging status of specified app. Used to generate HTML as
    well as JSON output.
    '''
    apps = list_apps()
    if not apps or appname not in apps:
        return None, None, None, None, None, None, None, None, None
    ignore_list = ['mini_portile2', 'newrelic_rpm', 'newrelic-grape',
                   'rb-fsevent', 'eco', 'eco-source', 'gitlab_meta', 'cause',
                   'rdoc']
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    appfilename = appname + "_debian_status.json"
    filepath = os.path.join(SITE_ROOT, "static", appfilename)
    inputfile = open(filepath)
    filecontent = inputfile.read()
    inputfile.close()
    updated_time = time.strftime(
        "%d/%m/%Y %H:%M:%S %Z", time.gmtime(os.path.getmtime(filepath)))
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
    percent_complete = (packaged_count * 100) / total
    return final_list, packaged_count, unpackaged_count, itp_count, mismatch, \
        total, percent_complete, updated_time, apps


@app.route('/status')
@app.route('/status/')
@app.route('/status/<appname>')
@app.route('/status/<appname>/')
def status(appname=''):
    '''
    Displays the packaging status of specified app.
    '''
    if appname == '':
        appname = request.args.get('appname')
    final_list, packaged_count, unpackaged_count, itp_count, mismatch, \
        total, percent_complete, updated_time, apps = statusbase(appname)
    if not apps:
        return render_template('no_files.html')
    return render_template('status.html',
                           appname=appname.title(),
                           deps=final_list,
                           packaged_count=packaged_count,
                           unpackaged_count=unpackaged_count,
                           itp_count=itp_count,
                           mismatch_count=mismatch,
                           total=total,
                           percent_complete=percent_complete,
                           updated_time=updated_time,
                           apps=apps
                           )


@app.route('/api/status')
@app.route('/api/status/')
def apistatus():
    '''
    Displays the packaging status of specified app in JSON format.
    '''
    appname = request.args.get('appname')
    if not appname:
        return "Specify an app"
    final_list, packaged_count, unpackaged_count, itp_count, mismatch, \
        total, percent_complete, updated_time, apps = statusbase(appname)
    if not apps:
        return "No files found to generate statistics. Run gemdeps again."
    json_out = {}
    for item in final_list:
        json_out[item['name']] = item
    return jsonify(json_out)


@app.route('/api')
@app.route('/api/')
def api():
    '''
    Displays the information page about API.
    '''
    apps = list_apps()
    return render_template('api.html', apps=apps)


@app.route('/about')
@app.route('/about/')
def about():
    '''
    Displays the about page.
    '''
    apps = list_apps()
    return render_template('about.html', apps=apps)


def compare_lists(first_list, second_list):
    '''
    Returns the elements belonging to both lists.
    '''
    first_list_names = [x['name'] for x in first_list]
    result = []
    for item in second_list:
        if item['name'] in first_list_names:
            result.append(item)
    return result


@app.route('/compare')
@app.route('/compare/')
def compare():
    '''
    Displays the comparison between version dependencies of gems that are
    common to specified apps.
    '''
    available_apps = list_apps()
    apps = request.args.getlist('appname')
    if len(apps) < 2:
        if len(apps) == 1:
            return redirect("/status/%s" % apps[0])
        else:
            return redirect("/")
    result = []
    app_dep_list = []
    for appname in apps:
        if appname not in available_apps:
            apps.remove(appname)
            continue
        else:
            SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
            appfilename = appname + "_debian_status.json"
            filepath = os.path.join(SITE_ROOT, "static", appfilename)
            inputfile = open(filepath)
            filecontent = inputfile.read()
            inputfile.close()
            deps = json.loads(filecontent)
            app_dep_list.append(deps)
    first_list = app_dep_list[0]
    second_list = app_dep_list[1]
    counter = 1
    while counter < len(app_dep_list):
        counter = counter + 1
        result = compare_lists(first_list, second_list)
        first_list = result
        if counter < len(app_dep_list):
            second_list = app_dep_list[counter]
    final = {}
    for i in result:
        current = {}
        counter = 0
        while counter < len(app_dep_list):
            appname = apps[counter]
            for item in app_dep_list[counter]:
                if item['name'] == i['name']:
                    current[appname] = item
            counter = counter + 1
        final[i['name']] = current
    color = {}
    for gem in final:
        keys = final[gem].keys()
        current_color = final[gem][keys[0]]['color']
        if current_color != 'green':
            color[gem] = 'red'
        else:
            for app in final[gem]:
                if current_color != final[gem][app]['color']:
                    color[gem] = 'violet'
                    break
                color[gem] = current_color
    return render_template('compare.html',
                           apps=available_apps,
                           selected_apps=apps,
                           final=final,
                           color=color
                           )
