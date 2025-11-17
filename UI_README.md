# Checkpoint UI - Quick Start Guide

## What Is This?

A simple HTML prototype for the **checkpoint approval flow** where users review and approve AI-generated research plans.

## How To Use

### 1. Start the FastAPI Server

```bash
export DATABASE_URL="sqlite:///./research_assistant.db"
export REDIS_URL="redis://localhost:6379"
export OPENAI_API_KEY="test-key"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Open the UI in Your Browser

```bash
# Option A: Open with default test project
open checkpoint_ui.html
# or on Linux: xdg-open checkpoint_ui.html

# Option B: Open with specific project ID
open "checkpoint_ui.html?project_id=YOUR_PROJECT_ID"
```

### 3. What You'll See

The UI displays:
- ✅ Original research goal
- ✅ AI analysis with refined goal, complexity, domains
- ✅ Proposed task list
- ✅ Two buttons: "Yes, continue" and "Let me clarify"

---

## Creating Test Data

### Create a New Project via API

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer TEST_AUTH_TOKEN" \
  -F "original_research_goal=Analyze COVID-19 spike protein mutations" \
  -F "context_docs=@your_file.pdf"
```

This returns a `project_id`. Wait ~10 seconds for the AI agent to process it, then:

```bash
# Check if analysis is complete
curl -X GET "http://localhost:8000/api/v1/projects/{project_id}" \
  -H "Authorization: Bearer TEST_AUTH_TOKEN"
```

When `refined_research_goal` is not null, the analysis is done!

### View in UI

```bash
open "checkpoint_ui.html?project_id={project_id}"
```

---

## Current State

### ✅ What Works
- Fetches project data from GET `/api/v1/projects/{id}`
- Displays checkpoint message in wireframe format
- Shows task list
- Responsive design (mobile-friendly)
- Error handling for 404/401/403

### 🚧 What's Not Implemented Yet
- "Yes, continue" button (just logs to console)
- "Let me clarify" dialog (just shows alert)
- Approval state persistence
- Multi-project navigation

---

## UI Architecture

**Single-file HTML** - No build tools, no framework bloat:
- **TailwindCSS** (via CDN) for styling
- **Vanilla JavaScript** for API calls
- **REST API** communication via fetch()

**Why this approach?**
- Fast iteration
- No dependencies to install
- Easy to understand and modify
- Works in any modern browser

---

## Next Steps

To make this production-ready:

1. **Implement approval flow**: POST to `/api/v1/projects/{id}/approve`
2. **Add clarification dialog**: Mini-chat to refine the goal
3. **Add authentication**: Real login instead of hardcoded token
4. **Add upload UI**: File upload + goal input form
5. **Polish styling**: Match your brand guidelines

---

## Files

- `checkpoint_ui.html` - The UI (single file)
- `UI_README.md` - This file
- API backend at `app/api/v1/endpoints/projects.py`

---

## Troubleshooting

**"Failed to fetch"** error?
- Make sure FastAPI server is running on port 8000
- Check CORS settings if serving from different domain

**"Project not found"** error?
- The default project ID might not exist in your DB
- Create a new project via POST endpoint
- Or update `PROJECT_ID` in the HTML file

**Old message format showing?**
- Projects created before the refactor have verbose messages
- Create a new project to see the new format
- Or manually update the message in the database
