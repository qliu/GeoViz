import time

import boto3
from boto3.session import Session as Boto3Session

import paramiko

# AWS Credentials
AWS_REGION = "us-west-2" # US West (Oregon)
AWS_ACCESS_KEY_ID = "AKIAJ5QSQONEDZYLDUGA"
AWS_SECRET_ACCESS_KEY = "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"
AWS_Key_Name = "geoviz"
#AWS_KEY_LOCATION = "/home/bitnami/apps/django/django_projects/geoviz/geoviz/geovizapp/static/data/geoviz.rsa"
AWS_KEY_LOCATION = "C:/QLiu/Devl/geoviz/geoviz/geovizapp/static/data/geoviz.rsa"
AWS_SECURITY_GROUPS = [{'name':"default",'id':"sg-a9fa08cd"},]
GPU_INSTANCE_TYPE = "g2.2xlarge"
GPU_TEMPLATE_AMI = "ami-3e81610d"
GPU_NUM = 1

# Check server status
def server_status(instance):
    instance_status = instance.state["Name"]
    while instance_status != "running":
        time.sleep(10)
        instance.reload()
        instance_status = instance.state["Name"]
    print instance_status
    return instance_status

# Start server
def start_server():
    print "start server"
    aws_session = Boto3Session(
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                  )
    client = aws_session.client('ec2')
    ec2 = aws_session.resource('ec2',region_name=AWS_REGION)
    gpu_cluster = ec2.create_instances(
        ImageId=GPU_TEMPLATE_AMI,
        MinCount=1,
        MaxCount=GPU_NUM,
        KeyName = AWS_Key_Name,
        SecurityGroups = [g['name'] for g in AWS_SECURITY_GROUPS],
        SecurityGroupIds = [g['id'] for g in AWS_SECURITY_GROUPS],
        InstanceType = GPU_INSTANCE_TYPE)
    print "DONE!"
    for index,gc in enumerate(gpu_cluster):
        print "initiating instance id: ", gc.id
        print "check instance status"
        if server_status(gc) == "running":
            print "server is up running"
            print "adding tags to instance name"
            if gc.tags:
                gc.tags[0]["Value"] = "GPU Cluster Instance #%d" % (index+1)
            else:
                gc.create_tags(Tags=[
                    {
                        'Key': 'Name',
                        'Value': "GPU Cluster Instance #%d" % (index+1)
                    },
                ])
            print "finished tagging instance"
            
            # check if instance is SSH ready
            print "checking instance status is SSH ready ..."  
            while True:
                statuses = client.describe_instance_status(InstanceIds=[gc.id])
                status = statuses['InstanceStatuses'][0]
                if status['InstanceStatus']['Status'] == 'ok' \
                        and status['SystemStatus']['Status'] == 'ok':
                    break
                time.sleep(10)
            print "Instance is running, you are ready to ssh to it"
    
# Stop server
def stop_server(ids):
    print "stop server"
    aws_session = Boto3Session(
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                  )
    ec2 = aws_session.resource('ec2',region_name=AWS_REGION)
    ec2.instances.filter(InstanceIds = ids).terminate()
    
#start_server()
#stop_server(["i-a953d706","i-a853d707"])

def ssh_cmd(ids):
    aws_session = Boto3Session(
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                  )
    ec2 = aws_session.resource('ec2',region_name=AWS_REGION)    
    if ids:
        for id in ids:
            instance = ec2.Instance(id)
            print "Got instance: ", instance.id
            print instance.public_dns_name
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                instance.public_dns_name,
                username = 'ubuntu',
                key_filename = AWS_KEY_LOCATION
            )
            print "cmd: " + "uptime;ls -l;touch mickmouse;ls -l;uptime"
            stdin, stdout, stderr = ssh.exec_command("uptime;ls -l;touch mickmouse;ls -l;uptime")
            stdin.flush()
            data = stdout.read().splitlines()
            for line in data:
                print line
            ssh.close()
            print "SSH Closed"
            
#ssh_cmd(["i-9053d73f","i-9153d73e"])

def test_ssh_cmd(ids):
    aws_session = Boto3Session(
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                  )
    ec2 = aws_session.resource('ec2',region_name=AWS_REGION)    
    if ids:
        for id in ids:
            instance = ec2.Instance(id)
            print "Got instance: ", instance.id
            print instance.public_dns_name
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                instance.public_dns_name,
                username = 'ubuntu',
                key_filename = AWS_KEY_LOCATION
            )
            cmd = "sudo /usr/bin/X :1 && screen"
            ssh.exec_command(cmd)
#            print "cmd: " + "uptime;ls -l;touch mickmouse;ls -l;uptime"
#            stdin, stdout, stderr = ssh.exec_command("uptime;ls -l;touch mickmouse;ls -l;uptime")
#            stdin.flush()
#            data = stdout.read().splitlines()
#            for line in data:
#                print line
            ssh.close()
            print "SSH Closed"
            
test_ssh_cmd(["i-93f9763c"])