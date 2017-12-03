# DockerCMS - Cloud Computing Assignment 2
## Oisin Redmond - C15492202

# Introduction
The Docker Container Management System is a web app that allows the user to manage all aspects of the docker containers and images. The user can create, run, alter and delete images and containers, and view their details such as ID, name and status. The user can also view nodes in a docker swarm and services running on the swarm.

# To run Docker CMS:
- Clone this repo
- Navigate to the folder in bash
- Type 'python3 dockercms.py'

# Available API Endpoints:
- GET/containers?list=all: List all containers
- GET/containers?list=running: List all running containers
- GET/images?list=all: List all images
- GET/containers/<id>: Inspect a specific container
- GET/containers/<id>/logs: Inspect a specific containers logs
- GET/services: List all services
- GET/nodes: List all nodes
- GET/images/<id>: Inspect a specific image
- POST/containers: Create a container
- POST/images: Create an image
- DELETE/containers: Delete all containers
- DELETE/images: Delete all images
- DELETE/containers/<id>: Delete a specific container
- DELETE/images/<id>: Delete a specific image
- PATCH/containers/<id>: Change a container's state
- PATCH/images/<id>: Change a containers attributes
  
  # Demonstrations
  - Running Nginx as a service: https://www.youtube.com/watch?v=4WXr3hMPM0w
  - Using Docker CMS: https://www.youtube.com/watch?v=LkDRbtE1dg8&t=1s
