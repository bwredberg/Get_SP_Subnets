#
#   This program should pull the list of subnets from the Orchestrator for a particular EdgeConnect device using the following API call:
#   https://mgosporchp1:443/gms/rest/subnets/true/17.NE?source=menu_rest_apis_id   {17.NE in this example is the device code for MGO-TESTSITE1-SP1}
#
#   This call must be authenticated.
#   Once it has the list it should store it and then next time it is run it should compare the lists of subnets to see if anythihg has changed.
#   If there has been a change (add or subtract) it should email me with that information.
#
#import sys
#sys.path.insert(1, '/home/g528525/python/network-iac-helpers')
from SPOrchestrator import SPOrchestrator
import smtplib, jinja2, datetime, time, requests
from pprint import pprint
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

Lab = "172.16.216.81"
Prod = "172.16.219.243"

Target_Device = "0.NE"  #This is MGO-SPLAB-SPR1
API_URL = "https://"+Lab+":443/gms/rest/subnets/true/"+Target_Device+"?source=menu_rest_apis_id"
#print(API_URL)

SP = SPOrchestrator(ipaddress=Lab, user="admin", password="Trisf2hfm!", debug=False)
SP.login()
SP.loginStatus()

Results = requests.get(API_URL, verify=False)
print(f'Status code: {Results.status_code}')
#pprint(f'Headers: {Results.headers}')
print(f'Content: {Results.content}')

#Subnets = Results
#print(Subnets)

SP.logout()
