from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib.auth.views import logout

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('geovizapp.views',
	# Home page URL
	url(r'^home/$','home'),
	url(r'^geovizcloud/$','geovizcloud'),
	url(r'^geovizcloud/demo/$','demo_page'),
	url(r'^runtest/$','runtest'),

	# Load data
	url(r'loaddata/$','loaddata'),
	# Write Config
	url(r'writeconfig_2d/$','writeconfig_2d_new'),
	url(r'writeconfig_ray/$','writeconfig_ray_new'),
	url(r'writeconfig_ray_animation/$','writeconfig_ray_animation_new'),
	url(r'writeconfig_iso/$','writeconfig_iso_new_2'),
	url(r'writeconfig_iso/animation/$','writeconfig_iso_animation'),
	url(r'writeconfig_flow/$','writeconfig_flow'),
	url(r'writeconfig_flow/animation/$','writeconfig_flow_animation'),
	
	# Write Config
	url(r'writeconfig/$','writeconfig'),
	
	# Start Cluster
	url(r'requestcluster/$','request_cluster'),
	url(r'launchcluster/(?P<secretkey>\w+)/$','launch_cluster_key'),
	url(r'launchcluster/(?P<secretgpunum>\d+)-(?P<secretkey>\w+)/$','launch_cluster'),
	url(r'startcluster/$','start_cluster'),
	url(r'terminatecluster/$','terminate_cluster'),
	
	# Get OPeNDAP
	url(r'getopendap/$','get_opendap'),
)
