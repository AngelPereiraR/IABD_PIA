@echo off
setlocal enabledelayedexpansion
REM =============================================================================
REM install.bat - Script de instalación interactivo para Windows
REM Proyecto: Detección de Layout Multi-Método (FASE 2.2)
REM Métodos: opencv | doclayout | yolo11 | paddleocr | docling
REM Motores OCR: easyocr | tesseract | paddleocr | deepseek (dependencias locales)
REM NOTA: Usa Python 3.11 directamente mediante py launcher
REM =============================================================================

REM Cambiar al directorio donde está el script
cd /d "%~dp0"

echo ================================================================================
echo INSTALACION: Layout + OCR (EasyOCR + Tesseract + PaddleOCR + DeepSeek deps)
echo ================================================================================
echo.

REM Verificar Python 3.11
echo [1/5] Verificando Python 3.11...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python 3.11 NO encontrado
    echo     Descarga Python 3.11 desde: https://www.python.org/downloads/release/python-3118/
    echo     IMPORTANTE: Marca "Add Python to PATH" durante instalacion
    echo.
    echo     Tambien puedes intentar con Python 3.10:
    echo     Edita este archivo y cambia "py -3.11" por "py -3.10"
    pause
    exit /b 1
)

REM Mostrar version de Python
py -3.11 --version
echo.

REM Verificar Tesseract
echo [2/5] Verificando Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo [X] Tesseract NO encontrado
    echo     Descarga desde: https://github.com/UB-Mannheim/tesseract/wiki
    echo     1. Instalar tesseract-ocr-w64-setup-5.3.x.exe
    echo     2. Marcar idioma "Espanol" durante instalacion
    echo     3. Anadir a PATH: C:\Program Files\Tesseract-OCR
    pause
    exit /b 1
) else (
    tesseract --version 2>&1 | findstr /C:"tesseract"
    tesseract --list-langs 2>nul | findstr /R /C:"^spa$" >nul
    if errorlevel 1 (
        echo [W] Idioma 'spa' no detectado en Tesseract ^(se recomienda instalarlo^)
    ) else (
        echo [OK] Idioma 'spa' detectado en Tesseract
    )
)
echo.

REM Verificar Git (opcional)
echo [3/5] Verificando Git (recomendado)...
git --version >nul 2>&1
if errorlevel 1 (
    echo [W] Git NO encontrado ^(recomendado para descargar modelos^)
    echo     Descarga desde: https://git-scm.com/
) else (
    git --version
)
echo.

REM Verificar GPU
echo [4/5] Verificando GPU NVIDIA...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    set GPU_AVAILABLE=0
    echo [i] GPU NVIDIA NO detectada - Se instalara version CPU
    echo.
    set /p CONFIRM_CPU="Continuar con instalacion CPU (mas lenta)? [S/n]: "
    if /i "!CONFIRM_CPU!"=="n" (
        echo Instalacion cancelada.
        pause
        exit /b 0
    )
) else (
    set GPU_AVAILABLE=1
    echo [OK] GPU NVIDIA detectada
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
    for /f "tokens=2 delims=:" %%A in ('nvidia-smi ^| findstr /C:"CUDA Version"') do set CUDA_VERSION=%%A
    if defined CUDA_VERSION (
        echo CUDA Version: !CUDA_VERSION!
    )
)
echo.

REM Verificacion completada
echo [5/5] Verificacion completada
echo.

echo ================================================================================
echo INSTALACION DE PAQUETES PYTHON
echo ================================================================================
echo.

