from pydantic import BaseModel
from nginx_api import NginxConfigRequest, NginxDeleteRequest, nginx_router, update_nginx_config
from cloudflare_api import create_dns, delete_dns   

class NewSeatRequest(BaseModel):
    last_name: str # e.g. Seiffert
    training_name: str # e.g. sfb (Sophos Firewall Basics)

class DeleteSeatRequest(BaseModel):
    last_name: str
    training_name: str

class WaitGuacamoleResponse(BaseModel):
    guacamole_ip: str
    
hyperv_router = APIRouter()

@hyperv_router.post("/seat")
async def create_new_seat(new_seat_request: NewSeatRequest):
    # Extract last_name, and training_name from the request
    last_name = new_seat_request.last_name
    training_name = new_seat_request.training_name

    try:
        # Generate a unique server_name based on the last_name and training_name
        server_name = f"{last_name}-{training_name}.lab.infinigate.io"

        # Call the /wait-guacamole endpoint to obtain the Guacamole server's IP address
        guacamole_response = await wait_for_guacamole_ip()

        if "error" in guacamole_response:
            return {"error": guacamole_response["error"]}

        guacamole_ip = guacamole_response["guacamole_ip"]

        # Create/update Nginx configuration with the obtained Guacamole server IP address
        proxy_pass = f"http://{guacamole_ip}:{training_name}"  # Assuming 'training_name' is the port
        config_request = NginxConfigRequest(server_name=server_name, proxy_pass=proxy_pass)
        update_nginx_response = await update_nginx_config(config_request)

        return {
            "message": "Seat created successfully",
            "nginx_update_response": update_nginx_response,
        }

    except Exception as e:
        return {"error": str(e)}
    
@hyperv_router.delete("/seat")
async def delete_seat(delete_seat_request: DeleteSeatRequest):
    # Extract last_name and training_name from the request
    last_name = delete_seat_request.last_name
    training_name = delete_seat_request.training_name

    try:
        # Generate the server_name based on last_name and training_name
        server_name = f"{last_name}-{training_name}.lab.infinigate.io"

        # Call the /delete-dns endpoint to remove DNS records
        delete_dns_request = NginxDeleteRequest(server_name=server_name)
        delete_dns_response = await delete_dns(delete_dns_request)

        # Call the /delete-nginx-config endpoint to remove Nginx configuration
        delete_nginx_request = NginxDeleteRequest(server_name=server_name)
        delete_nginx_response = await delete_nginx_config(delete_nginx_request)

        return {
            "message": "Seat deleted successfully",
            "dns_delete_response": delete_dns_response,
            "nginx_delete_response": delete_nginx_response,
        }

    except Exception as e:
        return {"error": str(e)}
    
@hyperv_router.get("/wait-guacamole")
async def wait_for_guacamole_ip():
    try:
        # Placeholder for the Guacamole server's IP address obtained via DHCP
        guacamole_ip = None

        # Define a timeout (in seconds) to wait for the Guacamole server's IP address
        timeout_seconds = 300  # Adjust as needed

        # Poll for the Guacamole server's IP address until it becomes available
        for _ in range(timeout_seconds):
            # Implement logic to obtain the Guacamole server's IP address via DHCP here
            # Once the IP address is obtained, assign it to the `guacamole_ip` variable
            # Example: guacamole_ip = obtain_guacamole_ip()

            if guacamole_ip:
                break  # Exit the loop once the IP address is obtained

            await asyncio.sleep(1)  # Wait for 1 second before checking again

        if not guacamole_ip:
            return {"error": "Guacamole server IP address not obtained within the timeout period"}

        return {"guacamole_ip": guacamole_ip}

    except Exception as e:
        return {"error": str(e)}