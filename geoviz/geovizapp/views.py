from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.template import RequestContext
from django.db import models
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, permission_required

# Import twisted
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.protocols.basic import NetstringReceiver
import json, base64

# Import from general utilities
from util import *
from shutil import copyfile
from timeit import default_timer as timer

# Import from app
from geoviz.settings import ROOT_APP_URL, STORAGE_ROOTPATH, STATIC_URL, ADMIN_EMAIL_ADDRESS
from geoviz.settings import AWS_CREDENTIALS
from geovizapp.models import *

## imports for starcluster
#import starcluster
#from starcluster.config import StarClusterConfig
#from starcluster.cluster import ClusterManager

# import for NetCDF
#from netCDF4 import Dataset, num2date

# import for merge image
from PIL import Image

'''-----------------------
Twisted clients
-----------------------'''
class EchoClientReader(NetstringReceiver):
    vars = None

    def connectionMade(self):
        send_data = json.dumps(self.factory.jsondata)
        print "json string to send: ", send_data
        self.sendString(send_data)

    def stringReceived(self, data):
        print "string received: ", data
        jsondata = json.loads(data)
        self.vars = jsondata
        self.transport.loseConnection()

    def connectionLost(self, reason):
        self.receiveddata(self.vars)
        print "self.vars: ", self.vars
        print "variable received! connection lost."
        
    def receiveddata(self, vars):
        print "receiveddata"
        self.factory.var_finished(self.vars)  
        
class EchoFactoryReader(ClientFactory):
    protocol = EchoClientReader

    def __init__(self, jsondata):
        self.jsondata = jsondata
        self.receiveddata = None

    def buildProtocol(self, address):
        proto = ClientFactory.buildProtocol(self, address)
        return proto
    
    def var_finished(self, vars=None):
#        ncreader = NCReader(datafile_path)
        write_var_path = STORAGE_ROOTPATH + "vars.txt"
        json.dump(vars, open(write_var_path,'w'))
        print "variables txt written successfully!"
#        reactor.stop()
        reactor.crash()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed"
        print connector
        print reason
        self.var_finished()

class EchoClient2D(NetstringReceiver):
    img = None

    def connectionMade(self):
        send_data = json.dumps(self.factory.jsondata)
        print "json string to send: ", send_data
        self.sendString(send_data)

    def stringReceived(self, data):
        print "string received: ", data
        jsondata = json.loads(data)
        self.img = jsondata
        self.transport.loseConnection()

    def connectionLost(self, reason):
        self.imgReceived(self.img)
        print "image received! connection lost."

    def imgReceived(self, img):
        self.factory.img_finished(self.img)


class EchoFactory2D(ClientFactory):
    protocol = EchoClient2D

    def __init__(self, jsondata):
        self.jsondata = jsondata
        self.receiveddata = None

    def buildProtocol(self, address):
        proto = ClientFactory.buildProtocol(self, address)
        return proto

    def img_finished(self, img=None):
        self.write_img(img)
#        reactor.stop()
        reactor.crash()

    def write_img(self, img):
        print "write image!"    
        local_img_path = STORAGE_ROOTPATH +"img/2d/"
        img_filename = img['imgname']
        print "writing: ", img_filename
        with open("%s%s" % (local_img_path,img_filename), "wb") as img_file:
            img_file.write(img['imgstr'].decode("base64"))
        print "image written successfully!"

    def clientConnectionFailed(self, connector, reason):
        print "connection failed"
        self.img_finished()

class EchoClientCUDARay(NetstringReceiver):
    img = None
    task_num = 0

    def connectionMade(self):
#        self.factory.jsondata['vars']['datatime'] = self.task_num - 1
        send_data = json.dumps(self.factory.jsondata)
        print "json string to send: ", send_data
        self.sendString(send_data)

    def stringReceived(self, data):
        print "string received for task: ", self.task_num
        #print data
        jsondata = json.loads(data)
        self.img = jsondata
        print "data received: ", jsondata
        #self.factory.receiveddata = jsondata
        if jsondata['curnum'] == (jsondata['gpunum']-1):
            print "get all images, lose connection now"
            self.transport.loseConnection()
        else:
            print "image received"
            self.imgReceived(self.img)

    def connectionLost(self, reason):
        self.imgReceived(self.img)
        print "image received! connection lost."

    def imgReceived(self, img):
        self.factory.img_finished(self.task_num, img)


class EchoFactoryCUDARay(ClientFactory):
    task_num = 1
    protocol = EchoClientCUDARay

    def __init__(self, jsondata, img_count):
        self.jsondata = jsondata
        self.receiveddata = None
        self.img_count = img_count
        self.imgs = {}

    def buildProtocol(self, address):
        proto = ClientFactory.buildProtocol(self, address)
        proto.task_num = self.task_num
        self.task_num += 1
        return proto

    def img_finished(self, task_num=None, img=None):
        if task_num is not None:
            curnum = img['curnum']
            gpunum = img['gpunum']
            imgnum = img['imgnum']
            print "curnum: ", curnum
            print "imgnum: ", imgnum
            self.imgs[(curnum-1)*gpunum] = img

        if curnum == (imgnum-1):
            self.img_count -= 1

        print self.img_count, "images left"

        if self.img_count == 0:
            self.write_img()
            #reactor.stop()
            reactor.crash()

    def write_img(self):
        print "write image!"
        root_path = STORAGE_ROOTPATH    
        local_img_path = root_path+"img/sub/"
        for i in self.imgs:
            print "writing: ", self.imgs[i]['filename']
            img_filename = "%s" % (self.imgs[i]['filename'])
            with open("%s%s" % (local_img_path,img_filename), "wb") as img_file:
                img_file.write(self.imgs[i]['imgstr'].decode("base64"))
        #reactor.stop()
        reactor.crash()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed"
        self.img_finished()


class EchoClientCUDAIso(NetstringReceiver):
    img = None
    task_num = 0

    def connectionMade(self):
        self.factory.jsondata['vars']['datatime'] = self.task_num - 1
        send_data = json.dumps(self.factory.jsondata)
        print "json string to send: ", send_data
        self.sendString(send_data)

    def stringReceived(self, data):
        print "string received for task: ", self.task_num
        #print data
        jsondata = json.loads(data)
        self.img = jsondata
        #self.factory.receiveddata = jsondata
        if jsondata['curnum'] == (jsondata['gpunum']-1):
            self.transport.loseConnection()
        else:
            self.imgReceived(self.img)

    def connectionLost(self, reason):
        self.imgReceived(self.img)
        print "image received! connection lost."

    def imgReceived(self, img):
        self.factory.img_finished(self.task_num, img)


class EchoFactoryCUDAIso(ClientFactory):
    task_num = 1
    protocol = EchoClientCUDAIso

    def __init__(self, jsondata, img_count):
        self.jsondata = jsondata
        self.receiveddata = None
        self.img_count = img_count
        self.imgs = {}

    def buildProtocol(self, address):
        proto = ClientFactory.buildProtocol(self, address)
        proto.task_num = self.task_num
        self.task_num += 1
        return proto

    def img_finished(self, task_num=None, img=None):
        print task_num
        if task_num is not None:
            curnum = img['curnum']
            gpunum = img['gpunum']
            imgnum = img['imgnum']
            print "curnum: ", curnum
            print "imgnum: ", imgnum
            self.imgs[(curnum-1)*gpunum] = img

        if curnum == (imgnum-1):
            self.img_count -= 1

        print self.img_count, "images left"

        if self.img_count == 0:
            self.write_img()
            #reactor.stop()
            reactor.crash()

    def write_img(self):
        print "write image!"
        for i in self.imgs:
            print "writing: ", self.imgs[i]['filename']
            img_filename = "%s" % (self.imgs[i]['filename'])
            with open("img/sub/%s" % img_filename, "wb") as img_file:
                img_file.write(self.imgs[i]['imgstr'].decode("base64"))
#        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed"
        self.img_finished()

'''-----------------------
Home Page
-----------------------'''
# App Page
@render_to("geovizapp/geovizcloud.html")
def geovizcloud(request):
    #varlist = json.dumps(["acp","hgt","alp"])
    #var3dlist = json.dumps(["delt","dl","sc","dd","dw","dflx"])
    #var3dlistflow = json.dumps(["uh,vh","zhyb","omg","rr","dc"])
    #return {"varlist":varlist,"var3dlist":var3dlist,"var3dlistflow":var3dlistflow}
    gpu_choices = []
    for n in GPU_CHOICES:
        gpu_choices.append(n[0])
    hour_choices = []
    for n in HOUR_CHOICES:
        hour_choices.append(n[0])        
    return {"gpu_choices":gpu_choices,"hour_choices":hour_choices}

