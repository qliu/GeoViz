from django.db import models

GPU_CHOICES = ((1,1),(2,2),(4,4),(8,8))
HOUR_CHOICES = ((1,1),(2,2),(3,3),(4,4))

class Instance(models.Model):
#    id =  models.IntegerField(primary_key=True)
    region = models.CharField(max_length=100,null=True,blank=True)
    type = models.CharField(max_length=100,null=True,blank=True)
    ami = models.CharField(max_length=100,null=True,blank=True)
    instance_id = models.CharField(max_length=100,null=True,blank=True)
 
    def __unicode__(self):
        return self.instance_id
    
    class Meta:
        db_table = u'instance'
        
class Cluster(models.Model):
#    id =  models.IntegerField(primary_key=True)
    csrf_token = models.CharField(max_length=100,null=True,blank=True)
    instances = models.ManyToManyField('Instance',null=True,blank=True)
 
    def __unicode__(self):
        return self.csrf_token
    
    class Meta:
        db_table = u'cluster'