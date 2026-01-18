"use client";
import React, { useMemo, useCallback, useState } from "react";
import { UsageProvider, useUsage } from "@/app/contexts/UsageContext";
import { useApiKeys } from "@/app/contexts/ApiKeysContext";
import { AgGridReact } from "ag-grid-react";
import {
  ModuleRegistry,
  ClientSideRowModelModule,
  ValidationModule,
  PaginationModule,
  RowSelectionModule,
  QuickFilterModule,
} from "ag-grid-community";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import { myTheme } from "@/lib/TableThemes";
import { Clock, Key, SearchIcon } from "lucide-react";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";

ModuleRegistry.registerModules([
  ClientSideRowModelModule,
  ValidationModule,
  PaginationModule,
  RowSelectionModule,
  QuickFilterModule,
]);

const UsageContent = () => {
  const { apiKeys } = useApiKeys();
  const {
    usageRows,
    loading,
    selectedApiKeyId,
    setApiKeyFilter,
    granularity,
    setGranularity,
    usageOverTime,
    creditsPerPeriod,
  } = useUsage();

  const [gridApi, setGridApi] = useState(null);
  const onGridReady = useCallback((params) => setGridApi(params.api), []);

  const [selectedRows, setSelectedRows] = useState([]);
  const onSelectionChanged = (event) => setSelectedRows(event.api.getSelectedRows());
  const onRowClicked = () => {};

  const columnDefs = useMemo(() => ([
    { headerName: "#", valueGetter: "node.rowIndex + 1", width: 80, checkboxSelection: true, headerCheckboxSelection: true },
    { headerName: "When", field: "timestamp", cellRenderer: (p) => new Date(p.value).toLocaleString() },
    { headerName: "Service", field: "service_used" },
    { 
      headerName: "Tokens", 
      valueGetter: (params) => {
        const row = params.data;
        // Calculate tokens from input_tokens + output_tokens, with fallback to tokens field for backward compatibility
        return (row.input_tokens || 0) + (row.output_tokens || 0) || (row.tokens || 0);
      }
    },
    { headerName: "Credits", field: "credits_used" },
  ]), []);

  const defaultColDef = useMemo(() => ({ flex: 1, resizable: true }), []);
  const gridOptions = useMemo(() => ({ rowHeight: 64, suppressRowClickSelection: true, rowSelection: "multiple" }), []);

  const onFilterTextBoxChanged = useCallback(() => {
    if (!gridApi) return;
    gridApi.setGridOption("quickFilterText", document.getElementById("usage-filter-text").value);
  }, [gridApi]);

  const apiKeyOptions = useMemo(() => [{ id: null, api_key_name: "All Keys" }, ...apiKeys], [apiKeys]);
  const selectedApiKeyLabel = useMemo(() => {
    const found = apiKeyOptions.find((k) => (k.id || null) === (selectedApiKeyId || null));
    return found ? found.api_key_name : "All Keys";
  }, [apiKeyOptions, selectedApiKeyId]);
  const granularityLabel = useMemo(() => ({ day: "Day", week: "Week", month: "Month" })[granularity] || "Day", [granularity]);

  return (
    <div className="flex flex-col h-full bg-tekk-bg text-white p-4 gap-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center border border-tekk-dark rounded-md px-2 py-1 bg-tekk-bg">
          <SearchIcon className="mr-2" />
          <input id="usage-filter-text" placeholder="Search usage..." onInput={onFilterTextBoxChanged} className="p-2 rounded text-white ring-0 border-0 outline-none" />
        </div>
        <div className="flex items-center gap-4">

       
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="bg-tekk-dark rounded-md px-3 py-2  flex items-center"><Key className="mr-2 w-4 h-4" /> {selectedApiKeyLabel}</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="bg-tekk-dark text-white border-tekk-dark">
            {apiKeyOptions.map((k) => (
              <DropdownMenuItem key={k.id || 'all'} onClick={() => setApiKeyFilter(k.id || null)} className="cursor-pointer">
                {k.api_key_name}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="bg-tekk-dark rounded-md px-3 py-2 flex items-center"><Clock className="mr-2 w-4 h-4" /> {granularityLabel}</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="bg-tekk-dark text-white border-tekk-dark">
            {['day','week','month'].map((g) => (
              <DropdownMenuItem key={g} onClick={() => setGranularity(g)} className="cursor-pointer">
                {g === 'day' ? 'Day' : g === 'week' ? 'Week' : 'Month'}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu> </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl bg-tekk-darkest p-3">
          <div className="text-sm text-white/70 mb-2">Usage Over Time (events)</div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={usageOverTime} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="date" stroke="#aaa" />
              <YAxis stroke="#aaa" />
              <Tooltip />
              <Line type="monotone" dataKey="events" stroke="#4fd1c5" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-xl bg-tekk-darkest p-3">
          <div className="text-sm text-white/70 mb-2">Credits Spent ({granularity})</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={creditsPerPeriod} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="period" stroke="#aaa" />
              <YAxis stroke="#aaa" />
              <Tooltip />
              <Bar dataKey="credits" fill="#93c5fd" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="ag-theme-quartz-dark grow" style={{ width: "100%", height: "100%" }}>
        <AgGridReact
          rowData={usageRows}
          columnDefs={columnDefs}
          gridOptions={gridOptions}
          onGridReady={onGridReady}
          theme={myTheme}
          onRowClicked={onRowClicked}
          onSelectionChanged={onSelectionChanged}
          defaultColDef={defaultColDef}
          animateRows={true}
        />
      </div>
    </div>
  );
};

const UsagePage = () => (
  <UsageProvider>
    <UsageContent />
  </UsageProvider>
);

export default UsagePage;