# Home page
@login_required
@render_to("geovizapp/home.html")
def home(request):
    varlist = json.dumps(["acp","hgt","alp"])
    var3dlist = json.dumps(["delt","dl","sc","dd","dw","dflx"])
    var3dlistflow = json.dumps(["uh,vh","zhyb","omg","rr","dc"])
    return {"varlist":varlist,"var3dlist":var3dlist,"var3dlistflow":var3dlistflow}

# Demo page
@render_to("geovizapp/demo.html")
def demo_page(request):
    varlist = json.dumps(["acp","hgt","alp"])
    var3dlist = json.dumps(["delt","dl","sc","dd","dw","dflx"])
    var3dlistflow = json.dumps(["uh,vh","zhyb","omg","rr","dc"])
    return {"varlist":varlist,"var3dlist":var3dlist,"var3dlistflow":var3dlistflow}

# Run Test page
@render_to("geovizapp/runtest.html")
def runtest(request):
    varlist = json.dumps(["acp","hgt","alp"])
    var3dlist = json.dumps(["delt","dl","sc","dd","dw","dflx"])
    var3dlistflow = json.dumps(["uh,vh","zhyb","omg","rr","dc"])
    return {"varlist":varlist,"var3dlist":var3dlist,"var3dlistflow":var3dlistflow}

#class NCReader:
#    def __init__(self, filename="data/dust2d.nc", varname = None, maxele = 200000):
#        self.filename = filename
#        self.varname = varname
#        self.varvalue = []
#        self.var2dlist = []
#        self.longvar2dlist = []
#        self.var3dlist =[]
#        self.longvar3dlist = []
#        self.lon = "longitude"
#        self.lat = "latitude"
#        self.time = "time"
#        self.lons = []
#        self.lats = []
#        self.eles = []
#        self.elestrue = []
#        self.times = []
#        self.longtimes = []
#        self.maxele = maxele ##add one 0
#        self.can_vis = False
#        self.ReadBasic()
#        #print self.varvalue.shape
#
#    ##read basic information
#    def ReadBasic(self):
#        ##read data
#        ncfile = Dataset(self.filename, mode='r')
#        KEY_LATITUDE = ("latitude","lat","nlat")
#        KEY_LONGITUDE = ("longitude","lon","nlon")
#        k_lat = None
#        k_lon = None
#        k_levels = "levels"
#        for k in ncfile.variables.keys():
#            if k.lower() in KEY_LATITUDE:
#                k_lat = k
#                self.lat = k_lat
#            if k.lower() in KEY_LONGITUDE:
#                k_lon = k
#                self.lon = k_lon
#            if k.lower().find("levels") or k.lower().find("lvls"):
#                k_levels = k
#        if k_lat and k_lon:
#            self.can_vis = True
#            self.lons = ncfile.variables[k_lon][:]
#            self.lats = ncfile.variables[k_lat][:]
#            self.eles =ncfile.variables[k_levels][:]
#            ##if 50 ... etc hmp
#            self.elestrue = self.maxele* (1- (self.eles -1)*1.0/(len(self.eles)-1))
#            var_shape_2d = 2
#            var_shape_3d = 3
#            if "time" in ncfile.variables.keys():
#                var_shape_2d = 3
#                var_shape_3d = 4
#                self.times = ncfile.variables['time'][:]
#                time_unit = ncfile.variables['time'].units
#                try:
#                    calendar = ncfile.variables['time'].calendar
#                except:
#                    calendar = "gregorian"
#                longtimes = num2date(self.times,units=time_unit,calendar=calendar)
#                longtimes = [t.isoformat(sep=" ") for t in longtimes]
#                self.longtimes = longtimes
#            if self.varname:
#                self.varvalue = ncfile.variables[self.varname][:,:,:,:]
#            for var in ncfile.variables:
#                print var
#                print len(ncfile.variables[var].shape)
#                try:
#                    var_long_name = ncfile.variables[var].long_name
#                except:
#                    var_long_name = ""
#                if  len(ncfile.variables[var].shape) == var_shape_2d:
#                    self.var2dlist.append(var)
#                    self.longvar2dlist.append("%s: %s" % (var,var_long_name))
#                elif len(ncfile.variables[var].shape) == var_shape_3d:
#                    self.var3dlist.append(var)
#                    self.longvar3dlist.append("%s: %s" % (var,var_long_name))
#        ncfile.close()

def loaddata(request):
    response_data = None
    
    if request.method == 'POST':
        csrfmiddlewaretoken = request.POST["csrfmiddlewaretoken"]
        gpu_region = request.POST["gpuregion"]
        datafile = request.POST["datafile"]
        local_datafile_path = STORAGE_ROOTPATH + datafile
        remote_datafile_path = AWS_CREDENTIALS['REMOTE_DATAFILE_PATH'] + datafile
        print "data to load: ", local_datafile_path
#        ncreader = NCReader(datafile_path)
#        var2dlist = json.dumps(ncreader.longvar2dlist)
#        var3dlist = json.dumps(ncreader.longvar3dlist)
#        varlatlons = json.dumps((float(min(ncreader.lats)),float(max(ncreader.lats)),float(min(ncreader.lons)),float(max(ncreader.lons))))
#        vartimes = json.dumps(ncreader.longtimes)
#
#        #config_txt = request.POST["configtxt"]
#        root_path = STORAGE_ROOTPATH
#        remote_datafile_path = "/home/ubuntu/CollabViz/data/" + datafile
#        #wwconfig_path = root_path + "wwconfig.txt"
#        
#        #with open(wwconfig_path,'wb') as f:
#            #f.write(config_txt)
#
#        conf_new_path = root_path+ "config"
#        cfg = StarClusterConfig(conf_new_path)
#        cfg.load()
#        cluster = cfg.get_cluster_template("geovizcluster")
#
#        for index,node in enumerate(cluster.nodes):
#            if not node.ssh.isfile(remote_datafile_path):
#                #local_config_path = wwconfig_path
#                #remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"
#                node.ssh.switch_user("ubuntu")
#                node.ssh.put(datafile_path,remote_datafile_path)
#    leneles = 24
#    response_data = {"var2dlist":var2dlist,"var3dlist":var3dlist,"varlatlons":varlatlons,"vartimes":vartimes,"leneles":leneles}
    
        # get cluster info from database 
        cluster = Cluster.objects.get(csrf_token=csrfmiddlewaretoken)
        instance_ids = []
        for i in cluster.instances.all():
            print i.instance_id
            instance_ids.append(i.instance_id)
        
        aws_session = Boto3Session(
                        aws_access_key_id=AWS_CREDENTIALS['ACCESS_KEY_ID'],
                        aws_secret_access_key=AWS_CREDENTIALS['SECRET_ACCESS_KEY'],
                        region_name=gpu_region
                      )    
        ec2 = aws_session.resource('ec2',region_name=gpu_region)
        
        if instance_ids:
            # copy the file onto gpu instances
            for id in instance_ids:
                instance = ec2.Instance(id)
                print "Got instance: ", instance.id
                print instance.public_dns_name
#                try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    instance.public_dns_name,
                    username = 'ubuntu',
                    key_filename = AWS_CREDENTIALS['KEY_LOCATION']
                )
                sftp = ssh.open_sftp()
                sftp.chdir(AWS_CREDENTIALS['REMOTE_DATAFILE_PATH'])
                try:
                    print(sftp.stat(datafile))
                    print('file exists')
                except IOError:
                    print('copying file')
                    sftp.put(local_datafile_path, datafile)
                ssh.close()                
#               except paramiko.SSHException:
#                   print("Connection Error")

            # read file and get 2D and 3D variables
            instance = ec2.Instance(instance_ids[0])
            SERVER_IP = instance.public_ip_address
            SERVER_PORT = 8007
            data_dict = {
                "API":"NetCDFReader",
                "vars":{
                    "filepath": remote_datafile_path,
                }
            }
            print "data_dict: ", data_dict
            print "connecting: ", instance.public_ip_address
            f = EchoFactoryReader(jsondata=data_dict)
            reactor.connectTCP(SERVER_IP, SERVER_PORT, f)

            if not reactor.running:
                reactor.run()
                
            print "reading vars from txt"
            var_dict = json.load(open(STORAGE_ROOTPATH+"vars.txt"))
            print "var_dict: ", var_dict
            var2dlist = json.dumps(var_dict['var2dlist'])
            print "var2dlist: ", var2dlist
            var3dlist = json.dumps(var_dict['var3dlist'])
            print "var3dlist: ", var3dlist
    
            response_data = {"var2dlist":var2dlist,"var3dlist":var3dlist}
    
    return HttpResponse(json.dumps(response_data),content_type="application/json") 

