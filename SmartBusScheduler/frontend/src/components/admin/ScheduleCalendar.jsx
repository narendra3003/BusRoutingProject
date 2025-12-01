import React from "react";
import Calendar from "react-calendar";
import "react-calendar/dist/Calendar.css";

function ScheduleCalendar({ selectedDate, setSelectedDate }) {
  const handleDateChange = (date) => {
    if (date > new Date()) return; // prevent future
    setSelectedDate(date);
  };

  return (
    <div className="bg-white p-4 shadow rounded flex flex-col items-center">
      <h2 className="text-xl font-bold mb-3">Check Schedule by Date</h2>
      <Calendar
        onChange={handleDateChange}
        value={selectedDate}
        className="mb-4"
        maxDate={new Date()}
      />
      <p className="text-gray-600">
        Showing schedule for:{" "}
        <span className="font-semibold">{selectedDate.toDateString()}</span>
      </p>
    </div>
  );
}

export default ScheduleCalendar;