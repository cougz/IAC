from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from decouple import config
from nginx_api import NginxConfigRequest, NginxDeleteRequest
from pydantic import BaseModel
from models import DNSRecordResponse, DNSRecordDelete, DNSARecordCreate
import requests

# Read Cloudflare credentials from environment variables using decouple
CF_EMAIL = config('CF_EMAIL')
CF_API_KEY = config('CF_API_KEY')
CF_ZONE_ID = config('CF_ZONE_ID')

cloudflare_router = APIRouter()

@cloudflare_router.post("/dns-record")
async def create_dns(record: DNSARecordCreate):
    try:
        # Construct the API URL for creating a DNS A record
        api_url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records"

        # Define the request headers, including the Cloudflare API token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CF_API_KEY}"
        }

        # Define the request payload based on the Pydantic model
        payload = {
            "type": "A",
            "name": record.name,
            "content": record.content,
            "ttl": record.ttl
        }

        # Send a POST request to create the DNS A record
        response = requests.post(api_url, headers=headers, json=payload)

        # Check the response status code
        if response.status_code == 200:
            return {"message": "DNS A record created successfully"}
        else:
            return {"error": f"Failed to create DNS A record: {response.text}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def delete_dns_record(record_id):
        # Construct the API URL for creating a DNS A record
        api_url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}"

        # Define the request headers, including the Cloudflare API token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CF_API_KEY}"
        }

        # Send a DELETE request to delete the DNS record
        response = requests.delete(api_url, headers=headers)

        # Check the response status code
        response.raise_for_status()

@cloudflare_router.delete("/dns-record")
async def delete_dns_record_by_name_and_type(request_body: DNSRecordDelete):
    try:
        dns_records = await list_dns_records()
        print(f"All DNS Records: {dns_records}")

        # Find the record with the specified name and type
        matching_records = [record for record in dns_records if record.name == request_body.record_name and record.type == request_body.record_type]

        print(f"Matching Records: {matching_records}")

        if not matching_records:
            error_message = f"{request_body.record_type} record '{request_body.record_name}' not found"
            print(f"Error: {error_message}")
            return JSONResponse(content={"error": error_message}, status_code=404)

        # Delete the first matching record (you may want to handle multiple matches differently)
        await delete_dns_record(matching_records[0].id)

        return {"message": f"{request_body.record_type} record '{request_body.record_name}' deleted successfully"}

    except Exception as e:
        # Print the exception
        print(f"An error occurred: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@cloudflare_router.get("/dns-records")
async def list_dns_records():
    try:
        # Construct the API URL for fetching all DNS records of the zone
        api_url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records"

        # Define the request headers, including the Cloudflare API token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CF_API_KEY}"
        }

        # Send a GET request to fetch all DNS records
        response = requests.get(api_url, headers=headers)

        # Check the response status code
        if response.status_code == 200:
            # Parse the JSON response into DNSRecordResponse objects
            #dns_records = response.json()["result"]
            dns_records = response.json().get("result", [])
            parsed_records = [DNSRecordResponse(**record) for record in dns_records]
            return parsed_records
        else:
            return {"error": f"Failed to retrieve DNS records: {response.text}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))