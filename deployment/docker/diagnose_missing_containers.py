# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
import json
import os
import subprocess

import yaml
"""
Diagnostic Script: Missing LangChain and AutoGen Containers
Checks for container service definitions, Docker images, and configuration issues
"""


def run_command(cmd):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_docker_containers():
    """Check currently running Docker containers"""
    print("=== DOCKER CONTAINER STATUS ===")
    returncode, stdout, stderr = run_command("docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'")
    
    if returncode == 0:
        print(stdout)
        langchain_containers = [line for line in stdout.split('\n') if 'langchain' in line.lower()]
        autogen_containers = [line for line in stdout.split('\n') if 'autogen' in line.lower()]
        
        print(f"\nLangChain containers found: {len(langchain_containers)}")
        for container in langchain_containers:
            print(f"  - {container}")
            
        print(f"\nAutoGen containers found: {len(autogen_containers)}")
        for container in autogen_containers:
            print(f"  - {container}")
    else:
        print(f"Error checking containers: {stderr}")

def check_docker_images():
    """Check available Docker images"""
    print("\n=== DOCKER IMAGES STATUS ===")
    returncode, stdout, stderr = run_command("docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}'")
    
    if returncode == 0:
        langchain_images = [line for line in stdout.split('\n') if 'langchain' in line.lower()]
        autogen_images = [line for line in stdout.split('\n') if 'autogen' in line.lower()]
        
        print(f"LangChain images found: {len(langchain_images)}")
        for image in langchain_images:
            print(f"  - {image}")
            
        print(f"\nAutoGen images found: {len(autogen_images)}")
        for image in autogen_images:
            print(f"  - {image}")
    else:
        print(f"Error checking images: {stderr}")

def check_compose_files():
    """Check docker-compose files for service definitions"""
    print("\n=== DOCKER COMPOSE ANALYSIS ===")
    
    compose_files = []
        "docker-compose.master-coordination.yml",
        "docker-compose.langchain-enhanced.yml",
        "docker/docker-compose-master.yml",
        "docker/docker-compose-coordination.yml"
    
    
    for compose_file in compose_files:
        file_path = Path(compose_file)
        if file_path.exists():
            print(f"\n--- {compose_file} ---")
            try:
                with open(file_path, 'r') as f:
                    content = yaml.safe_load(f)
                    
                services = content.get('services', {})
                langchain_services = [name for name in services.keys() if 'langchain' in name.lower()]
                autogen_services = [name for name in services.keys() if 'autogen' in name.lower()]
                
                print(f"LangChain services defined: {langchain_services}")
                print(f"AutoGen services defined: {autogen_services}")
                
                for service in langchain_services + autogen_services:
                    service_config = services[service]
                    build_config = service_config.get('build', {})
                    image = service_config.get('image', 'No image specified')
                    print(f"  {service}: image={image}, build={build_config}")
                    
            except Exception as e:
                print(f"Error parsing {compose_file}: {e}")
        else:
            print(f"{compose_file}: File not found")

def check_dockerfiles():
    """Check if required Dockerfiles exist"""
    print("\n=== DOCKERFILE ANALYSIS ===")
    
    dockerfiles = []
        ("docker/Dockerfile.langchain", "LangChain"),
        ("docker/Dockerfile.autogen", "AutoGen"),
        ("langchain/Dockerfile", "LangChain (langchain dir)")
    
    
    for dockerfile_path, description in dockerfiles:
        file_path = Path(dockerfile_path)
        print(f"\n{description}: {dockerfile_path}")
        if file_path.exists():
            print(f"  [OK] EXISTS")
            # Check the COPY commands to see what source files are expected
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    copy_lines = [line.strip() for line in content.split('\n') if line.strip().startswith('COPY')]
                    print(f"  COPY commands: {copy_lines}")
            except Exception as e:
                print(f"  Error reading file: {e}")
        else:
            print(f"  [ERROR] MISSING")

def check_source_directories():
    """Check if required source directories exist"""
    print("\n=== SOURCE DIRECTORIES ANALYSIS ===")
    
    source_dirs = []
        "src/langchain_coordinators/",
        "src/autogen_agents/",
        "autogen_agents/",
        "langchain/",
    
    
    for src_dir in source_dirs:
        dir_path = Path(src_dir)
        print(f"\n{src_dir}:")
        if dir_path.exists():
            print(f"  [OK] EXISTS")
            files = list(dir_path.rglob("*.py"))
            print(f"  Python files: {len(files)}")
            if len(files) <= 5:  # Show files if not too many
                for file in files:
                    print(f"    - {file}")
        else:
            print(f"  [ERROR] MISSING")

def main():
    """Main diagnostic function"""
    print("DIAGNOSTIC REPORT: Missing LangChain and AutoGen Containers")
    print("=" * 60)
    
    check_docker_containers()
    check_docker_images()
    check_compose_files()
    check_dockerfiles()
    check_source_directories()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS SUMMARY:")
    print("1. Check if services are defined in docker-compose files")
    print("2. Check if Docker images exist or can be built")
    print("3. Check if required source directories/files exist")
    print("4. Check if containers are actually started")
    print("=" * 60)

if __name__ == "__main__":
    main()