class NCVRImage:
    def __init__(self, filepath=""):
        self.filepath = filepath

    ##for stream flows
    def OverlayImage(self, folderpath, finaimage, width, height):
        ##create a transparent image of the same size
        list = os.listdir(folderpath)
        imgbase = Image.new("RGBA", (width, height))
        imgbase.save(finaimage, "PNG")
        #for filepath in list:
        for i in range(24):
            filepath = "flow_%d.png" % i
            img = Image.open(folderpath+filepath)
            imgbase.paste(img, (0,0), img)
            os.remove(folderpath+filepath)
        imgbase.save(finaimage, "PNG")
        
    ##create an image based on the intersection
    ##given a folder that saves the images, merge images, and delete original images
    def MergeImageFromFolder(self, folderpath, finalimage, width, height, iso=False):
        list = os.listdir(folderpath)
        imgbase = Image.new("RGBA", (width, height))
        imgbase.save(finalimage, "PNG")
        for everyfile in list:
            img = Image.open(folderpath+everyfile)
            imgsize = everyfile.split("_")
            if iso==True:
                ##[w1, viewconfig.height-h2, w2, viewconfig.height-h1]
                imgbase.paste(img,(int(imgsize[0]),int(height)-int(imgsize[3].split(".")[0]),int(imgsize[2]),int(height) -int(imgsize[1]) )) ## left upper right lower
            else:
                imgbase.paste(img,(int(imgsize[0]),int(imgsize[1]),int(imgsize[2]),int(imgsize[3].split(".")[0]))) ## left upper right lower
            os.remove(folderpath+"/"+everyfile)
        imgbase.save(finalimage, "PNG")
        ##delete previous file
        
def writeconfig_2d_new(request):
    if request.method == 'POST':
        csrfmiddlewaretoken = request.POST["csrfmiddlewaretoken"]
        # get 2d var name and time point
        var_name = request.POST["varname2d"]
        data_time = int(request.POST["curtime"])
        # get data file
        datafile = request.POST["datafile"]
        local_datafile_path = STORAGE_ROOTPATH + datafile
        remote_datafile_path = AWS_CREDENTIALS['REMOTE_DATAFILE_PATH'] + datafile  
        # write local view config file
        config_txt = request.POST["configtxt"]
        local_config_path = STORAGE_ROOTPATH + "wwconfig.txt"
        remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"     
        with open(local_config_path,'wb') as f:
            f.write(config_txt)
            
        # reading vars from local vars.txt
        print "reading vars from txt"
        var_dict = json.load(open(STORAGE_ROOTPATH+"vars.txt"))
        print "var_dict: ", var_dict
        var_2d_list = [v.split(":")[0] for v in var_dict["var2dlist"]]
        varlatlons = json.dumps(var_dict['varlatlons'])
        vartimes = range(0,len(var_dict['vartimes'])-1)
        print "var_times: ", vartimes
        
        print "render 2d vis for data: ", local_datafile_path
        
        print "initiating ssh..."
        # copy view config file to gpu instance
        ## get cluster info from database 
        cluster = Cluster.objects.get(csrf_token=csrfmiddlewaretoken)
        instance_ids = []
        for i in cluster.instances.all():
            instance_ids.append(i.instance_id)
            gpu_region = i.region
        ## create aws session
        aws_session = Boto3Session(
                        aws_access_key_id=AWS_CREDENTIALS['ACCESS_KEY_ID'],
                        aws_secret_access_key=AWS_CREDENTIALS['SECRET_ACCESS_KEY'],
                        region_name=gpu_region
                      )
        ec2 = aws_session.resource('ec2',region_name=gpu_region)
        instance = ec2.Instance(instance_ids[0]) 
        ## ssh      
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            instance.public_dns_name,
            username = 'ubuntu',
            key_filename = AWS_CREDENTIALS['KEY_LOCATION']
        )
        # copy file
        sftp = ssh.open_sftp()
        sftp.put(local_config_path, remote_config_path)
        ssh.close()
        print "view config copied onto gpu instance"       
        
        print "requesting 2d vis..."
        SERVER_IP = instance.public_ip_address
        SERVER_PORT = 8007
        
        for var_name in var_2d_list:
            for datatime in vartimes:
                data_dict = {
                    "API":"NetCDF2DImage",
                    "vars":{
                        "filepath": remote_datafile_path,
                        "varname": var_name,
                        "datatime": datatime,
                    }
                }
                print "data_dict: ", data_dict
                print "connecting: ", instance.public_ip_address
                f = EchoFactory2D(jsondata=data_dict)
                reactor.connectTCP(SERVER_IP, SERVER_PORT, f)

                if not reactor.running:
                    reactor.run()
            
        print "2d image received! Start rendering..."

        response_data = {
            "varlatlons": varlatlons,
            "vartimes": json.dumps(vartimes)
        }
        return HttpResponse(json.dumps(response_data),content_type="application/json")

def writeconfig_ray_new(request):
    response_data = None
    if request.method == 'POST':
        csrfmiddlewaretoken = request.POST["csrfmiddlewaretoken"]
        # get vars for raycasting viz
        gpunum = int(request.POST["gpunum"])
        tasknum = pow(gpunum,2)
        varname = request.POST["varname3d"]
        datatime = int(request.POST["curtime"])
        # get data file
        datafile = request.POST["datafile"]
        local_datafile_path = STORAGE_ROOTPATH + datafile
        remote_datafile_path = AWS_CREDENTIALS['REMOTE_DATAFILE_PATH'] + datafile  
        # write local view config file
        config_txt = request.POST["configtxt"]
        local_config_path = STORAGE_ROOTPATH + "wwconfig.txt"
        remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"     
        with open(local_config_path,'wb') as f:
            f.write(config_txt)
            
        # reading vars from local vars.txt
        print "reading vars from txt"
        var_dict = json.load(open(STORAGE_ROOTPATH+"vars.txt"))
        vartimes = range(0,len(var_dict['vartimes'])-1)
        print "var_times: ", vartimes
        
        print "render 3D raycasting vis for data: ", local_datafile_path
        
        print "initiating ssh..."
        # copy view config file to gpu instance
        ## get cluster info from database 
        cluster = Cluster.objects.get(csrf_token=csrfmiddlewaretoken)
        instance_ids = []
        for i in cluster.instances.all():
            instance_ids.append(i.instance_id)
            gpu_region = i.region
        ## create aws session
        aws_session = Boto3Session(
                        aws_access_key_id=AWS_CREDENTIALS['ACCESS_KEY_ID'],
                        aws_secret_access_key=AWS_CREDENTIALS['SECRET_ACCESS_KEY'],
                        region_name=gpu_region
                      )
        ec2 = aws_session.resource('ec2',region_name=gpu_region)
        for index,instance_id in enumerate(instance_ids):
            instance = ec2.Instance(instance_id) 
            ## ssh      
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                instance.public_dns_name,
                username = 'ubuntu',
                key_filename = AWS_CREDENTIALS['KEY_LOCATION']
            )
            # copy view config file
            sftp = ssh.open_sftp()
            sftp.put(local_config_path, remote_config_path)
            ssh.close()
            print "view config copied onto gpu instance"
            
            print "start raycasting rendering..."
            # set raycasting vars:
            len_times = 1
#            len_times = len(vartimes)
            intrange = 80
#            curtime = 8
            curtime = datatime
            rgb = request.POST["rgb"] # in a format: "rgb(204,175,100)"
            rgb = rgb.replace("rgb(","").replace(")","") # in a format "204,175,100"
            w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
            wdiv,hdiv = w/gpunum,h/gpunum
            # set image paths
            imgoutpath = "image/sub/"
            remote_root_path = "/home/ubuntu/CollabViz/"
            remote_img_path = remote_root_path + imgoutpath
            local_img_path = STORAGE_ROOTPATH+"img/sub/"

            # prepare the connection
            SERVER_IP = instance.public_ip_address
            SERVER_PORT = 8007

            for t in range(len_times):
                data_dict = {
                    "API":"NetCDFCUDARayCasting",
                    "vars":{
                        "filename": datafile,
                        "tasknum": tasknum,
                        "gpunumtotal": gpunum,
                        "curgpu": index,
                        "viewfilepath": "wwconfig.txt",
                        "imgoutpath": imgoutpath,
                        "varname": varname,
                        "intrange": intrange,
                        "curtime": curtime,
                        "rgb": rgb,
                        "datatime":t
                    }
                }
                print data_dict
                f = EchoFactoryCUDARay(jsondata=data_dict, img_count=len_times)
                print "about to connect tcp round ", t
                reactor.connectTCP(SERVER_IP, SERVER_PORT, f)
                print "finished loop ", t
            
                if not reactor.running:
                    reactor.run()
                    
            ncvrimage = NCVRImage(filepath=local_img_path)
            final_ray_img_file = "new_ray_%s.png" % datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')
            final_ray_img_file_path = STORAGE_ROOTPATH + "img/" + final_ray_img_file
            ncvrimage.MergeImageFromFolder(local_img_path,final_ray_img_file_path,w,h)
            print "final raycasting image path: ", final_ray_img_file_path                

        response_data = {"newimgfile":final_ray_img_file}
    return HttpResponse(json.dumps(response_data),content_type="application/json")

