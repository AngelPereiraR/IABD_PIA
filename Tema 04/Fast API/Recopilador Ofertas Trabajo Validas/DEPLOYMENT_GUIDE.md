# Deployment Guide - OptiCV Frontend

## Vercel Deployment

### Prerequisites
- GitHub repository with frontend code
- Vercel account (https://vercel.com)
- Environment variables ready

### Step 1: Connect Repository to Vercel

1. Go to https://vercel.com/new
2. Select "Import Git Repository"
3. Choose your GitHub repository
4. Select `frontend` directory (if monorepo)
5. Click "Deploy"

### Step 2: Configure Environment Variables

In Vercel Dashboard → Project Settings → Environment Variables:

```
VITE_API_URL = https://your-backend-domain.com
VITE_GOOGLE_CLIENT_ID = your_google_client_id_here
```

Add for: Production, Preview, Development

### Step 3: Build Settings

- **Framework:** Vite
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

Vercel should auto-detect these, but verify:

1. Go to Settings → Git → Deploy Hooks
2. Ensure build command is: `npm run build`
3. Output directory: `dist`

### Step 4: Deploy

```bash
# Vercel CLI (if preferred)
npm install -g vercel
cd frontend
vercel --prod
```

Or push to GitHub and Vercel will auto-deploy.

### Step 5: Verify Deployment

- [ ] Visit `your-project.vercel.app`
- [ ] Check that app loads
- [ ] Test login (will fail without backend, expected)
- [ ] Check console for errors
- [ ] Verify environment variables are set
- [ ] Test API calls to backend

---

## Alternative: Docker + Self-Hosted

### Step 1: Create Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Step 2: Build & Run

```bash
cd frontend
docker build -t opticv-frontend:latest .
docker run -p 3000:3000 \
  -e VITE_API_URL=http://your-backend:7860 \
  opticv-frontend:latest
```

### Step 3: Push to Registry

```bash
docker tag opticv-frontend:latest your-registry/opticv-frontend:latest
docker push your-registry/opticv-frontend:latest
```

---

## Production Optimization Checklist

- [ ] **Build Size**
  ```bash
  npm run build
  # dist/ should be <500KB total
  ```

- [ ] **Performance Metrics**
  - [ ] Lighthouse score >80
  - [ ] Core Web Vitals good
  - [ ] Time to Interactive <3s

- [ ] **Security**
  - [ ] No console errors
  - [ ] CSP headers configured
  - [ ] HTTPS enforced
  - [ ] Sensitive data not exposed

- [ ] **Environment Variables**
  - [ ] VITE_API_URL points to production backend
  - [ ] VITE_GOOGLE_CLIENT_ID is production ID
  - [ ] No hardcoded secrets

- [ ] **API Endpoints**
  - [ ] All endpoints point to production
  - [ ] CORS configured on backend
  - [ ] Rate limiting in place

---

## Troubleshooting

### Build Fails
```
Error: Missing dependency @hookform/resolvers
→ Run: npm install @hookform/resolvers
```

### Environment Variables Not Working
```
→ Restart build after setting env vars
→ Check VITE_ prefix (Vite requires this)
→ Verify in Vercel dashboard
```

### API Calls Failing
```
→ Check VITE_API_URL in Vercel env vars
→ Verify backend CORS allows frontend origin
→ Check backend is accessible
```

### Session Lost After Refresh
```
→ Check browser localStorage (should have token)
→ Verify session restoration in globalStore
→ Check if auth interceptor working
```

### White Screen / 404
```
→ Check dist/ folder exists
→ Verify package.json build script
→ Check Vercel build logs
→ Ensure vercel.json has correct rewrites
```

---

## Monitoring

### Enable Analytics
1. Vercel Dashboard → Analytics
2. Track page performance
3. Monitor API latency

### Logging
1. Browser console (client-side)
2. Backend logs (server-side)
3. Vercel function logs

---

## Rollback

If deployment has issues:

```bash
# Via Vercel CLI
vercel rollback

# Or select previous deployment in dashboard
# Settings → Deployments → Select previous → Promote
```

---

## CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Vercel

on:
  push:
    branches:
      - main
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install
      - run: cd frontend && npm run build
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
```

---

## Post-Deployment

1. **Test All Features**
   - [ ] Complete auth flow
   - [ ] CV upload & delete
   - [ ] Analysis creation
   - [ ] PDF download

2. **Monitor Performance**
   - [ ] Check Vercel analytics
   - [ ] Monitor API response times
   - [ ] Track error rates

3. **Collect User Feedback**
   - [ ] Test with real users
   - [ ] Gather feedback
   - [ ] Fix issues iteratively

4. **Set Up Alerts**
   - [ ] Failed deployments
   - [ ] API errors
   - [ ] Performance degradation

---

## Maintenance

### Weekly
- [ ] Check deployment logs
- [ ] Monitor error rates
- [ ] Review performance metrics

### Monthly
- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance optimization
- [ ] User feedback review

### Quarterly
- [ ] Major version updates
- [ ] Architecture review
- [ ] Capacity planning
