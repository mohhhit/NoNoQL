@echo off
REM TexQL Local Training Batch Script for Windows
REM Optimized for GTX 1060 3GB

echo ========================================
echo TexQL Local Training
echo ========================================
echo.

REM Check if data directory exists
if not exist "data\train.csv" (
    echo [ERROR] Training data not found!
    echo Please run: python data_generation.py
    echo.
    pause
    exit /b 1
)

echo [INFO] Training data found
echo.

REM Ask user which model to train
echo Which model do you want to train?
echo 1. SQL Model
echo 2. MongoDB Model
echo 3. Both (SQL first, then MongoDB)
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" goto train_sql
if "%choice%"=="2" goto train_mongodb
if "%choice%"=="3" goto train_both
echo [ERROR] Invalid choice
pause
exit /b 1

:train_sql
echo.
echo ========================================
echo Training SQL Model
echo ========================================
echo This will take approximately 20-30 hours
echo You can leave it running overnight
echo.
echo Starting in 5 seconds... (Ctrl+C to cancel)
timeout /t 5
python train_local.py --target sql --epochs 10 --batch-size 2
if errorlevel 1 (
    echo.
    echo [ERROR] Training failed!
    echo Try: python train_local.py --target sql --batch-size 1
    pause
    exit /b 1
)
echo.
echo ========================================
echo SQL Model Training Complete!
echo ========================================
goto end

:train_mongodb
echo.
echo ========================================
echo Training MongoDB Model
echo ========================================
echo This will take approximately 20-30 hours
echo You can leave it running overnight
echo.
echo Starting in 5 seconds... (Ctrl+C to cancel)
timeout /t 5
python train_local.py --target mongodb --epochs 10 --batch-size 2
if errorlevel 1 (
    echo.
    echo [ERROR] Training failed!
    echo Try: python train_local.py --target mongodb --batch-size 1
    pause
    exit /b 1
)
echo.
echo ========================================
echo MongoDB Model Training Complete!
echo ========================================
goto end

:train_both
echo.
echo ========================================
echo Training Both Models (Sequential)
echo ========================================
echo This will take approximately 40-60 hours total
echo SQL model first, then MongoDB model
echo.
echo Starting in 10 seconds... (Ctrl+C to cancel)
timeout /t 10

echo.
echo [1/2] Training SQL Model...
python train_local.py --target sql --epochs 10 --batch-size 2
if errorlevel 1 (
    echo.
    echo [ERROR] SQL training failed!
    pause
    exit /b 1
)

echo.
echo [1/2] SQL Model Complete!
echo.
echo [2/2] Training MongoDB Model...
timeout /t 5
python train_local.py --target mongodb --epochs 10 --batch-size 2
if errorlevel 1 (
    echo.
    echo [ERROR] MongoDB training failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Both Models Training Complete!
echo ========================================

:end
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Test your model:
echo    python inference.py --model-path models/texql-sql-final --type sql --interactive
echo.
echo 2. Run Streamlit app:
echo    streamlit run app.py
echo.
echo 3. View training logs in: models/
echo ========================================
echo.
pause
