Set-Location "E:\Проекты\MoodWatch"
& ".venv\Scripts\Activate.ps1"
python -m streamlit run src/app.py
if ($LASTEXITCODE -ne 0) {
    Read-Host "Press Enter to close"
}
