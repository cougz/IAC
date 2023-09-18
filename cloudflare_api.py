import cloudflare
from decouple import config
from nginx_api import NginxConfigRequest, NginxDeleteRequest
from pydantic import BaseModel

# Read Cloudflare credentials from environment variables using decouple
CF_EMAIL = config('CF_EMAIL')
CF_API_KEY = config('CF_API_KEY')
CF_ZONE_ID = config('CF_ZONE_ID')

cloudflare_router = APIRouter()

class DNSARecordCreate(BaseModel):
    name: str  # The name of the DNS record (e.g., subdomain.example.com)
    content: str  # The IPv4 address associated with the A record (e.g., 192.168.1.1)
    ttl: int = 3600  # Time to live (TTL) in seconds (default is 3600 seconds)

@cloudflare.post("/dns-record")
async def create_dns(config_request: DNSARecordCreate):
    name = config_request.name

    cf = cloudflare.CloudFlare(email=CF_EMAIL, token=CF_API_KEY)
    zone_id = CF_ZONE_ID

    # Specify the DNS record details
    dns_record = {
        "type": "A",
        "name": name,
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
    
@cloudflare_router.delete("/dns-record")
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