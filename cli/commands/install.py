"""
Command to install the assistant as a background daemon service.
"""
from services.manager import get_service_installer

def install_cmd():
    print("Iniciando instalador de rbot...")
    installer = get_service_installer()
    
    # Run the platform-specific installer
    if installer.install():
        print("\n✔ ¡rbot se ha registrado e instalado con éxito como servicio!")
        print("Puedes controlar el servicio usando la CLI: rbot start / rbot stop")
    else:
        print("\n❌ Error durante la instalación del servicio.")
