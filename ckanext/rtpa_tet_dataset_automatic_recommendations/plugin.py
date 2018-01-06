import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.base import BaseController
from logging import getLogger
from ckan.plugins.toolkit import Invalid
from ckan.lib.base import BaseController
from ckan.common import json, response, request
#from ckan.common import config as cf
import ckan.model as model
import os
import urllib2
from ckan.lib.base import c, g, h


def get_recommended_datasets(pkg_id):
    package = toolkit.get_action('package_show')(None, {'id': pkg_id.strip()})
    response_data  = {}
    testApi="http://vmrtpa05.deri.ie:8006/get/"
    useApi=True
    #useApi=cf.get(
    #    'ckan.extensions.rtpa_tet_dataset_automatic_recommendations.use_rtpa_api', None)
    if "linked_datasets" in package and package["linked_datasets"] != "":
        l = []
        pkgs = package["linked_datasets"].split(",")
        for pkg in pkgs:
            #log.debug("PKG_ID:"+pkg_id)
            #log.debug("type of:"+str(type(pkg_id)))
            p = toolkit.get_action('package_show')(None, {'id': pkg})
            item = {}
            item ["name"] = pkg
            item ["title"] = p["title"]
            item ["notes"] = p["notes"]
            l.append(item)
            response_data["datasets"] = l
    #if not ("linked datasets" in package and package["linked_datasets"] !="") :
        #response_data={}
    else:
        q= ''
        category_string = ''
        taget_audience_string = ''

        if "category" in package and not package["category"] == "" : category_string = "category:\"" + package["category"] + "\"~25"
        if "target_audience" in package and not package["target_audience"] == "" : taget_audience_string = "target_audience:\"" + package["target_audience"] + "\"~25"

        if (category_string and taget_audience_string):
            q = category_string + " OR " + taget_audience_string
        elif (category_string):
            q = category_string
        elif (taget_audience_string):
            q = taget_audience_string

        data_dict = {
            'qf':'target_audience^4 category^4 name^4 title^4 tags^2 groups^2 text',
            'q': q,
            'rows': 5
        }
        #log.debug(q)
        response_data["datasets"] = toolkit.get_action('package_search')(None, data_dict)["results"]
        for ds in response_data["datasets"]:
            if ds["name"] == pkg_id:
                response_data["datasets"].remove(ds)
    
    if(useApi): #TODO Add switch option
        relateddatasets=[]
        url=testApi+package["id"]+"/3"
        data=json.loads(urllib2.urlopen(url).read())
        i=0
        for element in data['result']:
            item={}
            item["name"]=element['id']
            item["title"]=element['title']
            item["notes"]="Description of dataset"
            relateddatasets.append(item)
            i+=1
            if(i>10):
                break
        print(relateddatasets)

        response_data["datasets"]=relateddatasets

    return response_data



class Rtpa_Tet_Dataset_Automatic_RecommendationsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer


    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'rtpa_tet_dataset_automatic_recommendations')
        
    @staticmethod
    def after_map(m):
         m.connect('get_recommended_datasets', '/api/3/util/tet/get_recommended_datasets',
           controller='ckanext.rtpa_tet_dataset_automatic_recommendations.plugin:RtpaApi', action='get_recommended_datasets')
         return m

     #ITemplateHelpers
    def get_helpers(self):
        return {'get_recdat': get_recommended_datasets }

#IPackageController

    def before_index(self, pkg_dict):
        return pkg_dict


        
        
class RtpaApi(BaseController):
    def get_recommended_datasets(self):
        response.content_type = 'application/json; charset=UTF-8'
        pkg_id = request.params["pkg"]
        data = get_recommended_datasets(pkg_id)
        return json.dumps(data)
