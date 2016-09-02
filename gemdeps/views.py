#!/usr/bin/env python

import glob
import json
import os
import re
import time
from distutils.version import LooseVersion

from flask import Markup, jsonify, redirect, render_template, request
from graphviz import Digraph

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
        gemnames += [str(x['name']) for y, x in deps.items()]
    gemnames = sorted(set(gemnames))
    gemnames = Markup(gemnames)
    return render_template('index.html', gemnames=gemnames,
                           apps=available_apps)


def infobase(request, gemname=None):
    '''
    Returns the information about a specific gem related to specified apps.
    Used to generate HTML as well as JSON output.
    '''
    apps = request.args.getlist('appname')
    if not gemname:
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
        gemnames += [str(x['name']) for t, x in deps.items()]
    gemnames = sorted(set(gemnames))
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
            gem = next((x for t, x in completedeplist[
                       app].items() if x['name'] == gemname), None)
            if gem:
                flag = 1
                gems[app] = gem
    return gemnames, gemname, gems, flag, available_apps, apps


@app.route('/info')
@app.route('/info/')
@app.route('/info/<gemname>')
@app.route('/info/<gemname>/')
def info(gemname=''):
    '''
    Displays the information about a specific gem related to specified apps.
    '''
    if gemname == '':
        gemnames, gemname, gems, flag, available_apps, apps = infobase(request)
    else:
        gemnames, gemname, gems, flag, available_apps, apps = infobase(
            request, gemname)
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
    ignore_list = ['fog-google', 'mini_portile2', 'newrelic_rpm',
                   'newrelic-grape', 'rb-fsevent', 'eco', 'eco-source',
                   'gitlab_meta', 'cause', 'rdoc', 'yard']
    try:

        listed_gems = []
        l = []
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        gemlockfilename = appname + "_Gemfile.lock"
        filepath = os.path.join(SITE_ROOT, "static", gemlockfilename)
        gemfile_lock = open(filepath).readlines()
        for line in gemfile_lock:
            listed_gems.append(filter(None, line).strip().split(' ')[0])
        l = [gem for gem in listed_gems if not gem.isupper()]
        l = set(l)
    except Exception as e:
        print e
        pass

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
    for x, i in deps.items():
        if i['name'] in ignore_list:
            continue
        elif i['name'] not in l:
            print "Ignored ", i['name']
            continue
        else:
            final_list.append(i)
            if i['status'] == 'Packaged' or i['status'] == 'NEW':
                packaged_count += 1
            elif i['status'] == 'ITP':
                itp_count += 1
            else:
                unpackaged_count += 1
            if i['satisfied'] is False:
                mismatch += 1
    total = len(final_list)
    percent_complete = (packaged_count * 100) / total
    return final_list, packaged_count, unpackaged_count, itp_count, mismatch, \
        total, percent_complete, updated_time, apps


def get_operator(requirement):
    '''
    Splits the operator and version from a requirement string.
    '''
    if requirement == '':
        return '>=', '0'
    m = re.search("\d", requirement)
    pos = m.start()
    if pos == 0:
        return '=', requirement
    check = requirement[:pos].strip()
    ver = requirement[pos:]
    return check, ver


