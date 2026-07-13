import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import ZarvisDashboard from './App.jsx'

const params = new URLSearchParams(window.location.search)
const flag = (name, def) => {
  const v = params.get(name)
  if (v === null) return def
  return !(v === '0' || v.toLowerCase() === 'false')
}
const accent = params.get('accent') || '#35E0FF'

createRoot(document.getElementById('root')).render(
  <ZarvisDashboard accent={accent} boot={flag('boot', true)} scanlines={flag('scanlines', true)} />
)
