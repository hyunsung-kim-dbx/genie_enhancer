#!/bin/bash

# Local development startup script for Genie Lamp Agent
# Starts both backend and frontend in parallel

set -e

echo "🚀 Starting Genie Lamp Agent locally..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the project root directory
if [ ! -f "app/app.yaml" ] || [ ! -f "app/databricks.yml" ]; then
    echo -e "${RED}Error: Must be run from project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/start-local.sh${NC}"
    exit 1
fi

# Check Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python not found${NC}"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js not found${NC}"
    exit 1
fi

# Backend setup
echo -e "${YELLOW}Setting up backend...${NC}"
cd app/backend

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

source .venv/bin/activate

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: backend/.env not found, copying from .env.example${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  Please edit backend/.env with your Databricks credentials${NC}"
fi

echo "Installing backend dependencies..."
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Backend setup complete${NC}"
cd ../..

# Frontend setup
echo -e "${YELLOW}Setting up frontend...${NC}"
cd app/frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Warning: frontend/.env.local not found, copying from .env.example${NC}"
    cp .env.example .env.local
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"
cd ../..

# Start services
echo ""
echo -e "${GREEN}Starting services...${NC}"
echo ""

# Start backend in background
echo -e "${YELLOW}Starting backend on http://localhost:8000${NC}"
cd app/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend started successfully${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: Backend failed to start${NC}"
        echo "Check backend.log for details"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Start frontend in background
echo -e "${YELLOW}Starting frontend on http://localhost:3000${NC}"
cd app/frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

# Wait for frontend to start
echo "Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend started successfully${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: Frontend failed to start${NC}"
        echo "Check frontend.log for details"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Genie Lamp Agent is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f backend.log"
echo -e "  Frontend: tail -f frontend.log"
echo ""
echo -e "${YELLOW}To stop:${NC}"
echo -e "  Press Ctrl+C or run: ./stop-local.sh"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Save PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for user interrupt
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; echo 'Done'; exit 0" INT TERM

# Keep script running
wait
