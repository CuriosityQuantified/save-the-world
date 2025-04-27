#!/usr/bin/env python3
"""
Setup Cloudflare R2 Private Access

This script helps configure your .env file to use Cloudflare R2 with private access
by setting CLOUDFLARE_R2_PUBLIC_ACCESS to false and ensuring URL_EXPIRY is set.

Usage:
    python setup_r2_private_access.py

This will:
1. Check if .env exists and create it if needed
2. Set CLOUDFLARE_R2_PUBLIC_ACCESS=false
3. Set CLOUDFLARE_R2_URL_EXPIRY=3600 (or your custom value)
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, Optional

def load_env_file(file_path: str) -> Dict[str, str]:
    """Load environment variables from .env file into a dictionary."""
    env_vars = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def save_env_file(file_path: str, env_vars: Dict[str, str], comments: Dict[str, str] = None) -> None:
    """Save environment variables to .env file, preserving comments and order."""
    if not os.path.exists(file_path):
        # Create a new .env file
        with open(file_path, 'w') as f:
            if comments and 'header' in comments:
                f.write(f"{comments['header']}\n\n")
                
            # Write variables in sections
            sections = {
                'API KEYS': [
                    'OPENAI_API_KEY', 'GROQ_API_KEY', 'RUNWAY_API_KEY', 
                    'HUGGINGFACE_API_KEY', 'ELEVENLABS_API_KEY', 'GOOGLE_API_KEY'
                ],
                'REDIS CONFIGURATION': [
                    'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD', 'REDIS_DB'
                ],
                'APPLICATION SETTINGS': [
                    'APP_HOST', 'APP_PORT', 'DEBUG', 'LOG_LEVEL', 'ENV'
                ],
                'SIMULATION SETTINGS': [
                    'MAX_TURNS'
                ],
                'SERVER CONFIGURATION': [
                    'HOST', 'PORT'
                ],
                'DEVELOPMENT SETTINGS': [
                    'RELOAD'
                ],
                'CLOUDFLARE R2 MEDIA STORAGE': [
                    'CLOUDFLARE_R2_ENDPOINT', 'CLOUDFLARE_R2_BUCKET_NAME', 
                    'CLOUDFLARE_R2_ACCESS_KEY_ID', 'CLOUDFLARE_R2_SECRET_ACCESS_KEY',
                    'CLOUDFLARE_R2_PUBLIC_ACCESS', 'CLOUDFLARE_R2_URL_EXPIRY'
                ]
            }
            
            for section, keys in sections.items():
                section_keys = [k for k in keys if k in env_vars]
                if section_keys:
                    f.write(f"# {section}\n")
                    for key in section_keys:
                        if comments and key in comments:
                            f.write(f"{comments[key]}\n")
                        f.write(f"{key}={env_vars[key]}\n")
                    f.write("\n")
            
            # Write any remaining variables not in predefined sections
            other_keys = [k for k in env_vars if not any(k in section_keys for section_keys in sections.values())]
            if other_keys:
                f.write("# OTHER SETTINGS\n")
                for key in other_keys:
                    if comments and key in comments:
                        f.write(f"{comments[key]}\n")
                    f.write(f"{key}={env_vars[key]}\n")
                
    else:
        # Update existing .env file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Process the file line by line
        updated_lines = []
        updates = set()
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                key, _ = line_stripped.split('=', 1)
                key = key.strip()
                
                if key in env_vars:
                    updated_lines.append(f"{key}={env_vars[key]}\n")
                    updates.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Add any new variables that weren't in the file
        new_vars = [k for k in env_vars if k not in updates]
        if new_vars:
            if not updated_lines[-1].strip():
                updated_lines.append("# CLOUDFLARE R2 MEDIA STORAGE\n")
            else:
                updated_lines.append("\n# CLOUDFLARE R2 MEDIA STORAGE\n")
                
            for key in new_vars:
                if comments and key in comments:
                    updated_lines.append(f"{comments[key]}\n")
                updated_lines.append(f"{key}={env_vars[key]}\n")
        
        with open(file_path, 'w') as f:
            f.writelines(updated_lines)

def setup_r2_private_access():
    """Configure .env file for Cloudflare R2 private access."""
    env_path = '.env'
    env_example_path = 'env.example'
    
    print("Setting up Cloudflare R2 private access...")
    
    # Check if .env exists, if not try to copy from env.example
    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            print(f".env file not found, creating from {env_example_path}")
            with open(env_example_path, 'r') as src, open(env_path, 'w') as dst:
                dst.write(src.read())
        else:
            print(".env file not found, creating a new file...")
            Path(env_path).touch()
    
    # Load current environment variables
    env_vars = load_env_file(env_path)
    
    # Configure R2 private access
    r2_vars_to_update = {
        'CLOUDFLARE_R2_PUBLIC_ACCESS': 'false'  # Set to false for private access
    }
    
    # Only set URL_EXPIRY if it doesn't exist
    if 'CLOUDFLARE_R2_URL_EXPIRY' not in env_vars:
        r2_vars_to_update['CLOUDFLARE_R2_URL_EXPIRY'] = '3600'  # Default 1 hour expiry
    
    # Check if we need to add R2 credentials placeholders
    r2_credentials = [
        'CLOUDFLARE_R2_ENDPOINT', 'CLOUDFLARE_R2_BUCKET_NAME',
        'CLOUDFLARE_R2_ACCESS_KEY_ID', 'CLOUDFLARE_R2_SECRET_ACCESS_KEY'
    ]
    
    for cred in r2_credentials:
        if cred not in env_vars:
            if cred == 'CLOUDFLARE_R2_ENDPOINT':
                r2_vars_to_update[cred] = 'https://your-account-id.r2.cloudflarestorage.com'
            elif cred == 'CLOUDFLARE_R2_BUCKET_NAME':
                r2_vars_to_update[cred] = 'your-bucket-name'
            else:
                r2_vars_to_update[cred] = f'your_{cred.lower()}'
    
    # Comments for new variables
    comments = {
        'CLOUDFLARE_R2_PUBLIC_ACCESS': '# Set to false for private access with signed URLs or true for public access',
        'CLOUDFLARE_R2_URL_EXPIRY': '# Expiry time in seconds for signed URLs when using private access'
    }
    
    # Update environment variables
    for key, value in r2_vars_to_update.items():
        env_vars[key] = value
    
    # Save updated .env file
    save_env_file(env_path, env_vars, comments)
    
    # Provide feedback
    print("\nCloudflare R2 private access configuration complete!")
    print(f"Updated .env file with: CLOUDFLARE_R2_PUBLIC_ACCESS=false")
    
    if 'CLOUDFLARE_R2_URL_EXPIRY' in r2_vars_to_update:
        print(f"Added default URL expiry: CLOUDFLARE_R2_URL_EXPIRY=3600 (1 hour)")
    
    if any(cred in r2_vars_to_update for cred in r2_credentials):
        print("\nNOTE: Placeholder values were added for missing R2 credentials.")
        print("You need to replace these with your actual Cloudflare R2 credentials:")
        for cred in r2_credentials:
            if cred in r2_vars_to_update:
                print(f"  - {cred}")
    
    print("\nTo test your configuration, run: python test_r2_private_access.py")

if __name__ == "__main__":
    setup_r2_private_access() 