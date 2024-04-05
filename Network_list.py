import oci
import pymysql 
from datetime import datetime, timedelta

def get_network_details():
    network_list=[]
    try:
        # compartment_id = 'ocid1.compartment.oc1..aaaaaaaa7nxivmvn7wff2j4azbwncx4ywnmfuhx4eugo55huwwuozxysdw4a'
        compartment_ids = ['ocid1.compartment.oc1..aaaaaaaajnmd2vir2bjsphzpskjaz3gohvqy7w6xwaz3jqfkqeshuwolauqq','ocid1.compartment.oc1..aaaaaaaa7nxivmvn7wff2j4azbwncx4ywnmfuhx4eugo55huwwuozxysdw4a']
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        identity_client = oci.identity.IdentityClient({}, signer=signer)
        compartments = identity_client.list_compartments(signer.tenancy_id)
        network_client = oci.core.VirtualNetworkClient({}, signer=signer)
        for compartment_id in compartment_ids:   
            # compartment_name=compartment.name
            # compartment_id=compartment.id
            list_vcns_response = network_client.list_vcns(compartment_id=compartment_id)
        
            for network in list_vcns_response.data:  
                Tag=network.defined_tags['Oracle-Tags']
                Tags=str(Tag)           
                Vcn_name=network.display_name
                Vcn_state=network.lifecycle_state
                Vcn_id=network.id
                Vcn_cidr=network.cidr_block
                Datacenter=network.vcn_domain_name

                network_list.append({
                    'display_name' :        Vcn_name or ' ',
                    'State' :               Vcn_state or ' ',
                    'id'  :                 Vcn_id or ' ',
                    'cidr_block':           Vcn_cidr or ' ',
                    'domain_name'  :        Datacenter or ' ',
                    'account_id':           compartment_id or ' ',
                    'Datacenter':           signer.region or ' ',
                    'Tags' :                Tags or ' '
                    
                    
                }
                )
        insert_network_detail_into_db(network_list)
    except Exception as e:
        print("Error fetching instance data:", e)


def insert_network_detail_into_db(network_list):
    db_host="10.0.1.75"
    # db_port=3306
    db_user="admin"
    db_pass="AdminAdmin@123"
    db_name="oci"
    
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
        
        table_name = 'cmdb_ci_network'

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
        CREATE TABLE IF NOT EXISTS cmdb_ci_network (
            Name varchar(100),
            State varchar(100),
            Object_Id varchar(100),
            Cidr varchar(50),
            Domain_Name varchar(50),
            AccoundID varchar(100),
            Datacenter varchar(50),
            Tags varchar(100)

        );"""


        cursor.execute(create_table)
    
        
        for iteam in network_list:
            insert_query = """
                INSERT INTO cmdb_ci_network(Name,State,Object_Id,Cidr,Domain_Name,AccoundID,Datacenter,Tags) 
                values(%s,%s,%s,%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(iteam['display_name'],iteam['State'],iteam['id'],iteam['cidr_block'],iteam['domain_name'],iteam['account_id'],iteam['Datacenter'],iteam['Tags']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_network is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")       
    
get_network_details()
