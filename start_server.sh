#!/bin/bash

# Start the Travel Planner API server

echo "========================================"
echo "  Travel Planner API Server"
echo "========================================"
echo ""
echo "Starting server on http://localhost:8000"
echo ""
echo "📚 API Documentation:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc:      http://localhost:8000/redoc"
echo "   - OpenAPI:    http://localhost:8000/openapi.json"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Start the server
uvicorn api:app --reload --host 0.0.0.0 --port 8000
