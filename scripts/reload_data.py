import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.data_service import data_service

def reload():
    print("Initializing database...")
    data_service.initialize_database()
    
    available_files = data_service.list_available_files()
    print(f"Found files: {available_files}")
    
    for file in available_files:
        if 'crm' in file.lower():
            print(f"Loading CRM data from {file}...")
            data_service.load_crm_data(file)
        elif 'bcg' in file.lower():
            print(f"Loading BCG data from {file}...")
            data_service.load_bcg_installed_base(file)
        elif 'install' in file.lower() or 'base' in file.lower():
            print(f"Loading installed base data from {file}...")
            data_service.load_installed_base(file)
            
    print("Creating unified view...")
    data_service.create_unified_view()
    
    print("Data reload complete.")

if __name__ == "__main__":
    reload()
