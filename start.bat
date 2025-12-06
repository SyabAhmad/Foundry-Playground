@echo off
echo Starting Foundry Playground...

echo Initializing database...
cd backend
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"
cd ..

echo Starting backend server...
start cmd /k "cd backend && python app.py"

timeout /t 3 /nobreak > nul

echo Starting frontend server...
start cmd /k "cd frontend && npm run dev"

echo.
echo Foundry Playground is starting up!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Make sure Foundry Local is running on http://127.0.0.1:56831/
echo You can start it with: foundry service start
pause