def get_incomplete(final_list):
    unpackaged = ""
    patch = ""
    minor_stable = ""
    minor_devel = ""
    major = ""
    already_newer = ""
    for item in final_list:
        if item['satisfied'] is False:
            if item['version'] == 'NA':
                unpackaged += " - [ ] " + item['name'] + " | " +\
                    item['requirement'] + "<br />"
            else:
                check, requirement_raw = get_operator(item['requirement'])
                required = LooseVersion(requirement_raw)
                version_raw = item['version'][:item['version'].index('-')]
                if ":" in version_raw:
                    epoch_pos = version_raw.index(":")
                    version_raw = version_raw[epoch_pos + 1:]
                version = LooseVersion(version_raw)
                if len(required.version) == len(version.version):
                    if len(required.version) == 3:
                        if required.version[0] > version.version[0]:
                            major += " - [ ] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                        elif required.version[0] < version.version[0]:
                            already_newer += " - [x] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                        elif required.version[1] != version.version[1]:
                            if required.version[1] < version.version[1]:
                                already_newer += " - [x] " + item['name'] + " | " +\
                                    item['requirement'] + " | " + version_raw +\
                                    "<br />"
                            elif required.version[0] > 0:
                                minor_stable += " - [ ] " + item['name'] + " | " +\
                                    item['requirement'] + " | " + version_raw +\
                                    "<br />"
                            else:
                                minor_devel += " - [ ] " + item['name'] + " | " +\
                                    item['requirement'] + " | " + version_raw +\
                                    "<br />"
                        else:
                            if required.version[2] < version.version[2]:
                                already_newer += " - [x] " + item['name'] + " | " +\
                                    item['requirement'] + " | " + version_raw +\
                                    "<br />"
                            patch += " - [ ] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                    elif len(required.version) == 2:
                        if required.version[0] > version.version[0]:
                            major += " - [ ] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                        elif required.version[0] < version.version[0]:
                            already_newer += " - [x] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                        elif required.version[1] != version.version[1]:
                            if required.version[1] < version.version[1]:
                                already_newer += " - [x] " + item['name'] + " | " +\
                                    item['requirement'] + " | " + version_raw +\
                                    "<br />"
                            elif required.version[0] > 0:
                                minor_stable += " - [ ] " + item['name'] + " | " +\
                                    item['requirement'] + " | " + version_raw +\
                                    "<br />"
                            else:
                                minor_devel += " - [ ] " + item['name'] + " | " +\
                                    item['requirement'] + " | " + version_raw +\
                                    "<br />"
                    elif len(required.version) == 1:
                        if required.version[0] > version.version[0]:
                            major += " - [ ] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                        elif required.version[0] < version.version[0]:
                            already_newer += " - [x] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                else:
                    min_length = min(len(required.version),
                                     len(version.version))
                    mismatch = 0
                    for position in range(min_length):
                        if required.version[position] != \
                                version.version[position]:
                            mismatch = position
                            break
                    if mismatch == 0:
                        major += " - [ ] " + item['name'] + " | " +\
                            item['requirement'] + " | " + version_raw +\
                            "<br />"
                    elif mismatch == 1:
                        if required.version[0] > 0:
                            minor_stable += " - [ ] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                        else:
                            minor_devel += " - [ ] " + item['name'] + " | " +\
                                item['requirement'] + " | " + version_raw +\
                                "<br />"
                    elif mismatch == 2:
                        patch += " - [ ] " + item['name'] + " | " +\
                            item['requirement'] + " | " + version_raw +\
                            "<br />"
    output = ""
    if unpackaged != "":
        unpackaged = "**Unpackaged gems** <br />" + unpackaged
        output += "<br />" + unpackaged
    if patch != "":
        patch = "**Patch updates** <br />" + patch
        output += "<br />" + patch
    if minor_stable != "":
        minor_stable = "**Minor updates (Stable)** <br />" + minor_stable
        output += "<br />" + minor_stable
    if minor_devel != "":
        minor_devel = "**Minor updates (Development)** <br />" + minor_devel
        output += "<br />" + minor_devel
    if major != "":
        major = "**Major updates** <br />" + major
        output += "<br />" + major
    if already_newer != "":
        already_newer = "**Already Newer** <br />" + already_newer
        output += "<br />" + already_newer

    return output


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
    if request.args.get('type'):
        if request.args.get('type') == 'incompletemarkdown':
            output = get_incomplete(final_list)
            return output
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
    result = {}
    for t, item in second_list.items():
        if t in first_list:
            result[t] = item
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
            current[appname] = app_dep_list[counter][i]
            counter = counter + 1
        final[i] = current
    color = {}
    gem_status = {}
    for gem in final:
        gem_status[gem] = None
        flag = False
        for app in final[gem]:
            if gem_status[gem] is None:
                gem_status[gem] = final[gem][app]['satisfied']
            else:
                if gem_status[gem] != final[gem][app]['satisfied']:
                    flag = True
                gem_status[gem] = gem_status[
                    gem] and final[gem][app]['satisfied']
        if gem_status[gem]:
            color[gem] = 'green'
        else:
            if flag:
                color[gem] = 'violet'
            else:
                color[gem] = 'red'
    return render_template('compare.html',
                           apps=available_apps,
                           selected_apps=apps,
                           final=final,
                           color=color
                           )


@app.route('/family')
@app.route('/family/')
@app.route('/family/<gemname>')
@app.route('/family/<gemname>/')
def family(gemname=''):
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    appname = request.args.get('appname')

    svgpath = os.path.join(SITE_ROOT, "static",
                           "%s_%s.dot" % (gemname, appname))
    available_apps = list_apps()
    if appname not in available_apps:
        return render_template('no_files.html')

    filepath = available_apps[appname]
    inputfile = open(filepath)
    filecontent = inputfile.read()
    inputfile.close()
    deps = json.loads(filecontent)
    json_out = {}
    for x, item in deps.items():
        json_out[x] = item

    filepath = os.path.join(SITE_ROOT, "static", "%s.dot" % appname)
    if os.path.isfile(svgpath):
        os.remove(svgpath)
    if os.path.isfile(svgpath + '.svg'):
        os.remove(svgpath + '.svg')

    f = open(filepath)
    dot_content = f.readlines()
    f.close()
    relation = {}
    for line in dot_content:
        if "->" not in line:
            continue
        line = line.strip()
        blocks = line.split('->')
        parent = blocks[0].strip().strip(';').strip('"')
        child = blocks[1].strip().strip(';').strip('"')
        if parent not in relation:
            relation[parent] = []
        relation[parent].append(child)
    counter = 0
    gemlist = []
    gemlist.append(gemname)
    dot = Digraph('sample', format='svg')
    while True:
        try:
            currentgem = gemlist[counter]
            print currentgem
            try:
                color = json_out[currentgem]['color']
            except:
                color = 'black'
            dot.node(currentgem, _attributes={'color': color})
            for item in relation:
                if currentgem in relation[item]:
                    gemlist.append(item)
                    string = '%s -> %s' % (item, currentgem)
                    string2 = '"%s" -> %s' % (item, currentgem)
                    string3 = '%s -> "%s"' % (item, currentgem)
                    string4 = '"%s" -> "%s"' % (item, currentgem)
                    if string not in str(dot) and \
                       string2 not in str(dot) and \
                       string3 not in str(dot) and \
                       string4 not in str(dot):
                        dot.edge(item, currentgem)
                    else:
                        print "Duplicate"
            counter = counter + 1
        except Exception as e:
            print e
            break

    dot.render(svgpath)
    string2 = str(dot)
    return render_template('graph.html',
                           path=os.path.join("/static", "%s_%s.dot.svg"
                                             % (gemname, appname)),
                           gemname=gemname,
                           appname=appname
                           )
