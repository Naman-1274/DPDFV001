import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
project_name = "Ecommerce_pricing_ai"

list_of_files = [
    f"{project_name}/__init__.py",
    f"{project_name}/data/__init__.py",
    f"{project_name}/data/raw/",
    f"{project_name}/data/processed/",
    f"{project_name}/notebooks/__init__.py",
    f"{project_name}/src/__init__.py",
    f"{project_name}/src/data/__init__.py",
    f"{project_name}/src/data/ingestion.py",
    f"{project_name}/src/data/transformation.py",
    f"{project_name}/src/data/models.py",
    f"{project_name}/src/data/pricing/__init__.py",
    f"{project_name}/src/data/pricing/elasticity.py",
    f"{project_name}/src/data/pricing/bandit.py",
    f"{project_name}/src/data/pricing/ddpg_agent.py",
    f"{project_name}/src/data/api/__init__.py",
    f"{project_name}/src/data/api/flask_app.py",
    f"{project_name}/src/data/api/fastapi_app.py",
    f"{project_name}/dashboard/__init__.py",
    f"{project_name}/dashboard/app.py",
    f"{project_name}/Dockerfile.etl",
    f"{project_name}/docker-compose.yml",
    f"{project_name}/requirements.txt",
    f"{project_name}/environment.yml",
    f"{project_name}/setup.py",
    f"{project_name}/etl.py",
    
]

for fp in list_of_files:
    filepath = Path(fp)
    filedir, filename = os.path.split(filepath)
    
    
    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory: {filedir}")
       
        
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        with open(filepath, "w") as f:
            pass
        logging.info(f"Creating file: {filepath}")
    else:
        logging.info(f"File already exists: {filepath}")