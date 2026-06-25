@echo off
cd /d E:\Проекты\MoodWatch
call .venv\Scripts\activate.bat
python -m streamlit run src/app.py
if errorlevel 1 pause
