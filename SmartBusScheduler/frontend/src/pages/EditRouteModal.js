import { useEffect } from "react";

export default function EditRouteModal({
  selectedRoute,
  setSelectedRoute,
  updateRoute,
  stops,
}) {
  // Close on ESC key
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") setSelectedRoute(null);
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [setSelectedRoute]);

  if (!selectedRoute) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">

      {/* BACKDROP */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={() => setSelectedRoute(null)}
      ></div>

      {/* MODAL */}
      <div className="relative bg-white w-full max-w-lg rounded-xl shadow-lg p-6 animate-fadeIn">

        {/* HEADER */}
        <div className="flex justify-between items-center mb-5">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              Edit Route
            </h2>
            <p className="text-sm text-gray-500">
              Update route details
            </p>
          </div>

          <button
            onClick={() => setSelectedRoute(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* FORM */}
        <div className="space-y-4">

          <div>
            <label className="text-sm text-gray-600">Route Name</label>
            <input
              value={selectedRoute.name}
              onChange={(e) =>
                setSelectedRoute({
                  ...selectedRoute,
                  name: e.target.value,
                })
              }
              className="w-full mt-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-green-500 outline-none"
            />
          </div>

          <div>
            <label className="text-sm text-gray-600">Start Stop</label>
            <select
              value={selectedRoute.start_stop_id}
              onChange={(e) =>
                setSelectedRoute({
                  ...selectedRoute,
                  start_stop_id: e.target.value,
                })
              }
              className="w-full mt-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-green-500 outline-none"
            >
              {stops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-600">End Stop</label>
            <select
              value={selectedRoute.end_stop_id}
              onChange={(e) =>
                setSelectedRoute({
                  ...selectedRoute,
                  end_stop_id: e.target.value,
                })
              }
              className="w-full mt-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-green-500 outline-none"
            >
              {stops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* ACTIONS */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setSelectedRoute(null)}
            className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-100"
          >
            Cancel
          </button>

          <button
            onClick={() => {
              updateRoute();
              setSelectedRoute(null);
            }}
            className="px-5 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition active:scale-95"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}