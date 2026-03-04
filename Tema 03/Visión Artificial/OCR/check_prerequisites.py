"""
check_prerequisites.py

Verifica que todos los prerequisitos del sistema estén instalados antes de
instalar los paquetes Python del proyecto.

Uso:
    python check_prerequisites.py
"""
import sys
import subprocess
import os
import platform

def check_command(cmd, name, required=True):
    """Verifica si un comando está disponible."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            shell=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print(f"✅ {name}: {version}")
            return True
        else:
            raise Exception("Command failed")
    except Exception as e:
        status = "❌ OBLIGATORIO" if required else "⚠️  RECOMENDADO"
        print(f"{status} - {name}: NO ENCONTRADO")
        return False

def check_python_version():
    """Verifica versión de Python."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major == 3 and version.minor in [10, 11]:
        print(f"✅ Python: {version_str}")
        return True
    elif version.major == 3 and version.minor >= 8:
        print(f"⚠️  Python: {version_str} (Funcional, pero se recomienda 3.10 o 3.11)")
        return True
    else:
        print(f"❌ Python: {version_str} (Requiere Python 3.10 o 3.11)")
        return False

def check_tesseract():
    """Verifica Tesseract OCR."""
    print("\n2. Verificando Tesseract OCR...")
    
    # Verificar comando
    has_tesseract = check_command("tesseract --version", "Tesseract OCR", required=True)
    
    if not has_tesseract:
        print("\n   📥 Cómo instalar Tesseract:")
        if platform.system() == "Windows":
            print("      Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            print("      1. Descargar tesseract-ocr-w64-setup-5.3.x.exe")
            print("      2. Instalar y marcar idioma 'Español'")
            print("      3. Añadir a PATH: C:\\Program Files\\Tesseract-OCR")
        elif platform.system() == "Linux":
            print("      Linux: sudo apt-get install tesseract-ocr tesseract-ocr-spa")
        elif platform.system() == "Darwin":
            print("      macOS: brew install tesseract tesseract-lang")
        return False
    
    # Verificar si pytesseract ya está instalado
    try:
        import pytesseract
        print(f"   ✅ pytesseract: Instalado")
        
        # Intentar obtener versión desde Python
        try:
            version = pytesseract.get_tesseract_version()
            print(f"   ✅ Tesseract accesible desde Python: {version}")
        except Exception as e:
            print(f"   ⚠️  Tesseract instalado pero pytesseract no puede accederlo")
            if platform.system() == "Windows":
                print(f"      Configura la ruta en tus scripts:")
                print(f"      pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
    except ImportError:
        print("   ℹ️  pytesseract: No instalado (se instalará con requirements.txt)")
    
    return has_tesseract

def check_gpu():
    """Verifica disponibilidad de GPU NVIDIA."""
    print("\n4. Verificando GPU NVIDIA...")
    
    try:
        result = subprocess.run(
            "nvidia-smi",
            capture_output=True,
            text=True,
            shell=True,
            timeout=5
        )
        if result.returncode == 0:
            # Buscar versión CUDA
            lines = result.stdout.strip().split('\n')
            cuda_version = None
            gpu_name = None
            
            for line in lines:
                if 'CUDA Version' in line:
                    # Extraer versión CUDA
                    parts = line.split('CUDA Version:')
                    if len(parts) > 1:
                        cuda_version = parts[1].strip().split()[0]
                if '|' in line and 'MiB' in line and not gpu_name:
                    # Línea con info de GPU
                    try:
                        gpu_info = [p.strip() for p in line.split('|')]
                        for part in gpu_info:
                            if 'GeForce' in part or 'RTX' in part or 'GTX' in part or 'Quadro' in part:
                                gpu_name = part
                                break
                    except:
                        pass
            
            print(f"✅ GPU NVIDIA detectada")
            if gpu_name:
                print(f"   Modelo: {gpu_name}")
            if cuda_version:
                print(f"   CUDA Version: {cuda_version}")
            
            return True, cuda_version
        else:
            raise Exception("nvidia-smi returned non-zero")
    except Exception as e:
        print("ℹ️  GPU NVIDIA: No detectada")
        print("   El sistema usará CPU para procesamiento")
        return False, None

def check_cuda_toolkit():
    """Verifica si CUDA Toolkit está instalado."""
    print("\n5. Verificando CUDA Toolkit (nvcc)...")
    
    has_nvcc = check_command("nvcc --version", "CUDA Compiler (nvcc)", required=False)
    
    if not has_nvcc:
        print("   ℹ️  No es necesario si usarás solo CPU o si tienes drivers NVIDIA sin toolkit")
    
    return has_nvcc

def main():
    print("=" * 80)
    print("VERIFICACIÓN DE PREREQUISITOS DEL SISTEMA")
    print("Proyecto: Detección de Columnas con DocLayout-YOLO")
    print("=" * 80)
    print()
    
    results = {
        'python': False,
        'tesseract': False,
        'git': False,
        'gpu': False,
        'cuda_toolkit': False
    }
    
    # Python
    print("1. Verificando Python...")
    results['python'] = check_python_version()
    
    # Tesseract
    results['tesseract'] = check_tesseract()
    
    # Git
    print("\n3. Verificando Git...")
    results['git'] = check_command("git --version", "Git", required=False)
    if not results['git']:
        print("   📥 Descargar: https://git-scm.com/")
        print("   ℹ️  Git es recomendado para descargar modelos de Hugging Face")
    
    # GPU
    has_gpu, cuda_version = check_gpu()
    results['gpu'] = has_gpu
    
    # CUDA Toolkit (solo si hay GPU)
    if has_gpu:
        results['cuda_toolkit'] = check_cuda_toolkit()
    
    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN Y PRÓXIMOS PASOS")
    print("=" * 80)
    print()
    
    # Verificar obligatorios
    obligatorios_ok = results['python'] and results['tesseract']
    
    if obligatorios_ok:
        print("✅ Todos los prerequisitos OBLIGATORIOS están instalados")
        print()
        
        # Recomendaciones según hardware
        if results['gpu']:
            print("🎮 GPU NVIDIA DETECTADA - Instalación con CUDA")
            print("-" * 80)
            if cuda_version and cuda_version.startswith("11.8"):
                print("✅ CUDA 11.8 detectado - Compatible con el proyecto")
                print()
                print("📦 Comandos de instalación:")
                print()
                print("1. Instalar PyTorch con CUDA 11.8:")
                print("   pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118")
                print()
                print("2. Instalar resto de paquetes:")
                print("   pip install -r requirements.txt")
            elif cuda_version:
                print(f"⚠️  CUDA {cuda_version} detectado - El proyecto está optimizado para CUDA 11.8")
                print("   Puedes intentar con tu versión o instalar CUDA 11.8")
                print()
                print("📦 Comandos de instalación (probar con tu CUDA):")
                print()
                print("1. Instalar PyTorch (detectará tu CUDA automáticamente):")
                print("   pip install torch torchvision torchaudio")
                print()
                print("2. Modificar requirements.txt:")
                print("   - Comentar líneas torch==2.0.1+cu118, torchvision, torchaudio")
                print("   - Ejecutar: pip install -r requirements.txt")
            else:
                print("⚠️  GPU detectada pero versión CUDA desconocida")
                print()
                print("📦 Instalación genérica con GPU:")
                print("1. pip install torch torchvision torchaudio")
                print("2. pip install -r requirements.txt (comentando líneas torch con +cu118)")
        else:
            print("💻 GPU NO DETECTADA - Instalación solo CPU")
            print("-" * 80)
            print("El procesamiento será ~10x más lento con DocLayout-YOLO en CPU,")
            print("pero OpenCV funcionará a velocidad normal.")
            print()
            print("📦 Comandos de instalación:")
            print()
            print("1. Instalar PyTorch CPU:")
            print("   pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu")
            print()
            print("3. Modificar requirements.txt:")
            print("   - Comentar líneas: torch==2.0.1+cu118, torchvision, torchaudio")
            print("   - Comentar línea: tensorflow-gpu==2.10.0")
            print("   - Mantener: tensorflow==2.10.0")
            print()
            print("2. Instalar resto de paquetes:")
            print("   pip install -r requirements.txt")
            print()
            print("💡 Recomendación: Usa --method opencv para mejor rendimiento en CPU")
        
        print()
        print("2. Descargar modelo DocLayout-YOLO:")
        print("   python download_doclayout_model.py")
        
    else:
        print("❌ FALTAN PREREQUISITOS OBLIGATORIOS")
        print("-" * 80)
        print()
        
        if not results['python']:
            print("📥 Instalar Python 3.10 o 3.11:")
            print("   https://www.python.org/downloads/")
            print("   ⚠️ Marcar 'Add Python to PATH' durante instalación")
            print()
        
        if not results['tesseract']:
            print("📥 Instalar Tesseract OCR:")
            if platform.system() == "Windows":
                print("   https://github.com/UB-Mannheim/tesseract/wiki")
            elif platform.system() == "Linux":
                print("   sudo apt-get install tesseract-ocr tesseract-ocr-spa")
            elif platform.system() == "Darwin":
                print("   brew install tesseract tesseract-lang")
            print()
        
        print("⚠️  Instala los prerequisitos faltantes antes de continuar")
    
    print("=" * 80)
    print()
    
    # Código de salida
    return 0 if obligatorios_ok else 1

if __name__ == "__main__":
    sys.exit(main())
