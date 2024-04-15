import oci
import pymysql 
from datetime import datetime, timedelta

# Define a function to retrieve details of all VMs
def get_all_vm_details():
    try:
        # Initialize list to store VM details
        vm_list=[] 
        # Use Instance Principals Security Token Signer for authentication
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        # List of compartment IDs where VMs are located
        identity_client = oci.identity.IdentityClient({}, signer=signer)
       
        compartments = identity_client.list_compartments(signer.tenancy_id)
        regions = identity_client.list_regions()
        all_region = []
        print(regions.data)
        for r in regions.data:
            all_region.append(r.name)
        print(all_region)
        # Use Instance Principals Security Token Signer for authentication
        
        
        
        # Loop through each compartment to get VM details
        for compartment in compartments.data:
            if compartment.lifecycle_state == "ACTIVE":  
                try:
                    for reg in all_region:
                        signer.region=reg
                        try:
                            compute_client = oci.core.ComputeClient({}, signer=signer)
                            list_instances_response = compute_client.list_instances(compartment.id)
                            # Loop through each instance (VM) in the compartment
                            for instance in list_instances_response.data:
                                instance_response = instance.__dict__                        
                                list_subnet = compute_client.list_vnic_attachments(compartment.id,instance_id=instance.id)

                                vm_list.append({
                                    'Object_id' :         instance_response.get('_id',' '),
                                    'Name'  :             instance_response.get('_display_name',' '),
                                    'Avalibility_zone':   instance_response.get('_availability_domain',' '),
                                    'State'   :           instance_response.get('_lifecycle_state',' '),
                                    'Memory' :            instance_response.get('_shape_config',' ').__dict__.get('_memory_in_gbs',' '),
                                    "Cpu":                instance_response.get('_shape_config',' ').__dict__.get('_ocpus',' '),
                                    "Account_id" :        signer.tenancy_id or ' ',
                                    'Datacenter':         signer.region or ' ',
                                    'Subnet':             list_subnet.data[0].__dict__.get('_subnet_id',' '),
                                    'Tags':               str(instance_response.get('_defined_tags',' ').get('Oracle-Tags',' '))

                                })
                        except Exception as e:
                            print(e)
                except Exception as e:
                    print(f"Account name = {compartment.__dict__.get('_name',' ')} is not authorized:", e)   

                # Call function to insert VM details into database
        insert_vm_details_into_database(vm_list)

    except Exception as e:
        print("Error fetching instance data:", e)
        
# Define a function to insert VM details into the database
def insert_vm_details_into_database(final_list):
    db_host="10.0.1.75"
    db_user="admin"
    db_pass="AdminAdmin@123"
    db_name="oci"
    
    try:
        # Connect to the MySQL database
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_vm_instance'

        cursor = connection.cursor()

        # Get current date and time for renaming the table
        current_date = datetime.now()
        current_time = datetime.now().strftime("%H:%M:%S")
        previous_date = (current_date - timedelta(days=1)).strftime("%d-%m-%Y")

        # Check if table exists, if yes rename it
        show_table = f"SHOW TABLES LIKE '{table_name}'"
        cursor.execute(show_table)
        tb = cursor.fetchone()
        if tb:
            rename_table_query = f"ALTER TABLE `{table_name}` RENAME TO `{table_name}_{previous_date}_{current_time}`"
            cursor.execute(rename_table_query)

        # Create table if not exists
        create_table = """
        CREATE TABLE IF NOT EXISTS cmdb_ci_vm_instance (
            Name varchar(100),
            Object_id varchar(100),
            State varchar(100),
            Memory varchar(100),
            Cpu varchar(100),
            Account_id varchar(100),
            Datacenter varchar(100),
            Avalibility_zone varchar(100),
            Subnet varchar(100),
            Tags varchar(200)
        );"""

        cursor.execute(create_table)
    
        # Insert VM details into the database
        for item in final_list:
            insert_query = """
                INSERT INTO cmdb_ci_vm_instance(Name,Object_id,State,Memory,Cpu,Account_id,Datacenter,Avalibility_zone,Subnet,Tags) 
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(item['Name'],item['Object_id'],item['State'],item['Memory'],item['Cpu'],item['Account_id'],item['Datacenter'],item['Avalibility_zone'],item['Subnet'],item['Tags']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_vm_instance is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")   

# Call the function to get VM details and insert into database
get_all_vm_details()
