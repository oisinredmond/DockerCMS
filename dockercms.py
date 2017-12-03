#Cloud Computing Assignment 2 - Docker Container Management System
#Oisin Redmond - C15492202

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
    <!doctype html>
     <h3>Available API endpoints:</h3>
     <p>GET /containers?list=all:            List all containers</p>
     <p>GET /containers?list=running:        List running containers (only)</p>
     <p>GET /containers/&ltid&gt:            Inspect a specific container</p>
     <p>GET /containers/&ltid&gt/logs:       Dump specific container logs</p>
     <p>GET /images?list=all:                List all images</p>
     <p>GET /images/<id>:                    Show a specific image
     <p>GET /nodes:                          List all nodes</p>
     <p>GET /services:                       List all services</p>
     <p>POST /images:                        Create a new image</p>
     <p>POST /containers:                    Create a new container</p>
     <p>PATCH /containers/&ltid&gt:          Change a container's state</p>
     <p>PATCH /images/&ltid&gt:              Change a specific image's attributes</p>
     <p>DELETE /containers/&ltid&gt:         Delete a specific container</p>
     <p>DELETE /containers:                  Delete all containers (including running)</p>
     <p>DELETE /images/&ltid&gt:             Delete a specific image</p>
     <p>DELETE /images:                      Delete all images</p>
    """

@app.route('/containers',methods=['GET'])
def containers_index():

    """
    List all containers

    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/containers?list=all | python -mjson.tool
    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/containers?list=running | python -mjson.tool
    """

    #If user clicks "running" button
    if request.args.get('list')=='running': 
        output = docker('ps')
        resp = json.dumps(docker_ps_to_array(output))
        return Response(response=resp, mimetype="application/json")

    #If user clicks "all" button
    elif request.args.get('list')=='all':
        output = docker('ps', '-a')
        resp = json.dumps(docker_ps_to_array(output))
        return Response(response=resp, mimetype="application/json")

    #If user clicks "delete" button
    elif request.args.get('_method')=='DELETE':
        output = docker_ps_to_array(docker('ps','-a'))
        for d in output:
            id = d['id']
            docker('stop',id)
            docker('rm',id)

        resp = 'All containers deleted'
        return Response(response=resp, mimetype="application/json")

    #Render html menu page
    else:
        return render_template("containers.html")


@app.route('/images', methods=['GET'])
def images_index():
    """
    List all images

    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/images?list=all | python -mjson.tool 
    """

    #If user clicks "all" button
    if request.args.get('list')=='all':
        output = docker('images')
        resp = json.dumps(docker_images_to_array(output))
        return Response(response=resp, mimetype="application/json")

    #If user clicks "delete" button
    if request.args.get('_method')=='DELETE':
        output = docker_images_to_array(docker('images'))
        for d in output:
            id = d['id']
            docker('rmi',id)

        resp = 'All images deleted'
        return Response(response=resp, mimetype="application/json")

    #Render html menu page
    else:
        return render_template('images.html')



@app.route('/containers/<id>', methods=['GET'])
def containers_show(id):

    """
    Inspect specific container

    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/containers/<id> | python -mjson.tool
    """

    #If user clicks "delete" button
    if request.args.get('_method')=='DELETE':
        docker('rm',id)
        resp = 'Container '+id+' deleted'
        return Response(response=resp,mimetype='application/json')

    #If user clicks "start" button
    elif request.args.get('stopstart')=='Start':
        docker('start',id)
        resp = 'Container '+id+' started'
        return Response(response=resp,mimetype='application/json')

    #If user clicks "Stop" button
    elif request.args.get('stopstart')=='Stop':
        docker('stop',id)
        resp = 'Container '+id+' stopped'
        return Response(response=resp,mimetype='application/json')

    #Render html menu page with a link to container logs endpoint
    else:
        logs = '<a href =\"' +id
        logs += '/logs\">View Container Logs</a>'
        logs = Markup(logs)
        output = docker_ps_to_array(docker('ps','-a','-f','id='+id)) #Output is passed to the html and rendered at top of page
        return render_template("specificcontainer.html",output=output,logs=logs)


@app.route('/containers/<id>/logs', methods=['GET'])
def containers_log(id):
    """
    Dump specific container logs
    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/containers/<id>/logs | python -mjson.tool
    """

    output = docker('logs',id)
    resp = json.dumps(docker_logs_to_object(id,output))

    return Response(response=resp, mimetype="application/json")

@app.route('/services',methods=['GET'])
def services_index():
    """
    List all services

    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/services | python -mjson.tool
    """

    output = docker('service','ls')
    resp = json.dumps(docker_services_to_array(output))

    return Response(response=resp, mimetype = "application/json")

@app.route('/nodes',methods=['GET'])
def nodes_index():
    """
    List all nodes

    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/nodes | python -mjson.tool
    """

    output = docker('node','ls')
    resp = json.dumps(docker_nodes_to_array(output))

    return Response(response=resp,mimetype = "application/json")

@app.route('/images/<id>', methods=['GET'])
def images_remove(id):
    """
    Inspect a specific image

    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/images/<id> | python -mjson.tool
    """

    #If user presses "delete" button
    if request.args.get('_method')=='DELETE':
        docker ('rmi', id)
        resp ='Image '+id+' deleted'

    #If user presses rename and enters a name into textbox
    elif request.args.get('rename')=='Rename':
        name = request.form['rename']
        docker('tag',id,name+':latest')
        resp = 'Image '+id+' renamed to '+name
        return Response(response=resp,mimetype='json/application')

    #Render menu html page
    else:
        return render_template('specificimage.html')


@app.route('/containers', methods=['POST'])
def containers_create():
    """
    Create container (from existing image using id or name)
    curl -s -X POST -H 'Content-Type: application/json' -F 'creatcontainer=[image id]' http://localhost:5000/containers | python -mjson.tool
    """
    #Gets image id from createcontainer form
    image_id = request.form['createcontainer']
    id = (docker('run','-d',image_id)[0:12]).decode('utf-8')
    resp='Container '+id+' created'
    return Response(response=resp,mimetype='application/json')


@app.route('/images', methods=['POST'])
def images_create():
    """
    Create image (from uploaded Dockerfile)
    curl -s -X POST -H 'Accept: application/json' -F 'imagename=[image name]' -F 'imagepath=[image path]' http://localhost:5000/images | python -mjson.tool
    """

    #Get image path and image name from forms in html or curl command
    image_path = '../'+request.form['imagepath']
    image_name = request.form['imagename']
    docker('build','-t',image_name,image_path)
    resp='Image created'
    return Response(response=resp,mimetype='application/json')

#
#Delete methods for use with curl commands in bash
#

@app.route('/containers',methods=['DELETE'])
def containers_delete():

    """
    Force remove all containers

    curl -s -X DELETE -H 'Accept: application/json' http://localhost:5000/containers | python -mjson.tool
    """

    output = docker_ps_to_array(docker('ps','-a'))
    for d in output:
        id = d['id']
        docker('stop',id)
        docker('rm',id)

    resp = 'All images removed.'
    return Response(response=resp,mimetype="application/json")

@app.route('/images',methods=['DELETE'])
def images_delete():
    """
    Force remove all images

    curl -s -X DELETE -H 'Accept: application/json' http://localhost:5000/images | python -mjson.tool
    """
    output = docker_images_to_array(docker('images'))
    for d in output:
        id = d['id']
        docker('rmi',id)

    resp = 'All images removed.'
    return Response(response=resp,mimetype="application/json")


@app.route('/containers/<id>',methods=['DELETE'])
def container_delete(id):
    """
    Delete a specific container

    curl -s -X DELETE -H 'Accept: application/json' http://localhost:5000/containers/<id> | python -mjson.tool
    """
    docker('stop',id)
    docker('rm',id)
    resp = 'Container '+id+' removed'
    return Response(response=resp,mimetype='application/json')


@app.route('/images/<id>',methods=['DELETE'])
def image_delete(id):
    """
    Delete a specific image

    curl -s -X DELETE -H 'Accept: application/json' http://localhost:5000/images/<id> | python -mjson.tool
    """
    docker('rmi',id)
    resp='Image '+id+' removed'
    return Response(response=resp,mimetype='application/json')

#
#Patch methods for use with curl commands in bash
#

@app.route('/containers/<id>',methods=['PATCH'])
def container_stop(id):
    """
    Stop or start a container

    curl -X PATCH -H 'Accept: application/json' -F 'stopstart=Start' http://localhost:5000/containers/<id> | python -mjson.tool
    """

    if request.args.get('stopstart')=='Start':
        docker('start',id)
        resp = 'Container '+id+' started'
        return Response(response=resp,mimtype='application/json')

    elif request.args.get('stopstart')=='Stop':
        docker('stop',id)
        resp ='Container '+id+' stopped'
        return Response(response=resp,mimtype='application/json')


@app.route('/images/<id>',methods=['PATCH'])
def image_rename(id):
    """
    Update image attributes. Tag should be lowercase only

    curl -X PATCH -H 'Accept: application/json' -F 'rename=[new name]' http://localhost:5000/images/<id> | python -mjson.tool
    """

    name = request.form['rename']
    docker('tag',id,name+':latest')
    resp = 'Image '+id+' renamed to '+name
    return Response(response=resp,mimetype='application/json')

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


# Parses the output of a Docker PS command to a python List
def docker_ps_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0].decode('utf-8')
        each['image'] = c[1].decode('utf-8')
        each['name'] = c[-1].decode('utf-8')
        all.append(each)
    return all

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

# Parses the output of a Docker image command to a python List
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

# Parses output of Docker node command to a python list
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
