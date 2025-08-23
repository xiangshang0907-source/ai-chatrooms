'use client';

import { useRouter, useParams } from 'next/navigation';
import { ChatRoom } from '@/components/ChatRoom';

export default function RoomPage() {
  const router = useRouter();
  const params = useParams();
  const roomId = params.roomId as string;

  const handleBack = () => {
    router.push('/rooms');
  };

  return (
    <ChatRoom 
      roomId={roomId}
      onBack={handleBack}
    />
  );
}