'use client';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

export default function ErrorPage() {
  const router = useRouter();

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-gray-50 p-6 text-center">
      {/* Logo */}
      <Image
        src="/logos/icon.png"
        alt="Error Logo"
        width={100}
        height={100}
        className="mb-6 rounded-lg"
      />

      {/* Error Message */}
      <h1 className="text-2xl font-semibold text-gray-800">
        Oops! Something went wrong.
      </h1>
      <p className="mt-2 text-gray-600">
        We encountered an unexpected error. Please try again later or return to
        the homepage.
      </p>

      {/* Redirect Button */}
      <Button
        className="mt-5 rounded-md bg-tekk-dark px-6 py-3 text-white"
        onClick={() => router.push('/')}
      >
        Go Back Home
      </Button>
    </div>
  );
}
