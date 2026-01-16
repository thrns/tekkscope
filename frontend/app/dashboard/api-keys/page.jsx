"use client";
import React, { useEffect, useMemo, useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/app/contexts/AuthContext";
import { useApiKeys } from "@/app/contexts/ApiKeysContext";
import { AgGridReact } from "ag-grid-react";
import { myTheme } from "@/lib/TableThemes";
import { toast } from "sonner";
import { CreateApiKeyDialog } from "@/components/CreateApiKeyDialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  ModuleRegistry,
  ClientSideRowModelModule,
  ValidationModule,
  PaginationModule,
  RowSelectionModule,
  QuickFilterModule,
} from "ag-grid-community";
import { SearchIcon } from "lucide-react";
ModuleRegistry.registerModules([
  ClientSideRowModelModule,
  ValidationModule,
  PaginationModule,
  RowSelectionModule,
  QuickFilterModule,
]);

const APIKeysPage = () => {
  const { user } = useAuth();
  const {
    apiKeys,
    generateApiKey,
    deleteApiKey,
  } = useApiKeys();
  const [gridApi, setGridApi] = useState(null);

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const [apiKeyToDelete, setApiKeyToDelete] = useState(null);
  const [isConfirmingBulkDelete, setIsConfirmingBulkDelete] = useState(false);

  const handleGenerateKey = async (name) => {
    setIsGenerating(true);
    const newKey = await generateApiKey(name);
    setIsGenerating(false);
    return newKey;
  };

  const handleDeleteRequest = (id) => {
    setApiKeyToDelete(id);
    setIsConfirmingDelete(true);
  };

  const confirmDelete = () => {
    if (apiKeyToDelete) {
      deleteApiKey(apiKeyToDelete);
    }
    setApiKeyToDelete(null);
    setIsConfirmingDelete(false);
  };

  const confirmBulkDelete = () => {
    selectedRows.forEach((row) => {
      deleteApiKey(row.id);
    });
    setIsConfirmingBulkDelete(false);
  };

  const columnDefs = [
    {
      headerName: "#",
      valueGetter: "node.rowIndex + 1",
      width: 80,

      checkboxSelection: true,
      headerCheckboxSelection: true,
    },
    {
      headerName: "Key",
      field: "api_key",
      cellRenderer: (params) => `${String(params.value || '').substring(0, 10)}...`,
    },
    {
      headerName: "Name",
      field: "api_key_name",
      cellRenderer: (params) => `${params.value || 'Untitled key'}`,
    },
    {
      headerName: "Created At",
      field: "created_at",
      cellRenderer: (params) => params.value ? new Date(params.value).toLocaleDateString() : '—',
    },
    {
      headerName: "Created By",
      field: "created_by",
    },
    {
      headerName: "",
      field: "id",
      cellRenderer: (params) => (
        <Button
          variant="destructive"
          onClick={() => handleDeleteRequest(params.value)}
        >
          Delete
        </Button>
      ),
    },
  ];
  const defaultColDef = useMemo(
    () => ({
      flex: 1,
      resizable: true,
    }),
    []
  );

  const gridOptions = useMemo(
    () => ({
      rowHeight: 80,
      suppressRowClickSelection: true,
      rowSelection: "multiple",
    }),
    []
  );

  const onGridReady = useCallback((params) => {
    setGridApi(params.api);
  }, []);

  const onRowClicked = (event) => console.log("A row was clicked", event);
  const [selectedRows, setSelectedRows] = useState([]);

  const onSelectionChanged = (event) => {
    setSelectedRows(event.api.getSelectedRows());
  };

  const onFilterTextBoxChanged = useCallback(() => {
    gridApi.setGridOption(
      "quickFilterText",
      document.getElementById("filter-text-box").value
    );
  }, [gridApi]);

  const deleteSelectedRows = () => {
    setIsConfirmingBulkDelete(true);
  };

  return (
    <div className="flex flex-col h-full bg-tekk-bg text-white p-4">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center border border-tekk-dark rounded-md px-2 py-1 bg-tekk-bg">
          <SearchIcon className="mr-2" />
        <input
          type="text"
          id="filter-text-box"
          placeholder="Search API KEYS..."
          onInput={onFilterTextBoxChanged}
          className="p-2 rounded  text-white ring-0 border-0 outline-none"
        /></div>
        {selectedRows.length > 0 && (
          <Button variant="destructive" onClick={() => setIsConfirmingBulkDelete(true)}>
            Delete Selected
          </Button>
        )}
      </div>
      {apiKeys.length === 0 ? (
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
          <p className="text-lg text-gray-400 mb-4">No API keys found.</p>
          <Button
            variant="outline"
            onClick={() => setIsDialogOpen(true)}
            className="bg-white text-black"
          >
            Create API Key
          </Button>
        </div>
      ) : (
        <div
          className="ag-theme-quartz-dark grow"
          style={{ width: "100%", height: "100%" }}
        >
          <AgGridReact
            rowData={apiKeys}
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
      )}
      <CreateApiKeyDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        onCreate={handleGenerateKey}
        isGenerating={isGenerating}
      />
      <AlertDialog open={isConfirmingDelete} onOpenChange={setIsConfirmingDelete}>
        <AlertDialogContent className="bg-tekk-darkest text-white border-tekk-dark">
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete your
              API key and remove your data from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-white  text-black hover:bg-white cursor-pointer">Cancel</AlertDialogCancel>
            <AlertDialogAction className="bg-red-500 text-white hover:bg-red-700 cursor-pointer" onClick={confirmDelete}>
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <AlertDialog
        open={isConfirmingBulkDelete}
        onOpenChange={setIsConfirmingBulkDelete}
      >
        <AlertDialogContent className="bg-tekk-darkest text-white border-tekk-dark">
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              selected API keys and remove your data from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-white  text-black hover:bg-white cursor-pointer">Cancel</AlertDialogCancel>
            <AlertDialogAction className="bg-red-500 text-white hover:bg-red-700 cursor-pointer" onClick={confirmBulkDelete}>
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default APIKeysPage;
