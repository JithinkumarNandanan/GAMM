# PowerShell script to pull the required Ollama model
# Run this first: .\setup_ollama_model.ps1

Write-Host "Pulling gemma3:4b model from Ollama..." -ForegroundColor Yellow
ollama pull gemma3:4b

Write-Host "`nVerifying installation..." -ForegroundColor Yellow
ollama list

Write-Host "`nDone! Now you can run: python test_unit_inference.py" -ForegroundColor Green
