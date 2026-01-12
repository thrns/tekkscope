"use client";
import { createContext, useState, useContext } from "react";

const ControllerContext = createContext();

export function ControllerProvider({ children }) {
  const [open, setOpen] = useState(true);

  return (
    <ControllerContext.Provider
      value={{
        open,
        setOpen,
      }}
    >
      {children}
    </ControllerContext.Provider>
  );
}

export function useController() {
  const context = useContext(ControllerContext);

  return context;
}
