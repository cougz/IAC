from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decouple import config
import os, re, asyncio, cloudflare

# Instantiate FastAPI
app = FastAPI()

# Read Cloudflare credentials from environment variables using decouple
CF_EMAIL = config('CF_EMAIL')
CF_API_KEY = config('CF_API_KEY')
CF_ZONE_ID = config('CF_ZONE_ID')

# Define the base directory where Nginx configuration files will be stored
nginx_config_dir = "/etc/nginx/conf.d"

# Pydantic model to represent the request body
class NginxConfigRequest(BaseModel):
    server_name: str # e.g., "tim-seiffert-sfb.lab.infinigate.io"
    proxy_pass: str  # e.g., "192.168.0.1:8080"

# Pydantic model to represent the request body for deleting configuration
class NginxDeleteRequest(BaseModel):
    server_name: str # e.g. "tim-seiffert.lab.infinigate.io"

class NewSeatRequest(BaseModel):
    last_name: str # e.g. Seiffert
    training_name: str # e.g. sfb (Sophos Firewall Basics)

class DeleteSeatRequest(BaseModel):
    last_name: str
    training_name: str

class WaitGuacamoleResponse(BaseModel):
    guacamole_ip: str

# GET Endpoints
@app.get("/wait-guacamole")
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

# POST Endpoints
@app.post("/update-nginx-config")
async def update_nginx_config(config_request: NginxConfigRequest):
    # Extract 'server_name' and 'proxy_pass' from the request body
    server_name = config_request.server_name
    proxy_pass = config_request.proxy_pass

    # Generate a unique configuration file name based on 'server_name'
    config_file_name = f"{server_name}.conf"
    config_file_path = os.path.join(nginx_config_dir, config_file_name)

    # Generate or update Nginx configuration based on 'server_name' and 'proxy_pass'
    nginx_config = f"""
    server {{
        listen 80;
        server_name {server_name};
        return 301 https://$host$request_uri;
    }}
    server {{
        listen 443 ssl;
        http2 on;
        include /etc/nginx/snippets/ssl.conf;
        ssl_certificate /etc/zerossl/ecc-certs/fullchain.pem;
        ssl_certificate_key /etc/zerossl/ecc-certs/privkey.pem;
        server_name {server_name};
        location / {{
		    proxy_pass {proxy_pass};
            proxy_buffering off;
		    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		    proxy_set_header Upgrade $http_upgrade;
		    proxy_set_header Connection $http_connection;
		    proxy_cookie_path /guacamole/ /;
        }}
    }}
    """

    try:
        # Write the updated configuration to the dynamically generated file
        with open(config_file_path, "w") as nginx_file:
            nginx_file.write(nginx_config)

        # Reload Nginx to apply the new configuration
        os.system("nginx -s reload")

        return {"message": "Nginx configuration updated successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/update-dns")
async def update_dns(config_request: NginxConfigRequest):
    # Extract 'server_name' from the request body
    server_name = config_request.server_name

    # Update DNS record using Cloudflare API (assuming 'server_name' is a subdomain)
    cf = cloudflare.CloudFlare(email=CF_EMAIL, token=CF_API_KEY)
    zone_id = CF_ZONE_ID

    # Specify the DNS record details
    dns_record = {
        "type": "A",
        "name": server_name,
        "content": "1.1.1.1",  # Replace with your actual server IP address
    }

    try:
        # Create or update the DNS record
        dns_records = cf.zones.dns_records.get(zone_id, params=dns_record)
        if not dns_records:
            cf.zones.dns_records.post(zone_id, data=dns_record)
        else:
            dns_record_id = dns_records[0]["id"]
            cf.zones.dns_records.put(zone_id, dns_record_id, data=dns_record)

        return {"message": "DNS record updated successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/new-seat")
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

# DELETE Endpoints
@app.delete("/delete-nginx-config")
async def delete_nginx_config(delete_request: NginxDeleteRequest):
    # Extract 'server_name' from the request body
    server_name = delete_request.server_name

    # Generate the configuration file path to be deleted
    config_file_name = f"{server_name}.conf"
    config_file_path = os.path.join(nginx_config_dir, config_file_name)

    try:
        # Delete the configuration file
        os.remove(config_file_path)

        # Reload Nginx to apply the removal
        os.system("nginx -s reload")

        return {"message": "Nginx configuration deleted successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/delete-dns")
async def delete_dns(delete_request: NginxDeleteRequest):
    # Extract 'server_name' from the request body
    server_name = delete_request.server_name

    try:
        # Delete the DNS record from Cloudflare
        cf = cloudflare.CloudFlare(email=CF_EMAIL, token=CF_API_KEY)
        zone_id = CF_ZONE_ID

        # Find and delete the DNS record
        dns_records = cf.zones.dns_records.get(zone_id, params={"name": server_name})
        for dns_record in dns_records:
            cf.zones.dns_records.delete(zone_id, dns_record["id"])

        return {"message": "DNS record deleted successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/delete-seat")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)