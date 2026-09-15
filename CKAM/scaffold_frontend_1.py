import os
import json

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

package_json = {
  "name": "mandiwise-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint src --ext js,jsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.6.8",
    "lucide-react": "^0.364.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.3",
    "recharts": "^2.12.3",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.1",
    "vite": "^5.2.0"
  }
}
write_file('frontend/package.json', json.dumps(package_json, indent=2))

vite_config_js = """
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
"""
write_file('frontend/vite.config.js', vite_config_js)

tailwind_config_js = """
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        agrigreen: {
          50: '#f2fbf5',
          100: '#e1f6e8',
          200: '#c3ecd4',
          300: '#94dcb1',
          400: '#5fc389',
          500: '#3ba76b',
          600: '#2a8553',
          700: '#236a44',
          800: '#1e5538',
          900: '#19462f',
        }
      }
    },
  },
  plugins: [],
}
"""
write_file('frontend/tailwind.config.js', tailwind_config_js)

postcss_config_js = """
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
write_file('frontend/postcss.config.js', postcss_config_js)

index_html = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MandiWise</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""
write_file('frontend/index.html', index_html)

main_jsx = """
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { AuthProvider } from './context/AuthContext.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>,
)
"""
write_file('frontend/src/main.jsx', main_jsx)

index_css = """
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-50 text-gray-900;
}
"""
write_file('frontend/src/index.css', index_css)
