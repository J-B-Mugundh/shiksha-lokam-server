## 📁 Project Folder Structure

```
shiksha-lokam-backend/
├── main.py                           # ✅ Main entry point
├── .env                              
├── requirements.txt                  
├── routes/
│   ├── __init__.py                   
│   ├── user_routes.py                
│   ├── organization_routes.py        
│   ├── impact_routes.py              
│   ├── outcome_routes.py             
│   ├── theme_routes.py               
│   ├── lfa_routes.py                 
│   ├── school_routes.py              
│   └── ai_generation_routes.py       
├── models/
│   ├── __init__.py                   
│   └── schemas.py                    
└── .cache/
    └── huggingface/                  
```

---

## 🔧 Step-by-Step Setup

### Create `.env` file

Create a `.env` file in the project root with these variables:

```env
# MongoDB Connection
MONGODB_URI=mongodb+srv://your-username:your-password@cluster.mongodb.net/?retryWrites=true&w=majority

# HuggingFace API Token (for AI generation)
HF_TOKEN=hf_your_token_here
```

**How to get these:**
- **MongoDB URI**: Sign up at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas), create a free cluster, and get the connection string
- **HF Token**: Sign up at [HuggingFace](https://huggingface.co/), go to Settings → Access Tokens → Create Token


---

## 🧪 Testing Your APIs

### Option 1: FastAPI Docs (Easiest)

Go to: **http://localhost:8000/docs**

You'll see an interactive API documentation where you can test all endpoints.

### Option 2: Using cURL

```bash
# 1. Health Check
curl http://localhost:8000/health

# 2. Register a User
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "password123"
  }'

# 3. Create an Organization
curl -X POST http://localhost:8000/api/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech for Good NGO",
    "org_type": "ngo",
    "state": "Karnataka",
    "district": "Bangalore",
    "focus_areas": ["FLN", "Career Readiness"]
  }'

# 4. Create a Theme
curl -X POST http://localhost:8000/api/themes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Foundational Literacy & Numeracy",
    "short_name": "FLN",
    "description": "Focus on basic reading and math skills",
    "challenge_statements": ["Low literacy rates", "Poor numeracy skills"]
  }'
```

---

## 📋 Your Complete API List

### Users
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - Login user
- `GET /api/users/me?user_id={id}` - Get current user
- `GET /api/users/{user_id}` - Get user by ID
- `PATCH /api/users/{user_id}` - Update user
- `POST /api/users/{user_id}/organizations` - Add user to org
- `GET /api/users/{user_id}/gamification` - Get XP/achievements
- `DELETE /api/users/{user_id}` - Deactivate user

### Organizations
- `POST /api/organizations` - Create organization
- `GET /api/organizations` - List all organizations
- `GET /api/organizations/{org_id}` - Get organization
- `PATCH /api/organizations/{org_id}` - Update organization
- `PATCH /api/organizations/{org_id}/verify` - Verify organization
- `GET /api/organizations/{org_id}/lfas` - Get org's LFAs
- `GET /api/organizations/{org_id}/stats` - Get statistics
- `DELETE /api/organizations/{org_id}` - Delete organization

### Impacts
- `POST /api/impacts` - Create impact
- `GET /api/impacts` - List impacts
- `GET /api/impacts/templates` - Get templates
- `GET /api/impacts/{impact_id}` - Get impact
- `PATCH /api/impacts/{impact_id}` - Update impact
- `DELETE /api/impacts/{impact_id}` - Delete impact
- `GET /api/impacts/categories/list` - Get categories

### Outcomes
- `POST /api/outcomes` - Create outcome
- `GET /api/outcomes` - List outcomes
- `GET /api/outcomes/templates` - Get templates
- `GET /api/outcomes/{outcome_id}` - Get outcome
- `PATCH /api/outcomes/{outcome_id}` - Update outcome
- `DELETE /api/outcomes/{outcome_id}` - Delete outcome
- `GET /api/outcomes/stakeholders/list` - Get stakeholder types

### Themes
- `POST /api/themes` - Create theme
- `GET /api/themes` - List themes
- `GET /api/themes/{theme_id}` - Get theme
- `PATCH /api/themes/{theme_id}` - Update theme
- `DELETE /api/themes/{theme_id}` - Deactivate theme
- `GET /api/themes/{theme_id}/lfas` - Get theme's LFAs

### LFAs (Main Feature!)
- `POST /api/lfas` - Create LFA manually
- `GET /api/lfas` - List all LFAs
- `GET /api/lfas/{lfa_id}` - Get LFA with full details
- `PATCH /api/lfas/{lfa_id}` - Update LFA
- `POST /api/lfas/{lfa_id}/submit` - Submit for review
- `POST /api/lfas/{lfa_id}/reviews` - Submit review
- `GET /api/lfas/{lfa_id}/reviews` - Get reviews
- `DELETE /api/lfas/{lfa_id}` - Delete LFA

### Schools
- `POST /api/schools/enroll` - Enroll school
- `GET /api/schools` - List schools
- `GET /api/schools/{progress_id}` - Get school progress
- `PATCH /api/schools/{progress_id}/actions/{index}` - Update action
- `GET /api/schools/execution/{exec_id}/summary` - Get summary
- `DELETE /api/schools/{progress_id}` - Remove school

### AI Generation
- `POST /api/ai/generate-lfa` - Generate full LFA with AI
- `POST /api/ai/suggest-impacts` - Get impact suggestions
- `POST /api/ai/suggest-outcomes` - Get outcome suggestions
- `GET /api/ai/health` - Check AI service status

---

## 🎯 Testing Workflow

### Full Flow Test (Do this in order):

```bash
# 1. Register a user
# Use /docs, save the user_id from response

# 2. Create an organization
# Save the org_id

# 3. Add user to organization
POST /api/users/{user_id}/organizations
{
  "organization_id": "{org_id}",
  "role": "Program Manager"
}

# 4. Create a theme
# Save the theme_id

# 5. Create impacts (2-3 templates)
POST /api/impacts
{
  "impact_statement": "Improved student reading comprehension",
  "category": "Student Learning",
  "indicators": [
    {
      "indicator_text": "% of students reading at grade level",
      "baseline_value": "30%",
      "target_value": "70%",
      "measurement_method": "ASER assessment"
    }
  ],
  "is_template": true
}

# 6. Create outcomes (2-3 templates)
POST /api/outcomes
{
  "outcome_statement": "Teachers effectively use phonics-based teaching methods",
  "stakeholder_type": "Teachers",
  "indicators": [
    {
      "indicator_text": "% of teachers demonstrating correct phonics instruction",
      "baseline_value": "20%",
      "target_value": "80%",
      "measurement_method": "Classroom observation rubric"
    }
  ],
  "is_template": true
}

# 7. Generate LFA with AI (THE COOL PART!)
POST /api/ai/generate-lfa
{
  "prompt": "Create a program to improve foundational literacy in grades 1-3 in rural Karnataka. Focus on phonics-based instruction and teacher training.",
  "organization_id": "{org_id}",
  "created_by": "{user_id}",
  "theme_id": "{theme_id}",
  "target_grades": ["1", "2", "3"]
}

# 8. Review the generated LFA
GET /api/lfas/{lfa_id}

# 9. Submit for review
POST /api/lfas/{lfa_id}/submit

# 10. Approve it
POST /api/lfas/{lfa_id}/reviews?reviewer_id={user_id}
{
  "decision": "approved",
  "summary_feedback": "Excellent program design!",
  "detailed_feedback": []
}
```

---

## 🐛 Common Issues & Solutions

### Issue 1: MongoDB Connection Failed
```
Error: ServerSelectionTimeoutError
```
**Solution:** 
- Check your MongoDB URI in `.env`
- Make sure your IP is whitelisted in MongoDB Atlas (Network Access)
- Check if MongoDB cluster is running

### Issue 2: HuggingFace Token Error
```
Error: HF_TOKEN not found
```
**Solution:**
- Make sure `.env` file exists in project root
- Verify `HF_TOKEN=hf_...` is correctly set
- Restart the server after adding the token

### Issue 3: Import Errors
```
ModuleNotFoundError: No module named 'routes'
```
**Solution:**
- Make sure `__init__.py` exists in `routes/` folder
- Run server from the project root directory
- Check that all route files are in `routes/` folder

### Issue 4: AI Generation Returns Invalid JSON
```
AI generated invalid JSON
```
**Solution:**
- The model sometimes adds markdown formatting
- The code already handles this with cleanup
- If it still fails, try simplifying your prompt
- Make sure HuggingFace API is not rate-limited

---

## 📊 Data Flow Diagram

```
User Register
    ↓
User Joins Organization
    ↓
Create Theme (Optional)
    ↓
Create Impact/Outcome Templates (Optional)
    ↓
Generate LFA with AI ← Uses templates + AI
    ↓
Review & Edit LFA
    ↓
Submit for Approval
    ↓
Reviewer Approves
    ↓
[Phase  2 takes over: Create Execution]
```

---

## ✅ Checklist Before Handoff to Phase 2

- [ ] All APIs working in `/docs`
- [ ] Can register user and create organization
- [ ] Can create themes, impacts, outcomes
- [ ] AI generation working (test with simple prompt)
- [ ] Can create LFA manually
- [ ] Can submit and approve LFA
- [ ] MongoDB has sample data (at least 1 approved LFA)
- [ ] Schools can be enrolled (basic test)

---

## 🤝 Handoff to 2nd Phase

Once your APIs are working, 2nd Phase needs:

1. **Your MongoDB connection string** (same `.env`)
2. **At least 1 approved LFA** in the database
3. **The LFA ID** to test execution creation
4. **Organization ID and User ID** for testing

**What Phase 2 will build:**
- Execution creation (when LFA approved)
- Action management
- Result submission
- Corrective actions

**Integration point:**
- When you approve an LFA (`status` = "approved"), Phase 2 code will create an `Execution` from it

---

## 📞 Need Help?

- Check `/docs` for live API documentation
- Use `/health` endpoint to verify MongoDB connection
- Use `/api/ai/health` to verify HuggingFace connection
- Check console logs for detailed error messages