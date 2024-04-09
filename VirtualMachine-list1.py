import oci
import pymysql 
from datetime import datetime, timedelta
# vm_list=[]   

def get_all_vm_details():
    try:
        subnet_list=[]
        vm_list=[] 
        compartment_ids = ['ocid1.compartment.oc1..aaaaaaaa7nxivmvn7wff2j4azbwncx4ywnmfuhx4eugo55huwwuozxysdw4a','ocid1.compartment.oc1..aaaaaaaajnmd2vir2bjsphzpskjaz3gohvqy7w6xwaz3jqfkqeshuwolauqq']
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        compute_client = oci.core.ComputeClient({}, signer=signer)
        for compartment_id in compartment_ids:
            list_instances_response = compute_client.list_instances(compartment_id)
            list_subnet = compute_client.list_vnic_attachments(compartment_id)

            for instance in list_instances_response.data:
                instance_response = instance.__dict__
                
                Instance_id=instance.id
                


                for subnet in list_subnet.data:
        
                    subnet_response=subnet.__dict__
                

                    if subnet.instance_id==Instance_id:
                        subnet_list.append({
                            'Subnet':subnet_response.get('_subnet_id', ' ')
                        })

                    # instance_response.get('_shape_config', ' ').get('_memory_in_gbs',' ')
                vm_list.append({
                    'Object_id' :         instance_response.get('_id',' '),
                    'Name'  :             instance_response.get('_display_name',' '),
                    'Avalibility_zone':   instance_response.get('_availability_domain',' '),
                    'State'   :           instance_response.get('_lifecycle_state',' '),
                    'Memory' :            instance_response.get('_shape_config',' ').__dict__.get('_memory_in_gbs',' '),
                    "Cpu":                instance_response.get('_shape_config',' ').__dict__.get('_ocpus',' '),
                    "Account_id" :        signer.tenancy_id or ' ',
                    'Datacenter':         signer.region or ' ',
                    'Tags':               str(instance_response.get('_defined_tags',' ').get('Oracle-Tags',' '))
                    
                })

        for count in range(len(vm_list)):
            vm_list[count].update(subnet_list[count])    
                
        insert_vm_details_into_database(vm_list)

    except Exception as e:
        print("Error fetching instance data:", e)
    




def insert_vm_details_into_database(final_list):
    db_host="10.0.1.75"
    # db_port=3306
    db_user="admin"
    db_pass="AdminAdmin@123"
    db_name="oci"
    
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_vm_instance'

        cursor = connection.cursor()

        current_date = datetime.now()
        current_time = datetime.now().strftime("%H:%M:%S")
        previous_date = (current_date - timedelta(days=1)).strftime("%d-%m-%Y")

        show_table = f"SHOW TABLES LIKE '{table_name}'"
        cursor.execute(show_table)
        tb = cursor.fetchone()
        if tb:
            rename_table_query = f"ALTER TABLE `{table_name}` RENAME TO `{table_name}_{previous_date}_{current_time}`"
            cursor.execute(rename_table_query)

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
    
        
        for iteam in final_list:
            insert_query = """
                INSERT INTO cmdb_ci_vm_instance(Name,Object_id,State,Memory,Cpu,Account_id,Datacenter,Avalibility_zone,Subnet,Tags) 
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(iteam['Name'],iteam['Object_id'],iteam['State'],iteam['Memory'],iteam['Cpu'],iteam['Account_id'],iteam['Datacenter'],iteam['Avalibility_zone'],iteam['Subnet'],iteam['Tags']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_vm_instance is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")   
        

get_all_vm_details()
