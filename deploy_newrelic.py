#!/usr/bin/env python3
"""
New Relic Deployment Recording Script
Records deployments in New Relic APM for tracking and monitoring.
"""

import requests
import json
import os
from datetime import datetime

def record_deployment(api_key, app_id, revision, description=None, user=None, changelog=None):
    """
    Record a deployment in New Relic APM
    
    Args:
        api_key: New Relic API key
        app_id: New Relic application ID
        revision: Git commit hash or version
        description: Deployment description
        user: User who deployed
        changelog: List of changes
    """
    
    url = f"https://api.newrelic.com/v2/applications/{app_id}/deployments.json"
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "deployment": {
            "revision": revision,
            "description": description or f"Deployment {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "user": user or "deployment-script",
            "changelog": changelog or "Deployment via script"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print(f"✅ Deployment recorded successfully!")
        print(f"   Revision: {revision}")
        print(f"   Description: {data['deployment']['description']}")
        print(f"   Response: {response.status_code}")
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to record deployment: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return None

def get_current_revision():
    """Get current git commit hash"""
    import subprocess
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"

def get_github_info():
    """Get GitHub-specific information if running in GitHub Actions"""
    github_sha = os.getenv('GITHUB_SHA')
    github_actor = os.getenv('GITHUB_ACTOR')
    github_ref = os.getenv('GITHUB_REF')
    github_event_name = os.getenv('GITHUB_EVENT_NAME')
    
    return {
        'sha': github_sha,
        'actor': github_actor,
        'ref': github_ref,
        'event': github_event_name
    }

if __name__ == "__main__":
    # Configuration - Update these values
    NEW_RELIC_API_KEY = os.getenv('NEW_RELIC_API_KEY', 'your-api-key-here')
    NEW_RELIC_APP_ID = os.getenv('NEW_RELIC_APP_ID', 'your-app-id-here')
    
    # Get GitHub info if available
    github_info = get_github_info()
    
    # Get current git revision (prefer GitHub SHA if available)
    revision = github_info.get('sha') or get_current_revision()
    
    # Build description
    if github_info.get('actor'):
        description = f"Deployment by {github_info['actor']} via GitHub Actions"
        user = github_info['actor']
    else:
        description = "FinOps Assessment Platform deployment"
        user = "deployment-script"
    
    # Add commit info if available
    if revision and revision != "unknown":
        description += f" (commit: {revision[:8]})"
    
    # Record deployment
    record_deployment(
        api_key=NEW_RELIC_API_KEY,
        app_id=NEW_RELIC_APP_ID,
        revision=revision,
        description=description,
        user=user,
        changelog="Updated with context managers and login decorators"
    ) 