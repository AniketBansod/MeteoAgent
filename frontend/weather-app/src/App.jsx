import "./App.css";
import Home from "./pages/Home.jsx";
import { AppProvider } from "./context/AppContext.jsx";

export default function App() {
  return (
    <AppProvider>
      <Home />
    </AppProvider>
  );
}
