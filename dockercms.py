from flask import Flask, Response, render_template, request, Markup
import json
from subprocess import Popen, PIPE
import os
from tempfile import mkdtemp
from werkzeug import secure_filename

app = Flask(__name__)

@app.route("/")
def index():
    return """
Available API endpoints:\n
GET /containers                     List all containers\n  ++
GET /containers?state=running      List running containers (only)\n  ++
GET /containers/<id>                Inspect a specific container\n  ++
GET /containers/<id>/logs           Dump specific container logs\n  ++
GET /images                         List all images\n  ++
POST /images                        Create a new image\n
POST /containers                    Create a new container\n  ++
PATCH /containers/<id>              Change a container's state\n
PATCH /images/<id>                  Change a specific image's attributes\n
DELETE /containers/<id>             Delete a specific container\n
DELETE /containers                  Delete all containers (including running)\n ++
DELETE /images/<id>                 Delete a specific image\n
DELETE /images                      Delete all images\n ++
"""

@app.route('/containers',methods=['GET'])
def containers_index():

    """
    List all containers

    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/containers | python -mjson.tool
    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/containers?state=running | python -mjson.tool
    """
    if request.args.get('list')=='running': 
        output = docker('ps')
        resp = json.dumps(docker_ps_to_array(output))
        return Response(response=resp, mimetype="application/json")

    elif request.args.get('list')=='all':
        output = docker('ps', '-a')
        resp = json.dumps(docker_ps_to_array(output))
        return Response(response=resp, mimetype="application/json")

    elif request.args.get('_method')=='DELETE':
        output = docker_ps_to_array(docker('ps','-a'))
        for d in output:
            id = d['id']
            docker('stop',id)
            docker('rm',id)

        return Markup('<p>All containers deleted</p>')

    else:
        return render_template("containers.html")

@app.route('/images', methods=['GET'])
def images_index():
    """
    List all images

    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/images | python -mjson.tool 
    """
    if request.args.get('list')=='all':
        output = docker('images')
        resp = json.dumps(docker_images_to_array(output))
        return Response(response=resp, mimetype="application/json")

    if request.args.get('_method')=='DELETE':
        output = docker_images_to_array(docker('images'))
        for d in output:
            id = d['id']
            docker('rmi',id)

        return Response('<p>All images deleted</p>')

    else:
        return render_template('images.html')

@app.route('/containers/<id>', methods=['GET'])
def containers_show(id):

    """
    Inspect specific container

    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/containers/<id> | python -mjson.tool
    """

    if request.args.get('_method')=='DELETE':
        docker('rm',id)
        return Markup('<p>Container '+id+' deleted</p>')

    elif request.args.get('start')=='Start':
        docker('start',id)
        return Markup('<p>Container '+id+' started</p>')

    elif request.args.get('stop')=='Stop':
        docker('stop',id)
        return Markup('<p>Container '+id+' stopped</p>')

    else:
        logs = '<a href =\"' +id
        logs += '/logs\">View Container Logs</a>'
        logs = Markup(logs)
        output = docker_ps_to_array(docker('ps','-a','-f','id='+id))
        return render_template("specificcontainer.html",output=output,logs=logs)

@app.route('/containers/<id>/logs', methods=['GET'])
def containers_log(id):
    """
    Dump specific container logs
    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/containers/<id>/logs | python -mjson.tool
    """

    output = docker('logs',id)
    resp = json.dumps(docker_logs_to_object(id,output))

    return Response(response=resp, mimetype="application/json")

@app.route('/services',methods=['GET'])
def services_index():
    """
    List all services

    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/services | python -mjson.tool
    """

    output = docker('service','ls')
    resp = json.dumps(docker_services_to_array(output))

    return Response(response=resp, mimetype = "application/json")

@app.route('/nodes',methods=['GET'])
def nodes_index():
    """
    List all nodes

    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/nodes | python -mjson.tool
    """

    output = docker('node','ls')
    resp = json.dumps(docker_nodes_to_array(output))

    return Response(response=resp,mimetype = "application/json")

@app.route('/images/<id>', methods=['GET'])
def images_remove(id):

    if request.args.get('_method')=='DELETE':
        docker ('rmi', id)
        return Markup('<p>Image '+id+' deleted')

    elif request.args.get('rename')=='Rename':
        name = request.form['rename']
        docker('tag',id,name+':latest')
        return Markup('<p>Image '+id+' renamed to '+name+'</p>')

    else:
        return render_template('specificimage.html')

@app.route('/containers', methods=['POST'])
def containers_create():
    """
    Create container (from existing image using id or name)
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "my-app"}'
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "b14752a6590e"}'
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "b14752a6590e","publish":"8081:22"}'
    """
    image_id = request.form['createcontainer']
    id = (docker('run','-d',image_id)[0:12]).decode('utf-8')
    return Markup('<p>Container '+id+' created</p>')


@app.route('/images', methods=['POST'])
def images_create():
    """
    Create image (from uploaded Dockerfile)
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/images '{"id": "b14752a6590e"}'
    """

    image_path = '../'+request.form['imagepath']
    image_name = request.form['imagename']
    docker('build','-t',image_name,image_path)
    return Markup('<p>Image '+id+' created</p>')


def docker(*args):
    cmd = ['sudo','docker']
    for sub in args:
        cmd.append(sub)
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if stderr.startswith(b'Error'):
        print('Error: {0} -> {1}'.format(' '.join(cmd), stderr))
    return stderr + stdout

# 
# Docker output parsing helpers
#

#
# Parses the output of a Docker PS command to a python List
# 
def docker_ps_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0].decode('utf-8')
        each['image'] = c[1].decode('utf-8')
        each['name'] = c[-1].decode('utf-8')
        all.append(each)
    return all

#
# Parses the output of a Docker logs command to a python Dictionary
# (Key Value Pair object)
def docker_logs_to_object(id, output):
    logs = {}
    logs['id'] = id
    all = []
    for line in output.splitlines():
        all.append(line.decode('utf-8'))
    logs['logs'] = all
    return logs

#
# Parses the output of a Docker image command to a python List
# 
def docker_images_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[2].decode('utf-8')
        each['tag'] = c[1].decode('utf-8')
        each['name'] = c[0].decode('utf-8')
        all.append(each)
    return all

#
# Parses output of Docker service command to a python list
#
def docker_services_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0].decode('utf-8')
        each['name'] = c[1].decode('utf-8')
        each['mode'] = c[2].decode('utf-8')
        each['image'] = c[4].decode('utf-8')
        each['ports'] = c[5].decode('utf-8')
        all.append(each)
    return all
#
# Parses output of Docker node command to a python list
#
def docker_nodes_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0].decode('utf-8')
        each['hostname'] = c[1].decode('utf-8')
        each['status'] = c[2].decode('utf-8')
        each['availability'] = c[3].decode('utf-8')
        all.append(each)
    return all

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000, debug=True)
