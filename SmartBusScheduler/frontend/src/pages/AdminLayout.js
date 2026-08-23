import { useState } from "react";
import Sidebar from "./AdminSidebar";

export default function AdminLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div>
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

      <div
        className={`bg-gray-100 min-h-screen p-6 transition-all duration-300
          ${collapsed ? "ml-20" : "ml-64"}`}
      >
        {children}
      </div>
    </div>
  );
}