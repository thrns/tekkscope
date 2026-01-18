"use client";
//================ IMPORTS ================//
import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";

import { useAuth } from './AuthContext';
import { toast } from 'sonner';

//================ CONTEXT CREATION ================//
const UsageContext = createContext();

//================ CUSTOM HOOK ================//
export const useUsage = () => useContext(UsageContext);

//================ HELPER ================//
function startOfPeriod(date, granularity) {
  const d = new Date(date);
  if (granularity === 'week') {
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.getFullYear(), d.getMonth(), diff, 0, 0, 0, 0);
  }
  if (granularity === 'month') {
    return new Date(d.getFullYear(), d.getMonth(), 1, 0, 0, 0, 0);
  }
  return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0);
}

//================ PROVIDER COMPONENT ================//
export const UsageProvider = ({ children }) => {
  //================ STATE & HOOKS ================//
  const { user } = useAuth();
  const [usageRows, setUsageRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedApiKeyId, setSelectedApiKeyId] = useState(null);
  const [granularity, setGranularity] = useState('day');
  const [range, setRange] = useState({ from: null, to: null });

  //================ HANDLERS ================//
  const fetchUsage = useCallback(async ({ userId, apiKeyId, from, to } = {}) => {
    const uid = userId ?? user?.uuid;
    if (!uid) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/supabase/usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: uid,
          apiKeyId,
          from: from ? from.toISOString() : null,
          to: to ? to.toISOString() : null,
        }),
      });
      if (!response.ok) throw new Error('Failed to fetch usage');

      const { data } = await response.json();
      setUsageRows(data || []);
    } catch (err) {
      console.error('Error fetching usage:', err);
      setError(err);
      toast.error('Failed to fetch usage');
    } finally {
      setLoading(false);
    }
  }, [user]);

  //================ EFFECTS ================//
  useEffect(() => {
    fetchUsage({ apiKeyId: selectedApiKeyId, from: range.from, to: range.to });
  }, [fetchUsage, selectedApiKeyId, range.from, range.to]);

  //================ MEMOIZED VALUES ================//
  const usageOverTime = useMemo(() => {
    const map = new Map();
    for (const r of usageRows) {
      const key = startOfPeriod(r.timestamp || r.created_at || r.timestamp, granularity).toISOString().slice(0, 10);
      const prev = map.get(key) || { date: key, events: 0, tokens: 0 };
      prev.events += 1;

      // calc tokens from input_tokens + output_tokens, 
      const tokens = (r.input_tokens || 0) + (r.output_tokens || 0) || (r.tokens || 0);
      prev.tokens += Number(tokens);
      map.set(key, prev);
    }
    return Array.from(map.values());
  }, [usageRows, granularity]);

  const creditsPerPeriod = useMemo(() => {
    const map = new Map();
    for (const r of usageRows) {
      const key = startOfPeriod(r.timestamp || r.created_at || r.timestamp, granularity).toISOString().slice(0, 10);
      const prev = map.get(key) || { period: key, credits: 0 };
      prev.credits += Number(r.credits_used || 0);
      map.set(key, prev);
    }
    return Array.from(map.values());
  }, [usageRows, granularity]);

  const setApiKeyFilter = useCallback((id) => {
    setSelectedApiKeyId(id || null);
  }, []);

  const setDateRange = useCallback((from, to) => {
    setRange({ from, to });
  }, []);

  const value = {
    usageRows,
    loading,
    error,
    selectedApiKeyId,
    granularity,
    range,
    usageOverTime,
    creditsPerPeriod,
    fetchUsage,
    setApiKeyFilter,
    setGranularity,
    setDateRange,
  };

  //================ RENDER ================//
  return <UsageContext.Provider value={value}>{children}</UsageContext.Provider>;
};