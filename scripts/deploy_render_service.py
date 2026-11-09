"""
Deploy PriceWise AI backend to Render via Render CLI.
Reads Neon pooled connection from .env.local without printing secrets.
Creates the free web service and outputs service ID and URL.
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

def load_env_local():
    env_local = BASE_DIR / ".env.local"
    if not env_local.exists():
        print("ERROR: .env.local not found")
        sys.exit(1)
    with open(env_local, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'").strip('"')

def deploy_service():
    load_env_local()
    pooled_url = os.environ.get("DATABASE_URL")
    if not pooled_url:
        print("ERROR: DATABASE_URL not set in .env.local")
        sys.exit(1)

    print("=" * 60)
    print("RENDER BACKEND DEPLOYMENT VIA RENDER CLI")
    print("=" * 60)

    repo_url = "https://github.com/humaidmalik63-png/price-comparison-website"
    service_name = "pricewise-backend-staging"

    render_bin = r"C:\Users\humai\AppData\Roaming\npm\render.exe"
    cmd = [
        render_bin, "services", "create",
        "--name", service_name,
        "--type", "web_service",
        "--repo", repo_url,
        "--branch", "main",
        "--runtime", "python",
        "--plan", "free",
        "--region", "oregon",
        "--build-command", "pip install -r requirements.txt",
        "--start-command", "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT",
        "--health-check-path", "/api/health/ready",
        "--env-var", "ENVIRONMENT=staging",
        "--env-var", f"DATABASE_URL={pooled_url}",
        "--env-var", "CORS_ORIGINS=https://pricewise-staging.vercel.app,http://localhost:5173",
        "--env-var", "SECRET_KEY=pricewise-staging-jwt-secret-key-phase13-secure-2026",
        "--env-var", "GEMINI_MODEL=gemini-2.5-flash",
        "--env-var", "RATE_LIMIT_PER_MINUTE=120",
        "--output", "json"
    ]

    print("Executing: render services create (secrets masked)...")
    res = subprocess.run(cmd, capture_output=True, text=True, shell=False)

    if res.returncode != 0:
        # Check if service already exists
        if "already exists" in res.stderr or "already in use" in res.stderr:
            print("Notice: Service name already exists. Fetching existing service details...")
        else:
            print("Render CLI error (secrets filtered):")
            # Scrub any accidental passwords in stderr
            err_clean = res.stderr
            if pooled_url in err_clean:
                err_clean = err_clean.replace(pooled_url, "[MASKED_DATABASE_URL]")
            print(err_clean)
            sys.exit(1)

    # Fetch services list to get details
    list_cmd = [render_bin, "services", "--output", "json"]
    list_res = subprocess.run(list_cmd, capture_output=True, text=True, shell=False)
    if list_res.returncode == 0:
        services_data = json.loads(list_res.stdout)
        target_service = None
        for item in services_data:
            svc = item.get("service", {})
            if svc.get("name") == service_name:
                target_service = svc
                break

        if target_service:
            svc_id = target_service.get("id")
            svc_details = target_service.get("serviceDetails", {})
            live_url = svc_details.get("url")
            dash_url = target_service.get("dashboardUrl")
            print("\n" + "=" * 60)
            print("RENDER SERVICE CREATED / CONFIGURED SUCCESSFULLY")
            print("=" * 60)
            print(f"Service Name: {service_name}")
            print(f"Service ID:   {svc_id}")
            print(f"Live API URL: {live_url}")
            print(f"Dashboard:    {dash_url}")
            print(f"Region:       {svc_details.get('region')}")
            print(f"Plan:         {svc_details.get('plan')}")
            print("=" * 60)
            
            # Save deployment info to staging config
            out_info = {
                "service_id": svc_id,
                "url": live_url,
                "dashboard_url": dash_url,
                "name": service_name
            }
            with open(BASE_DIR / ".render_staging_backend.json", "w", encoding="utf-8") as f:
                json.dump(out_info, f, indent=2)
            return True

    print("Warning: Could not retrieve service details immediately.")
    return False

if __name__ == "__main__":
    deploy_service()
