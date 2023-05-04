#
#   This program should pull the list of subnets from the Orchestrator for a particular EdgeConnect device using the following API call:
#   https://mgosporchp1:443/gms/rest/subnets/true/17.NE?source=menu_rest_apis_id   {17.NE in this example is the device code for MGO-TESTSITE1-SP1}
#
#   This call must be authenticated.
#   Once it has the list it should store it and then next time it is run it should compare the lists of subnets to see if anythihg has changed.
#   If there has been a change (add or subtract) it should email me with that information.
#
#import smtplib, jinja2, datetime, time
#from email.mime.text import MIMEText
#from email.mime.multipart import MIMEMultipart

from SPOrchestrator import SPOrchestrator
from pprint import pprint
import csv, requests

def get_core_list_from_API(debug=False):
    #From Dan's lab environment
    Core_List_Result = requests.get(url="https://vl-kaosdev01:8443/rest/v1/gmi-core", verify=False)
    Core_List = Core_List_Result.json()
    if debug:
        print(f'Result = {Core_List_Result}')
        print(f'Core_List = {Core_List["result"]}')
    return Core_List

def get_core_list_from_csv():
    file_temp = []
    Core_list = []

    with open("/home/g528525/python/Get_SP_Subnets/core_list.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            file_temp.append(row)

    for file in file_temp:
        temp_dict = {}
        temp_dict["core"] = file[0]
        temp_dict["asNum"] = file[2]
        Core_list.append(temp_dict)
    return Core_list

def get_subnet_info(orchIP, ecID, cached="true", debug=False): 
    #orchIP = the IP address of the target Orchestrator
    #ecID = the ??.NE device ID of the target EdgeConnect
    #If cached = true then it will use the subnet list from Orchestrator.
    #If it is false it will pull a new list directly from the specified EC.
    #create an instance of SPOrchestrator
    spOrch = SPOrchestrator(ipaddress=orchIP, user="admin", password="Trisf2hfm!", debug=debug)
    #authenticate to spOrch
    spOrch.login()

    api_url = "/subnets/"+cached+"/"+ecID+"?source=menu_rest_apis_id"
    if debug:
        print(f'The API URL used is: {api_url}\n')

    #query the Orchestrator for the subnet information
    Results = spOrch.get(url=api_url)
    if debug:
        print(f'Status code: {Results.status_code}\n')
        pprint(Results.headers)
        print(f'\nContent: {Results.content}')
    
    #close the connection
    spOrch.logout()
    return Results

def process_subnets(Results, Core_List, interface="all", debug=False):
    #Figures out what the source AS is for each subnet
    #Compares the source AS against the list of known cores and identifies which core it originated on
    #Results = the json results from the API call
    list_of_prefixes = []
    Subnet_Dict = Results.json()
    for Subnet in Subnet_Dict['subnets']['entries']:
        item = {}
        if interface == "all":
            if 'peername' in Subnet['state']:
                item['peername'] = Subnet['state']['peername']
            else:
                item['peername'] = ""
            item['prefix'] = Subnet['state']['prefix']
            item['aspath'] = Subnet['state']['aspath']
            item['ifname'] = Subnet['state']['ifName']
            source_as = Subnet['state']['aspath'].split(',')  #break up the aspath item so we can grab the first entry
            item['source_as'] = source_as[0]
            item['source_core'] = "None Identified"  #default to "None", if one is found it will overwrite
            for core in Core_List['result']:
                if debug:
                    print(core)
                    #print(f'core["asNum"] = {core["asNum"]}')
                    #print(f'core name is {core["core"]}')
                if item["source_as"] == str(core["asNum"]):
                    item['source_core'] = core["core"]
                    break
            list_of_prefixes.append(item)
        elif Subnet['state']['ifName'] == interface:
            if 'peername' in Subnet['state']:
                item['peername'] = Subnet['state']['peername']
            else:
                item['peername'] = ""
            item['prefix'] = Subnet['state']['prefix']
            item['aspath'] = Subnet['state']['aspath']
            item['ifname'] = Subnet['state']['ifName']
            source_as = Subnet['state']['aspath'].split(',')
            item['source_as'] = source_as[0]
            item['source_core'] = "None Identified"
            for core in Core_List['result']:
                if item["source_as"] == str(core["asNum"]):
                    item['source_core'] = core["core"]
                    break
            list_of_prefixes.append(item)
    return list_of_prefixes

Lab_Orch_IP = "172.16.216.81"
Prod = "172.16.219.243"
MGO_SPLAB_SPR1 = "0.NE"
MGO_TESTSITE_SPR1 = "17.NE"
MGO_TESTSITE_SPR2 = "18.NE"
AUMLSPR1 = "68.NE"
MGOSPR1 = "10.NE"
JDCSPR1 = "11.NE"

Target_Device = MGO_TESTSITE_SPR1

#howdy = get_core_list_from_API()
#pprint(howdy['result'])

list_of_prefixes = process_subnets(get_subnet_info(orchIP=Prod, ecID=Target_Device, cached="true", debug=False), get_core_list_from_API(), interface="all", debug=False)

pprint(list_of_prefixes)
