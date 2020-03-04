import os
import urllib
from flask import Flask, request, jsonify, send_file, send_from_directory, safe_join, abort
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import json
import os 
from datetime import datetime
import docker
import requests
import time
# This module is to make logs in zip type
import zipfile 
import shutil
import sys

def print_f(message):
    '''
    For debug scopes
    '''
    return print(message,file=sys.stderr)

def docker_setups():
    '''
    NOT USED
    Connect with docker api
    '''
    client = docker.from_env()
    return client

# Init app


app = Flask(__name__)

# Run server
if __name__ == '__main__':
    #debug is true for dev mode
    app.run(debug=True)
    

# Dag_directory
dag_directory = "generated_dags/"
#not fixed we use tha same dir for tool and workflows
# dag_wf_directory = "generated_dags/wf/"
# dag_tl_directory = "generated_dags/tool/"
compressed_logfiles = "compressed_logs/"

def create_filename(id):
    '''
    create file_path for workflows or tool
    os.path.join(path,*path)
    path : path representing a file system path
    *path: It represents the path components to be joined. 
    Name example : kitsos.py (kitsos:wf_id or tool_id)
    '''
    return f'{id}', os.path.join(dag_directory, f'{id}.py')

def get_full_path(filename):
    '''
    Get the full path of dag file 
    '''
    dag_type='workflow'
    # if dag_type == 'workflow':
    #     return f"{dag_wf_directory}/{filename}"
    # elif dag_type == 'tool':
    #     return f"{dag_tl_directory}/{filename}"
    return f"{dag_directory}"
def generate_file(id,instructions):
    '''
    Get the data from request to generate the dag file
    name : The name of file to be generated
    instruction : The  contents of file to be generated
    return:
        generate_date: The generation date of dag file
    '''
    
    ret={}
    filename,filename_path = create_filename(id)
    
    if os.path.exists(filename_path):
        print_f("This file exists")
        # delete_dag_file(filename_path)
        with open(filename_path,'w') as dag_file:
            dag_file.write(instructions)
        # ret['generate_date'] = datetime.now()
        # ret['update_date']= datetime.now()
    else:
        with open(filename_path,'w') as dag_file:
            dag_file.write(instructions)
        # ret['generate_date'] = datetime.now()
    # ret['owner']= 
    # return ret

# def delete_from_airflow(dag_name):
#     '''
#     Delete the dag from airflow Database
#     '''
#     url = f'http://172.18.0.5:8080/api/experimental/dags/{dag_name}/dag_runs'
#     headers = {
#         "Content-Type": "application/json",
#         "Cache-Control": "no-cache"
#         }

#     response = requests.delete(url)

#     return response

# def delete_dag_file(dag_name):
#     '''
#     Delete selected dag file
#     '''
#     ret={}
#     full_path = get_full_path(dag_name)
#     if os.path.exists(full_path):
#         os.remove(full_path)
#         ret['delete_date'] = datetime.now()
#     else:
#         ret['generate_date'] = None
#         ret['msg']= "The file does not exist"
#     return ret


# @app.route(f"/{os.environ['OBC_USER_ID']}/delete_dag", methods=['DELETE','GET'])
# def delete_dag():
#     '''
#     NOT USED YET
#     Get request from openBio platform
#     which contains the file name, dag instructions
#     request data :
#     filename:blah,
#     bash:blah,
#     owner:blah,

#     response:
#         generate_date: blah
#         owner: blah
#         status:deleted
#     '''
#     # Parse data json to dict

#     delete_result={}
#     data = json.loads(request.get_data())
#     name = data['name']
#     edit = data['edit']   
#     dag_filename=f"{name}_{edit}.py" 
#     dag_name=f"{name}__{edit}"
#     delete_result['date'] = delete_dag_file(dag_name)
   

#     # # delete_result['owner']= owner
#     # delete_result['dag_name']=dag_name
#     delete_result['status']="deleted"
#     delete_result['output'] = delete_from_airflow(dag_name)
#     print_f(f"delete_result = {type(delete_result)}")
#     print_f(f"data = {type(data)}")
    
