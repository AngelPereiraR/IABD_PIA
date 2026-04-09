# Plan 05: Panel de Control (Dashboard React + Vite)

## Objetivo
Crear proyecto React + Vite en `frontend/` con tres vistas: historial de ofertas, gestión de CV maestro, y configuración. Desplegar en Vercel conectado a la API FastAPI en HF.

## Prerrequisitos
- Plan 04 completado (API FastAPI con CORS configurado)
- Node.js 18+ instalado
- Cuenta Vercel (free tier suficiente)

---

## Paso 1: Scaffold del proyecto

```bash
cd frontend
npm create vite@latest . -- --template react
npm install

# Dependencias UI y datos
npm install axios react-router-dom @tanstack/react-query
npm install lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 1.1 Configurar Tailwind (`tailwind.config.js`)

```js
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

### 1.2 Añadir a `src/index.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 1.3 Variables de entorno (`frontend/.env`)
```env
VITE_API_URL=http://localhost:7860
```

`frontend/.env.production`:
```env
VITE_API_URL=https://<user>-opticv-engine.hf.space
```

---

## Paso 2: Estructura de archivos

```
frontend/src/
├── api/
│   └── client.js          # Axios instance + query functions
├── components/
│   ├── OfferCard.jsx       # Tarjeta de oferta individual
│   ├── OfferTable.jsx      # Tabla de historial
│   ├── StatusBadge.jsx     # Badge coloreado por status
│   └── ScoreBar.jsx        # Barra de progreso del score
├── pages/
│   ├── Dashboard.jsx       # Historial de ofertas (página principal)
│   ├── UploadCV.jsx        # Gestión CV maestro
│   └── Settings.jsx        # Configuración (placeholder)
├── App.jsx                 # Router principal
└── main.jsx
```

---

## Paso 3: Cliente API (`src/api/client.js`)

```js
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 300_000, // 5 min para generación LaTeX
});

export const fetchOffers = (params = {}) =>
  api.get("/api/offers", { params }).then((r) => r.data);

export const fetchOffer = (id) =>
  api.get(`/api/offers/${id}`).then((r) => r.data);

export const generateCV = (offerId) =>
  api.post(`/api/generate/${offerId}`).then((r) => r.data);

export const uploadMasterCV = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/api/upload-master-cv", form).then((r) => r.data);
};

export default api;
```

---

## Paso 4: Componentes base

### 4.1 `StatusBadge.jsx`

```jsx
const STATUS_STYLES = {
  pending:    "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  done:       "bg-green-100 text-green-800",
  error:      "bg-red-100 text-red-800",
};

export function StatusBadge({ status }) {
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[status] ?? "bg-gray-100"}`}>
      {status}
    </span>
  );
}
```

### 4.2 `ScoreBar.jsx`

```jsx
export function ScoreBar({ score }) {
  const pct = score ?? 0;
  const color = pct >= 75 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono">{pct}</span>
    </div>
  );
}
```

---

## Paso 5: Páginas principales

### 5.1 `pages/Dashboard.jsx`

```jsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchOffers, generateCV } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import { ScoreBar } from "../components/ScoreBar";
import { FileText, ExternalLink } from "lucide-react";