def writeconfig_ray_animation_new(request):
    response_data = None
    if request.method == 'POST':
        csrfmiddlewaretoken = request.POST["csrfmiddlewaretoken"]
        # get vars for raycasting viz
        gpunum = int(request.POST["gpunum"])
        tasknum = pow(gpunum,2)
        varname = request.POST["varname3d"]
        # get data file
        datafile = request.POST["datafile"]
        local_datafile_path = STORAGE_ROOTPATH + datafile
        remote_datafile_path = AWS_CREDENTIALS['REMOTE_DATAFILE_PATH'] + datafile  
        # write local view config file
        config_txt = request.POST["configtxt"]
        local_config_path = STORAGE_ROOTPATH + "wwconfig.txt"
        remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"     
        with open(local_config_path,'wb') as f:
            f.write(config_txt)
            
        # reading vars from local vars.txt
        print "reading vars from txt"
        var_dict = json.load(open(STORAGE_ROOTPATH+"vars.txt"))
        vartimes = range(0,len(var_dict['vartimes'])-1)
        print "var_times: ", vartimes
        
        print "render 3D raycasting vis for data: ", local_datafile_path
        
        print "initiating ssh..."
        # copy view config file to gpu instance
        ## get cluster info from database 
        cluster = Cluster.objects.get(csrf_token=csrfmiddlewaretoken)
        instance_ids = []
        for i in cluster.instances.all():
            instance_ids.append(i.instance_id)
            gpu_region = i.region
        ## create aws session
        aws_session = Boto3Session(
                        aws_access_key_id=AWS_CREDENTIALS['ACCESS_KEY_ID'],
                        aws_secret_access_key=AWS_CREDENTIALS['SECRET_ACCESS_KEY'],
                        region_name=gpu_region
                      )
        ec2 = aws_session.resource('ec2',region_name=gpu_region)
        for index,instance_id in enumerate(instance_ids):
            instance = ec2.Instance(instance_id) 
            ## ssh      
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                instance.public_dns_name,
                username = 'ubuntu',
                key_filename = AWS_CREDENTIALS['KEY_LOCATION']
            )
            # copy view config file
            sftp = ssh.open_sftp()
            sftp.put(local_config_path, remote_config_path)
            ssh.close()
            print "view config copied onto gpu instance"
            
            print "start raycasting rendering..."
            # set raycasting vars:
#            len_times = 1
            len_times = len(vartimes)
            intrange = 80
#            curtime = 8
#            curtime = datatime
            rgb = request.POST["rgb"] # in a format: "rgb(204,175,100)"
            rgb = rgb.replace("rgb(","").replace(")","") # in a format "204,175,100"
            w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
            wdiv,hdiv = w/gpunum,h/gpunum
            # set image paths
            imgoutpath = "image/sub/"
            remote_root_path = "/home/ubuntu/CollabViz/"
            remote_img_path = remote_root_path + imgoutpath
            local_img_path = STORAGE_ROOTPATH+"img/sub/"

            # prepare the connection
            SERVER_IP = instance.public_ip_address
            SERVER_PORT = 8007

            for t in range(len_times):
                curtime = t
                data_dict = {
                    "API":"NetCDFCUDARayCasting",
                    "vars":{
                        "filename": datafile,
                        "tasknum": tasknum,
                        "gpunumtotal": gpunum,
                        "curgpu": index,
                        "viewfilepath": "wwconfig.txt",
                        "imgoutpath": imgoutpath,
                        "varname": varname,
                        "intrange": intrange,
                        "curtime": curtime,
                        "rgb": rgb,
                        "datatime":t
                    }
                }
                print data_dict
                f = EchoFactoryCUDARay(jsondata=data_dict, img_count=1)
                print "about to connect tcp round ", t
                reactor.connectTCP(SERVER_IP, SERVER_PORT, f)
                print "finished loop ", t
                
                if not reactor.running:
                    reactor.run()                
                
                ncvrimage = NCVRImage(filepath=local_img_path)
                if t == 0:
                    first_final_ray_img_file = "new_ray_%s" % datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')
                final_ray_img_file = "%s_%d.png" % (first_final_ray_img_file, t)
                final_ray_img_file_path = STORAGE_ROOTPATH + "img/" + final_ray_img_file
                ncvrimage.MergeImageFromFolder(local_img_path,final_ray_img_file_path,w,h)

        response_data = {"newimgfile":first_final_ray_img_file}
    return HttpResponse(json.dumps(response_data),content_type="application/json")

def writeconfig_ray(request):
    if request.method == 'POST':
        config_txt = request.POST["configtxt"]
        root_path = STORAGE_ROOTPATH
        wwconfig_path = root_path + "wwconfig.txt"
        with open(wwconfig_path,'wb') as f:
            f.write(config_txt)

        conf_new_path = root_path+ "config"
        cfg = StarClusterConfig(conf_new_path)
        cfg.load()
        cluster = cfg.get_cluster_template("geovizcluster")

        tasknum = int(request.POST["tasknum"])
        gpunum = int(request.POST["gpunum"])
        datafile = "data/"+request.POST["datafile"]
        varname = "dd"
        if request.POST["varname3d"] and request.POST["varname3d"] != "":
            varname = request.POST["varname3d"]
        intrange = 80
        curtime = 8
        if request.POST["curtime"] and request.POST["curtime"] != "":
            curtime = int(request.POST["curtime"])
        rgb = "rgb(204,175,100)"
        if request.POST["rgb"] and request.POST["rgb"] != "":
            rgb = request.POST["rgb"]
        rgb = rgb.replace("rgb(","").replace(")","")

        w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
        wdiv,hdiv = w/gpunum,h/gpunum

        #node_alias_list = []
        img_list = []

        t1 = timer()
        for index,node in enumerate(cluster.nodes):
            #node_alias_list.append(node.alias)
            # send wwconfig file   
            #local_config_path = "/home/bitnami/apps/django/django_projects/geoviz/geoviz/geovizapp/static/data/wwconfig.txt"
            local_config_path = wwconfig_path
            remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"
            node.ssh.switch_user("ubuntu")
            node.ssh.put(local_config_path,remote_config_path)

            imgoutpath = "image/sub/"
            remote_root_path = "/home/ubuntu/CollabViz/"
            remote_img_path = remote_root_path + imgoutpath

            tmp_imgs = []
            
            for i in range(index*eachround,(index+1)*eachround):
                if i < tasknum:
                    curgpu = i
                    wrange, hrange = int(i/gpunum),int(i%gpunum)
                    w1,h1 = int(wrange*wdiv),int(hrange*hdiv)
                    w2,h2 = int((wrange+1)*wdiv),int((hrange+1)*hdiv)
                    tmp_imgs.append("%d_%d_%d_%d.png" % (w1,h1,w2,h2))
            img_list.append(tmp_imgs)

            cmd = "sudo /home/ubuntu/anaconda/bin/python %s%s %d %d %d %s %s %d %d %s" % (remote_root_path,"NetCDFCUDARayCasting.py",tasknum,gpunum,index,datafile,varname,intrange,curtime,rgb)
            node.ssh.execute(cmd,source_profile=False,detach=True)

        local_img_path = root_path+"img/sub/"
        for index,node in enumerate(cluster.nodes):
            for img in img_list[index]:
                img_get = False
                img_get_path = remote_img_path + img
                while not img_get:
                    if node.ssh.isfile(img_get_path):
                        node.ssh.get(img_get_path,local_img_path+img)
                        imgstatinfo = os.stat(local_img_path+img)
                        if imgstatinfo.st_size > 0:
                            img_get = True
                            cmd = "sudo rm %s" % img_get_path
                            node.ssh.execute(cmd,source_profile=False,detach=True)

        t2 = timer()
        raise Exception('time',str(t2-t1))
        ncvrimage = NCVRImage(filepath=local_img_path)
        final_ray_img_file = "ray_%s.png" % datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')
        final_ray_img_file_path = root_path + "img/" + final_ray_img_file
        ncvrimage.MergeImageFromFolder(local_img_path,final_ray_img_file_path,w,h)

        response_data = {"newimgfile":final_ray_img_file}
        return HttpResponse(json.dumps(response_data),content_type="application/json")


def writeconfig_iso_new(request):
    response_data = None
    if request.method == 'POST':
        csrfmiddlewaretoken = request.POST["csrfmiddlewaretoken"]
        # get vars for raycasting viz
        gpunum = int(request.POST["gpunum"])
        tasknum = pow(gpunum,2)
