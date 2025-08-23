'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/auth';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (authService.isLoggedIn()) {
      router.push('/rooms');
    } else {
      router.push('/login');
    }
  }, [router]);

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