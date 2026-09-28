import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [employees, setEmployees] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDashboardData();
  }, []);

  async function fetchDashboardData() {
    try {
      setLoading(true);

      const [employeesResponse, attendanceResponse] =
        await Promise.all([
          axios.get(`${API_URL}/employees`),
          axios.get(`${API_URL}/attendance/today`),
        ]);

      setEmployees(employeesResponse.data);
      setAttendance(attendanceResponse.data);
      setError("");
    } catch (error) {
      console.error(error);
      setError("Unable to connect to attendance API.");
    } finally {
      setLoading(false);
    }
  }

  const totalEmployees = employees.length;

  const presentToday = attendance.length;

  const lateToday = attendance.filter(
    (record) => record.late_minutes > 0
  ).length;

  function getStatus(record) {
    if (record.check_out) {
      return "Completed";
    }

    return "Inside";
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Employee Attendance Dashboard</h1>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <h1>Employee Attendance Dashboard</h1>
        <p className="error">{error}</p>

        <button onClick={fetchDashboardData}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="page">

      {/* Header */}

      <header className="header">
        <div>
          <h1>Employee Attendance Dashboard</h1>
          <p>HR Attendance Management System</p>
        </div>

        <button onClick={fetchDashboardData}>
          Refresh
        </button>
      </header>

      {/* Summary Cards */}

      <section className="cards">

        <div className="card">
          <h3>Total Employees</h3>
          <p>{totalEmployees}</p>
        </div>

        <div className="card">
          <h3>Present Today</h3>
          <p>{presentToday}</p>
        </div>

        <div className="card">
          <h3>Late Today</h3>
          <p>{lateToday}</p>
        </div>

      </section>

      {/* Attendance Table */}

      <section className="table-section">

        <div className="section-header">
          <h2>Today's Attendance</h2>
          <span>
            {attendance.length} records
          </span>
        </div>

        {attendance.length === 0 ? (
          <p className="empty">
            No attendance records for today.
          </p>
        ) : (
          <div className="table-container">

            <table>

              <thead>
                <tr>
                  <th>Employee</th>
                  <th>ID</th>
                  <th>Shift</th>
                  <th>Check-in</th>
                  <th>Check-out</th>
                  <th>Late</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>

                {attendance.map((record) => (
                  <tr key={record.id}>

                    <td>
                      {record.employee_name}
                    </td>

                    <td>
                      {record.employee_id}
                    </td>

                    <td>
                      {record.shift_start}
                    </td>

                    <td>
                      {record.check_in}
                    </td>

                    <td>
                      {record.check_out || "--"}
                    </td>

                    <td>
                      {record.late_minutes > 0
                        ? `${record.late_minutes} min`
                        : "On time"}
                    </td>

                    <td>
                      <span
                        className={
                          record.check_out
                            ? "status completed"
                            : "status inside"
                        }
                      >
                        {getStatus(record)}
                      </span>
                    </td>

                  </tr>
                ))}

              </tbody>

            </table>

          </div>
        )}

      </section>

    </div>
  );
}

export default App;