if !GPU_AVAILABLE!==1 (
    echo Instalacion con GPU NVIDIA ^(CUDA 11.8^)
    echo --------------------------------------------------------------------------------
    echo.
    echo [1/5] Comprobando PyTorch 2.2.2+cu118...
    py -3.11 -c "import torch; v=torch.__version__; exit^(0 if v=='2.2.2+cu118' else 1^)" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] PyTorch 2.2.2+cu118 ya instalado - saltando
    ) else (
        py -3.11 -m pip install --no-warn-script-location torch==2.2.2+cu118 torchvision==0.17.2+cu118 --index-url https://download.pytorch.org/whl/cu118
        if errorlevel 1 (
            echo [X] Error instalando PyTorch con CUDA
            pause
            exit /b 1
        )
    )
    echo.

    echo [2/5] Comprobando paddlepaddle==3.2.2 ^(PINNED^)...
    py -3.11 -c "import pkg_resources; pkg_resources.require^('paddlepaddle==3.2.2'^)" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] paddlepaddle 3.2.2 ya instalado - saltando
    ) else (
        py -3.11 -m pip install --no-warn-script-location paddlepaddle==3.2.2
        if errorlevel 1 (
            echo [W] Error con paddlepaddle GPU, intentando continuar...
        )
    )
    py -3.11 -m pip show paddleocr >nul 2>&1
    if not errorlevel 1 (
        echo [OK] paddleocr ya instalado - saltando
    ) else (
        py -3.11 -m pip install --no-warn-script-location "paddleocr[doc-parser]"
    )
    echo.

    echo [3/5] Comprobando Docling...
    py -3.11 -m pip show docling >nul 2>&1
    if not errorlevel 1 (
        echo [OK] docling ya instalado - saltando
    ) else (
        py -3.11 -m pip install --no-warn-script-location docling
        if errorlevel 1 (
            echo [X] Error instalando docling
            pause
            exit /b 1
        )
    )

    echo.

    echo [4/5] Instalando resto de paquetes ^(pip omite los ya satisfechos^)...
    REM Filtrar requirements.txt para excluir lineas con +cu118 ^(si existen^)
    findstr /V /C:"+cu118" requirements.txt > requirements_temp.txt
    py -3.11 -m pip install --no-warn-script-location -r requirements_temp.txt
    if errorlevel 1 (
        echo [X] Error instalando paquetes
        del requirements_temp.txt
        pause
        exit /b 1
    )
    del requirements_temp.txt

    echo.
    echo [i] Dependencia opcional DeepSeek: flash-attn ^(recomendado en GPU^)
    py -3.11 -m pip show flash-attn >nul 2>&1
    if not errorlevel 1 (
        echo [OK] flash-attn ya instalado - saltando
    ) else (
        py -3.11 -m pip install --no-warn-script-location flash-attn==2.7.3 --no-build-isolation
        if errorlevel 1 (
            echo [W] No se pudo instalar flash-attn. DeepSeek puede funcionar con atencion eager ^(mas lento^).
        ) else (
            echo [OK] flash-attn instalado correctamente
        )
    )
) else (
    echo Instalacion CPU ^(sin GPU^)
    echo --------------------------------------------------------------------------------
    echo.
    echo [1/5] Comprobando PyTorch 2.2.2+cpu...
    py -3.11 -c "import torch; v=torch.__version__; exit^(0 if v=='2.2.2+cpu' else 1^)" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] PyTorch 2.2.2+cpu ya instalado - saltando
    ) else (
        py -3.11 -m pip install --no-warn-script-location torch==2.2.2+cpu torchvision==0.17.2+cpu --index-url https://download.pytorch.org/whl/cpu
        if errorlevel 1 (
            echo [X] Error instalando PyTorch CPU
            pause
            exit /b 1
        )
        REM Eliminar stubs CUDA que fallan en sistemas sin drivers NVIDIA
        for /f "delims=" %%P in ('py -3.11 -c "import site; print^(site.getsitepackages^(^)[0]^)"') do set SITE_PKG=%%P
        del /f /q "!SITE_PKG!\torch\lib\c10_cuda.dll" >nul 2>&1
        del /f /q "!SITE_PKG!\torch\lib\c10d_cuda.dll" >nul 2>&1
        echo [OK] Stubs CUDA eliminados ^(no se necesitan en instalacion CPU^)
    )
    echo.

    echo [2/5] Comprobando paddlepaddle==3.2.2 ^(PINNED^)...
    py -3.11 -c "import pkg_resources; pkg_resources.require^('paddlepaddle==3.2.2'^)" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] paddlepaddle 3.2.2 ya instalado - saltando
    ) else (
        echo IMPORTANTE: paddlepaddle se pina a 3.2.2 ^(versiones >=3.3.0 tienen bug PIR/oneDNN en Windows^)
        py -3.11 -m pip install --no-warn-script-location paddlepaddle==3.2.2
        if errorlevel 1 (
            echo [W] Error con paddlepaddle, intentando continuar...
        )
    )
    py -3.11 -m pip show paddleocr >nul 2>&1
    if not errorlevel 1 (
        echo [OK] paddleocr ya instalado - saltando
    ) else (
        py -3.11 -m pip install --no-warn-script-location "paddleocr[doc-parser]"
    )
    echo.

    echo [3/5] Comprobando Docling...
    py -3.11 -m pip show docling >nul 2>&1
    if not errorlevel 1 (
        echo [OK] docling ya instalado - saltando
    ) else (
        py -3.11 -m pip install --no-warn-script-location docling
    )
    echo.

    echo [4/5] Instalando resto de paquetes ^(pip omite los ya satisfechos^)...
    REM Filtrar requirements.txt para excluir lineas con +cu118 ^(GPU^)
    findstr /V /C:"+cu118" requirements.txt > requirements_temp.txt
    py -3.11 -m pip install --no-warn-script-location -r requirements_temp.txt
    if errorlevel 1 (
        echo [X] Error instalando paquetes
        del requirements_temp.txt
        pause
        exit /b 1
    )
    del requirements_temp.txt
)
echo.

