import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import DataManager from './pages/DataManager';
import Analysis from './pages/Analysis';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="page">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/data" element={<DataManager />} />
          <Route path="/analysis" element={<Analysis />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
