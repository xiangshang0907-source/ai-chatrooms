'use client';

import { useRouter } from 'next/navigation';
import { RoomList } from '@/components/RoomList';

export default function RoomsPage() {
  const router = useRouter();

  const handleJoinRoom = (roomId: string) => {
    router.push(`/rooms/${roomId}`);
  };

  const handleLogout = () => {
    router.push('/login');
  };

  return (
    <RoomList 
      onJoinRoom={handleJoinRoom}
      onLogout={handleLogout}
    />
  );
}