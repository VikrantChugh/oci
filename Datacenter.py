import oci
import pymysql as mysql
from datetime import datetime, timedelta

def fetch_active_compartments(identity_client, compartment_id):
    active_compartments = []
    try:
        compartments = identity_client.list_compartments(compartment_id, compartment_id_in_subtree=True, lifecycle_state='ACTIVE').data
        for compartment in compartments:
            active_compartments.append({
                'compartment_name': compartment.name,
                'compartment_id': compartment.id
            })
    except oci.exceptions.ServiceError as e:
        print("Error fetching active compartments:", e)
    return active_compartments

def fetch_oci_datacenters(signer):
    datacenters = []
    try:
        identity_client = oci.identity.IdentityClient({}, signer=signer)
        tenancy_id = signer.tenancy_id
        subscribed_regions = identity_client.list_region_subscriptions(tenancy_id).data

        for subscribed_region in subscribed_regions:
            region_name = subscribed_region.region_name
            compartment_id = tenancy_id

            datacenters.append({
                'name' : region_name,
                'region': region_name,
                'object_id' : region_name,
                'Account ID': tenancy_id
            })

            active_compartments = fetch_active_compartments(identity_client, compartment_id)
            for compartment in active_compartments:
                datacenters.append({
                    'name' : region_name,
                    'region': region_name,
                    'object_id' : region_name,
                    'Account ID': compartment['compartment_id']
                })

    except oci.exceptions.ServiceError as e:
        print("Error fetching OCI data centers:", e)
    return datacenters

def connect_to_mysql():
    db_host = "10.0.1.75"
    db_user = "admin"
    db_password = "AdminAdmin@123"
    db_name = "oci_test"
    try:
        connection = mysql.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        print("Connected to MySQL database successfully!")
        return connection
    except mysql.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def create_table(cursor):
    try:
        table_name = "cmdb_ci_oci_datacenter"
        current_date = datetime.now()
        current_time = datetime.now().strftime("%H:%M:%S")
        previous_date = (current_date - timedelta(days=1)).strftime("%d-%m-%Y")
    
        show_table = f"SHOW TABLES LIKE '{table_name}'"
        cursor.execute(show_table)
        tb = cursor.fetchone()
        if tb:
            rename_table_query = f"ALTER TABLE `{table_name}` RENAME TO `{table_name}_{previous_date}_{current_time}`"
            cursor.execute(rename_table_query)
        create_table_query = """
        CREATE TABLE IF NOT EXISTS cmdb_ci_oci_datacenter (
            name VARCHAR(500),
            region VARCHAR(500), 
            object_id VARCHAR(500),
            `Account ID` VARCHAR(500)
        )
        """
        cursor.execute(create_table_query)
        print("Database table created successfully!")
    except mysql.Error as e:
        print(f"Error creating database table: {e}")

def insert_details(connection, cursor, Dc_details):
    try:
        for detail in Dc_details:
            insert_query = """
            INSERT INTO cmdb_ci_oci_datacenter (name, region, object_id, `Account ID`)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (detail['name'], detail['region'], detail['object_id'], detail['Account ID']))
        connection.commit()
        print("Details inserted into database successfully!")
    except mysql.Error as e:
        print(f"Error inserting details into database: {e}")

if __name__ == "__main__":
    # Create a signer using instance principals
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

    # Fetch OCI data centers
    oci_datacenters = fetch_oci_datacenters(signer)

    # Connect to MySQL database
    connection = connect_to_mysql()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Create table if not exists
                create_table(cursor)

                # Insert OCI data center details into MySQL database
                insert_details(connection, cursor, oci_datacenters)
        finally:
            connection.close()










