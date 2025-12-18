export const backend = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

function joinUrl(base, path) {
  if (!base) return path;
  const b = base.endsWith('/') ? base.slice(0, -1) : base;
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${b}${p}`;
}

export async function sendChat(message){
  const res = await fetch(joinUrl(backend, '/chat'),{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message})
  })
  if(!res.ok){
    const text = await res.text().catch(()=> '')
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json()
}

export async function fetchWeather(city){
  const url = new URL(joinUrl(backend, '/weather'))
  url.searchParams.set('city', city)
  const res = await fetch(url, { method: 'GET' })
  if(!res.ok){
    throw new Error(`HTTP ${res.status}`)
  }
  return res.json()
}

export async function fetchWeatherBatch(cities){
  const res = await fetch(joinUrl(backend, '/weather/batch'),{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({cities})
  })
  if(!res.ok){
    const text = await res.text().catch(()=> '')
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json()
}
