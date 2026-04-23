# E2E Testing Guide

## Prerequisites

- FastAPI backend running on `http://localhost:7860`
- Frontend dev server running on `http://localhost:5173`
- Valid test credentials for API endpoints

---

## 🚀 Setup & Running

### 1. Start Backend

```bash
# In the backend directory
python main.py
# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

Verify health at: `http://localhost:7860/health`

### 2. Start Frontend Dev Server

```bash
cd frontend
npm run dev
```

Navigate to: `http://localhost:5173`

---

## ✅ Manual Testing Checklist

### Test Suite 1: Authentication

#### 1.1 User Registration
- [ ] Navigate to `/auth/register`
- [ ] Fill in name, email, password
- [ ] Submit form
- [ ] Should redirect to dashboard
- [ ] Verify user info in sidebar

#### 1.2 User Login
- [ ] Navigate to `/auth/login`
- [ ] Enter registered email & password
- [ ] Click "Login"
- [ ] Should redirect to dashboard
- [ ] Verify token in localStorage

#### 1.3 Session Persistence
- [ ] After login, refresh page
- [ ] User should still be logged in
- [ ] Check localStorage for token & user

#### 1.4 Logout
- [ ] Click logout button (top-right navbar)
- [ ] Should redirect to landing page
- [ ] localStorage should be cleared
- [ ] Trying to access `/dashboard` should redirect to login

#### 1.5 Token Expiry
- [ ] Manually delete token from localStorage
- [ ] Try to access protected route
- [ ] Should redirect to login

---

### Test Suite 2: CV Management

#### 2.1 CV Upload
- [ ] Navigate to `/dashboard/cv`
- [ ] Drag & drop a valid PDF file
- [ ] OR click upload area and select file
- [ ] Should show "CV Uploaded" status
- [ ] Preview should appear with file info

#### 2.2 Invalid File Upload
- [ ] Try to upload non-PDF file
- [ ] Should show error message
- [ ] "Invalid file type or size"

#### 2.3 CV Preview
- [ ] After successful upload
- [ ] CV preview should show filename
- [ ] Delete button should be visible

#### 2.4 CV Deletion
- [ ] Click delete button
- [ ] Confirmation dialog appears
- [ ] Confirm deletion
- [ ] CV should be removed
- [ ] Status should change to "No CV"

#### 2.5 CV Required Guard
- [ ] Without CV, navigate to `/dashboard/analysis`
- [ ] Should redirect to `/dashboard/cv`

---

### Test Suite 3: Job Offer Analysis

#### 3.1 Analysis by URL
- [ ] Navigate to `/dashboard/analysis`
- [ ] Select "URL" tab
- [ ] Paste valid job URL (e.g., LinkedIn)
- [ ] Click "Analyze Offer"
- [ ] Loading spinner should appear
- [ ] Results should display:
  - [ ] Job title
  - [ ] Company
  - [ ] Match score (0-100)
  - [ ] Valid/Not Suitable status
  - [ ] Salary (if available)
  - [ ] Location
  - [ ] Benefits (if available)

#### 3.2 Analysis by Text
- [ ] Select "Text" tab
- [ ] Paste job description (50-5000 chars)
- [ ] Click "Analyze Offer"
- [ ] Results should display same as URL analysis

#### 3.3 Form Validation
- [ ] Try to submit empty form → Should show error
- [ ] Try short text (<50 chars) → Should show error
- [ ] Try invalid URL → Should show error

#### 3.4 Analysis History
- [ ] Create multiple analyses
- [ ] Navigate to `/dashboard/analysis/history`
- [ ] Should show paginated list
- [ ] Each item should show:
  - [ ] Score badge
  - [ ] Title & company
  - [ ] Valid/Not Suitable badge
  - [ ] "View" button

#### 3.5 History Pagination
- [ ] Create >10 analyses
- [ ] History should paginate (limit 10 per page)
- [ ] Previous/Next buttons should work
- [ ] Page number should update

#### 3.6 View Specific Analysis
- [ ] From history, click "View" on an item
- [ ] Should navigate to `/dashboard/analysis/:id`
- [ ] Should show detailed result card
- [ ] If score >= 50 (valid), show "Generate CV Adaptation" button

---

### Test Suite 4: CV Adaptation

#### 4.1 Generate Adaptation
- [ ] View a valid offer result (is_valid=true)
- [ ] Click "Generate CV Adaptation"
- [ ] Navigate to `/dashboard/adaptations/:analysisId`
- [ ] Loading spinner should appear
- [ ] HTML preview should show adapted CV

#### 4.2 HTML Preview
- [ ] Adapted CV should display nicely formatted
- [ ] Should include highlights for matched keywords
- [ ] Should be readable on screen

#### 4.3 PDF Download
- [ ] Click "Download PDF" button
- [ ] PDF should download to device
- [ ] Filename should be `cv_adaptation_[id].pdf`
- [ ] PDF should be readable

