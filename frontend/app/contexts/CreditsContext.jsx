'use client';
//================ IMPORTS ================//
import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from './AuthContext';

//================ CONTEXT CREATION ================//
const CreditsContext = createContext(null);

//================ CUSTOM HOOK ================//
export const useCredits = () => {
  const ctx = useContext(CreditsContext);
  if (!ctx) throw new Error('useCredits must be used within CreditsProvider');
  return ctx;
};

//================ PROVIDER COMPONENT ================//
export const CreditsProvider = ({ children }) => {
  //================ STATE & HOOKS ================//
  const { user } = useAuth();
  const userId = user?.uuid || '';
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const channelRef = useRef(null);

  //================ HANDLERS ================//
  const refreshCredits = async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const response = await fetch('/api/supabase/credits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId }),
      });
      if (response.ok) {
        const { data } = await response.json();
        if (data) {
          setBalance(Number(data.balance || 0));
          setLastUpdated(data.last_updated || new Date().toISOString());
        }
      }
    } catch (error) {
      console.error('Error refreshing credits:', error);
    } finally {
      setLoading(false);
    }
  };

  const spendOptimistic = (amount) => {
    const next = Math.max(0, Number(balance) - Number(amount || 0));
    setBalance(next);
    setLastUpdated(new Date().toISOString());
  };

  //================ EFFECTS ================//
  useEffect(() => {
    if (!userId) return;
    refreshCredits();
    // No realtime subscription: credits is not a realtime table.
    // We only refresh on mount/user change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const value = {
    balance,
    loading,
    lastUpdated,
    refreshCredits,
    spendOptimistic,
  };

  //================ RENDER ================//
  return (
    <CreditsContext.Provider value={value}>{children}</CreditsContext.Provider>
  );
};

//================ EXPORTS ================//
export default CreditsContext;