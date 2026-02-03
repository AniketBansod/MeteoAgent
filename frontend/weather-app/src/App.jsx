import "./App.css";
import Home from "./pages/Home.jsx";
import { AppProvider } from "./context/AppContext.jsx";
import { Navigate, Route, Routes } from "react-router-dom";

import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import MemoryChat from "./pages/MemoryChat.jsx";
import { isAuthenticated } from "./api/auth.js";


function RequireAuth({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <AppProvider>
            <Home />
          </AppProvider>
        }
      />

      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route
        path="/memory-chat"
        element={
          <RequireAuth>
            <MemoryChat />
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
