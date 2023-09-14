from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()

# Define the base directory where Nginx configuration files will be stored
nginx_config_dir = "/etc/nginx/conf.d"

# Pydantic model to represent the request body
class NginxConfigRequest(BaseModel):
    server_name: str # e.g., "tim-seiffert.lab.infinigate.io"
    proxy_pass: str  # e.g., "192.168.0.1:8080"

# Pydantic model to represent the request body for deleting configuration
class NginxDeleteRequest(BaseModel):
    server_name: str # e.g., "tim-seiffert.lab.infinigate.io"

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)