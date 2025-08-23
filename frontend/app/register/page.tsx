'use client';

import { useRouter } from 'next/navigation';
import { RegisterForm } from '@/components/RegisterForm';

export default function RegisterPage() {
  const router = useRouter();

  const handleRegister = () => {
    router.push('/rooms');
  };

  const handleSwitchToLogin = () => {
    router.push('/login');
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      padding: '24px'
    }}>
      <RegisterForm 
        onRegister={handleRegister}
        onSwitchToLogin={handleSwitchToLogin}
      />
    </div>
  );
}