#        tasknum = 16
        w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
        wdiv,hdiv = w/gpunum,h/gpunum
        varname = request.POST["varname3d"]
        # get data file
        datafile = request.POST["datafile"]
        local_datafile_path = STORAGE_ROOTPATH + datafile
        remote_datafile_path = AWS_CREDENTIALS['REMOTE_DATAFILE_PATH'] + datafile  
        # write local view config file
        config_txt = request.POST["configtxt"]
        local_config_path = STORAGE_ROOTPATH + "wwconfig.txt"
        remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"     
        with open(local_config_path,'wb') as f:
            f.write(config_txt)
            
        # reading vars from local vars.txt
        print "reading vars from txt"
        var_dict = json.load(open(STORAGE_ROOTPATH+"vars.txt"))
        vartimes = range(0,len(var_dict['vartimes'])-1)
        print "var_times: ", vartimes
        
        print "render 3D raycasting vis for data: ", local_datafile_path
        
        print "initiating ssh..."
        # copy view config file to gpu instance
        ## get cluster info from database 
        cluster = Cluster.objects.get(csrf_token=csrfmiddlewaretoken)
        instance_ids = []
        for i in cluster.instances.all():
            instance_ids.append(i.instance_id)
            gpu_region = i.region
        ## create aws session
        aws_session = Boto3Session(
                        aws_access_key_id=AWS_CREDENTIALS['ACCESS_KEY_ID'],
                        aws_secret_access_key=AWS_CREDENTIALS['SECRET_ACCESS_KEY'],
                        region_name=gpu_region
                      )
        ec2 = aws_session.resource('ec2',region_name=gpu_region)
        
        # set iso vars
#       intrange = 80
        intrange = int(request.POST["intrange"])
#       curtime = 4
        curtime = int(request.POST["curtime"])
#       isovale = 0.0000001
        isovalue = float(request.POST["isovalue"])
        
        len_times = 1
        
        # set img paths
        imgoutpath = "image/sub/"
        remote_root_path = "/home/ubuntu/CollabViz/"
        remote_img_path = remote_root_path + imgoutpath
        local_img_path = STORAGE_ROOTPATH + "img/sub/"
        
        for index,instance_id in enumerate(instance_ids):
            instance = ec2.Instance(instance_id) 
            ## ssh      
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                instance.public_dns_name,
                username = 'ubuntu',
                key_filename = AWS_CREDENTIALS['KEY_LOCATION']
            )
            # copy view config file
            sftp = ssh.open_sftp()
            sftp.put(local_config_path, remote_config_path)
            ssh.close()
            print "view config copied onto gpu instance"
            
            print "start isosurface rendering..."
            SERVER_IP = instance.public_ip_address
            SERVER_PORT = 8007

            for t in range(len_times):
                data_dict = {
                    "API":"NetCDFCUDAIsosurface",
                    "vars":{
                        "filename": datafile,
                        "tasknum": tasknum,
                        "gpunumtotal": gpunum,
                        "curgpu": index,
                        "viewfilepath": "wwconfig.txt",
                        "imgoutpath": imgoutpath,
                        "varname": varname,
                        "intrange": intrange,
                        "curtime": curtime,
                        "isovalue": isovalue,
                        "datatime":t,
                    }
                }
                print data_dict
                if t == 0:
                    f = EchoFactoryCUDAIso(jsondata=data_dict, img_count=len_times)
                print "about to connect tcp round ", t
                reactor.connectTCP(SERVER_IP, SERVER_PORT, f)
                print "finished loop ", t

        if not reactor.running:
            reactor.run()

        ncvrimage = NCVRImage(filepath=local_img_path)
        final_iso_img_file = "new_iso_%s.png" % datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')
        final_iso_img_file_path = root_path + "img/" + final_iso_img_file
        ncvrimage.MergeImageFromFolder(local_img_path,final_iso_img_file_path,w,h)

        response_data = {"newimgfile":final_iso_img_file}
        return HttpResponse(json.dumps(response_data),content_type="application/json")

def writeconfig_iso_new_2(request):
    if request.method == 'POST':
        csrfmiddlewaretoken = request.POST["csrfmiddlewaretoken"]
        # get vars for raycasting viz
        gpunum = int(request.POST["gpunum"])
        tasknum = pow(gpunum,2)
#        tasknum = 16
        w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
        wdiv,hdiv = w/gpunum,h/gpunum
        varname = request.POST["varname3d"]
        # get data file
        datafile = request.POST["datafile"]
        local_datafile_path = STORAGE_ROOTPATH + datafile
        remote_datafile_path = AWS_CREDENTIALS['REMOTE_DATAFILE_PATH'] + datafile  
        # write local view config file
        config_txt = request.POST["configtxt"]
        local_config_path = STORAGE_ROOTPATH + "wwconfig.txt"
        remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"     
        with open(local_config_path,'wb') as f:
            f.write(config_txt)
            
        # reading vars from local vars.txt
        print "reading vars from txt"
        var_dict = json.load(open(STORAGE_ROOTPATH+"vars.txt"))
        vartimes = range(0,len(var_dict['vartimes'])-1)
        print "var_times: ", vartimes
        
        print "render 3D raycasting vis for data: ", local_datafile_path
        
        print "initiating ssh..."
        # copy view config file to gpu instance
        ## get cluster info from database 
        cluster = Cluster.objects.get(csrf_token=csrfmiddlewaretoken)
        instance_ids = []
        for i in cluster.instances.all():
            instance_ids.append(i.instance_id)
            gpu_region = i.region
        ## create aws session
        aws_session = Boto3Session(
                        aws_access_key_id=AWS_CREDENTIALS['ACCESS_KEY_ID'],
                        aws_secret_access_key=AWS_CREDENTIALS['SECRET_ACCESS_KEY'],
                        region_name=gpu_region
                      )
        ec2 = aws_session.resource('ec2',region_name=gpu_region)
        
        # set iso vars
#       intrange = 80
        intrange = int(request.POST["intrange"])
#       curtime = 4
        curtime = int(request.POST["curtime"])
#       isovalue = 0.0000001
        isovalue = float(request.POST["isovalue"])
        
        len_times = 1
        
        # set img paths
        imgoutpath = "image/sub/"
        remote_root_path = "/home/ubuntu/CollabViz/"
        remote_img_path = remote_root_path + imgoutpath
        local_img_path = STORAGE_ROOTPATH + "img/sub/"
        
        img_list = []
        
        for index,instance_id in enumerate(instance_ids):
            instance = ec2.Instance(instance_id) 
            ## ssh      
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                instance.public_dns_name,
                username = 'ubuntu',
                key_filename = AWS_CREDENTIALS['KEY_LOCATION']
            )
            # copy view config file
            sftp = ssh.open_sftp()
            sftp.put(local_config_path, remote_config_path)
#            ssh.close()
            print "view config copied onto gpu instance"
            
            print "start isosurface rendering..."
            tmp_imgs = []
            eachround = int(math.ceil(tasknum*1.0/gpunum))
            for i in range(index*eachround,(index+1)*eachround):
                if i < tasknum:
                    curgpu = i
                    wrange, hrange = int(i/gpunum),int(i%gpunum)
                    w1,h1 = int(wrange*wdiv),int(hrange*hdiv)
                    w2,h2 = int((wrange+1)*wdiv),int((hrange+1)*hdiv)
                    tmp_imgs.append("%d_%d_%d_%d.png" % (w1,h1,w2,h2))
            img_list.append(tmp_imgs)

            cmd = "sudo DISPLAY=:1 /home/ubuntu/anaconda/bin/python %s%s %d %d %d %s %s %d %d %f 0" % (remote_root_path,"NetCDFCUDAIsosurface.py",tasknum,gpunum,index,datafile,varname,intrange,curtime,isovalue)
            ssh.exec_command(cmd + ' > /dev/null 2>&1 &')
            ssh.close()           
            
        for index,instance_id in enumerate(instance_ids):
            instance = ec2.Instance(instance_id)
            ## ssh      
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                instance.public_dns_name,
                username = 'ubuntu',
                key_filename = AWS_CREDENTIALS['KEY_LOCATION']
            )
            sftp = ssh.open_sftp()            
            for img in img_list[index]:
                img_get = False
                img_get_path = remote_img_path + img
                
                while not img_get:
                    try:
                        print img_get_path
                        print(sftp.stat(img_get_path))
                        print('file exists')
                        sftp.get(img_get_path,local_img_path+img)
                        imgstatinfo = os.stat(local_img_path+img)
                        if imgstatinfo.st_size > 0:
                            img_get = True
                            cmd = "sudo rm %s" % img_get_path
                            ssh.exec_command(cmd + ' > /dev/null 2>&1 &')                        
                    except IOError:
