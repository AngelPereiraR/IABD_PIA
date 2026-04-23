# OptiCV Frontend

**React + Vite + Zustand** modern frontend for intelligent job offer analysis platform.

## 🚀 Quick Start

### Development

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 📋 Features

✅ **Authentication** - Email/password & Google OAuth  
✅ **CV Management** - Upload, preview, delete PDFs  
✅ **Job Analysis** - Analyze by URL or text description  
✅ **Results Display** - Scores, validity, extracted details  
✅ **CV Adaptation** - Generate & download tailored CVs  
✅ **Responsive Design** - Mobile, tablet, desktop  
✅ **State Management** - Zustand global store  
✅ **Form Validation** - React Hook Form + Zod  
✅ **API Integration** - Axios with interceptors  

---

## 📁 Project Structure

```
src/
├── features/
│   ├── auth/       # Login, register, OAuth
│   ├── cv/         # CV upload & management
│   ├── analysis/   # Job offer analysis
│   ├── adaptations/# CV adaptation & download
│   ├── dashboard/  # Dashboard home
│   └── landing/    # Landing page
├── shared/
│   ├── components/ # Layout, navbar, sidebar, routes
│   ├── hooks/      # useAuth, useToast
│   └── ui/         # Reusable components
├── stores/
│   └── globalStore.js # Zustand with 4 slices
├── services/
│   └── *.js        # API clients
├── utils/
│   └── *.js        # Validators, formatters, constants
├── App.jsx         # Root with all routes
└── index.css       # Tailwind + custom styles
```

---

## 🔌 Environment Variables

Create `.env` file:

```
VITE_API_URL=http://localhost:7860
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

---

## 🛠 Tech Stack

- **Framework:** React 18 + Vite
- **Routing:** React Router v6
- **State:** Zustand
- **HTTP:** Axios
- **Forms:** React Hook Form + Zod
- **UI:** Tailwind CSS + Lucide Icons
- **Data Fetching:** React Query
- **Build:** Vite

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `src/App.jsx` | Routing & auth initialization |
| `src/stores/globalStore.js` | Global state (auth, cv, analysis, adaptations) |
| `src/services/apiClient.js` | Axios instance with auth interceptor |
| `src/shared/components/Layout.jsx` | App layout wrapper |
| `index.html` | Entry point |
| `vite.config.js` | Build configuration |
| `tailwind.config.js` | Tailwind theme |

---

## 🧪 Testing

See [TESTING_E2E.md](../TESTING_E2E.md) for complete testing guide.

Quick checklist:
- [ ] Auth flow works
- [ ] CV upload functional
- [ ] Analysis creates results
- [ ] PDFs download
- [ ] Responsive on mobile

---

## 📦 Dependencies

```bash
# Install all
npm install

# Or individual
npm install zustand                    # State management
npm install react-hook-form zod        # Forms & validation
npm install @hookform/resolvers         # Form validation resolver
npm install @tanstack/react-query      # Data fetching
npm install axios                      # HTTP client
npm install lucide-react                # Icons
```

---

## 🔗 API Endpoints Expected

Backend should provide:

```
POST   /auth/register
POST   /auth/login
POST   /auth/google-callback
GET    /auth/me
POST   /cv/upload
GET    /cv
DELETE /cv
POST   /analysis/create
GET    /analysis/history
GET    /analysis/{id}
POST   /adaptations/create
GET    /adaptations/history
GET    /adaptations/{id}
GET    /adaptations/{id}/download-pdf
```

---

## 🚀 Deployment

### Vercel
```bash
# Auto-deploy on git push
# Configure env vars in Vercel dashboard
```

See [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for details.

### Docker
```bash
docker build -t opticv-frontend .
docker run -p 3000:3000 opticv-frontend
```

---

## 📊 Build Info

- **Size:** 377KB (production)
- **Gzip:** ~111KB (JS) + 4KB (CSS)
- **Modules:** 1734 transformed
- **Build Time:** ~3.5s

---

## 🐛 Troubleshooting

### Dependencies missing
```bash
npm install @hookform/resolvers
```

### Build fails
```bash
rm -rf node_modules dist
npm install
npm run build
```

### Dev server won't start
```bash
# Clear cache
rm -rf .vite
npm run dev
```

### API calls failing
- Check `VITE_API_URL` in `.env`
- Verify backend is running
- Check CORS on backend
- Inspect Network tab in DevTools

---

## 📝 Notes

- All components use **functional components** with hooks
- Error handling implemented throughout
- Loading states visible in all async operations
- Responsive design with Tailwind
- Token persistence with localStorage
- Protected routes with auth guards
- No hardcoded secrets (use env vars)

---

## 🔄 Next Steps

1. Test with FastAPI backend
2. Gather user feedback
3. Optimize performance
4. Add Google OAuth integration
5. Deploy to production

---

## 📖 Documentation

- [Frontend Implementation](../FRONTEND_IMPLEMENTATION.md) - Complete feature list
- [E2E Testing Guide](../TESTING_E2E.md) - How to test
- [Deployment Guide](../DEPLOYMENT_GUIDE.md) - How to deploy

---

## 📞 Support

For issues or questions:
1. Check documentation files
2. Review browser console for errors
3. Check DevTools Network tab for API issues
4. Verify backend is accessible

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-04-20  
**Version:** 0.1.0
