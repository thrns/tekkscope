'use client';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Image from 'next/image';

const LogoutPage = () => {
  const router = useRouter();

  useEffect(() => {
    setTimeout(() => router.push('/'), 2000);
  }, []);

  return (
    <div className="animate-fade-in flex h-screen w-full flex-col items-center justify-center bg-tekk-bg text-white p-6">
      <Image
        src="/logos/icon.png"
        alt="Logout Image"
        width={150}
        height={150}
        className="mb-6 rounded-xl"
      />
      <h1 className="text-2xl font-semibold text-white">
        You have logged out.
      </h1>
      <p className="mt-2 text-gray-200">Redirecting you to the homepage...</p>
    </div>
  );
};

export default LogoutPage;