#### 4.4 Invalid Offer
- [ ] For non-valid offers, adaptation button should not appear
- [ ] Clicking back should not attempt generation

---

### Test Suite 5: UI/UX

#### 5.1 Navigation
- [ ] Sidebar links should work
- [ ] Active state should highlight current page
- [ ] Logo should navigate to home

#### 5.2 Responsive Design
- [ ] Test on mobile (375px width)
- [ ] Test on tablet (768px width)
- [ ] Test on desktop (1920px width)
- [ ] Sidebar should collapse on mobile
- [ ] Forms should stack vertically

#### 5.3 Error Handling
- [ ] Network error → Should show user-friendly message
- [ ] 401 Unauthorized → Should redirect to login
- [ ] 404 Not Found → Should show "Not found"
- [ ] 429 Too Many Requests → Should show rate limit message
- [ ] 500 Server Error → Should show "Try again later"

#### 5.4 Loading States
- [ ] Auth form: "Logging in..." / "Registering..." button text
- [ ] CV upload: Progress/spinner visible
- [ ] Analysis: Loading spinner with "Analyzing..." text
- [ ] Adaptation: Loading spinner with "Generating adapted CV..." text

#### 5.5 Toast Notifications
- [ ] Success message after login
- [ ] Error message on failed upload
- [ ] Confirmation after CV deletion
- [ ] Error message on API failures

---

## 🔍 Browser DevTools Testing

### 1. Network Tab
- [ ] Verify all API calls to `http://localhost:7860`
- [ ] Check request headers include `Authorization: Bearer <token>`
- [ ] Verify response status codes (200, 201, 400, 401, etc.)
- [ ] Check response payloads match expected structure

### 2. Application Tab
- [ ] localStorage should contain:
  - [ ] `token` (JWT string)
  - [ ] `user` (JSON with email, id, etc.)
- [ ] Verify data is cleared on logout

### 3. Console
- [ ] No JavaScript errors
- [ ] No 404s for assets
- [ ] Check for any deprecation warnings

---

## 🚨 Error Scenario Testing

### Scenario 1: Network Offline
1. Disable network in browser DevTools
2. Try to analyze offer
3. Should show "Network error" message
4. Enable network, retry should work

### Scenario 2: Invalid Token
1. Login successfully
2. Manually modify token in localStorage (corrupt it)
3. Try API call
4. Should get 401 and redirect to login

### Scenario 3: Multiple Tabs
1. Login in Tab A
2. Open app in Tab B
3. Both should be authenticated
4. Logout in Tab A
5. Tab B should also be logged out on next action

---

## 📊 Performance Testing

### Build Performance
```bash
npm run build
# Check dist/ folder size (target: <500KB)
# Check gzip size (target: <150KB)
```

### Runtime Performance
1. Open DevTools → Performance tab
2. Analyze first page load
3. Analyze navigation between pages
4. Check for memory leaks (Open multiple analyses)

---

## 📝 Test Report Template

Create `tests/E2E_RESULTS.md`:

```markdown
# E2E Testing Results

**Date:** YYYY-MM-DD  
**Tester:** Name  
**Frontend Version:** [git commit]  
**Backend Version:** [git commit]

## Test Suites

### Authentication ✅/❌
- Registration: ✅/❌
- Login: ✅/❌
- Session Persistence: ✅/❌
- Logout: ✅/❌
- Token Expiry: ✅/❌

### CV Management ✅/❌
- Upload: ✅/❌
- Invalid File: ✅/❌
- Preview: ✅/❌
- Deletion: ✅/❌
- CV Guard: ✅/❌

### Analysis ✅/❌
- URL Analysis: ✅/❌
- Text Analysis: ✅/❌
- Form Validation: ✅/❌
- History: ✅/❌
- Pagination: ✅/❌

### Adaptation ✅/❌
- Generate: ✅/❌
- Preview: ✅/❌
- Download: ✅/❌

### UI/UX ✅/❌
- Navigation: ✅/❌
- Responsive: ✅/❌
- Error Handling: ✅/❌
- Loading States: ✅/❌
- Notifications: ✅/❌

## Issues Found
- [Issue #1 - Description]
- [Issue #2 - Description]

## Notes
- Performance good/acceptable/needs work
- No major blocking issues found
```

---

## 🎯 Success Criteria

All tests pass when:
- ✅ All authentication flows work
- ✅ CV upload/management functional
- ✅ Analysis creates results correctly
- ✅ Adaptation generates and downloads PDFs
- ✅ Responsive on all screen sizes
- ✅ No JavaScript console errors
- ✅ All API calls successful
- ✅ Error messages clear and helpful
- ✅ Loading states visible
- ✅ Session management works

---

## 🔗 Quick Links

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:7860`
- Backend Docs: `http://localhost:7860/docs`
- Backend ReDoc: `http://localhost:7860/redoc`
