import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { App } from "./app/App";
import { queryClient } from "./lib/api/queryClient";
import { initTheme } from "./lib/theme/theme";
import { initPresentation } from "./lib/settings/presentation";
import "./index.css";

// Paint the persisted color theme + density onto <html> before first render.
initTheme();
initPresentation();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
