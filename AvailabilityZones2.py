import oci
import pymysql 
from datetime import datetime, timedelta
#     [Yesterday 10:27 PM] Kukkapally Chennakesava Rao
# import oci
 
# config = oci.config.from_file()
# identity_client = oci.identity.IdentityClient(config)
 
# availability_domains = identity_client.list_availability_domains(config["tenancy"]).data
 
# for ad in availability_domains:
#     print("Availability Domain:", ad.name)
#     fault_domains = identity_client.list_fault_domains(config["tenancy"], ad.name).data
#     for fd in fault_domains:
#         print("  Fault Domain:", fd.name)
def get_availability_zone_details():
    zone_list=[]
    try:
        # Load the configuration
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        # Initialize the IdentityClient to fetch service account details
        identity_client = oci.identity.IdentityClient({}, signer=signer)      
        # Initialize the availability_domains to fetch zone details
        compartments = identity_client.list_compartments(signer.tenancy_id)
        for compartment in compartments.data:
            compartment_id=compartment.id
            availability_domains = identity_client.list_availability_domains(compartment_id).data
            # List availability domains in the region    
            for availability_domain in availability_domains:
                availability_domain_id=availability_domain.id
                availability_domain_name=availability_domain.name
                fault_domains = identity_client.list_fault_domains(compartment_id, availability_domain.name).data
                for fd in fault_domains:
                    fault_domain=fd.name
            # Extract the desired fields from the response data
                    zone_list.append({
                            'Fault_domain':fault_domain or ' ',
                            'Object_id':availability_domain_id or ' ',
                            'Name':availability_domain_name or ' ',
                            'Account_id':signer.tenancy_id or ' ',
                            'Datacenter':signer.region or ' ',
                            'State':"Available" or ' '
                        })
        insert_availability_zone_details_into_database(zone_list)
            
    except oci.exceptions.ServiceError as e:
        print("Error fetching availability domains:", e)


def insert_availability_zone_details_into_database(zone_list):
    db_host="10.0.1.75"
    # db_port=3306
    db_user="admin"
    db_pass="AdminAdmin@123"
    db_name="oci"
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_availability_zone'
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
        CREATE TABLE IF NOT EXISTS cmdb_ci_availability_zone (
            Fault_domain varchar(50),
            Name varchar(50),
            Object_id varchar(100),
            Account_id varchar(100),
            Datacenter varchar(50),
            State varchar(50)
        );"""
        cursor.execute(create_table)
         
        for zones in zone_list:
            insert_query = """
                INSERT INTO cmdb_ci_availability_zone(Fault_domain,Name,Object_id,Account_id,Datacenter,State) 
                values(%s,%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(zones['Fault_domain'],zones['Name'],zones['Object_id'],zones['Account_id'],zones['Datacenter'],zones['State']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_availability_zone is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")
           
get_availability_zone_details()
