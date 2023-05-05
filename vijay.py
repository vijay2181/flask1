import os
import boto3
import re
import time
import pymsteams
import sys

# List of target services
#target_services = ["crud", "rc"]

#sys.stdout.flush()
# Get the list of arguments passed to the script
target_services = sys.argv[1:]

values = "rcx --backend RCX-Dev7 --tenant Sandbox --aws-profile dev7"
profile = values.split('--aws-profile ')[1].split()[0]

# Extracting backend value
backend = values.split("--backend ")[1].split(" ")[0]

# Extracting tenant value
tenant = values.split("--tenant ")[1].split(" ")[0]

#teams webhook connector
#myTeamsMessage = pymsteams.connectorcard("https://vijay.com")

myTeamsMessage = pymsteams.connectorcard("67f2237b-a1c1-4205-9ade-b28b26365c98")

final_msg=[]

# Set the AWS profile and Create an ECS client
session = boto3.Session(profile_name=profile)
ecs = session.client('ecs')

# List all clusters
clusters = []
next_token = ''
while True:
    try:
        response = ecs.list_clusters(nextToken=next_token)
        clusters += response['clusterArns']
        if 'nextToken' not in response:
            break
        next_token = response['nextToken']
    except Exception as e:
        print(f"Error listing clusters: {e}")
        exit()

# Print the total number of clusters
total_clusters = len(clusters)
print(f"Total number of clusters: {total_clusters}")
sys.stdout.flush()

# Print the cluster names
cluster_list = [cluster_arn.split('/')[-1] for cluster_arn in clusters]
print(f"PERFORMING REFRESH ACTIVITY ON {backend} {tenant} FOR {target_services} SERVICES")
sys.stdout.flush()
print(f"########################################################################################################")
sys.stdout.flush()

