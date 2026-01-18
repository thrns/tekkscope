"use client";
import React from "react";

const BillingPage = () => {
  return (
    <div className="flex flex-col h-full bg-tekk-bg text-white p-4">
      <div className="flex flex-col items-center justify-center h-full rounded-xl bg-tekk-darkest max-h-[700px]">
        <svg
          className="w-24 h-24 text-tekk-primary mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 11c-1.657 0-3-1.343-3-3s1.343-3 3-3 3 1.343 3 3-1.343 3-3 3zm0 2c2.21 0 4 1.79 4 4v1H8v-1c0-2.21 1.79-4 4-4zm6 4h-2v-1c0-1.103-.897-2-2-2h-4c-1.103 0-2 .897-2 2v1H6v-1c0-2.21 1.79-4 4-4h4c2.21 0 4 1.79 4 4v1z"
          />
        </svg>
        <p className="text-lg text-gray-400">Coming soon.</p>
      </div>
    </div>
  );
};

export default BillingPage;