#     return data
#      # return data



def get_tool_OBC_rest(callback,tool_id, tl_name, tl_edit,tl_version):
    '''
    Send GET request to OBC REST to get the dagfile
    RETURN dag File contents
    0.0.0.0:8200 MUST BE CHANGED WITH THE MAIN OBC SERVER
    '''
    response = requests.get(f'{callback}rest/tools/{tl_name}/{tl_version}/{tl_edit}/?dag=true&tool_id={tool_id}')

    if response.status_code != 200:
        print_f(f"Error while retrieving data. ERROR_CODE : {response.status_code}")
        dag_contents['success']='false'
        dag_contents['error']=f"Error while retrieving data. ERROR_CODE : {response.status_code}"
    else:
        print_f("success")
        dag_contents=response.json()
    
    return dag_contents


def get_workflow_OBC_rest(callback,wf_name, wf_edit,workflow_id):
    '''
    Send GET request to OBC REST to get the dagfile
    RETURN dag File contents
    '''
    response = requests.get(f'{callback}rest/workflows/{wf_name}/{wf_edit}/?dag=true&workflow_id={workflow_id}')
    dag_contents={}
    if response.status_code != 200:
        print_f(f"Error while retrieving data. ERROR_CODE : {response.status_code}")
        dag_contents['success']='false'
        dag_contents['error']=f"Error while retrieving data. ERROR_CODE : {response.status_code}"
    else:
        print_f("success")
        dag_contents=response.json()
    
    return dag_contents


def dag__trigger(id,name,edit):
    '''
    Trigger the dag from OpenBio
    Function starts using docker between containers which didn't work
    As a result, we will use experimental api from airflow

    Request using curl :
    curl -X POST \
      http://< PUBLIC IP >:8080/api/experimental/dags/pca_plink_and_plot__1/dag_runs \
      -H 'Cache-Control: no-cache' \
      -H 'Content-Type: application/json' \
      -d '{}'

    According to docker-compose file we have create containers network 
    which communicate both airflow and OBC_client
    '''
    ret = {}
    url = f'http://172.18.0.5:8080/api/experimental/dags/{id}/dag_runs'
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
        }
    # TODO -> MUST BE CHANGED BETTER NOT TO USE WHILE !
    payload={} # Future changes for scheduling workflow
    effort = 0
    while True:
        effort += 1
        print_f (f'Effort: {effort}')
        response = requests.post(url,data=json.dumps(payload),headers=headers)
        print_f(f"{response.ok}")
        if response.ok == False:
            print_f (f'Response error:{response.status_code}')
            print_f (f'{json.dumps(response.json(), indent=4)}')
            time.sleep(1)
        else:
            break


    print_f("---> Response from airflow : ")
    print_f(response.json())
    return response.json()


