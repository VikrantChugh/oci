import oci
import pymysql 
from datetime import datetime, timedelta


def get_volumes():
    storage_list=[]    
    try:
        compartment_id = 'ocid1.compartment.oc1..aaaaaaaa7nxivmvn7wff2j4azbwncx4ywnmfuhx4eugo55huwwuozxysdw4a'
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        blockstorage_client = oci.core.BlockstorageClient({}, signer=signer)

        list_volumes_response = blockstorage_client.list_volumes(
            compartment_id=compartment_id
        )       

        volumes = list_volumes_response.data
       

        for volume in volumes:
            Name=volume.display_name
            Object_id=volume.id
            State=volume.lifecycle_state
            d=volume.size_in_gbs
            d=d * 1024 * 1024 * 1024
            Size_bytes=f"{d:.5e}"
            Volume_ID=volume.id
            Size_in_gbs=volume.size_in_gbs
            Availability_domain=volume.availability_domain
            
            storage_list.append({
                'Name' :             Name or ' ',
                'Object_id'  :       Object_id or ' ',
                'State'  :           State or ' ',
                'Size_bytes':        Size_bytes or ' ',
                'Volume_ID' :        Volume_ID or ' ',
                "Account_id" :       signer.tenancy_id or ' ',
                'size_in_gb':        Size_in_gbs or ' ',
                'Datacenter':        signer.tenancy_id or ' ',
                "Avalibility_zone" : Availability_domain or ' '
            })
        insert_storage_volume_into_db(storage_list)    
    except Exception as e:
        print("Error fetching volumes:", e)
  


def insert_storage_volume_into_db(storage_list):
    db_host="10.0.1.75"
    # db_port=3306
    db_user="admin"
    db_pass="AdminAdmin@123"
    db_name="oci"
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_storage_volume'

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
        CREATE TABLE IF NOT EXISTS cmdb_ci_storage_volume (
            Name varchar(100),
            Object_id varchar(100),
            State varchar(50),
            Size_bytes varchar(50),
            Volume_ID varchar(100),
            Account_id varchar(100),
            Size varchar(50),
            DataCenter varchar(100),
            Avalibility_zone varchar(50)

        );"""


        cursor.execute(create_table)
    
        
        for iteam in storage_list:
            insert_query = """
                INSERT INTO cmdb_ci_storage_volume(Name,Object_id,State,Size_bytes,Volume_ID,Account_id,Size,Datacenter,Avalibility_zone) 
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """
        
            try:
                cursor.execute(insert_query,(iteam['Name'],iteam['Object_id'],iteam['State'],iteam['Size_bytes'],iteam['Volume_ID'],iteam['Account_id'],iteam['size_in_gb'],iteam['Datacenter'],iteam['Avalibility_zone']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_storage_volume is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")       

# get_volumes()
