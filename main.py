import threading
# from oci-availability_zone import get_availability_zone_details
# from oci-service_account import get_service_account_details

from ServiceAccount import get_service_account_details
from AvailabilityZones import get_availability_zone_details
from virtual_machine import get_all_vm_details
from StorageVolume import get_volumes
def main():
    VM=threading.Thread(target=get_all_vm_details)
    SA =threading.Thread(target=get_service_account_details)
    Zone =threading.Thread(target=get_availability_zone_details)
    Vol=threading.Thread(target=get_volumes)
    Zone.start()
    Zone.join()
    SA.start()
    SA.join()
    VM.start()
    VM.join()
    Vol.start()
    Vol.join()


main()