@app.route(f"/{os.environ['OBC_USER_ID']}/run", methods=['POST'])
def run_wf():
    '''
    Trigger the dag from OpenBio
    Function starts using docker between containers which didn't work
    As a result, we will use experimental api from airflow
    -> Get request from OpenBio Platform with data below:
        1) Type : it has two different types (tool or workflow)
        2) Name : workflow name,
        3) Edit : specific version of workflow from OpenBio rest.
    -> Send request to OpenBio restAPI to get the dag file. The request must contains:
        1) Name : name of workflow (or tool) to search 
        2) Version : version of tool only to search
        3) Edit : edit of workflow (or tool to search)
                
    Get dag content from 
    Request using curl to run the generated dag:
    curl -X POST \
      http://< PUBLIC IP >:8080/api/experimental/dags/pca_plink_and_plot__1/dag_runs \
      -H 'Cache-Control: no-cache' \
      -H 'Content-Type: application/json' \
      -d '{}'

    According to docker-compose file we have create containers network 
    which communicate both airflow and OBC_client
    '''
    payload={} # Future changes for scheduling workflow
    d = request.get_data()
    app.logger.info(str(d))
    data = json.loads(request.get_data())

    name = data['name']
    edit = data['edit']
    work_type = data['type']
    callback= data['callback']
    
    print_f(request.base_url)
    app.logger.info(data)
    if work_type == 'tool':
        tool_id = data['tool_id']
        version = data['version']
        dag_contents= get_tool_OBC_rest(callback,name,edit,version)
        try:
            if dag_contents['success']!='failed':
                generate_file(tool_id)
                payload['status']=dag__trigger(tool_id,name,edit)
            else:
                payload['status']='failed'
                payload['reason']=dag_contents
        except KeyError:
            print_f('Dag not found')
            payload=dag_contents
    elif work_type == 'workflow':
        workflow_id = data['workflow_id']
        dag_contents = get_workflow_OBC_rest(callback,name,edit,workflow_id)
        try:
            if dag_contents['success']!='failed':
                generate_file(workflow_id,dag_contents['dag'])
                payload['status']=dag__trigger(workflow_id,name,edit)
            else:
                payload['status']='failed'
                payload['reason']=dag_contents
        except KeyError:
            print_f('Dag not found')
            payload=dag_contents
    else:
        payload['status']="failed"
        payload['error']="Unknown type (worfkflow or tool)"
    return json.dumps(payload)


@app.route(f"/{os.environ['OBC_USER_ID']}/check/id/<string:dag_id>", methods=['GET'])
def get_status_of_workflow(dag_id):
    '''
    Get dag status from airflow
    Request using curl to get the status of running or finished dag:
    curl -X GET \
      http://< PUBLIC IP >:8080/api/experimental/dags/pca_plink_and_plot__1/dag_runs \
      -H 'Cache-Control: no-cache' \
      -H 'Content-Type: application/json' \
      -d '{
          "id":"bla bla"
      }'

    '''

    ret = {}
    url = f'http://172.18.0.5:8080/api/experimental/dags/{dag_id}/dag_runs'
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
        }

    payload={} # Future changes for scheduling workflow
    response = requests.get(url)

    print_f("---> Response from airflow : ")
    res=response.json()
    return json.dumps(res)



@app.route(f"/{os.environ['OBC_USER_ID']}/download/<string:dag_id>/<string:filename>")
def downloadFile(report_type,dag_id,filename):
    '''
        Download the result from workflow execution
        The data are seperated in three different folders TOOL,DATA,WORK

        dag_id : the id of dag that the user could take the reports
        filename : the name of file which the user want to download
        TODO -> Change in the future the filename because of replaced by compressed file that contains all results
    '''
    downloaded_path=f"REPORTS/WORK/{filename}"
    return send_file(downloaded_path, as_attachment=True)

def create_zipfile(content_path,zipped_path,name):
    '''
    The main usage of this function is to generate zip file containing logs from dag which they run.
    The log files are seperated into a folders, every folder was named according to the steps of dag.
    Path of logs /code/REPORTS/logs/<dag_id>/
    Path of compressed logs /code/REPORTS/logs/<dag_id>/<dag_id.zip>
    log_path = source of log folder
    zipped_path = source of zipped logs to be saved
    zipfile_name = is the name of dag (<dag_id>.zip)
    '''
    shutil.make_archive(f'{zipped_path}/{name}', 'zip', content_path)
    download_path = f"{zipped_path}/{name}.zip"
    return download_path

@app.route(f"/{os.environ['OBC_USER_ID']}/logs/<string:dag_id>")
def getLogs(dag_id):
    '''
        example:
        http://192.168.1.21:5000/d8a05e4b0d2a46b78dce482378d2c39d/logs/mitsos6

        Get the whole logs from workflow execution to zip type
        The logs of execution are seperated in different files (file per step)
        dag_id : the name of dag
    '''
    log_path= f"/code/REPORTS/logs/{dag_id}" 
    destination_log_path = f"/code/REPORTS/compressed_logs"
    
    download_path= create_zipfile(log_path,destination_log_path,dag_id)
    return send_file(download_path, as_attachment=True)
