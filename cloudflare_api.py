from fastapi import APIRouter, HTTPException
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
    
@cloudflare_router.delete("/dns-record")
async def delete_dns_record(record_info: DNSRecordDelete):
    try:
        # Get All DNS records
        list_dns_records_response = await list_dns_records()
        if list_dns_records_response.status_code != 200:
            raise HTTPException(status_code=list_dns_records_response.status_code, detail="Failed to retrieve DNS records")
        # Extract the record ID from the response
        dns_records = list_dns_records_response.json()
        matching_record = None
        for record in dns_records:
            if (
                record["name"] == record_info.record_name
                and record["type"] == record_info.record_type
            ):
                matching_record = record
                break

        if matching_record is None:
            raise HTTPException(status_code=404, detail="DNS record not found")

        # Extract the identifier (e.g., 'id') of the matching DNS record
        record_id = matching_record["id"]

        # Construct the API URL for deleting a DNS record
        api_url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}"
        print(f"{record_id}")
        print(f"{api_url}")
        # Define the request headers, including the Cloudflare API token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CF_API_KEY}"
        }

        # Send a DELETE request to delete the DNS record
        response = requests.delete(api_url, headers=headers)

        # Check the response status code
        if response.status_code == 204:
            return {"message": "DNS record deleted successfully"}
        elif response.status_code == 404:
            return {"error": "DNS record not found"}
        else:
            return {"error": f"Failed to delete DNS record: {response.text}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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
        #print(f"CF_EMAIL: {CF_EMAIL}")
        #print(f"CF_API_KEY: {CF_API_KEY}")
        #print(f"CF_ZONE_ID: {CF_ZONE_ID}")
        
        # Send a GET request to fetch all DNS records
        response = requests.get(api_url, headers=headers)

        # Check the response status code
        if response.status_code == 200:
            # Parse the JSON response into DNSRecordResponse objects
            dns_records = response.json()["result"]
            parsed_records = [DNSRecordResponse(**record) for record in dns_records]
            return parsed_records
        else:
            return {"error": f"Failed to retrieve DNS records: {response.text}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))