export function Dashboard() {
  const qc = useQueryClient();
  const { data: offers = [], isLoading } = useQuery({
    queryKey: ["offers"],
    queryFn: () => fetchOffers({ limit: 50 }),
    refetchInterval: 30_000, // Poll cada 30s
  });

  const generate = useMutation({
    mutationFn: generateCV,
    onSuccess: () => qc.invalidateQueries(["offers"]),
  });

  if (isLoading) return <p className="p-8 text-gray-500">Cargando ofertas...</p>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">📋 Historial de Ofertas</h1>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Puesto</th>
              <th className="px-4 py-3 text-left">Empresa</th>
              <th className="px-4 py-3 text-left">Score</th>
              <th className="px-4 py-3 text-left">Estado</th>
              <th className="px-4 py-3 text-left">Fecha</th>
              <th className="px-4 py-3 text-left">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {offers.map((offer) => (
              <tr key={offer.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{offer.job_title ?? "—"}</td>
                <td className="px-4 py-3 text-gray-600">{offer.company ?? "—"}</td>
                <td className="px-4 py-3"><ScoreBar score={offer.score} /></td>
                <td className="px-4 py-3"><StatusBadge status={offer.status} /></td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(offer.created_at).toLocaleDateString("es-ES")}
                </td>
                <td className="px-4 py-3 flex gap-2">
                  {offer.optimized_cv_url ? (
                    <a
                      href={offer.optimized_cv_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-blue-600 hover:underline text-xs"
                    >
                      <FileText size={14} /> CV
                    </a>
                  ) : (
                    <button
                      onClick={() => generate.mutate(offer.id)}
                      disabled={offer.status === "processing" || generate.isPending}
                      className="text-xs bg-indigo-600 text-white px-2 py-1 rounded hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {offer.status === "processing" ? "Generando..." : "Generar CV"}
                    </button>
                  )}
                  {offer.offer_url && (
                    <a href={offer.offer_url} target="_blank" rel="noopener noreferrer"
                       className="text-gray-400 hover:text-gray-600">
                      <ExternalLink size={14} />
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

### 5.2 `pages/UploadCV.jsx`

```jsx
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { uploadMasterCV } from "../api/client";
import { Upload, CheckCircle } from "lucide-react";

export function UploadCV() {
  const [file, setFile] = useState(null);
  const upload = useMutation({ mutationFn: uploadMasterCV });

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-6">📄 CV Maestro</h1>
      <p className="text-gray-600 mb-4">
        Sube tu CV base en PDF. El engine lo adaptará a cada oferta automáticamente.
      </p>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <Upload className="mx-auto mb-3 text-gray-400" size={32} />
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files[0])}
          className="hidden"
          id="cv-upload"
        />
        <label htmlFor="cv-upload" className="cursor-pointer text-indigo-600 hover:underline">
          Seleccionar PDF
        </label>
        {file && <p className="mt-2 text-sm text-gray-600">{file.name}</p>}
      </div>

      {upload.isSuccess && (
        <div className="mt-4 flex items-center gap-2 text-green-700 bg-green-50 p-3 rounded">
          <CheckCircle size={18} />
          <span>CV subido correctamente</span>
          <a href={upload.data.master_cv_url} target="_blank" rel="noopener noreferrer"
             className="ml-auto text-sm underline">Ver PDF</a>
        </div>
      )}

      {upload.isError && (
        <p className="mt-4 text-red-600 text-sm">Error: {upload.error.message}</p>
      )}

      <button
        onClick={() => file && upload.mutate(file)}
        disabled={!file || upload.isPending}
        className="mt-4 w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
      >
        {upload.isPending ? "Subiendo..." : "Subir CV Maestro"}
      </button>
    </div>
  );
}
```

---

## Paso 6: Router y layout (`App.jsx`)

```jsx
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "./pages/Dashboard";
import { UploadCV } from "./pages/UploadCV";

const qc = new QueryClient();

function Nav() {
  const cls = ({ isActive }) =>
    `px-4 py-2 rounded ${isActive ? "bg-indigo-600 text-white" : "text-gray-600 hover:bg-gray-100"}`;
  return (
    <nav className="flex gap-2 p-4 border-b border-gray-200 bg-white">
      <span className="font-bold text-indigo-700 mr-4">OptiCV</span>
      <NavLink to="/" end className={cls}>Dashboard</NavLink>
      <NavLink to="/upload-cv" className={cls}>CV Maestro</NavLink>
    </nav>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Nav />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload-cv" element={<UploadCV />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

---

## Paso 7: Despliegue en Vercel

```bash
# Desde frontend/
npm run build       # Genera dist/
npx vercel          # Login + deploy

# Variables de entorno en Vercel Dashboard:
# VITE_API_URL = https://<user>-opticv-engine.hf.space
```

### `vercel.json` (routing SPA)
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

---

## Verificación

```bash
# Dev local
npm run dev
# → http://localhost:5173

# Verificar que llama a la API correctamente
# Abrir DevTools → Network → ver requests a localhost:7860/api/offers
```

## Archivos Creados

| Archivo | Descripción |
|---------|-------------|
| `frontend/` | Proyecto completo React + Vite |
| `frontend/src/api/client.js` | Axios client |
| `frontend/src/pages/Dashboard.jsx` | Historial de ofertas |
| `frontend/src/pages/UploadCV.jsx` | Subida CV maestro |
| `frontend/src/components/StatusBadge.jsx` | Badge de estado |
| `frontend/src/components/ScoreBar.jsx` | Barra de puntuación |
| `frontend/vercel.json` | Config SPA routing |