for service in target_services:
    sys.stdout.flush()
    # Blue target service info
    def blue_service(values,service):
        info = os.popen(f"{values} service info -t Blue {service}").read().strip()
        return info

    # Green target service info
    def green_service(values,service):
        info = os.popen(f"{values} service info -t Green {service}").read().strip()
        return info
    #msg1
    #teams_msg1=f"Performing Refresh Activity in {backend} {tenant} on **{service}**"
    print(f"Proceeding with {service} service")
    sys.stdout.flush()
    final_msg.append(f"Performing Refresh Activity in {backend} {tenant} on ***{service}***")

    # Get blue_service and filter variables
    print(f"****** Checking Blue Target for {service} service ******")
    sys.stdout.flush()


    #1st execute blue_service_info
    blue_service=blue_service(values,service)

    if blue_service=='Service does not exist':
        print(f'{service} service does not exist on Blue Target')
        sys.stdout.flush()
        #msg2
        #teams_msg2=f"**{service}** Blue does not exist in {backend} {tenant} "
        final_msg.append(f"***{service}*** Green does not exist in {backend} {tenant}")
    else:
        blue_service=blue_service.split()
        blue_service_name = blue_service[0]

        if '-EC2-' in blue_service_name:
            filter_variable = blue_service_name.split('-EC2-')[0]
        elif '-cAdvisor-' in blue_service_name:
            filter_variable = blue_service_name.split('-cAdvisor-')[0]
        else:
            filter_variable = blue_service_name

        print('service:', blue_service_name)
        sys.stdout.flush()
        print('filters:', filter_variable)
        sys.stdout.flush()

        # Find the cluster that matches the filter pattern
        blue_cluster_name = None
        pattern = f"{filter_variable}*-Cluster-*"
        for cluster in cluster_list:
            if re.match(pattern, cluster):
                blue_cluster_name = cluster
                break

        if blue_cluster_name is None:
            print("Error: cluster not found")
            sys.stdout.flush()
            exit()

        print('cluster:', blue_cluster_name)
        sys.stdout.flush()

        # Get the service details
        try:
            response = ecs.describe_services(
                cluster=blue_cluster_name,
                services=[blue_service_name]
            )
        except Exception as e:
            print(f"Error describing service: {e}")
            sys.stdout.flush()
            exit()

        # Extract the desired count, pending count, and running count from the service details
        service_details = response['services'][0]
        blue_desired_count = service_details.get('desiredCount', 0)
        blue_pending_count = service_details.get('pendingCount', 0)
        blue_running_count = service_details.get('runningCount', 0)

        # Print the  blue results
        print(f"Blue Desired count: {blue_desired_count}")
        sys.stdout.flush()
        print(f"Blue Pending count: {blue_pending_count}")
        sys.stdout.flush()
        print(f"Blue Running count: {blue_running_count}")
        sys.stdout.flush()

        #os.system(f'{values} service status {service}')
        #status=os.popen(f"{values} service status {service}").read().strip()
        #print(status)

        #checking blue service is up or not
        if blue_desired_count==0 and blue_running_count==0:
            print(f"{service} service is not running currently in Blue")
            sys.stdout.flush()
        else:
            time.sleep(5)
            #stopping blue service
            print(f"stopping {service} service on Blue Target")
            sys.stdout.flush()
            #os.system(f'echo y | {values} service stop -t Blue {service}')
            #echo y | rcx --backend RCX-Dev7 --tenant Sandbox --aws-profile dev7 service start crud > /dev/null
            os.system(f'echo y | {values} service stop -t Blue {service} > blue-stop.txt')
            sys.stdout.flush()
            #time.sleep(30)

            #recursive_function_to_stop_service_on_blue_target
            def stop_repeat_until(condition,blue_cluster_name,blue_service_name,myTeamsMessage,final_msg):
                #teams_msg3 = ''  # initialize with default value
                response = ecs.describe_services(
                    cluster=blue_cluster_name,
                    services=[blue_service_name]
                )
                service_details = response['services'][0]
                blue_desired_count = service_details.get('desiredCount', 0)
                condition = service_details.get('runningCount', 0)
                if condition == 0 and blue_desired_count == 0:
                    print(f'{service} service is stopped on Blue Target')
                    sys.stdout.flush()
                    #msg3
                    #teams_msg3=f"**{service}** Blue is **STOPPED** in {backend} {tenant} "
                    #final_msg.append(teams_msg3)
                    time.sleep(5)
                    #os.system(f'{values} service status {service}')
                    #status=os.popen(f"{values} service status {service}").read().strip()
                    #print(status)
                else:
                    # Code to be repeated
                    time.sleep(30)
                    # Call the function again with the same condition
                    stop_repeat_until(condition,blue_cluster_name,blue_service_name,myTeamsMessage,final_msg)
                #return teams_msg3
            # Call the function with a condition that will eventually be met
            stop_repeat_until('blue_count',blue_cluster_name,blue_service_name,myTeamsMessage,final_msg)
            final_msg.append(f"***{service}*** Blue is ***STOPPED*** in {backend} {tenant}")

            time.sleep(5)
            #starting blue service
            print(f"starting {service} service on Blue Target")
            sys.stdout.flush()
            time.sleep(5)
            #os.system(f'echo y | {values} service start -t Blue {service}')
            os.system(f'echo y | {values} service start -t Blue {service} > blue-start.txt')
            sys.stdout.flush()
            #time.sleep(30)

            #recursive_function_to_start_service_on_blue_target
            def start_repeat_until(condition,blue_running_count,blue_cluster_name,blue_service_name,myTeamsMessage,final_msg):
                #teams_msg4 = ''  # initialize with default value
                response = ecs.describe_services(
                    cluster=blue_cluster_name,
                    services=[blue_service_name]
                )
                service_details = response['services'][0]
                condition = service_details.get('runningCount', 0)
                if blue_running_count==condition:
                    print(f'{service} service is started on Blue Target')
                    sys.stdout.flush()
                    #msg4
                    #teams_msg4=f"**{service}** Blue is **STARTED** in {backend} {tenant} "
                    #final_msg.append(teams_msg4)
                    time.sleep(5)
                    #os.system(f'{values} service status {service}')
                    #status=os.popen(f"{values} service status {service}").read().strip()
                    #print(status)
                else:
                    # Code to be repeated
                    time.sleep(30)
                    # Call the function again with the same condition
                    start_repeat_until(condition,blue_running_count,blue_cluster_name,blue_service_name,myTeamsMessage,final_msg)
                #return teams_msg4
            # Call the function with a condition that will eventually be met
            teams_msg4=start_repeat_until('blue_count',blue_running_count,blue_cluster_name,blue_service_name,myTeamsMessage,final_msg)
            final_msg.append(f"**{service}** Blue is ***STARTED*** in {backend} {tenant}")


            #Checking Blue Targets Health
            time.sleep(5)
            print(f"checking {service} service Blue Target Health")
            sys.stdout.flush()
            targets=os.popen(f"{values} service targets -t Blue {service}").read().strip()
            if targets=='No targets registered in target group':
                print(targets)
                sys.stdout.flush()
                #msg5
                #teams_msg5=f" No targets registered in target group for **{service}** Blue in {backend} {tenant} "
                final_msg.append(f" No targets registered in target group for ***{service}*** Blue in {backend} {tenant}")
            else:
                #print(targets)
                #sys.stdout.flush()
                #health=echo "$health" | awk 'NR == 1' | grep -o healthy
                health=os.popen(f"echo $'{targets}' | awk 'NR == 1' | grep -o healthy").read().strip()
                if health=='healthy':
                    print(f"{service} service Blue targets are healthy")
                    sys.stdout.flush()
                    #msg6
                    #teams_msg6=f" Targets are healthy for **{service}** Blue in {backend} {tenant} "
                    final_msg.append(f" Targets are healthy for ***{service}*** Blue in {backend} {tenant}")
                else:
                    print(f"{service} service Blue targets are unhealthy")
                    sys.stdout.flush()
                    #msg7
                    #teams_msg7=f" Targets are unhealthy for **{service}** Blue in {backend} {tenant} "
                    final_msg.append(f" Targets are unhealthy for ***{service}*** Blue in {backend} {tenant}")

    #final=teams_msg1+teams_msg2+teams_msg3+teams_msg4+teams_msg5+teams_msg6+teams_msg7
    print(final_msg)
    sys.stdout.flush()




    # Get green_service and filter variables
    print(f"****** Checking Green Target for {service} service ******")
    sys.stdout.flush()

    #1st execute green_service_info
    green_service=green_service(values,service)

    if green_service=='Service does not exist':
        print(f'{service} service does not exist on Green Target')
        sys.stdout.flush()
        #msg2
        #teams_msg2=f"**{service}** Blue does not exist in {backend} {tenant} "
        final_msg.append(f"***{service}*** Blue does not exist in {backend} {tenant}")
    else:
        green_service=green_service.split()
        green_service_name = green_service[0]

        if '-EC2-' in green_service_name:
            filter_variable = green_service_name.split('-EC2-')[0]
        elif '-cAdvisor-' in green_service_name:
            filter_variable = green_service_name.split('-cAdvisor-')[0]
        else:
            filter_variable = green_service_name

        print('service:', green_service_name)
        sys.stdout.flush()
        print('filters:', filter_variable)
        sys.stdout.flush()

        # Find the cluster that matches the filter pattern
        green_cluster_name = None
        pattern = f"{filter_variable}*-Cluster-*"
        for cluster in cluster_list:
            if re.match(pattern, cluster):
                green_cluster_name = cluster
                break

        if green_cluster_name is None:
            print("Error: cluster not found")
            sys.stdout.flush()
            exit()

        print('cluster:', green_cluster_name)
        sys.stdout.flush()

        # Get the service details
        try:
            response = ecs.describe_services(
                cluster=green_cluster_name,
                services=[green_service_name]
            )
        except Exception as e:
            print(f"Error describing service: {e}")
            sys.stdout.flush()
            exit()

        # Extract the desired count, pending count, and running count from the service details
        service_details = response['services'][0]
        green_desired_count = service_details.get('desiredCount', 0)
        green_pending_count = service_details.get('pendingCount', 0)
        green_running_count = service_details.get('runningCount', 0)

        # Print the  green results
        print(f"Green Desired count: {green_desired_count}")
        sys.stdout.flush()
        print(f"Green Pending count: {green_pending_count}")
        sys.stdout.flush()
        print(f"Green Running count: {green_running_count}")
        sys.stdout.flush()

        #os.system(f'{values} service status {service}')
        #status=os.popen(f"{values} service status {service}").read().strip()
        #print(status)

        #checking green service is up or not
        if green_desired_count==0 and green_running_count==0:
            print(f"{service} service is not running currently in Green")
            sys.stdout.flush()
        else:
            time.sleep(5)
            #stopping green service
            print(f"stopping {service} service on Green Target")
            sys.stdout.flush()
            #os.system(f'echo y | {values} service stop -t Green {service}')
            #echo y | rcx --backend RCX-Dev7 --tenant Sandbox --aws-profile dev7 service start crud > /dev/null
            os.system(f'echo y | {values} service stop -t Green {service} > green-stop.txt')
            sys.stdout.flush()
            #time.sleep(30)

            #recursive_function_to_stop_service_on_green_target
            def stop_repeat_until(condition,green_cluster_name,green_service_name,myTeamsMessage,final_msg):
                #teams_msg3 = ''  # initialize with default value
                response = ecs.describe_services(
                    cluster=green_cluster_name,
                    services=[green_service_name]
                )
                service_details = response['services'][0]
                green_desired_count = service_details.get('desiredCount', 0)
                condition = service_details.get('runningCount', 0)
                if condition == 0 and green_desired_count == 0:
                    print(f'{service} service is stopped on Green Target')
                    sys.stdout.flush()
                    #msg3
                    #teams_msg3=f"**{service}** Green is **STOPPED** in {backend} {tenant} "
                    #final_msg.append(teams_msg3)
                    time.sleep(5)
                    #os.system(f'{values} service status {service}')
                    #status=os.popen(f"{values} service status {service}").read().strip()
                    #print(status)
                else:
                    # Code to be repeated
                    time.sleep(30)
                    # Call the function again with the same condition
                    stop_repeat_until(condition,green_cluster_name,green_service_name,myTeamsMessage,final_msg)
                #return teams_msg3
            # Call the function with a condition that will eventually be met
            stop_repeat_until('blue_count',green_cluster_name,green_service_name,myTeamsMessage,final_msg)
            final_msg.append(f"***{service}*** Green is ***STOPPED*** in {backend} {tenant}")

            time.sleep(5)
            #starting green service
            print(f"starting {service} service on Green Target")
            sys.stdout.flush()
            time.sleep(5)
            #os.system(f'echo y | {values} service start -t Green {service}')
            os.system(f'echo y | {values} service start -t Green {service} > green-start.txt')
            sys.stdout.flush()
            #time.sleep(30)

            #recursive_function_to_start_service_on_green_target
            def start_repeat_until(condition,green_running_count,green_cluster_name,green_service_name,myTeamsMessage,final_msg):
                #teams_msg4 = ''  # initialize with default value
                response = ecs.describe_services(
                    cluster=green_cluster_name,
                    services=[green_service_name]
                )
                service_details = response['services'][0]
                condition = service_details.get('runningCount', 0)
                if green_running_count==condition:
                    print(f'{service} service is started on Green Target')
                    sys.stdout.flush()
                    #msg4
                    #teams_msg4=f"**{service}** Green is **STARTED** in {backend} {tenant} "
                    #final_msg.append(teams_msg4)
                    time.sleep(5)
                    #os.system(f'{values} service status {service}')
                    #status=os.popen(f"{values} service status {service}").read().strip()
                    #print(status)
                else:
                    # Code to be repeated
                    time.sleep(30)
                    # Call the function again with the same condition
                    start_repeat_until(condition,green_running_count,green_cluster_name,green_service_name,myTeamsMessage,final_msg)
                #return teams_msg4
            # Call the function with a condition that will eventually be met
            teams_msg4=start_repeat_until('green_count',green_running_count,green_cluster_name,green_service_name,myTeamsMessage,final_msg)
            final_msg.append(f"**{service}** Green is ***STARTED*** in {backend} {tenant}")


            #Checking Green Targets Health
            time.sleep(5)
            print(f"checking {service} service Green Target Health")
            sys.stdout.flush()
            targets=os.popen(f"{values} service targets -t Green {service}").read().strip()
            if targets=='No targets registered in target group':
                #print(targets)
                #sys.stdout.flush()
                #msg5
                #teams_msg5=f" No targets registered in target group for **{service}** Green in {backend} {tenant} "
                final_msg.append(f" No targets registered in target group for ***{service}*** Green in {backend} {tenant}")
            else:
                print(targets)
                sys.stdout.flush()
                #health=echo "$health" | awk 'NR == 1' | grep -o healthy
                health=os.popen(f"echo $'{targets}' | awk 'NR == 1' | grep -o healthy").read().strip()
                if health=='healthy':
                    print(f"{service} service Green targets are healthy")
                    sys.stdout.flush()
                    #msg6
                    #teams_msg6=f" Targets are healthy for **{service}** Green in {backend} {tenant} "
                    final_msg.append(f" Targets are healthy for ***{service}*** Green in {backend} {tenant}")
                else:
                    print(f"{service} service Green targets are unhealthy")
                    sys.stdout.flush()
                    #msg7
                    #teams_msg7=f" Targets are unhealthy for **{service}** Green in {backend} {tenant} "
                    final_msg.append(f" Targets are unhealthy for ***{service}*** Green in {backend} {tenant}")

    #final=teams_msg1+teams_msg2+teams_msg3+teams_msg4+teams_msg5+teams_msg6+teams_msg7
    print(final_msg)
    sys.stdout.flush()

print(f"########################################################################################################")