#                        print('file not ready')
                        pass
                    ssh.close()

        ncvrimage = NCVRImage(filepath=local_img_path)
        final_iso_img_file = "iso_%s.png" % datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')
        final_iso_img_file_path = root_path + "img/" + final_iso_img_file
        ncvrimage.MergeImageFromFolder(local_img_path,final_iso_img_file_path,w,h,iso=True)

        response_data = {"newimgfile":final_iso_img_file}
        return HttpResponse(json.dumps(response_data),content_type="application/json")

def writeconfig_iso(request):
    if request.method == 'POST':
        config_txt = request.POST["configtxt"]
        root_path = STORAGE_ROOTPATH
        wwconfig_path = root_path + "wwconfig.txt"
        with open(wwconfig_path,'wb') as f:
            f.write(config_txt)

        conf_new_path = root_path+ "config"
        cfg = StarClusterConfig(conf_new_path)
        cfg.load()
        cluster = cfg.get_cluster_template("geovizcluster")

        tasknum = 16
        if request.POST["tasknum"] and request.POST["tasknum"] != "":
            tasknum = int(request.POST["tasknum"])
        gpunum = int(request.POST["gpunum"])
        datafile = "data/"+request.POST["datafile"]
        varname = "dd"
        if request.POST["varname3d"] and request.POST["varname3d"] != "":
            varname = request.POST["varname3d"]
        intrange = 80
        if request.POST["intrange"] and request.POST["intrange"] !="":
            intrange = int(request.POST["intrange"])
        curtime = 4
        if request.POST["curtime"] and request.POST["curtime"] != "":
            curtime = int(request.POST["curtime"])
        isovale = 0.0000001
        if request.POST["isovalue"] and request.POST["isovalue"] != "":
            isovalue = float(request.POST["isovalue"])

        w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
        wdiv,hdiv = w/gpunum,h/gpunum

        #node_alias_list = []
        img_list = []

        for index,node in enumerate(cluster.nodes):
            #node_alias_list.append(node.alias)
            # send wwconfig file   
            #local_config_path = "/home/bitnami/apps/django/django_projects/geoviz/geoviz/geovizapp/static/data/wwconfig.txt"
            local_config_path = wwconfig_path
            remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"
            node.ssh.switch_user("ubuntu")
            node.ssh.put(local_config_path,remote_config_path)

            imgoutpath = "image/sub/"
            remote_root_path = "/home/ubuntu/CollabViz/"
            remote_img_path = remote_root_path + imgoutpath

            tmp_imgs = []
            eachround = int(math.ceil(tasknum*1.0/gpunum))
            for i in range(index*eachround,(index+1)*eachround):
                if i < tasknum:
                    curgpu = i
                    wrange, hrange = int(i/gpunum),int(i%gpunum)
                    w1,h1 = int(wrange*wdiv),int(hrange*hdiv)
                    w2,h2 = int((wrange+1)*wdiv),int((hrange+1)*hdiv)
                    tmp_imgs.append("%d_%d_%d_%d.png" % (w1,h1,w2,h2))
            img_list.append(tmp_imgs)

            cmd = "sudo DISPLAY=:1 /home/ubuntu/anaconda/bin/python %s%s %d %d %d %s %s %d %d %f 0" % (remote_root_path,"NetCDFCUDAIsosurface.py",tasknum,gpunum,index,datafile,varname,intrange,curtime,isovale)
            node.ssh.execute(cmd,source_profile=False,detach=True)

        local_img_path = root_path+"img/sub/"
        for index,node in enumerate(cluster.nodes):
            for img in img_list[index]:
                img_get = False
                img_get_path = remote_img_path + img
                while not img_get:
                    if node.ssh.isfile(img_get_path):
                        node.ssh.get(img_get_path,local_img_path+img)
                        imgstatinfo = os.stat(local_img_path+img)
                        if imgstatinfo.st_size > 0:
                            img_get = True
                            cmd = "sudo rm %s" % img_get_path
                            node.ssh.execute(cmd,source_profile=False,detach=True)

        ncvrimage = NCVRImage(filepath=local_img_path)
        final_iso_img_file = "iso_%s.png" % datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')
        final_iso_img_file_path = root_path + "img/" + final_iso_img_file
        ncvrimage.MergeImageFromFolder(local_img_path,final_iso_img_file_path,w,h,iso=True)

        response_data = {"newimgfile":final_iso_img_file}
        return HttpResponse(json.dumps(response_data),content_type="application/json")

def writeconfig_iso_animation(request):
    if request.method == 'POST':
        config_txt = request.POST["configtxt"]
        root_path = STORAGE_ROOTPATH
        wwconfig_path = root_path + "wwconfig.txt"
        with open(wwconfig_path,'wb') as f:
            f.write(config_txt)

        conf_new_path = root_path+ "config"
        cfg = StarClusterConfig(conf_new_path)
        cfg.load()
        cluster = cfg.get_cluster_template("geovizcluster")

        tasknum = int(request.POST["tasknum"])
        gpunum = int(request.POST["gpunum"])
        datafile = "data/"+request.POST["datafile"]
        varname = "dd"
        if request.POST["varname3d"] and request.POST["varname3d"] != "":
            varname = request.POST["varname3d"]
        intrange = 40
        vartime = 25
        isovale = 0.0000001
        if request.POST["isovalue"] and request.POST["isovalue"] != "":
            isovalue = float(request.POST["isovalue"])

        w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
        wdiv,hdiv = w/gpunum,h/gpunum

        #node_alias_list = []

        response_final_iso_img_file = "iso_%s" % datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')

        for t in range(vartime):

            img_list = []

            for index,node in enumerate(cluster.nodes):
                #node_alias_list.append(node.alias)
                # send wwconfig file   
                #local_config_path = "/home/bitnami/apps/django/django_projects/geoviz/geoviz/geovizapp/static/data/wwconfig.txt"
                local_config_path = wwconfig_path
                remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"
                node.ssh.switch_user("ubuntu")
                node.ssh.put(local_config_path,remote_config_path)

                imgoutpath = "image/sub/"
                remote_root_path = "/home/ubuntu/CollabViz/"
                remote_img_path = remote_root_path + imgoutpath

                tmp_imgs = []
                eachround = int(math.ceil(tasknum*1.0/gpunum))
                for i in range(index*eachround,(index+1)*eachround):
                    if i < tasknum:
                        curgpu = i
                        wrange, hrange = int(i/gpunum),int(i%gpunum)
                        w1,h1 = int(wrange*wdiv),int(hrange*hdiv)
                        w2,h2 = int((wrange+1)*wdiv),int((hrange+1)*hdiv)
                        tmp_imgs.append("%d_%d_%d_%d.png" % (w1,h1,w2,h2))
                img_list.append(tmp_imgs)

                cmd = "sudo DISPLAY=:1 /home/ubuntu/anaconda/bin/python %s%s %d %d %d %s %s %d %d %f 0" % (remote_root_path,"NetCDFCUDAIsosurface.py",tasknum,gpunum,index,datafile,varname,intrange,t,isovale)
                node.ssh.execute(cmd,source_profile=False,detach=True)

            local_img_path = root_path+"img/sub/"
            for index,node in enumerate(cluster.nodes):
                for img in img_list[index]:
                    img_get = False
                    img_get_path = remote_img_path + img
                    while not img_get:
                        if node.ssh.isfile(img_get_path):
                            node.ssh.get(img_get_path,local_img_path+img)
                            imgstatinfo = os.stat(local_img_path+img)
                            if imgstatinfo.st_size > 0:
                                img_get = True
                                cmd = "sudo rm %s" % img_get_path
                                node.ssh.execute(cmd,source_profile=False,detach=True)

            ncvrimage = NCVRImage(filepath=local_img_path)
            final_iso_img_file = "%s_%d.png" % (response_final_iso_img_file,t)
            final_iso_img_file_path = root_path + "img/" + final_iso_img_file
            ncvrimage.MergeImageFromFolder(local_img_path,final_iso_img_file_path,w,h,iso=True)

        response_data = {"newimgfile":response_final_iso_img_file}
        return HttpResponse(json.dumps(response_data),content_type="application/json")

