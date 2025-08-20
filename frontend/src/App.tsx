import { useEffect, useState } from 'react'
import { authService } from './auth'
import { LoginForm } from './components/LoginForm'
import { RegisterForm } from './components/RegisterForm'
import { RoomList } from './components/RoomList'
import { ChatRoom } from './components/ChatRoom'

type AppState = 'loading' | 'login' | 'register' | 'rooms' | 'chat'

export default function App() {
  const [appState, setAppState] = useState<AppState>('loading')
  const [currentRoomId, setCurrentRoomId] = useState<string | null>(null)

  useEffect(() => {
    // 检查用户登录状态
    if (authService.isLoggedIn()) {
      setAppState('rooms')
    } else {
      setAppState('login')
    }
  }, [])

  const handleLogin = () => {
    setAppState('rooms')
  }

  const handleRegister = () => {
    setAppState('rooms')
  }

  const handleLogout = () => {
    setAppState('login')
  }

  const handleJoinRoom = (roomId: string) => {
    setCurrentRoomId(roomId)
    setAppState('chat')
  }

  const handleBackToRooms = () => {
    setCurrentRoomId(null)
    setAppState('rooms')
  }

  if (appState === 'loading') {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial',
        fontSize: '18px',
        color: '#6b7280'
      }}>
        加载中...
      </div>
    )
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: '#f3f4f6',
      fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial'
    }}>
      {appState === 'login' && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '100vh',
          padding: '24px'
        }}>
          <LoginForm 
            onLogin={handleLogin}
            onSwitchToRegister={() => setAppState('register')}
          />
        </div>
      )}

      {appState === 'register' && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '100vh',
          padding: '24px'
        }}>
          <RegisterForm 
            onRegister={handleRegister}
            onSwitchToLogin={() => setAppState('login')}
          />
        </div>
      )}

      {appState === 'rooms' && (
        <RoomList 
          onJoinRoom={handleJoinRoom}
          onLogout={handleLogout}
        />
      )}

      {appState === 'chat' && currentRoomId && (
        <ChatRoom 
          roomId={currentRoomId}
          onBack={handleBackToRooms}
        />
      )}
    </div>
  )
}