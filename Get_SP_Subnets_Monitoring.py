#
#   This program should pull the list of subnets from the Orchestrator for a particular EdgeConnect device using the following API call:
#   https://mgosporchp1:443/gms/rest/subnets/true/17.NE?source=menu_rest_apis_id   {17.NE in this example is the device code for MGO-TESTSITE1-SP1}
#
#   This call must be authenticated.
#   Once it has the list it should store it and then next time it is run it should compare the lists of subnets to see if anythihg has changed.
#   If there has been a change (add or subtract) it should email me with that information.
#
#   not needed at the end of the api_url = +"?source=menu_rest_apis_id"
import smtplib, jinja2, datetime, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from SPOrchestrator import SPOrchestrator
from pprint import pprint
from sqlHelper import sql

def orch_get_subnet_info(orch_ip, ec_id, cached="true", debug=False): 
    #orch_ip = the IP address of the target Orchestrator
    #ec_id = the ??.NE device ID of the target EdgeConnect
    #If cached = true then it will use the subnet list from Orchestrator.
    #If it is false it will pull a new list directly from the specified EC.
    
    #create an instance of SPOrchestrator
    sp_orch = SPOrchestrator(ipaddress=orch_ip, user="admin", password="Trisf2hfm!", debug=debug)
    #authenticate to spOrch
    sp_orch.login()

    api_url = "/subnets/"+cached+"/"+ec_id
    if debug:
        print(f'The API URL used is: {api_url}\n')

    #query the Orchestrator for the subnet information
    Results = sp_orch.get(url=api_url)
    if debug:
        print(f'Status code: {Results.status_code}\n')
        pprint(Results.headers)
        print(f'\nContent: {Results.content}')
    
    #close the connection
    sp_orch.logout()
    return Results

def process_subnets(Results, debug=False, interface="all"):
    #Figures out what the source AS is for each subnet
    list_of_subnets = []
    Subnet_Dict = Results.json()
    for Subnet in Subnet_Dict['subnets']['entries']:
        item = {}
        if interface == "all":
            if debug:
                print(f"current subnet = {Subnet['state']['prefix']}")
            item['subnet'] = Subnet['state']['prefix']
            source_as = Subnet['state']['aspath'].split(',')  #break up the aspath item so we can grab the first entry
            if debug:
                print(f"current source as = {source_as[0]}")
            if source_as[0] == "":
                item['source_as'] = 0
            else:
                item['source_as'] = int(source_as[0])
            list_of_subnets.append(item)
        elif Subnet['state']['ifName'] == interface:
            item['subnet'] = Subnet['state']['prefix']
            source_as = Subnet['state']['aspath'].split(',')
            item['source_as'] = int(source_as[0])
            list_of_subnets.append(item)
    return list_of_subnets

def db_get_table_data(db_connection, table="monitor_subnets", debug=False):
    q_get_table_data = db_connection.query("select * from "+table+";")
    q_get_table_data_result = db_connection.getAllRows(q_get_table_data)
    return q_get_table_data_result

def db_build_data_push_to_table(list_of_dicts, db_connection, table="monitor_subnets", debug=False):
    temp_list = []
    for data_row in list_of_dicts:
        temp_list.append(db_connection.prepareInsert(data_row, table))
    return temp_list

def db_execute_push_to_table(q_list, db_connection, debug=False):
    number_of_lines = 0
    errors = 0
    for data_row in q_list:
        affected = db_connection.execute(data_row)
        if debug:
            print(f'Return from execute funcion is {affected}')
        if affected == 0:
            errors += 1
        else:
            number_of_lines += affected
    if debug:
        print(f'Number of execute errors (assumed duplicate) = {errors}')
        print(f'The number of rows pushed to the database is {number_of_lines}')
    return number_of_lines

def db_update_list_of_subnets(orch_ip, ec_id, cached="true", debug=False):
    #not currently used for anything
    #pulls the list from Orchestrator, processes it and pushes it to the monitor_subnets table
    #Get the list of subnets from Orchestrator
    orch_results = orch_get_subnet_info(orch_ip, ec_id, cached, debug)
    #put the results in the format I want
    list_of_subnets = process_subnets(orch_results, debug, interface="all")
    #Build the data to insert into the db
    push_to_table = db_build_data_push_to_table(list_of_subnets, kaosdb_connection)
    #Execute the db insert
    number_of_rows = db_execute_push_to_table(push_to_table, kaosdb_connection, debug)
    print(f'The number of rows pushed to the database is {number_of_rows}')
    return number_of_rows

def db_inc_down_count_subnet_missing():
    #Query update monitor_subnets, sla_locations set down_count = down_count + 1 where (source_as = asNum AND NOT in <passed list of subnets>);
    return

def db_zero_down_count_subnet_exists():
    #Query update monitor_subnets, sla_locations set down_count = down_count + 1 where (source_as = asNum AND in <passed list of subnets>);
    return

def db_alert_down_count_equal_number(count):
    #count is the number of times we should see the subnet missing before we alert
    return

def send_alert_email(message, to_address="brian.wredberg@genmills.com"):
    #message is the email body of the alert to be sent
    #to_address is where the email will be sent
    msg = MIMEMultipart()
    msg['Subject'] = f'XXXXXXXX'
    msg['From'] = "noreply@vm-mgo-g528525l.genmills.com"
    msg['To'] = to_address
    msg.attach(MIMEText(message, 'html'))
    s = smtplib.SMTP('mail.genmills.com')
    s.send_message(msg)
    s.quit()
    return

kaosdb_connection = sql(dbUser="admin", dbPassword="Trisf2hfm")
#Lab_Orch_IP = "172.16.216.81"
Prod = "172.16.219.243"
#MGO_SPLAB_SPR1 = "0.NE"
#MGO_TESTSITE_SPR1 = "17.NE"
#MGO_TESTSITE_SPR2 = "18.NE"
#AUMLSPR1 = "68.NE"
MGOSPR1 = "10.NE"
#JDCSPR1 = "11.NE"

#Step 1 get the list of subnets and update the database
db_update_list_of_subnets(Prod, MGOSPR1, debug=False)