def writeconfig_flow(request):
    if request.method == 'POST':
        config_txt = request.POST["configtxt"]
        root_path = STORAGE_ROOTPATH
        wwconfig_path = root_path + "wwconfig.txt"
        with open(wwconfig_path,'wb') as f:
            f.write(config_txt)

        conf_new_path = root_path+ "config"
        cfg = StarClusterConfig(conf_new_path)
        cfg.load()
        cluster = cfg.get_cluster_template("geovizcluster")

        tasknum = int(request.POST["tasknum"])
        gpunum = int(request.POST["gpunum"])
        real_gpunum = gpunum
        datafile = "data/"+request.POST["datafile"]
        varname1,varname2 = "u","v"
        if request.POST["varnameflow"] and request.POST["varnameflow"] != "":
            varnameflow = request.POST["varnameflow"].split(",")
            varname1,varname2 = varnameflow[0],varnameflow[1]
        intrange = 80
        tseq = 4
        #if request.POST["tseq"] and request.POST["tseq"] != "":
            #tseq = int(request.POST["tseq"])
        colorselect = "jet"
        if request.POST["colorselect"] and request.POST["colorselect"] != "":
            colorselect = request.POST["colorselect"]
        totalclass = 20
        if request.POST["totalclass"] and request.POST["totalclass"] != "":
            totalclass = int(request.POST["totalclass"])
            
        w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
        wdiv,hdiv = w/gpunum,h/gpunum

        leneles = 24
        if request.POST["leneles"] and request.POST["leneles"] != "":
            if int(request.POST["leneles"]) > 0:
                leneles = int(request.POST["leneles"])
        div = 2
        flowlayers = range(24)
##        if request.POST["flowlayers"] and request.POST["flowlayers"] != "":
##            flowlayers = map(int,request.POST["flowlayers"].split(","))

        #node_alias_list = []
        img_list = []

        for index,node in enumerate(cluster.nodes):
            local_config_path = wwconfig_path
            remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"
            node.ssh.switch_user("ubuntu")
            node.ssh.put(local_config_path,remote_config_path)

        for index in range(gpunum):
            imgoutpath = "image/"
            remote_root_path = "/home/ubuntu/CollabViz/"
            remote_img_path = remote_root_path + imgoutpath

            tmp_imgs = []
            if leneles % int(gpunum) == 0:
                eachlayer = leneles/int(gpunum)
            else:
                eachlayer = leneles/int(gpunum)+1

            for layer in range(index*eachlayer,(index+1)*eachlayer):
                if layer < leneles:
                    if layer in flowlayers:
                        tmp_imgs.append("flow_%d.png" % layer)
            tmp_imgs.append("legend.png")
            img_list.append(tmp_imgs)

        for index in reversed(range(gpunum)):
            cmd = "sudo DISPLAY=:1 /home/ubuntu/anaconda/bin/python %s%s %d %d %s %s %s %d %s %d" % (remote_root_path,"NetCDFCUDAFlow.py",int(gpunum),index,datafile,varname1,varname2,tseq,colorselect,totalclass)
            node = cluster.nodes[index]
            if index == 0:
                node.ssh.execute(cmd,source_profile=False,detach=False)
            else:
                node.ssh.execute(cmd,source_profile=False,detach=True)

        local_img_path = root_path+"img/sub/"
        img_datetime = datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')
        for index,node in enumerate(cluster.nodes):
            for img in img_list[index]:
                img_get = False
                img_get_path = remote_img_path + img
                print "gpu ",index,": fetching ",img_get_path
                while not img_get:
                    if node.ssh.isfile(img_get_path):
                        img_save_path = local_img_path+img
                        if img == "legend.png":
                            img_save_path = root_path + "img/" + "legend_%s.png" % img_datetime
                        node.ssh.get(img_get_path,img_save_path)
                        imgstatinfo = os.stat(img_save_path)
                        if imgstatinfo.st_size > 0:
                            img_get = True
                            cmd = "sudo rm %s" % img_get_path
                            node.ssh.execute(cmd,source_profile=False,detach=True)

        ncvrimage = NCVRImage(filepath=local_img_path)
        final_flow_img_file = "flow_%s.png" % img_datetime
        final_flow_img_file_path = root_path + "img/" + final_flow_img_file
        ncvrimage.OverlayImage(local_img_path,final_flow_img_file_path,w,h)

        response_data = {"newimgfile":final_flow_img_file}
        return HttpResponse(json.dumps(response_data),content_type="application/json")

def writeconfig_flow_animation(request):
    if request.method == 'POST':
        config_txt = request.POST["configtxt"]
        root_path = STORAGE_ROOTPATH
        wwconfig_path = root_path + "wwconfig.txt"
        with open(wwconfig_path,'wb') as f:
            f.write(config_txt)

        conf_new_path = root_path+ "config"
        cfg = StarClusterConfig(conf_new_path)
        cfg.load()
        cluster = cfg.get_cluster_template("geovizcluster")

        tasknum = int(request.POST["tasknum"])
        gpunum = int(request.POST["gpunum"])
        real_gpunum = gpunum
        datafile = "data/"+request.POST["datafile"]
        varname1,varname2 = "u","v"
        if request.POST["varnameflow"] and request.POST["varnameflow"] != "":
            varnameflow = request.POST["varnameflow"].split(",")
            varname1,varname2 = varnameflow[0],varnameflow[1]
        intrange = 80
        tseq = 4
        vartime = 25
        if request.POST["tseq"] and request.POST["tseq"] != "":
            tseq = int(request.POST["tseq"])
        colorselect = "jet"
        if request.POST["colorselect"] and request.POST["colorselect"] != "":
            colorselect = request.POST["colorselect"]
        totalclass = 20
        if request.POST["totalclass"] and request.POST["totalclass"] != "":
            totalclass = int(request.POST["totalclass"])
            
        w,h = int(request.POST["wwwidth"]),int(request.POST["wwheight"])
        wdiv,hdiv = w/gpunum,h/gpunum

        leneles = 24
        if request.POST["leneles"] and request.POST["leneles"] != "":
            if int(request.POST["leneles"]) > 0:
                leneles = int(request.POST["leneles"])
        div = 2
        flowlayers = range(24)
##        if request.POST["flowlayers"] and request.POST["flowlayers"] != "":
##            flowlayers = map(int,request.POST["flowlayers"].split(","))

        img_datetime = datetime.datetime.now().strftime('%Y%m%d%H%H%M%S')
        response_final_flow_img_file = "flow_%s" % img_datetime

        for index,node in enumerate(cluster.nodes):
            local_config_path = wwconfig_path
            remote_config_path = "/home/ubuntu/CollabViz/wwconfig.txt"
            node.ssh.switch_user("ubuntu")
            node.ssh.put(local_config_path,remote_config_path)

        for t in range(vartime):
            #node_alias_list = []
            img_list = []
            for index in range(gpunum):
                imgoutpath = "image/"
                remote_root_path = "/home/ubuntu/CollabViz/"
                remote_img_path = remote_root_path + imgoutpath

                tmp_imgs = []
                if leneles % int(gpunum) == 0:
                    eachlayer = leneles/int(gpunum)
                else:
                    eachlayer = leneles/int(gpunum)+1

                for layer in range(index*eachlayer,(index+1)*eachlayer):
                    if layer < leneles:
                        if layer in flowlayers:
                            tmp_imgs.append("flow_%d.png" % layer)
                tmp_imgs.append("legend.png")
                img_list.append(tmp_imgs)
                
            for index in reversed(range(gpunum)):
                cmd = "sudo DISPLAY=:1 /home/ubuntu/anaconda/bin/python %s%s %d %d %s %s %s %d %s %d" % (remote_root_path,"NetCDFCUDAFlow.py",int(gpunum),index,datafile,varname1,varname2,t,colorselect,totalclass)
                node = cluster.nodes[index]
                if index == 0:
                    node.ssh.execute(cmd,source_profile=False,detach=False)
                else:
                    node.ssh.execute(cmd,source_profile=False,detach=True)

            local_img_path = root_path+"img/sub/"

            for index,node in enumerate(cluster.nodes):
                for img in img_list[index]:
                    img_get = False
                    img_get_path = remote_img_path + img
                    print "gpu ",index,": fetching ",img_get_path
                    while not img_get:
                        if node.ssh.isfile(img_get_path):
                            img_save_path = local_img_path+img
                            if img == "legend.png":
                                img_save_path = root_path + "img/" + "legend_%s.png" % img_datetime
                            node.ssh.get(img_get_path,img_save_path)
                            imgstatinfo = os.stat(img_save_path)
                            if imgstatinfo.st_size > 0:
                                img_get = True
                                cmd = "sudo rm %s" % img_get_path
                                node.ssh.execute(cmd,source_profile=False,detach=True)

            ncvrimage = NCVRImage(filepath=local_img_path)
            final_flow_img_file = "%s_%d.png" % (response_final_flow_img_file,t)
            final_flow_img_file_path = root_path + "img/" + final_flow_img_file
            ncvrimage.OverlayImage(local_img_path,final_flow_img_file_path,w,h)

        response_data = {"newimgfile":response_final_flow_img_file}
        return HttpResponse(json.dumps(response_data),content_type="application/json")

