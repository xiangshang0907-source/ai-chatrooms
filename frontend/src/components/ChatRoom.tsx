import { useState, useEffect, useRef } from 'react';
import { Send, ArrowLeft, Users, Bot, User as UserIcon, Loader } from 'lucide-react';
import { authService } from '@/auth';
import { Message, Room, User, StreamMessage } from '@/types';

interface ChatRoomProps {
  roomId: string;
  onBack: () => void;
}

export function ChatRoom({ roomId, onBack }: ChatRoomProps) {
  const [room, setRoom] = useState<Room | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    setCurrentUser(authService.getCurrentUser());
    loadRoomData();

    return () => {
      // 清理EventSource连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [roomId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadRoomData = async () => {
    try {
      setLoading(true);
      
      // 加载房间信息
      const roomResponse = await authService.fetchWithAuth(`/rooms/${roomId}`);
      if (!roomResponse.ok) {
        throw new Error('获取房间信息失败');
      }
      const roomData = await roomResponse.json();
      setRoom(roomData);

      // 检查是否已加入房间，如果没有则自动加入
      try {
        await authService.fetchWithAuth(`/rooms/${roomId}/join`, {
          method: 'POST',
          body: JSON.stringify({}),
        });
      } catch {
        // 忽略加入失败（可能已经在房间中）
      }

      // 加载消息历史
      const messagesResponse = await authService.fetchWithAuth(`/rooms/${roomId}/messages`);
      if (messagesResponse.ok) {
        const messagesData = await messagesResponse.json();
        setMessages(messagesData.messages || []);
      }

      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载房间数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || sending || isStreaming) return;

    const messageContent = newMessage.trim();
    setNewMessage('');
    setSending(true);
    setIsStreaming(true);

    try {
      // 关闭之前的EventSource连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // 创建新的EventSource连接用于流式响应
      const token = authService.getToken();
      const eventSource = new EventSource(`/api/rooms/${roomId}/messages/stream?token=${encodeURIComponent(token || '')}`);

      eventSourceRef.current = eventSource;

      // 发送消息
      const response = await authService.fetchWithAuth(`/api/rooms/${roomId}/messages/stream`, {
        method: 'POST',
        body: JSON.stringify({
          content: messageContent,
        }),
      });

      if (!response.ok) {
        throw new Error('发送消息失败');
      }

      let currentAiMessage: Message | null = null;

      eventSource.onmessage = (event) => {
        try {
          const data: StreamMessage = JSON.parse(event.data);
          
          switch (data.type) {
            case 'user_message':
              // 添加用户消息到列表
              if (data.id && data.content) {
                const userMessage: Message = {
                  id: data.id,
                  content: data.content,
                  type: 'text',
                  status: 'sent',
                  sequence_number: messages.length + 1,
                  room_id: roomId,
                  participant_id: '',
                  participant: {
                    id: '',
                    type: 'user',
                    status: 'active',
                    display_name: currentUser?.display_name || currentUser?.username || '用户',
                    room_id: roomId,
                    created_at: new Date().toISOString(),
                    joined_at: new Date().toISOString(),
                  },
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                };
                setMessages(prev => [...prev, userMessage]);
              }
              break;

            case 'ai_message_start':
              // 开始AI消息
              if (data.id) {
                currentAiMessage = {
                  id: data.id,
                  content: '',
                  type: 'text',
                  status: 'generating',
                  sequence_number: messages.length + 2,
                  room_id: roomId,
                  participant_id: '',
                  participant: {
                    id: '',
                    type: 'agent',
                    status: 'active',
                    display_name: 'AI助手',
                    room_id: roomId,
                    created_at: new Date().toISOString(),
                    joined_at: new Date().toISOString(),
                  },
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                };
                setMessages(prev => [...prev, currentAiMessage!]);
              }
              break;

            case 'content':
              // 更新AI消息内容
              if (data.content && currentAiMessage) {
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === currentAiMessage!.id 
                      ? { ...msg, content: msg.content + data.content }
                      : msg
                  )
                );
              }
              break;

            case 'ai_message_complete':
              // AI消息完成
              if (currentAiMessage) {
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === currentAiMessage!.id 
                      ? { ...msg, status: 'sent' }
                      : msg
                  )
                );
              }
              setIsStreaming(false);
              eventSource.close();
              break;

            case 'error':
              throw new Error(data.message || '流式响应错误');
          }
        } catch (parseError) {
          console.error('解析流式数据失败:', parseError);
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource错误:', error);
        setIsStreaming(false);
        setError('连接中断，请重试');
        eventSource.close();
      };

    } catch (err) {
      setError(err instanceof Error ? err.message : '发送消息失败');
      setIsStreaming(false);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        color: '#6b7280'
      }}>
        加载中...
      </div>
    );
  }

  if (!room) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        color: '#dc2626'
      }}>
        房间不存在
      </div>
    );
  }

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial'
    }}>
      {/* 头部 */}
      <div style={{
        padding: '16px 24px',
        backgroundColor: '#fff',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        gap: '16px'
      }}>
        <button
          onClick={onBack}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 12px',
            backgroundColor: '#f3f4f6',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            color: '#374151'
          }}
        >
          <ArrowLeft size={16} />
          返回
        </button>
        
        <div style={{ flex: 1 }}>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '600', color: '#1f2937' }}>
            {room.name}
          </h1>
          {room.description && (
            <p style={{ margin: '2px 0 0', fontSize: '14px', color: '#6b7280' }}>
              {room.description}
            </p>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6b7280' }}>
          <Users size={16} />
          <span style={{ fontSize: '14px' }}>
            {room.participant_count || 0}/{room.max_participants}
          </span>
        </div>
      </div>

      {/* 错误信息 */}
      {error && (
        <div style={{
          padding: '12px 24px',
          backgroundColor: '#fef2f2',
          borderBottom: '1px solid #fecaca',
          color: '#dc2626',
          fontSize: '14px'
        }}>
          {error}
        </div>
      )}

      {/* 消息列表 */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: '24px',
        backgroundColor: '#f9fafb'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          {messages.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '48px 24px',
              color: '#6b7280'
            }}>
              <p style={{ fontSize: '16px', margin: 0 }}>
                还没有消息，开始对话吧！
              </p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <MessageBubble 
                  key={message.id} 
                  message={message} 
                  isOwn={message.participant?.type === 'user'} 
                />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* 消息输入框 */}
      <div style={{
        padding: '16px 24px',
        backgroundColor: '#fff',
        borderTop: '1px solid #e5e7eb'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={isStreaming ? "AI正在回复中..." : "输入消息..."}
              disabled={sending || isStreaming}
              style={{
                flex: 1,
                padding: '12px 16px',
                border: '1px solid #d1d5db',
                borderRadius: '24px',
                fontSize: '14px',
                outline: 'none',
                backgroundColor: (sending || isStreaming) ? '#f9fafb' : '#fff'
              }}
            />
            <button
              type="submit"
              disabled={!newMessage.trim() || sending || isStreaming}
              style={{
                padding: '12px 16px',
                backgroundColor: (!newMessage.trim() || sending || isStreaming) ? '#9ca3af' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '24px',
                cursor: (!newMessage.trim() || sending || isStreaming) ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              {sending ? (
                <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} />
              ) : (
                <Send size={16} />
              )}
              发送
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
}

function MessageBubble({ message, isOwn }: MessageBubbleProps) {
  const isAI = message.participant?.type === 'agent';
  
  return (
    <div style={{
      display: 'flex',
      justifyContent: isOwn ? 'flex-end' : 'flex-start',
      marginBottom: '16px',
      gap: '12px'
    }}>
      {!isOwn && (
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          backgroundColor: isAI ? '#3b82f6' : '#10b981',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          {isAI ? (
            <Bot size={16} color="white" />
          ) : (
            <UserIcon size={16} color="white" />
          )}
        </div>
      )}
      
      <div style={{
        maxWidth: '70%',
        backgroundColor: isOwn ? '#3b82f6' : '#fff',
        color: isOwn ? 'white' : '#1f2937',
        padding: '12px 16px',
        borderRadius: isOwn ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
        border: isOwn ? 'none' : '1px solid #e5e7eb',
        boxShadow: isOwn ? 'none' : '0 1px 2px rgba(0, 0, 0, 0.05)'
      }}>
        {!isOwn && (
          <div style={{
            fontSize: '12px',
            fontWeight: '500',
            marginBottom: '4px',
            color: isAI ? '#3b82f6' : '#10b981'
          }}>
            {message.participant?.display_name || (isAI ? 'AI助手' : '用户')}
          </div>
        )}
        
        <div style={{
          fontSize: '14px',
          lineHeight: '1.4',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}>
          {message.content}
          {message.status === 'generating' && (
            <span style={{ 
              display: 'inline-block',
              width: '8px',
              height: '12px',
              backgroundColor: 'currentColor',
              marginLeft: '4px',
              animation: 'blink 1s infinite'
            }} />
          )}
        </div>
        
        <div style={{
          fontSize: '11px',
          marginTop: '4px',
          opacity: 0.7
        }}>
          {new Date(message.created_at).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>

      {isOwn && (
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          backgroundColor: '#6b7280',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          <UserIcon size={16} color="white" />
        </div>
      )}
    </div>
  );
}
