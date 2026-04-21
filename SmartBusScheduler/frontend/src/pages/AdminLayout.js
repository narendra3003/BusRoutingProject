// AdminLayout.jsx
import Sidebar from "./AdminSidebar";

export default function AdminLayout({ children }) {
  return (
    <div className="flex">
      <Sidebar />

      <div className="flex-1 bg-gray-100 min-h-screen p-6">
        {children}
      </div>
    </div>
  );
}