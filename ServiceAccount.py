import oci
import pymysql 
from datetime import datetime, timedelta

def get_service_account_details():
    account_list=[]
    try:
        # Load the configuration
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        # Initialize the IdentityClient to fetch service account details
        identity_client = oci.identity.IdentityClient({}, signer=signer)

        tenancy = identity_client.get_tenancy(signer.tenancy_id).data
        compartments = identity_client.list_compartments(signer.tenancy_id)
        tenancy_name = tenancy.name 
        tenancy_id = tenancy.id 

        Master_account="Yes" if tenancy_id==signer.tenancy_id else "No"
        # Extract the desired fields from the response data
        account_list.append({
            'Name': tenancy_name or ' ',
            'Account_id': tenancy_id or ' ',
            'Object_id':   tenancy_id or ' ',
            'Organization_id': tenancy_id or ' ',
            'Is_master_account': Master_account or ' ',
        })
        # Get the list of compartments
        for compartment in compartments.data:   
            compartment_name=compartment.name
            compartment_id=compartment.id
            compartment_lifecycle_state=compartment.lifecycle_state    
            master_account="Yes" if compartment_id==signer.tenancy_id else "No"

            if compartment_lifecycle_state == "ACTIVE": 
        # Extract the desired fields from the response data               
                account_list.append(
                    {
                        'Name':compartment_name or ' ',
                        'Account_id':compartment_id or ' ',
                        'Object_id':  compartment_id or ' ',
                        'Organization_id':  tenancy_id or ' ',
                        'Is_master_account':master_account or ' ',
                    }
                )

        insert_service_account_details_into_database(account_list)
    except oci.exceptions.ServiceError as e:
        print("Error fetching active compartments", e)

def insert_service_account_details_into_database(account_list):
    db_host="10.0.1.75"
    # db_port=3306
    db_user="admin"
    db_pass="AdminAdmin@123"
    db_name="oci"    
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
        table_name = 'cmdb_ci_cloud_service_account'

        cursor = connection.cursor()

        current_time = datetime.now().strftime("%H:%M:%S")
        previous_date = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        show_table = f"SHOW TABLES LIKE '{table_name}'"
        cursor.execute(show_table)
        tb = cursor.fetchone()
        if tb:
            rename_table_query = f"ALTER TABLE `{table_name}` RENAME TO `{table_name}_{previous_date}_{current_time}`"
            cursor.execute(rename_table_query)

        create_table = """
        CREATE TABLE IF NOT EXISTS cmdb_ci_cloud_service_account (
            Name varchar(100),
            Account_id varchar(100),
            Object_id varchar(100),
            Is_master_account varchar(100),
            Organization_id varchar(100)
         );"""

        cursor.execute(create_table)
        
        for iteam in account_list:
            insert_query = """
                INSERT INTO cmdb_ci_cloud_service_account(Name,Account_id,Object_id,Is_master_account,Organization_id) 
                values(%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(iteam['Name'],iteam['Account_id'],iteam['Object_id'],iteam['Is_master_account'],iteam['Organization_id']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_cloud_service_account is successful")

        connection.commit()

        connection.close()

    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")   
  

# get_service_account_details()
