# PowerShell script to pull the required Ollama model
# Run this first: .\setup_ollama_model.ps1

Write-Host "Pulling llama3.2 model from Ollama..." -ForegroundColor Yellow
ollama pull llama3.2

Write-Host "`nVerifying installation..." -ForegroundColor Yellow
ollama list

Write-Host "`nDone! Now you can run: python test_unit_inference.py" -ForegroundColor Green
