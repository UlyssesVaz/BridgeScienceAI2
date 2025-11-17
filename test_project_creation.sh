#!/bin/bash

# Test Project Creation API
# Make sure FastAPI server is running on http://localhost:8000

API_URL="http://localhost:8000/api/v1/projects"
AUTH_TOKEN="TEST_AUTH_TOKEN"

echo "Testing project creation..."
echo ""

# Simple test without file upload
curl -X POST "$API_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "original_research_goal=Analyze the protein structure of SARS-CoV-2 spike protein and identify potential drug targets" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -v

echo ""
echo "If successful, you should see:"
echo "  - HTTP 202 (Accepted)"
echo "  - project_id in response"
echo "  - Check worker logs for job processing"
