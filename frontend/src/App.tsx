import { useEffect, useState } from 'react'

export default function App() {
  const [health, setHealth] = useState('loading...')

  useEffect(() => {
    fetch('/health')
      .then((r) => r.json())
      .then((d) => setHealth(`${d.status} - ${d.service} v${d.version}`))
      .catch((e) => setHealth(`error: ${String(e)}`))
  }, [])

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial' }}>
      <h1>AI Chatrooms</h1>
      <p>Backend health: {health}</p>
    </div>
  )
}