curl -s -X GET -H 'Accept: application/json' http://35.205.74.228:5000/containers?list=all | python3 -mjson.tool
curl -s -X GET -H 'Accept: application/json' http://35.205.74.228:5000/containers?list=running | python3 -mjson.tool
curl -s -X GET -H 'Accept: application/json' http://35.205.74.228:5000/images?list=all | python3 -mjson.tool
curl -s -X GET -H 'Accept: application/json' http://35.205.74.228:5000/services | python3 -mjson.tool
curl -s -X GET -H 'Accept: application/json' http://35.205.74.228:5000/nodes | python3 -mjson.tool
curl -s -X POST -H 'Content-Type: application/json' -F 'imagepath=lab6' -F 'imagename=lab6webapp' http://35.205.74.228:5000/images | python3 -mjson.tool 
curl -s -X POST -H 'Content-Type: application/json' -F 'creatcontainer=lab6webapp' http://35.205.74.228:5000/containers | python3 -mjson.tool 
curl -s -X GET -H 'Accept: application/json' http://35.205.74.228:5000/images/9e7424e5dbae | python3 -mjson.tool
curl -s -X GET -H 'Accept: application/json' http://35.205.74.228:5000/containers/9631adcbfbaa | python3 -mjson.tool
curl -s -X GET -H 'Accept: application/json' http://35.205.74.228:5000:5000/containers/9631adcbfbaa/logs | python3 -mjson.tool
curl -s -X DELETE -H 'Accept: application/json' http://35.205.74.228:5000:5000/containers | python3 -mjson.tool
curl -s -X DELETE -H 'Accept: application/json' http://35.205.74.228:5000:5000/images | python3 -mjson.tool 
