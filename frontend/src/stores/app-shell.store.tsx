import {
  createContext,
  useContext,
  useState,
  type PropsWithChildren
} from "react";

type AppShellStoreValue = {
  collapsed: boolean;
  toggleCollapsed: () => void;
};

const AppShellStoreContext = createContext<AppShellStoreValue | null>(null);

export function AppShellStoreProvider({ children }: PropsWithChildren) {
  const [collapsed, setCollapsed] = useState(false);
  const value = {
    collapsed,
    toggleCollapsed: () => setCollapsed((current) => !current)
  };

  return (
    <AppShellStoreContext.Provider value={value}>
      {children}
    </AppShellStoreContext.Provider>
  );
}

export function useAppShellStore() {
  const context = useContext(AppShellStoreContext);
  if (!context) {
    throw new Error("useAppShellStore must be used within AppShellStoreProvider");
  }
  return context;
}
