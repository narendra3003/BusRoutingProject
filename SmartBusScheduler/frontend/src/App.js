import React from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import LoginForm from "./components/LoginForm";
import CustomerDashboard from "./pages/CustomerDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import DriverDashboard from "./pages/DriverDashboard";
<<<<<<< Updated upstream
=======
import Signup from "./components/SignUp";
import ProtectedRoute from "./components/ProtectedRoute";
import Unauthorized from "./pages/Unauthorized";
import StopsDataFeed from "./pages/StopsDataFeed";
import RoutesDataFeed from "./pages/RoutesDataFeed";
import BusDataFeed from "./pages/BusDataFeed";
import RouteBuilder from "./pages/RouteBuilder";
import DriverDataFeed from "./pages/DriverDataFeed";
import ScheduleManagement from "./pages/ScheduleManagement";
import SmartScheduleBuilder from "./pages/BulkManagement";
import LeaveApprovalPage from "./pages/LeaveApprovalPage";
import OverridePage from "./pages/OverridePage";
import DispatchPage from "./pages/DispatchPage";
import DriverLeavePage from "./pages/DriverLeavePage";
import ConductorDashboard from "./pages/conductor";
import AdminScheduleManagement from "./pages/schedule";
import St from "./pages/static1";
>>>>>>> Stashed changes

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
    {/* <h1 className="text-3xl font-bold text-purple-600">Hello Tailwind!</h1> */}
      <Navbar />
      <div className="p-4">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LoginForm />} />

          <Route path="/customer" element={
              <CustomerDashboard />
          }/>

          <Route path="/admin" element={
            
              <AdminDashboard />
          }/>

<<<<<<< Updated upstream
          <Route path="/driver" element={
              <DriverDashboard />
          }/>
=======
          <Route
            path="/driver"
            element={
              <ProtectedRoute allowedRoles={["driver"]}>
                <DriverDashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/stops-data-feed" 
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <StopsDataFeed />
              </ProtectedRoute>
            }/>
        <Route path="/routes-data-feed" 
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <RoutesDataFeed />
              </ProtectedRoute>
            }/>
        <Route path="/buses-data-feed" 
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <BusDataFeed />
              </ProtectedRoute>
            }/>
          <Route path="/route-builder"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <RouteBuilder />
              </ProtectedRoute>
            }/>
            <Route path="/driver-data-feed"
              element={
                <ProtectedRoute allowedRoles={["admin"]}>
                  <DriverDataFeed />
                </ProtectedRoute>
              }
            />
              <Route path="/schedule"
                element={
                  <ProtectedRoute allowedRoles={["admin"]}>
                    <ScheduleManagement />
                  </ProtectedRoute>
                }
              />
              <Route path="/bulk-management"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <SmartScheduleBuilder />
                    </ProtectedRoute>
                  }
              />
              <Route path="/leave-approvals"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <LeaveApprovalPage />
                    </ProtectedRoute>
                  }
              />
              <Route path="/override"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <OverridePage />
                    </ProtectedRoute>
                  }
              />
              <Route path="/schedule-create"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <St />
                    </ProtectedRoute>
                  }
              />
              <Route path="/dispatch"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <DispatchPage />
                    </ProtectedRoute>
                  }
              />
              <Route path="/driver/leave"
                  element={
                    <ProtectedRoute allowedRoles={["driver"]}>
                      <DriverLeavePage />
                    </ProtectedRoute>
                  }
              />
>>>>>>> Stashed changes
        </Routes>
      </div>
    </div>
  );
}

export default App;
