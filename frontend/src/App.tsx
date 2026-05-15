import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import JobsPage from './pages/JobsPage';
import NewJobPage from './pages/NewJobPage';
import ReviewPage from './pages/ReviewPage';
import ProfilePage from './pages/ProfilePage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<JobsPage />} />
            <Route path="/new" element={<NewJobPage />} />
            <Route path="/jobs/:id" element={<ReviewPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
