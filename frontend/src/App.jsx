/**
 * src/App.jsx
 * ────────────
 * Root router configuration for Nyaya Sahayak.
 *
 * Routes:
 *   /          → redirect to /login
 *   /login     → LoginPage (public)
 *   /dashboard → DashboardPage (protected — requires JWT in localStorage)
 */

import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import ResearchPage from "./pages/ResearchPage";
import ResearchResultPage from "./pages/ResearchResultPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import ClaimVerificationPage from "./pages/ClaimVerificationPage";
import HistoryPage from "./pages/HistoryPage";
import EvidenceViewPage from "./pages/EvidenceViewPage";
import ConflictViewPage from "./pages/ConflictViewPage";
import AuditTrailPage from "./pages/AuditTrailPage";
import CasesPage from "./pages/CasesPage";
import CaseWorkspacePage from "./pages/CaseWorkspacePage";
import DraftingPage from "./pages/DraftingPage";

export default function App() {
  return (
    <Routes>
      {/* Default: redirect root to /login */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Public */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/research"
        element={
          <ProtectedRoute>
            <ResearchPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/research/:queryId"
        element={
          <ProtectedRoute>
            <ResearchResultPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/research/:queryId/verify"
        element={
          <ProtectedRoute>
            <ClaimVerificationPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/research/:queryId/evidence"
        element={
          <ProtectedRoute>
            <EvidenceViewPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/research/:queryId/conflict"
        element={
          <ProtectedRoute>
            <ConflictViewPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/cases"
        element={
          <ProtectedRoute>
            <CasesPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/cases/:caseId"
        element={
          <ProtectedRoute>
            <CaseWorkspacePage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/drafts"
        element={
          <ProtectedRoute>
            <DraftingPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <HistoryPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/admin/audit"
        element={
          <ProtectedRoute>
            <AuditTrailPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/audit"
        element={
          <ProtectedRoute>
            <AuditTrailPage />
          </ProtectedRoute>
        }
      />

      {/* Catch-all: redirect unknown paths to /login */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