echo [5/5] Descargando modelo DocLayout-YOLO...
py -3.11 download_doclayout_model.py
if errorlevel 1 (
    echo [W] Error descargando modelo DocLayout-YOLO ^(puedes intentarlo manualmente despues^)
) else (
    echo [OK] Modelo DocLayout-YOLO descargado correctamente
)
echo.
echo NOTA: El modelo YOLO11 (Armaggheddon/yolo11-document-layout) se descarga
echo       automaticamente de Hugging Face en la primera ejecucion con --method yolo11
echo NOTA: Los modelos de PaddleOCR y Docling tambien se descargan en primera ejecucion
echo.

echo ================================================================================
echo VERIFICACION DE INSTALACION
echo ================================================================================
echo.

echo Verificando paquetes instalados...
py -3.11 -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
py -3.11 -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
py -3.11 -c "import numpy; print(f'NumPy: {numpy.__version__}')"
py -3.11 -c "from doclayout_yolo import YOLOv10; print('DocLayout-YOLO: OK')" 2>nul
py -3.11 -c "from ultralytics import YOLO; print('Ultralytics YOLO11: OK')" 2>nul
py -3.11 -c "from paddleocr import LayoutDetection; print('PaddleOCR LayoutDetection: OK')" 2>nul
py -3.11 -c "from docling.document_converter import DocumentConverter; print('Docling: OK')" 2>nul
py -3.11 -c "import easyocr; print('EasyOCR: OK')" 2>nul
py -3.11 -c "import pytesseract; print('PyTesseract: OK')" 2>nul
py -3.11 -c "import transformers; print('Transformers: OK')" 2>nul
py -3.11 -c "import accelerate, safetensors, tokenizers; print('DeepSeek deps: OK')" 2>nul
echo.

echo ================================================================================
echo INSTALACION COMPLETADA
echo ================================================================================
echo.
echo Metodos disponibles:
echo   opencv       - Rapido, proyeccion de columnas (CPU, sin modelo)
echo   doclayout    - DocLayout-YOLO YOLOv10 (mejor calidad general)
echo   yolo11       - YOLO11 fine-tuned DocLayNet (descarga auto en 1a ejecucion)
echo   paddleocr    - PaddleOCR LayoutDetection PP-DocLayout_plus-L (16 regiones)
echo   docling      - Docling RT-DETR IBM (15 regiones, descarga ~500 MB 1a vez)
echo.
echo Motores OCR disponibles para validate_ocr.py:
echo   easyocr      - OCR neuronal CPU/GPU
echo   tesseract    - OCR clasico ^(requiere binario instalado + pytesseract^)
echo   paddle       - OCR de PaddleOCR
echo   deepseek     - OCR VLM local ^(requiere GPU CUDA + modelo descargado^)
echo.
echo Proximos pasos:
echo 1. Probar cada metodo:
echo    py -3.11 detect_columns.py --image imgs/popurri01.jpg --method doclayout --debug
echo    py -3.11 detect_columns.py --image imgs/popurri01.jpg --method yolo11 --debug
echo    py -3.11 detect_columns.py --image imgs/popurri01.jpg --method paddleocr --debug
echo    py -3.11 detect_columns.py --image imgs/popurri01.jpg --method docling --debug
echo.
echo 2. Consultar documentacion:
echo    - plan_mejora_proyecto.md: Estado completo del proyecto (FASE 2.2 completada)
echo    - README.md: Documentacion de uso
echo.
echo ================================================================================
pause