def request_cluster(request):
    gpunum = request.POST["gpunum"]
    csrftoken = request.POST["csrfmiddlewaretoken"]
    journal = request.POST["journal"]
    email = request.POST["email"]
    gpunum = request.POST["gpunum"]
    hours = request.POST["hours"]
    sdate = request.POST["sdate"]
    stime = request.POST["stime"]   
    
    response_data = {"secretkey":csrftoken,"gpunum":gpunum}
    
    # send email to admin
    email_msg = "New cluster request for %s GPU instances\n" % gpunum + \
                "at 52.26.239.116/geoviz/geoviz/launchcluster/%s/ \n" % csrftoken + \
                "Journal: %s \n" % journal + \
                "Email: %s \n" % email + \
                "Scheduled Time: %s %s \n" % (sdate,stime) + \
                "Access Hours: %s hrs" % hours
                
    email_list = [ADMIN_EMAIL_ADDRESS,"liu.qing.1984@gmail.com","Jing.Li145@du.edu"]
    #email_list = ["liu.qing.1984@gmail.com"]

    email_content = {"subject":"[ClusterRequest] New Cluster Request: ID = %s" % csrftoken,
                     "message":email_msg,
                     "from": ADMIN_EMAIL_ADDRESS,
                     "to": email_list
                    }
    send_mail(email_content['subject'],email_content['message'],email_content['from'],email_content['to'])

    # send email confirmation to reviewer
    email_msg_2 = "Thank you for submitting the request.\nA cluster request for %s GPU instances has been submitted.\n\n" % gpunum + \
                  "Request Information:\n" + \
                  "Journal: %s \n" % journal + \
                  "Email: %s \n" % email + \
                  "Scheduled Time: %s %s \n" % (sdate,stime) + \
                  "Access Hours: %s hrs\n\n" % hours + \
                  "We will send you another email later when the scheduled GPU cluster is ready for use.\n\nBest Regards,\nGeoViz Team"

    email_list_2 = [email]

    email_content_2 = {"subject":"[GeoViz] New Cluster Request Confirmation",
                       "message":email_msg_2,
                       "from": ADMIN_EMAIL_ADDRESS,
                       "to": email_list_2
                      }
    send_mail(email_content_2['subject'],email_content_2['message'],email_content_2['from'],email_content_2['to'])

    return HttpResponse(json.dumps(response_data),content_type="application/json")

def get_opendap(request):
    csrftoken = request.POST["csrfmiddlewaretoken"]
    data_url = request.POST["opendapurl"]
    
    root_path = STORAGE_ROOTPATH    
    file_name = data_url.split('/')[-1]+".nc"
    save_data_path = root_path + file_name
    u = urllib2.urlopen(data_url)
    with open(save_data_path,'wb') as f:
        f.write(u.read())
    response_data = {"file_name":file_name,"data_url":data_url}

    return HttpResponse(json.dumps(response_data),content_type="application/json")

@render_to("geovizapp/launchcluster.html")
def launch_cluster(request,secretgpunum,secretkey):
    varlist = json.dumps(["acp","hgt","alp"])
    var3dlist = json.dumps(["delt","dl","sc","dd","dw","dflx"])
    var3dlistflow = json.dumps(["uh,vh","zhyb","omg","rr","dc"])
    return {"gpunum":secretgpunum,"varlist":varlist,"var3dlist":var3dlist,"var3dlistflow":var3dlistflow}

@render_to("geovizapp/launchcluster_key.html")
def launch_cluster_key(request,secretkey):
    varlist = json.dumps(["acp","hgt","alp"])
    var3dlist = json.dumps(["delt","dl","sc","dd","dw","dflx"])
    var3dlistflow = json.dumps(["uh,vh","zhyb","omg","rr","dc"])
    return {"gpunum":secretgpunum,"varlist":varlist,"var3dlist":var3dlist,"var3dlistflow":var3dlistflow}

def writeconfig(request):
    if request.method == 'POST':
        config_txt = request.POST["configtxt"]
        root_path = "C:/QLiu/RemoteVizNow/NOW_geoviz/"
        wwconfig_path = root_path + "wwconfig.txt"
        with open(wwconfig_path,'wb') as f:
            f.write(config_txt)
        os.remove(wwconfig_path)
        return HttpResponse()    

# Check server status
def server_status(instance):
    instance_status = instance.state["Name"]
    while instance_status != "running":
        time.sleep(10)
        instance.reload()
        instance_status = instance.state["Name"]
    print instance_status
    return instance_status

# Check server terminating status
def server_terminate_status(instance):
    instance_status = instance.state["Name"]
    while instance_status != "shutting-down":
        time.sleep(10)
        instance.reload()
        instance_status = instance.state["Name"]
    print instance_status
    return instance_status

@login_required
def start_cluster(request):
    if request.method == 'POST':
        csrfmiddlewaretoken = request.POST["csrfmiddlewaretoken"]
        print "start: " , csrfmiddlewaretoken
        
        gpu_region = request.POST["gpuregion"]
        gpu_type = request.POST["gputype"]
        gpu_num = int(request.POST["gpunum"])
        
        print gpu_region
        print gpu_type
        print gpu_num
        
        # Comment below for testing
        
        # create a cluster object in database, saving cluster and instance info
        cluster, created = Cluster.objects.get_or_create(csrf_token=csrfmiddlewaretoken)
        if created:
            cluster.save()
        else:
            cluster.instances.clear()
        cluster.csrf_token = csrfmiddlewaretoken    
        
        # start AWS session
        aws_session = Boto3Session(
                        aws_access_key_id=AWS_CREDENTIALS['ACCESS_KEY_ID'],
                        aws_secret_access_key=AWS_CREDENTIALS['SECRET_ACCESS_KEY'],
                        region_name=gpu_region
                      )
        client = aws_session.client('ec2')
        ec2 = aws_session.resource('ec2',region_name=gpu_region)
        # create EC2 instances
        gpu_cluster = ec2.create_instances(
            ImageId=AWS_CREDENTIALS['GPU_TEMPLATE_AMI'],
            MinCount=1,
            MaxCount=gpu_num,
            KeyName = AWS_CREDENTIALS['Key_Name'],
            SecurityGroups = [g['name'] for g in AWS_CREDENTIALS['SECURITY_GROUPS']],
            SecurityGroupIds = [g['id'] for g in AWS_CREDENTIALS['SECURITY_GROUPS']],
            InstanceType = gpu_type)
        print "DONE!"

        for index,gc in enumerate(gpu_cluster):
            print "initiating instance id: ", gc.id
            instance = Instance(
                region = gpu_region,
                type = gpu_type,
                ami = AWS_CREDENTIALS['GPU_TEMPLATE_AMI'],
                instance_id = gc.id                
            )
            instance.save()
            cluster.instances.add(instance)            
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
                            'Value': "Session '%s' GPU Cluster Instance #%d" % (csrfmiddlewaretoken,index+1)
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
                
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    gc.public_dns_name,
                    username = 'ubuntu',
                    key_filename = AWS_CREDENTIALS['KEY_LOCATION']
                )                
                cmd = "sudo /usr/bin/X :1 && screen"
                ssh.exec_command(cmd + ' > /dev/null 2>&1 &')
#                cmd = "sudo DISPLAY=:1 /home/ubuntu/anaconda/bin/python /home/ubuntu/CollabViz/test_server.py"
#                ssh.exec_command(cmd + ' > /dev/null 2>&1 &')        
                      
        
        # save cluster info in database
        cluster.save()

        # <--- End of comment
        
        response_data = {}
    
    return HttpResponse(json.dumps(response_data),content_type="application/json")

@login_required
def terminate_cluster(request):
    if request.method == 'POST':
        csrfmiddlewaretoken = request.POST["csrfmiddlewaretoken"]
        print "terminate: ", csrfmiddlewaretoken
                
        gpu_region = request.POST["gpuregion"]
        gpu_type = request.POST["gputype"]
        gpu_num = int(request.POST["gpunum"])

        print gpu_region
        print gpu_type
        print gpu_num
        
        # Comment below for testing
        
        # get cluster info from database 
        cluster = Cluster.objects.get(csrf_token=csrfmiddlewaretoken)
        instance_ids = []
        for i in cluster.instances.all():
            print i.instance_id
            instance_ids.append(i.instance_id)
        
        aws_session = Boto3Session(
                        aws_access_key_id=AWS_CREDENTIALS['ACCESS_KEY_ID'],
                        aws_secret_access_key=AWS_CREDENTIALS['SECRET_ACCESS_KEY'],
                        region_name=gpu_region
                      )
        ec2 = aws_session.resource('ec2',region_name=gpu_region)
        if instance_ids:
            print instance_ids
            ec2.instances.filter(InstanceIds = instance_ids).terminate()
        
        for instance_id in instance_ids:
            instance = ec2.Instance(instance_id)
            instance_status = instance.state["Name"]
            print instance_status
            while instance_status != "terminated":
                time.sleep(10)
                instance.reload()
                instance_status = instance.state["Name"]
                
        # <--- End of comment
    
    response_data = {}

    return HttpResponse(json.dumps(response_data),content_type="application/json")