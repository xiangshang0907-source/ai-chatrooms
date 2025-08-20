// 类型定义文件

export interface User {
  id: string;
  username: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  role: string;
  status: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Room {
  id: string;
  name: string;
  description?: string;
  status: string;
  max_participants: number;
  allow_user_interruption: boolean;
  max_rounds_per_session?: number;
  round_timeout_seconds?: number;
  settings?: Record<string, any>;
  owner_id: string;
  created_at: string;
  updated_at: string;
  participant_count?: number;
}

export interface Participant {
  id: string;
  type: string;
  status: string;
  display_name: string;
  room_id: string;
  user_id?: string;
  agent_profile_id?: string;
  created_at: string;
  joined_at: string;
}

export interface Message {
  id: string;
  content: string;
  type: string;
  status: string;
  sequence_number: number;
  reply_to_id?: string;
  extra_data?: Record<string, any>;
  room_id: string;
  participant_id: string;
  participant?: Participant;
  created_at: string;
  updated_at: string;
}

export interface StreamMessage {
  type: 'user_message' | 'ai_message_start' | 'content' | 'ai_message_complete' | 'error' | 'info';
  id?: string;
  content?: string;
  message?: string;
}
