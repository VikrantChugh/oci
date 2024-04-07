import oci
import pymysql 
from datetime import datetime, timedelta
# Set up configuration
# config = oci.config.from_file() # Reads the default configuration file

# Initialize the ComputeClient to interact with Compute service
# subnet_client = oci.core.VirtualNetworkClient(config)
# subnet_list=[]
# Function to get all VM names in a compartment
def get_all_subnet():
    subnet_list=[]
    try:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        subnet_client = oci.core.VirtualNetworkClient({}, signer=signer)
        # List all instances in the compartment
        compartment_ids=['ocid1.compartment.oc1..aaaaaaaajnmd2vir2bjsphzpskjaz3gohvqy7w6xwaz3jqfkqeshuwolauqq','ocid1.compartment.oc1..aaaaaaaa7nxivmvn7wff2j4azbwncx4ywnmfuhx4eugo55huwwuozxysdw4a']
        for compartment_id in compartment_ids:
            list_subnets_response = subnet_client.list_subnets(compartment_id)
            # print(list_instances_response)
            # identity_client = oci.identity.IdentityClient(config)
            # user = identity_client.get_user(config['user'])
            # Account_id = user.data.compartment_id



            # Extract and print instance details
            for subnet in list_subnets_response.data:
                # print(subnet)
                # print(subnet.vcn_id)
                subnet_list.append({
                    'display_name' : subnet.display_name,
                    'id'  : subnet.id,
                    'cidr_block':subnet.cidr_block,
                    'domain_name'  : subnet.subnet_domain_name,
                    'State'   : subnet.lifecycle_state,
                    'account_id':signer.tenancy_id,
                    'Datacenter': signer.region,
                    'Network_Object_ID':subnet.vcn_id

                    })
        insert_subnet(subnet_list)
      
    except Exception as e:
        print("Error fetching instance data:", e)
    # print(l)
# Example compartment OCID (change this to your actual compartment OCID)
# compartment_ocid = 'ocid1.compartment.oc1..aaaaaaaajnmd2vir2bjsphzpskjaz3gohvqy7w6xwaz3jqfkqeshuwolauqq'

# Call the function to print all VM names in the compartment

# print(subnet_list)


def insert_subnet(subnet_list):
    db_host="10.0.1.75"
    # db_port=3306
    db_user="admin"
    db_pass="AdminAdmin@123"
    db_name="oci"
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_cloud_subnet'

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
        CREATE TABLE IF NOT EXISTS cmdb_ci_cloud_subnet (
            Name varchar(50),
            Object_id varchar(100),
            cidr varchar(50),
            Domain_name varchar(50),
            state varchar(50),
            Account_ID varchar(100),
            Datacenter varchar(50),
            Network_Object_ID varchar(100)

        );"""


        cursor.execute(create_table)
    
        
        for n in subnet_list:
            insert_query = """
                INSERT INTO cmdb_ci_cloud_subnet(Name,Object_id,cidr,Domain_name,state,Account_ID,Datacenter,Network_Object_ID) 
                values(%s,%s,%s,%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(n['display_name'],n['id'],n['cidr_block'],n['domain_name'],n['State'],n['account_id'],n['Datacenter'],n['Network_Object_ID']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_cloud_subnet is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")   


# insert_subnet(subnet_list)
get_all_subnet()

