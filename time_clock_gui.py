"""
Time Clock Program with GUI and Hourly Wage Tracking
"""

# pyright: reportMissingTypeStubs=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportMissingParameterType=false, reportUnknownLambdaType=false, reportArgumentType=false, reportAssignmentType=false, reportAttributeAccessIssue=false, reportIndexIssue=false

import json
import calendar
import os
import shutil
import tkinter as tk
from pathlib import Path
import urllib.error
import urllib.request
import webbrowser
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    from tkcalendar import DateEntry
except ImportError:
    class DateEntry(ttk.Frame):
        """Fallback date picker when tkcalendar is unavailable."""

        def __init__(self, master=None, **kwargs):
            width = kwargs.pop("width", 12)
            self._date_pattern = kwargs.pop("date_pattern", "mm/dd/yyyy")
            self._firstweekday = kwargs.pop("firstweekday", "sunday")
            self._current_date = datetime.now().date()
            super().__init__(master)

            self._date_var = tk.StringVar(value=self._format_date(self._current_date))
            self._entry = ttk.Entry(self, width=width, textvariable=self._date_var)
            self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._button = ttk.Button(self, text="📅", width=2, command=self._open_calendar)
            self._button.pack(side=tk.LEFT, padx=(4, 0))

        def _format_date(self, value):
            return value.strftime("%m/%d/%Y")

        def _parse_date(self, text):
            return datetime.strptime(text.strip(), "%m/%d/%Y").date()

        def _sync_text(self):
            self._date_var.set(self._format_date(self._current_date))

        def _set_current_date(self, value):
            if isinstance(value, datetime):
                self._current_date = value.date()
            else:
                self._current_date = value
            self._sync_text()

        def _open_calendar(self):
            popup = tk.Toplevel(self)
            popup.title("Select Date")
            popup.resizable(False, False)
            popup.transient(self.winfo_toplevel())
            popup.grab_set()

            anchor_widget = self._button.winfo_toplevel()
            popup.update_idletasks()
            x = anchor_widget.winfo_rootx() + self._button.winfo_rootx() - anchor_widget.winfo_rootx()
            y = anchor_widget.winfo_rooty() + self._button.winfo_rooty() - anchor_widget.winfo_rooty() + self._button.winfo_height()
            popup.geometry(f"+{x}+{y}")

            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December",
            ]
            weekday_names = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
            weekday_offset = 6 if str(self._firstweekday).lower().startswith("mon") else 0

            today = self._current_date
            month_var = tk.IntVar(value=today.month)
            year_var = tk.IntVar(value=today.year)

            container = ttk.Frame(popup, padding=10)
            container.pack(fill=tk.BOTH, expand=True)

            header = ttk.Frame(container)
            header.pack(fill=tk.X, pady=(0, 8))

            month_combo = ttk.Combobox(header, width=12, state="readonly", values=month_names)
            month_combo.current(today.month - 1)
            month_combo.pack(side=tk.LEFT)

            year_spin = ttk.Spinbox(header, from_=1900, to=2100, width=6, textvariable=year_var)
            year_spin.pack(side=tk.LEFT, padx=(6, 0))

            calendar_frame = ttk.Frame(container)
            calendar_frame.pack()

            button_rows = []

            def refresh_calendar(*_):
                for child in calendar_frame.winfo_children():
                    child.destroy()

                month_index = month_combo.current() + 1
                year_value = int(year_var.get())
                month_label = ttk.Label(container, text=f"{month_names[month_index - 1]} {year_value}", style="Header.TLabel")
                month_label.pack_forget()

                for column, weekday_name in enumerate(weekday_names):
                    display_index = (column + weekday_offset) % 7
                    ttk.Label(calendar_frame, text=weekday_names[display_index], width=4, anchor=tk.CENTER).grid(row=0, column=column, padx=1, pady=(0, 4))

                month_calendar = calendar.monthcalendar(year_value, month_index)
                for row_index, week in enumerate(month_calendar, start=1):
                    for column, day in enumerate(week):
                        if day == 0:
                            ttk.Label(calendar_frame, text="", width=4).grid(row=row_index, column=column, padx=1, pady=1)
                            continue

                        def choose_date(day_value=day, month_value=month_index, year_value=year_value):
                            self._set_current_date(datetime(year_value, month_value, day_value).date())
                            popup.destroy()

                        is_today = day == today.day and month_index == today.month and year_value == today.year
                        style = "Accent.TButton" if is_today else "TButton"
                        ttk.Button(calendar_frame, text=str(day), width=4, style=style, command=choose_date).grid(row=row_index, column=column, padx=1, pady=1)

            def on_month_change(_=None):
                refresh_calendar()

            def on_year_change(_=None):
                refresh_calendar()

            month_combo.bind("<<ComboboxSelected>>", on_month_change)
            year_var.trace_add("write", on_year_change)
            refresh_calendar()

        def pack(self, *args, **kwargs):
            return super().pack(*args, **kwargs)

        def grid(self, *args, **kwargs):
            return super().grid(*args, **kwargs)

        def place(self, *args, **kwargs):
            return super().place(*args, **kwargs)

        def set_date(self, value):
            self._set_current_date(value)

        def get_date(self):
            try:
                self._current_date = self._parse_date(self._date_var.get())
            except ValueError:
                pass
            return self._current_date

        def get(self):
            return self._date_var.get()

        def delete(self, first, last=None):
            self._entry.delete(first, last)

        def insert(self, index, string):
            self._entry.insert(index, string)

from time_clock_paths import get_backup_dir, get_data_file_path
from time_clock_version import APP_NAME, APP_VERSION, GITHUB_REPO, is_newer_version


class TimeClockData:
    def __init__(self, data_file: str = None):
        self.data_file = data_file if data_file is not None else get_data_file_path()
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        """Load time clock data from JSON file"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                # Ensure new data structures exist
                if "schedules" not in data:
                    data["schedules"] = []
                if "payroll_periods" not in data:
                    data["payroll_periods"] = []
                if "leave_requests" not in data:
                    data["leave_requests"] = []
                if "departments" not in data:
                    data["departments"] = ["General", "Sales", "Operations", "Administration", "IT"]
                if "project_notes" not in data:
                    data["project_notes"] = []
                if "invoices" not in data:
                    data["invoices"] = []
                return data
        return {
            "employees": {},
            "time_entries": [],
            "schedules": [],
            "payroll_periods": [],
            "leave_requests": [],
            "departments": ["General", "Sales", "Operations", "Administration", "IT"],
            "project_notes": [],
            "invoices": []
        }
    
    def save_data(self):
        """Save time clock data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_employee(self, employee_id: str, first_name: str, middle_name: str, last_name: str, hourly_rate: float, overtime_rate: float, street: str = "", city: str = "", state: str = "", zip_code: str = "", phone: str = "", email: str = "", department: str = "", job_title: str = "", employee_type: str = "Full-Time", hire_date: str = None):
        """Add a new employee to the system"""
        if employee_id in self.data["employees"]:
            return False, f"Employee {employee_id} already exists!"
        
        full_name = f"{first_name} {middle_name} {last_name}" if middle_name else f"{first_name} {last_name}"
        
        if hire_date is None:
            hire_date = datetime.now().strftime('%Y-%m-%d')
        
        self.data["employees"][employee_id] = {
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "name": full_name,
            "hourly_rate": hourly_rate,
            "overtime_rate": overtime_rate,
            "street": street,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "phone": phone,
            "email": email,
            "department": department,
            "job_title": job_title,
            "employee_type": employee_type,
            "hire_date": hire_date,
            "pto_balance": 0.0,
            "sick_balance": 0.0,
            "vacation_balance": 0.0,
            "clocked_in": False,
            "current_entry": None,
            "on_break": False,
            "break_start": None
        }
        self.save_data()
        return True, f"Employee {full_name} added successfully!"
    
    def update_hourly_rate(self, employee_id: str, new_rate: float):
        """Update an employee's hourly rate"""
        if employee_id not in self.data["employees"]:
            return False, f"Employee {employee_id} not found!"
        
        old_rate = self.data["employees"][employee_id]["hourly_rate"]
        self.data["employees"][employee_id]["hourly_rate"] = new_rate
        self.save_data()
        return True, f"Hourly rate updated from ${old_rate:.2f} to ${new_rate:.2f}"
    
    def clock_in(self, employee_id: str, project: str = "General"):
        """Clock in an employee with project assignment"""
        if employee_id not in self.data["employees"]:
            return False, f"Employee {employee_id} not found!"
        
        employee = self.data["employees"][employee_id]
        
        if employee["clocked_in"]:
            return False, f"{employee['name']} is already clocked in!"
        
        clock_in_time = datetime.now().isoformat()
        employee["clocked_in"] = True
        employee["current_entry"] = len(self.data["time_entries"])
        
        entry = {
            "employee_id": employee_id,
            "name": employee["name"],
            "clock_in": clock_in_time,
            "clock_out": None,
            "hours_worked": 0,
            "hourly_rate": employee["hourly_rate"],
            "wages": 0,
            "project": project
        }
        
        self.data["time_entries"].append(entry)
        self.save_data()
        
        time_str = datetime.fromisoformat(clock_in_time).strftime('%Y-%m-%d %I:%M:%S %p')
        return True, f"{employee['name']} clocked in at {time_str}"
    
    def clock_out(self, employee_id: str):
        """Clock out an employee and calculate wages"""
        if employee_id not in self.data["employees"]:
            return False, f"Employee {employee_id} not found!"
        
        employee = self.data["employees"][employee_id]
        
        if not employee["clocked_in"]:
            return False, f"{employee['name']} is not clocked in!"
        
        clock_out_time = datetime.now().isoformat()
        entry_index = employee["current_entry"]
        entry = self.data["time_entries"][entry_index]
        
        # Calculate hours worked
        clock_in_dt = datetime.fromisoformat(entry["clock_in"])
        clock_out_dt = datetime.fromisoformat(clock_out_time)
        hours_worked = (clock_out_dt - clock_in_dt).total_seconds() / 3600
        
        # Calculate wages
        wages = hours_worked * employee["hourly_rate"]
        
        # Update entry
        entry["clock_out"] = clock_out_time
        entry["hours_worked"] = round(hours_worked, 2)
        entry["wages"] = round(wages, 2)
        
        # Update employee status
        employee["clocked_in"] = False
        employee["current_entry"] = None
        
        self.save_data()
        
        time_str = clock_out_dt.strftime('%Y-%m-%d %I:%M:%S %p')
        message = f"{employee['name']} clocked out at {time_str}\n\n"
        message += f"Hours worked: {entry['hours_worked']:.2f}\n"
        message += f"Hourly rate: ${entry['hourly_rate']:.2f}\n"
        message += f"Wages earned: ${entry['wages']:.2f}"
        return True, message
    
    def get_all_employees(self):
        """Get list of all employees"""
        return self.data["employees"]
    
    def get_employee(self, employee_id: str):
        """Get specific employee data"""
        return self.data["employees"].get(employee_id)
    
    def get_time_entries(self, employee_id: Optional[str] = None):
        """Get time entries, optionally filtered by employee"""
        entries = self.data["time_entries"]
        if employee_id:
            entries = [e for e in entries if e["employee_id"] == employee_id]
        return entries

    def normalize_break_record(self, break_entry: Dict):
        """Return a break record with the legacy and current field names populated."""
        start_time = break_entry.get("start_time") or break_entry.get("start")
        end_time = break_entry.get("end_time") or break_entry.get("end")
        break_type = break_entry.get("break_type") or break_entry.get("type") or "Unpaid"

        if not start_time or not end_time:
            return None

        break_start = datetime.fromisoformat(start_time)
        break_end = datetime.fromisoformat(end_time)
        duration = (break_end - break_start).total_seconds() / 3600

        return {
            "start_time": start_time,
            "end_time": end_time,
            "break_type": break_type,
            "start": start_time,
            "end": end_time,
            "type": break_type,
            "duration": round(duration, 2)
        }

    def calculate_break_hours(self, entry: Dict, unpaid_only: bool = False) -> float:
        """Calculate break hours for an entry, optionally limiting to unpaid breaks."""
        total = 0.0
        for break_entry in entry.get("breaks", []):
            normalized = self.normalize_break_record(break_entry)
            if not normalized:
                continue
            if unpaid_only and normalized["break_type"] != "Unpaid":
                continue
            total += normalized["duration"]
        return total
    
    def calculate_total_wages(self, employee_id: Optional[str] = None):
        """Calculate total wages"""
        entries = self.get_time_entries(employee_id)
        completed_entries = [e for e in entries if e["clock_out"] is not None]
        
        total_hours = sum(e["hours_worked"] for e in completed_entries)
        total_wages = sum(e["wages"] for e in completed_entries)
        
        return total_hours, total_wages, len(completed_entries)
    
    def add_manual_entry(self, employee_id: str, clock_in_time: datetime, clock_out_time: datetime, project: str = "General"):
        """Manually add a past time entry"""
        if employee_id not in self.data["employees"]:
            return False, f"Employee {employee_id} not found!"
        
        employee = self.data["employees"][employee_id]
        
        # Validate times
        if clock_out_time <= clock_in_time:
            return False, "Clock out time must be after clock in time!"
        
        # Calculate hours worked
        hours_worked = (clock_out_time - clock_in_time).total_seconds() / 3600
        
        # Calculate wages
        wages = hours_worked * employee["hourly_rate"]
        
        # Create entry
        entry = {
            "employee_id": employee_id,
            "name": employee["name"],
            "clock_in": clock_in_time.isoformat(),
            "clock_out": clock_out_time.isoformat(),
            "hours_worked": round(hours_worked, 2),
            "hourly_rate": employee["hourly_rate"],
            "wages": round(wages, 2),
            "project": project
        }
        
        self.data["time_entries"].append(entry)
        self.save_data()
        
        message = f"Manual entry added for {employee['name']}\n"
        message += f"Hours worked: {entry['hours_worked']:.2f}\n"
        message += f"Wages: ${entry['wages']:.2f}"
        return True, message
    
    def delete_employee(self, employee_id: str):
        """Delete an employee and optionally their time entries"""
        if employee_id not in self.data["employees"]:
            return False, "Employee not found!"
        
        employee_name = self.data["employees"][employee_id]["name"]
        
        # Check if employee is clocked in
        if self.data["employees"][employee_id]["clocked_in"]:
            return False, f"{employee_name} is currently clocked in! Clock them out first."
        
        # Delete employee
        del self.data["employees"][employee_id]
        self.save_data()
        
        return True, f"{employee_name} has been deleted."
    
    def delete_employee_with_entries(self, employee_id: str):
        """Delete an employee and all their time entries"""
        if employee_id not in self.data["employees"]:
            return False, "Employee not found!"
        
        employee_name = self.data["employees"][employee_id]["name"]
        
        # Check if employee is clocked in
        if self.data["employees"][employee_id]["clocked_in"]:
            return False, f"{employee_name} is currently clocked in! Clock them out first."
        
        # Delete all time entries for this employee
        self.data["time_entries"] = [e for e in self.data["time_entries"] if e["employee_id"] != employee_id]
        
        # Delete employee
        del self.data["employees"][employee_id]
        self.save_data()
        
        return True, f"{employee_name} and all their time entries have been deleted."
    
    def start_break(self, employee_id: str, break_type: str = "Unpaid"):
        """Start a break for an employee"""
        if employee_id not in self.data["employees"]:
            return False, f"Employee {employee_id} not found!"
        
        employee = self.data["employees"][employee_id]
        
        if not employee["clocked_in"]:
            return False, f"{employee['name']} must be clocked in to take a break!"
        
        if employee.get("on_break", False):
            return False, f"{employee['name']} is already on break!"
        
        break_time = datetime.now().isoformat()
        employee["on_break"] = True
        employee["break_start"] = break_time
        employee["break_type"] = break_type
        self.save_data()
        
        time_str = datetime.fromisoformat(break_time).strftime('%I:%M:%S %p')
        return True, f"{employee['name']} started {break_type} break at {time_str}"
    
    def end_break(self, employee_id: str):
        """End a break for an employee"""
        if employee_id not in self.data["employees"]:
            return False, f"Employee {employee_id} not found!"
        
        employee = self.data["employees"][employee_id]
        
        if not employee.get("on_break", False):
            return False, f"{employee['name']} is not on break!"
        
        break_end = datetime.now()
        break_start = datetime.fromisoformat(employee["break_start"])
        break_duration = (break_end - break_start).total_seconds() / 3600
        break_type = employee.get("break_type", "Unpaid")
        
        # Update the current time entry with break info
        entry_index = employee.get("current_entry")
        if entry_index is not None and entry_index < len(self.data["time_entries"]):
            entry = self.data["time_entries"][entry_index]
            if "breaks" not in entry:
                entry["breaks"] = []
            entry["breaks"].append({
                "start_time": employee["break_start"],
                "end_time": break_end.isoformat(),
                "break_type": break_type,
                "start": employee["break_start"],
                "end": break_end.isoformat(),
                "type": break_type,
                "duration": round(break_duration, 2)
            })
        
        employee["on_break"] = False
        employee["break_start"] = None
        employee["break_type"] = None
        self.save_data()
        
        time_str = break_end.strftime('%I:%M:%S %p')
        message = f"{employee['name']} ended break at {time_str}\\n"
        message += f"Break duration: {break_duration:.2f} hours ({break_type})"
        return True, message
    
    def get_payroll_report(self, start_date: datetime, end_date: datetime, employee_id: Optional[str] = None):
        """Generate payroll report for a date range"""
        entries = self.get_time_entries(employee_id)
        report_entries = []
        
        for entry in entries:
            if entry["clock_out"] is None:
                continue
            
            entry_date = datetime.fromisoformat(entry["clock_in"])
            if start_date <= entry_date <= end_date:
                # Calculate break time
                break_hours = self.calculate_break_hours(entry)
                unpaid_break_hours = self.calculate_break_hours(entry, unpaid_only=True)
                
                # Calculate regular and overtime hours
                worked_hours = entry["hours_worked"]
                net_hours = worked_hours - unpaid_break_hours
                
                # Determine regular vs overtime (40 hour week threshold)
                regular_hours = min(net_hours, 40)
                overtime_hours = max(0, net_hours - 40)
                
                # Get employee for overtime rate
                emp = self.data["employees"].get(entry["employee_id"])
                ot_rate = emp.get("overtime_rate", entry["hourly_rate"] * 1.5) if emp else entry["hourly_rate"] * 1.5
                
                regular_pay = regular_hours * entry["hourly_rate"]
                overtime_pay = overtime_hours * ot_rate
                gross_pay = regular_pay + overtime_pay
                
                report_entries.append({
                    "employee_id": entry["employee_id"],
                    "name": entry["name"],
                    "date": entry_date.strftime('%Y-%m-%d'),
                    "clock_in": entry["clock_in"],
                    "clock_out": entry["clock_out"],
                    "total_hours": worked_hours,
                    "break_hours": break_hours,
                    "unpaid_break_hours": unpaid_break_hours,
                    "net_hours": net_hours,
                    "regular_hours": regular_hours,
                    "overtime_hours": overtime_hours,
                    "hourly_rate": entry["hourly_rate"],
                    "overtime_rate": ot_rate,
                    "regular_pay": round(regular_pay, 2),
                    "overtime_pay": round(overtime_pay, 2),
                    "gross_pay": round(gross_pay, 2),
                    "entry_type": "work"
                })
        
        # Add approved leave requests as paid time
        leave_requests = self.data.get("leave_requests", [])
        for leave in leave_requests:
            if leave["status"] != "Approved":
                continue
            
            # Check if employee matches filter
            if employee_id and leave["employee_id"] != employee_id:
                continue
            
            # Parse leave dates
            try:
                leave_start = datetime.strptime(leave["start_date"], '%m/%d/%Y')
            except:
                try:
                    leave_start = datetime.strptime(leave["start_date"], '%Y-%m-%d')
                except:
                    continue
            
            # Check if leave falls in date range
            if start_date <= leave_start <= end_date:
                emp = self.data["employees"].get(leave["employee_id"])
                if emp:
                    regular_pay = leave["hours"] * emp["hourly_rate"]
                    
                    report_entries.append({
                        "employee_id": leave["employee_id"],
                        "name": leave["employee_name"],
                        "date": leave["start_date"],
                        "clock_in": leave["start_date"],
                        "clock_out": leave["end_date"],
                        "total_hours": leave["hours"],
                        "break_hours": 0,
                        "unpaid_break_hours": 0,
                        "net_hours": leave["hours"],
                        "regular_hours": leave["hours"],
                        "overtime_hours": 0,
                        "hourly_rate": emp["hourly_rate"],
                        "overtime_rate": 0,
                        "regular_pay": round(regular_pay, 2),
                        "overtime_pay": 0,
                        "gross_pay": round(regular_pay, 2),
                        "entry_type": "leave",
                        "leave_type": leave["leave_type"]
                    })
        
        return report_entries
    
    def request_leave(self, employee_id: str, leave_type: str, start_date: str, end_date: str, hours: float, reason: str = ""):
        """Submit a leave request"""
        if employee_id not in self.data["employees"]:
            return False, "Employee not found!"
        
        employee = self.data["employees"][employee_id]
        
        # Check balance
        balance_key = f"{leave_type.lower()}_balance"
        current_balance = employee.get(balance_key, 0)
        
        if current_balance < hours:
            return False, f"Insufficient {leave_type} balance! Available: {current_balance:.2f} hours"
        
        request = {
            "request_id": len(self.data["leave_requests"]) + 1,
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "hours": hours,
            "reason": reason,
            "status": "Pending",
            "submitted_date": datetime.now().strftime('%Y-%m-%d'),
            "approved_by": None,
            "approved_date": None
        }
        
        self.data["leave_requests"].append(request)
        self.save_data()
        
        return True, f"Leave request submitted successfully! Request ID: {request['request_id']}"
    
    def approve_leave_request(self, request_id: int, approver_name: str):
        """Approve a leave request"""
        request = next((r for r in self.data["leave_requests"] if r["request_id"] == request_id), None)
        
        if not request:
            return False, "Leave request not found!"
        
        if request["status"] != "Pending":
            return False, f"Request is already {request['status']}"
        
        employee = self.data["employees"].get(request["employee_id"])
        if not employee:
            return False, "Employee not found!"
        
        # Deduct from balance
        balance_key = f"{request['leave_type'].lower()}_balance"
        employee[balance_key] = employee.get(balance_key, 0) - request["hours"]
        
        request["status"] = "Approved"
        request["approved_by"] = approver_name
        request["approved_date"] = datetime.now().strftime('%Y-%m-%d')
        
        self.save_data()
        return True, f"Leave request approved! {request['hours']} hours deducted from {request['leave_type']} balance"
    
    def deny_leave_request(self, request_id: int, approver_name: str, reason: str = ""):
        """Deny a leave request"""
        request = next((r for r in self.data["leave_requests"] if r["request_id"] == request_id), None)
        
        if not request:
            return False, "Leave request not found!"
        
        if request["status"] != "Pending":
            return False, f"Request is already {request['status']}"
        
        request["status"] = "Denied"
        request["approved_by"] = approver_name
        request["approved_date"] = datetime.now().strftime('%Y-%m-%d')
        request["denial_reason"] = reason
        
        self.save_data()
        return True, "Leave request denied"
    
    def adjust_pto_balance(self, employee_id: str, leave_type: str, hours: float, reason: str = ""):
        """Manually adjust PTO balance"""
        if employee_id not in self.data["employees"]:
            return False, "Employee not found!"
        
        employee = self.data["employees"][employee_id]
        balance_key = f"{leave_type.lower()}_balance"
        
        old_balance = employee.get(balance_key, 0)
        employee[balance_key] = old_balance + hours
        
        self.save_data()
        return True, f"{leave_type} balance adjusted: {old_balance:.2f} → {employee[balance_key]:.2f} hours"
    
    def edit_employee(self, employee_id: str, first_name: str = None, middle_name: str = None, last_name: str = None, new_rate: float = None, new_overtime_rate: float = None, new_street: str = None, new_city: str = None, new_state: str = None, new_zip: str = None, new_phone: str = None, new_email: str = None, new_department: str = None, new_job_title: str = None, new_employee_type: str = None, new_hire_date: str = None):
        """Edit an employee's name and/or hourly rate"""
        if employee_id not in self.data["employees"]:
            return False, "Employee not found!"
        
        employee = self.data["employees"][employee_id]
        
        if first_name is not None:
            employee["first_name"] = first_name
        if middle_name is not None:
            employee["middle_name"] = middle_name
        if last_name is not None:
            employee["last_name"] = last_name
        
        # Update full name if any name component changed
        if first_name is not None or middle_name is not None or last_name is not None:
            fn = employee.get("first_name", "")
            mn = employee.get("middle_name", "")
            ln = employee.get("last_name", "")
            employee["name"] = f"{fn} {mn} {ln}" if mn else f"{fn} {ln}"
        
        if new_rate is not None:
            employee["hourly_rate"] = new_rate
        
        if new_overtime_rate is not None:
            employee["overtime_rate"] = new_overtime_rate
        
        if new_street is not None:
            employee["street"] = new_street
        
        if new_city is not None:
            employee["city"] = new_city
        
        if new_state is not None:
            employee["state"] = new_state
        
        if new_zip is not None:
            employee["zip_code"] = new_zip
        
        if new_phone is not None:
            employee["phone"] = new_phone
        
        if new_email is not None:
            employee["email"] = new_email
        
        if new_department is not None:
            employee["department"] = new_department
        
        if new_job_title is not None:
            employee["job_title"] = new_job_title
        
        if new_employee_type is not None:
            employee["employee_type"] = new_employee_type
        
        if new_hire_date is not None:
            employee["hire_date"] = new_hire_date
        
        self.save_data()
        
        message = f"Employee updated successfully!"
        if first_name is not None or middle_name is not None or last_name is not None:
            message += f"\nName: {employee['name']}"
        if new_rate is not None:
            message += f"\nHourly Rate: ${new_rate:.2f}"
        if new_overtime_rate is not None:
            message += f"\nOvertime Rate: ${new_overtime_rate:.2f}"
        
        return True, message
    
    def delete_entry(self, entry_index: int):
        """Delete a time entry"""
        if entry_index < 0 or entry_index >= len(self.data["time_entries"]):
            return False, "Invalid entry index!"
        
        entry = self.data["time_entries"][entry_index]
        
        # Update employee status if they are currently clocked in for this entry
        employee = self.data["employees"].get(entry["employee_id"])
        if employee and employee.get("current_entry") == entry_index:
            employee["clocked_in"] = False
            employee["current_entry"] = None
        
        # Adjust current_entry indices for other employees
        for emp in self.data["employees"].values():
            if emp.get("current_entry") is not None and emp["current_entry"] > entry_index:
                emp["current_entry"] -= 1
        
        del self.data["time_entries"][entry_index]
        self.save_data()
        return True, "Entry deleted successfully!"
    
    def update_entry(self, entry_index: int, clock_in_time: datetime, clock_out_time: datetime = None, breaks: Optional[list] = None):
        """Update an existing time entry"""
        if entry_index < 0 or entry_index >= len(self.data["time_entries"]):
            return False, "Invalid entry index!"
        
        entry = self.data["time_entries"][entry_index]
        employee = self.data["employees"].get(entry["employee_id"])
        
        if not employee:
            return False, "Employee not found!"
        
        original_clock_out = entry.get("clock_out")
        effective_clock_out = clock_out_time
        if effective_clock_out is None and original_clock_out is not None:
            effective_clock_out = datetime.fromisoformat(original_clock_out)

        if effective_clock_out is not None and effective_clock_out <= clock_in_time:
            return False, "Clock out time must be after clock in time!"
        
        if breaks is not None:
            entry["breaks"] = breaks
        
        # Update entry
        entry["clock_in"] = clock_in_time.isoformat()
        if clock_out_time is not None:
            entry["clock_out"] = clock_out_time.isoformat()
            hours_worked = (clock_out_time - clock_in_time).total_seconds() / 3600
            entry["hours_worked"] = round(hours_worked, 2)
            entry["wages"] = round(hours_worked * entry["hourly_rate"], 2)
        elif original_clock_out is not None:
            hours_worked = (effective_clock_out - clock_in_time).total_seconds() / 3600
            entry["hours_worked"] = round(hours_worked, 2)
            entry["wages"] = round(hours_worked * entry["hourly_rate"], 2)
        elif original_clock_out is None:
            entry["clock_out"] = None
            entry["hours_worked"] = 0
            entry["wages"] = 0
        
        if original_clock_out is None and entry.get("clock_out") is not None:
            employee["clocked_in"] = False
            employee["current_entry"] = None

        self.save_data()
        
        message = f"Entry updated for {entry['name']}\n"
        message += f"Hours worked: {entry['hours_worked']:.2f}\n"
        message += f"Wages: ${entry['wages']:.2f}"
        return True, message


class TimeClockGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.state('zoomed')  # Start maximized
        self.root.resizable(True, True)
        
        # Set color scheme
        self.bg_color = "#2c3e50"
        self.fg_color = "#ecf0f1"
        self.accent_color = "#3498db"
        self.success_color = "#27ae60"
        self.danger_color = "#e74c3c"
        
        self.data_manager = TimeClockData()
        
        # Configure style
        self.setup_styles()
        
        # Create UI
        self.create_widgets()
        
        # Update display
        self.refresh_employee_list()
        self.update_clock()
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground=self.accent_color)
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'), foreground=self.accent_color)
        style.configure('TButton', font=('Segoe UI', 10), padding=10)
        style.configure('Action.TButton', font=('Segoe UI', 11, 'bold'))
        style.configure('TEntry', fieldbackground='white', font=('Segoe UI', 10))
        style.configure('TCombobox', fieldbackground='white', font=('Segoe UI', 10))
        
        self.root.configure(bg=self.bg_color)
    
    def create_widgets(self):
        """Create all GUI widgets with tabbed interface"""
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Print Report", command=self.print_report)
        file_menu.add_command(label="Backup Data", command=self.backup_data)
        file_menu.add_command(label="Export All Data", command=self.export_all_data)
        file_menu.add_command(label="Import Data", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit Program", command=self.exit_program)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Payroll Report", command=self.quick_payroll_report)
        reports_menu.add_command(label="Attendance Report", command=self.quick_attendance_report)
        reports_menu.add_command(label="Employee Hours Summary", command=self.quick_hours_summary)
        reports_menu.add_command(label="Leave Requests Summary", command=self.leave_requests_summary)
        reports_menu.add_command(label="Department Report", command=self.department_report)
        
        # Tools/Settings menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Application Settings", command=self.application_settings)
        tools_menu.add_command(label="Backup/Restore Database", command=self.backup_restore_db)
        tools_menu.add_command(label="Clear Old Data", command=self.clear_old_data)
        tools_menu.add_command(label="Recalculate Balances", command=self.recalculate_balances)
        tools_menu.add_command(label="Manage Departments", command=self.manage_departments)
        
        # Admin menu
        admin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Admin", menu=admin_menu)
        admin_menu.add_command(label="User Management", command=self.user_management)
        admin_menu.add_command(label="Audit Log", command=self.audit_log)
        admin_menu.add_command(label="System Configuration", command=self.system_configuration)
        admin_menu.add_command(label="Holiday Calendar", command=self.holiday_calendar)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.user_guide)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.keyboard_shortcuts)
        help_menu.add_command(label="Check for Updates", command=self.check_updates)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.about_dialog)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title and Clock
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="⏰ TIME CLOCK MANAGEMENT SYSTEM", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        self.clock_label = ttk.Label(title_frame, text="", style='Header.TLabel')
        self.clock_label.pack(side=tk.RIGHT)
        
        # Create Notebook (Tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_time_clock_tab()
        self.create_payroll_tab()
        self.create_leave_management_tab()
        self.create_reports_tab()
        self.create_employee_management_tab()
        self.create_projects_tab()
        self.create_invoice_tab()
        
        # Initialize data in tabs
        self.refresh_leave_requests()
        self.refresh_project_list()
        self.refresh_invoice_list()
    
    def create_time_clock_tab(self):
        """Create the Time Clock tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="⏰ Time Clock")
        
        # Configure grid
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Left Panel - Quick Actions
        left_panel = ttk.Frame(tab)
        left_panel.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 20))
        
        # Employee Selection
        ttk.Label(left_panel, text="Select Employee:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        self.employee_combo = ttk.Combobox(left_panel, state='readonly', width=30, font=('Segoe UI', 11))
        self.employee_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        self.employee_combo.bind('<<ComboboxSelected>>', self.on_employee_selected)
        
        # Project Selection
        ttk.Label(left_panel, text="Select Project:", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        self.project_combo = ttk.Combobox(left_panel, state='readonly', width=30, font=('Segoe UI', 11))
        self.project_combo.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Initialize projects list if not exists
        if "projects" not in self.data_manager.data:
            self.data_manager.data["projects"] = ["General", "Project A", "Project B", "Project C", "Maintenance", "Training"]
            self.data_manager.save_data()
        
        self.project_combo['values'] = self.data_manager.data.get("projects", ["General"])
        if self.project_combo['values']:
            self.project_combo.current(0)
        
        # Employee Info Display
        info_frame = ttk.Frame(left_panel)
        info_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.info_text = tk.Text(info_frame, height=10, width=35, font=('Segoe UI', 10), 
                                bg='#34495e', fg=self.fg_color, relief=tk.FLAT, padx=10, pady=10)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Clock In/Out Buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.clock_in_btn = tk.Button(button_frame, text="🟢 CLOCK IN", font=('Segoe UI', 12, 'bold'),
                                      bg=self.success_color, fg='white', relief=tk.FLAT, 
                                      command=self.clock_in, cursor='hand2', pady=15)
        self.clock_in_btn.pack(fill=tk.X, pady=(0, 10))
        
        self.clock_out_btn = tk.Button(button_frame, text="🔴 CLOCK OUT", font=('Segoe UI', 12, 'bold'),
                                       bg=self.danger_color, fg='white', relief=tk.FLAT,
                                       command=self.clock_out, cursor='hand2', pady=15)
        self.clock_out_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Break Buttons
        self.start_break_btn = tk.Button(button_frame, text="☕ START BREAK", font=('Segoe UI', 11, 'bold'),
                                        bg=self.accent_color, fg='white', relief=tk.FLAT,
                                        command=self.start_break_dialog, cursor='hand2', pady=12)
        self.start_break_btn.pack(fill=tk.X, pady=(0, 10))
        
        self.end_break_btn = tk.Button(button_frame, text="⏸️ END BREAK", font=('Segoe UI', 11, 'bold'),
                                      bg="#95a5a6", fg='white', relief=tk.FLAT,
                                      command=self.end_break, cursor='hand2', pady=12)
        self.end_break_btn.pack(fill=tk.X)
        
        # Right Panel - Time Entries
        right_panel = ttk.Frame(tab)
        right_panel.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        
        ttk.Label(right_panel, text="📋 Recent Time Entries", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Time entries display
        entries_frame = ttk.Frame(right_panel)
        entries_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(entries_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.entries_text = scrolledtext.ScrolledText(entries_frame, width=70, height=25, 
                                                      font=('Consolas', 9), bg='#34495e', 
                                                      fg=self.fg_color, yscrollcommand=scrollbar.set)
        self.entries_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.entries_text.yview)
        
        # Entry management buttons
        entry_mgmt_frame = ttk.Frame(right_panel)
        entry_mgmt_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(entry_mgmt_frame, text="📝 Log Past Hours", command=self.log_past_hours_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(entry_mgmt_frame, text="✏️ Edit Entry", command=self.edit_entry_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(entry_mgmt_frame, text="🗑️ Delete Entry", command=self.delete_entry_dialog).pack(side=tk.LEFT, padx=5)
    
    def create_payroll_tab(self):
        """Create the Payroll tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="💵 Payroll")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        
        ttk.Label(tab, text="💼 Payroll Report Generator", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 20))
        
        # Date range selection
        date_frame = ttk.Frame(tab)
        date_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(date_frame, text="Start Date:").pack(side=tk.LEFT, padx=(0, 10))
        self.payroll_start_date = DateEntry(date_frame, width=12, 
                                            date_pattern='mm/dd/yyyy',
                                            firstweekday='sunday')
        self.payroll_start_date.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(date_frame, text="End Date:").pack(side=tk.LEFT, padx=(0, 10))
        self.payroll_end_date = DateEntry(date_frame, width=12, 
                                          date_pattern='mm/dd/yyyy',
                                          firstweekday='sunday')
        self.payroll_end_date.pack(side=tk.LEFT, padx=(0, 20))
        
        # Set dates after both are created
        self.payroll_start_date.set_date(datetime.now().replace(day=1))
        self.payroll_end_date.set_date(datetime.now())
        
        ttk.Button(date_frame, text="🔍 Generate Report", command=self.generate_payroll_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(date_frame, text="📥 Export to CSV", command=self.export_payroll_csv).pack(side=tk.LEFT)
        
        # Payroll report display
        report_frame = ttk.Frame(tab)
        report_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.payroll_text = scrolledtext.ScrolledText(report_frame, font=('Consolas', 9), 
                                                      bg='#34495e', fg=self.fg_color)
        self.payroll_text.pack(fill=tk.BOTH, expand=True)
    
    def create_leave_management_tab(self):
        """Create the Leave Management tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="🏖️ Leave Management")
        
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(2, weight=1)
        
        # Left side - Request Leave
        left_frame = ttk.LabelFrame(tab, text="Request Leave", padding="15")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10), rowspan=3)
        
        ttk.Label(left_frame, text="Employee:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.leave_employee_combo = ttk.Combobox(left_frame, state='readonly', width=25)
        self.leave_employee_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.leave_employee_combo.bind('<<ComboboxSelected>>', self.update_leave_balance)
        
        ttk.Label(left_frame, text="Leave Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        leave_type_frame = ttk.Frame(left_frame)
        leave_type_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.leave_type_combo = ttk.Combobox(leave_type_frame, state='readonly', width=15, values=["PTO", "Sick", "Vacation"])
        self.leave_type_combo.pack(side=tk.LEFT)
        self.leave_type_combo.current(0)
        self.leave_type_combo.bind('<<ComboboxSelected>>', self.update_leave_balance)
        
        self.leave_balance_label = ttk.Label(leave_type_frame, text="Balance: 0.0 hrs", 
                                            foreground='#27ae60', font=('Segoe UI', 12, 'bold'))
        self.leave_balance_label.pack(side=tk.LEFT, padx=(15, 0))
        
        ttk.Label(left_frame, text="Start Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.leave_start_date = DateEntry(left_frame, width=23, 
                                          date_pattern='mm/dd/yyyy',
                                          firstweekday='sunday')
        self.leave_start_date.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.leave_start_date.set_date(datetime.now())
        
        ttk.Label(left_frame, text="End Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.leave_end_date = DateEntry(left_frame, width=23, 
                                        date_pattern='mm/dd/yyyy',
                                        firstweekday='sunday')
        self.leave_end_date.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        self.leave_end_date.set_date(datetime.now())
        
        ttk.Label(left_frame, text="Hours:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.leave_hours = ttk.Entry(left_frame, width=25)
        self.leave_hours.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(left_frame, text="Reason:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.leave_reason = tk.Text(left_frame, width=25, height=4)
        self.leave_reason.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(left_frame, text="📤 Submit Request", command=self.submit_leave_request).grid(row=6, column=0, columnspan=2, pady=(15, 5))
        ttk.Button(left_frame, text="⚙️ Adjust PTO Balance", command=self.adjust_pto_dialog).grid(row=7, column=0, columnspan=2, pady=5)
        
        # Right side - Pending Requests
        right_frame = ttk.LabelFrame(tab, text="Pending Leave Requests", padding="15")
        right_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        self.leave_requests_text = scrolledtext.ScrolledText(right_frame, font=('Consolas', 9), 
                                                             bg='#34495e', fg=self.fg_color)
        self.leave_requests_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(btn_frame, text="✅ Approve", command=self.approve_leave).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Deny", command=self.deny_leave).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_leave_requests).pack(side=tk.LEFT, padx=5)
    
    def create_reports_tab(self):
        """Create the Reports tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="📊 Reports")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        
        # Report selection
        report_frame = ttk.Frame(tab)
        report_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(report_frame, text="Report Type:").pack(side=tk.LEFT, padx=(0, 10))
        self.report_type_combo = ttk.Combobox(report_frame, state='readonly', width=25,
                                             values=["Employee Hours Summary", "Wage Report", "Attendance Report"])
        self.report_type_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.report_type_combo.current(0)
        self.report_type_combo.bind('<<ComboboxSelected>>', self.on_report_type_changed)
        
        ttk.Button(report_frame, text="📈 View Report", command=self.view_employee_report).pack(side=tk.LEFT)
        
        # Employee selection (for Wage Report)
        emp_select_frame = ttk.Frame(tab)
        emp_select_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(emp_select_frame, text="Select Employee:").pack(side=tk.LEFT, padx=(0, 10))
        self.report_employee_combo = ttk.Combobox(emp_select_frame, state='readonly', width=40)
        self.report_employee_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Hide employee selector by default
        emp_select_frame.grid_remove()
        self.emp_select_frame = emp_select_frame
        
        # Report display
        self.report_text = scrolledtext.ScrolledText(tab, font=('Consolas', 9), 
                                                     bg='#34495e', fg=self.fg_color)
        self.report_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_employee_management_tab(self):
        """Create the Employee Management tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="👥 Employees")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        
        # Employee selector frame
        selector_frame = ttk.Frame(tab)
        selector_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(selector_frame, text="Select Employee:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.employee_mgmt_combo = ttk.Combobox(selector_frame, state='readonly', width=50)
        self.employee_mgmt_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Buttons frame
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Button(btn_frame, text="\u2795 Add Employee", command=self.add_employee_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="\u270f\ufe0f Edit Employee", command=self.edit_employee_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="\ud83d\udcb5 Update Rate", command=self.update_rate_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="\ud83d\uddd1\ufe0f Delete Employee", command=self.delete_employee_dialog).pack(side=tk.LEFT, padx=5)
        
        # Employee list display
        self.employee_list_text = scrolledtext.ScrolledText(tab, font=('Consolas', 9), 
                                                           bg='#34495e', fg=self.fg_color)
        self.employee_list_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_projects_tab(self):
        """Create the Projects Management tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="📁 Projects")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        
        # Buttons frame
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Button(btn_frame, text="➕ Add Project", command=self.add_project_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Project", command=self.edit_project_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Project", command=self.delete_project_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Project Report", command=self.view_project_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📝 Project Notes", command=self.manage_project_notes).pack(side=tk.LEFT, padx=5)
        
        # Projects list display
        self.project_list_text = scrolledtext.ScrolledText(tab, font=('Consolas', 9), 
                                                          bg='#34495e', fg=self.fg_color)
        self.project_list_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_invoice_tab(self):
        """Create the Invoice Management tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="💰 Invoices")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        
        # Buttons frame
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Button(btn_frame, text="📄 Generate Invoice", command=self.generate_invoice_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="👁️ View/Print Invoice", command=self.view_print_invoice_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⚡ Add Electricity Cost", command=self.add_electricity_cost_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Invoice", command=self.edit_invoice_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Invoice", command=self.delete_invoice_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_invoice_list).pack(side=tk.LEFT, padx=5)
        
        # Invoices list display
        self.invoice_list_text = scrolledtext.ScrolledText(tab, font=('Consolas', 9), 
                                                          bg='#34495e', fg=self.fg_color)
        self.invoice_list_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def update_clock(self):
        """Update the clock display"""
        now = datetime.now()
        time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%A, %B %d, %Y")
        self.clock_label.config(text=f"{date_str} | {time_str}")
        self.root.after(1000, self.update_clock)
    
    def refresh_employee_list(self):
        """Refresh the employee dropdown"""
        employees = self.data_manager.get_all_employees()
        emp_list = [f"{emp_id} - {emp['name']}" for emp_id, emp in employees.items()]
        self.employee_combo['values'] = emp_list
        
        # Also update employee management tab combobox
        if hasattr(self, 'employee_mgmt_combo'):
            self.employee_mgmt_combo['values'] = emp_list
        
        # Don't auto-select first employee on startup
        if emp_list and self.employee_combo.get():
            # Only update if there was already a selection
            current_selection = self.employee_combo.get()
            if current_selection in emp_list:
                self.on_employee_selected(None)
        
        # Also refresh employee management tab
        self.refresh_employee_list_display()
    
    def refresh_employee_list_display(self):
        """Refresh the employee list display in the Employees tab"""
        self.employee_list_text.delete('1.0', tk.END)
        
        employees = self.data_manager.get_all_employees()
        
        if not employees:
            self.employee_list_text.insert('1.0', "No employees found.\n\nClick '➕ Add Employee' to add your first employee.")
            return
        
        # Header
        self.employee_list_text.insert(tk.END, f"{'='*100}\n")
        self.employee_list_text.insert(tk.END, f"{'EMPLOYEE DIRECTORY':^100}\n")
        self.employee_list_text.insert(tk.END, f"{'='*100}\n\n")
        
        # Display each employee
        for emp_id, emp in sorted(employees.items(), key=lambda x: x[1].get('name', '')):
            self.employee_list_text.insert(tk.END, f"{'─'*100}\n")
            self.employee_list_text.insert(tk.END, f"ID: {emp_id:<15} Name: {emp.get('name', 'N/A')}\n")
            self.employee_list_text.insert(tk.END, f"{'─'*100}\n")
            
            # Basic info
            self.employee_list_text.insert(tk.END, f"Department: {emp.get('department', 'N/A'):<30} Job Title: {emp.get('job_title', 'N/A')}\n")
            self.employee_list_text.insert(tk.END, f"Type: {emp.get('employee_type', 'Full-Time'):<30} Hire Date: {emp.get('hire_date', 'N/A')}\n")
            self.employee_list_text.insert(tk.END, f"Hourly Rate: ${emp.get('hourly_rate', 0):.2f}/hr\n")
            
            # Contact info
            if emp.get('phone') or emp.get('email'):
                self.employee_list_text.insert(tk.END, f"\nContact:\n")
                if emp.get('phone'):
                    self.employee_list_text.insert(tk.END, f"  Phone: {emp['phone']}\n")
                if emp.get('email'):
                    self.employee_list_text.insert(tk.END, f"  Email: {emp['email']}\n")
            
            # Address
            address_line = emp.get('street') or emp.get('address')
            if address_line or emp.get('city') or emp.get('state') or emp.get('zip_code'):
                self.employee_list_text.insert(tk.END, f"\nAddress:\n")
                if address_line:
                    self.employee_list_text.insert(tk.END, f"  {address_line}\n")
                city_state_zip = emp.get('city', '')
                if emp.get('state'):
                    city_state_zip += f", {emp['state']}" if city_state_zip else emp['state']
                if emp.get('zip_code'):
                    city_state_zip += f" {emp['zip_code']}"
                if city_state_zip:
                    self.employee_list_text.insert(tk.END, f"  {city_state_zip}\n")
            
            # PTO Balances
            self.employee_list_text.insert(tk.END, f"\nLeave Balances:\n")
            self.employee_list_text.insert(tk.END, f"  PTO: {emp.get('pto_balance', 0):.1f} hrs  |  ")
            self.employee_list_text.insert(tk.END, f"Sick: {emp.get('sick_balance', 0):.1f} hrs  |  ")
            self.employee_list_text.insert(tk.END, f"Vacation: {emp.get('vacation_balance', 0):.1f} hrs\n")
            
            # Status
            status = "🟢 CLOCKED IN" if emp.get('clocked_in', False) else "🔴 CLOCKED OUT"
            self.employee_list_text.insert(tk.END, f"\nStatus: {status}\n\n")
        
        self.employee_list_text.insert(tk.END, f"{'='*100}\n")
        self.employee_list_text.insert(tk.END, f"Total Employees: {len(employees)}\n")
        self.employee_list_text.insert(tk.END, f"{'='*100}\n")
    
    def on_employee_selected(self, event):
        """Handle employee selection"""
        selection = self.employee_combo.get()
        if not selection:
            self.info_text.delete('1.0', tk.END)
            self.info_text.insert('1.0', "Please select an employee\nfrom the dropdown above.")
            self.entries_text.delete('1.0', tk.END)
            self.entries_text.insert('1.0', "Select an employee to view time entries.")
            return
        
        emp_id = selection.split(' - ')[0]
        employee = self.data_manager.get_employee(emp_id)
        
        if employee:
            self.info_text.delete('1.0', tk.END)
            info = f"Employee ID: {emp_id}\n"
            info += f"Name: {employee.get('name', '')}\n"
            if employee.get('first_name'):
                info += f"First: {employee['first_name']}\n"
            if employee.get('middle_name'):
                info += f"Middle: {employee['middle_name']}\n"
            if employee.get('last_name'):
                info += f"Last: {employee['last_name']}\n"
            info += f"Hourly Rate: ${employee['hourly_rate']:.2f}\n"
            if employee.get('overtime_rate'):
                info += f"Overtime Rate: ${employee['overtime_rate']:.2f}\n"
            address_line = employee.get('street') or employee.get('address')
            if address_line or employee.get('city') or employee.get('state') or employee.get('zip_code'):
                info += f"\nAddress:\n"
                if address_line:
                    info += f"{address_line}\n"
                city_state_zip = ""
                if employee.get('city'):
                    city_state_zip += employee['city']
                if employee.get('state'):
                    city_state_zip += f", {employee['state']}"
                if employee.get('zip_code'):
                    city_state_zip += f" {employee['zip_code']}"
                if city_state_zip:
                    info += f"{city_state_zip}\n"
            if employee.get('phone'):
                info += f"Phone: {employee['phone']}\n"
            if employee.get('email'):
                info += f"Email: {employee['email']}\n"
            info += f"\nStatus: {'🟢 CLOCKED IN' if employee['clocked_in'] else '🔴 CLOCKED OUT'}\n"
            
            if employee['clocked_in']:
                entry = self.data_manager.data["time_entries"][employee["current_entry"]]
                clock_in_dt = datetime.fromisoformat(entry["clock_in"])
                info += f"\nClocked in at:\n{clock_in_dt.strftime('%I:%M:%S %p')}\n"
                info += f"{clock_in_dt.strftime('%B %d, %Y')}"
            
            self.info_text.insert('1.0', info)
        
        self.refresh_time_entries()
    
    def refresh_time_entries(self):
        """Refresh the time entries display"""
        selection = self.employee_combo.get()
        if not selection:
            return
        
        emp_id = selection.split(' - ')[0]
        entries = self.data_manager.get_time_entries(emp_id)
        
        self.entries_text.delete('1.0', tk.END)
        
        if not entries:
            self.entries_text.insert('1.0', "No time entries found.")
            return
        
        for i, entry in enumerate(reversed(entries[-10:]), 1):  # Show last 10 entries
            self.entries_text.insert(tk.END, f"{'='*60}\n")
            self.entries_text.insert(tk.END, f"Entry #{len(entries) - i + 1}\n")
            self.entries_text.insert(tk.END, f"{'='*60}\n")
            
            clock_in_dt = datetime.fromisoformat(entry["clock_in"])
            self.entries_text.insert(tk.END, f"Clock In:  {clock_in_dt.strftime('%Y-%m-%d %I:%M:%S %p')}\n")
            
            # Display project if available
            if entry.get("project"):
                self.entries_text.insert(tk.END, f"Project:   {entry['project']}\n")
            
            if entry["clock_out"]:
                clock_out_dt = datetime.fromisoformat(entry["clock_out"])
                self.entries_text.insert(tk.END, f"Clock Out: {clock_out_dt.strftime('%Y-%m-%d %I:%M:%S %p')}\n")
                self.entries_text.insert(tk.END, f"Hours:     {entry['hours_worked']:.2f} hrs\n")
                self.entries_text.insert(tk.END, f"Rate:      ${entry['hourly_rate']:.2f}/hr\n")
                self.entries_text.insert(tk.END, f"Wages:     ${entry['wages']:.2f}\n")
            else:
                self.entries_text.insert(tk.END, "Clock Out: Still clocked in\n")
            
            self.entries_text.insert(tk.END, "\n")
    
    def clock_in(self):
        """Clock in selected employee"""
        selection = self.employee_combo.get()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        project = self.project_combo.get()
        if not project:
            messagebox.showwarning("No Selection", "Please select a project first.")
            return
        
        emp_id = selection.split(' - ')[0]
        success, message = self.data_manager.clock_in(emp_id, project)
        
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_all()
        else:
            messagebox.showerror("Error", message)
    
    def clock_out(self):
        """Clock out selected employee"""
        selection = self.employee_combo.get()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        emp_id = selection.split(' - ')[0]
        success, message = self.data_manager.clock_out(emp_id)
        
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_all()
        else:
            messagebox.showerror("Error", message)
    
    def add_employee_dialog(self):
        """Open dialog to add new employee"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Employee")
        
        # Calculate center position
        window_width = 550
        window_height = 900
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Employee ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        id_entry = ttk.Entry(frame, width=30)
        id_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="First Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        first_name_entry = ttk.Entry(frame, width=30)
        first_name_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Middle Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        middle_name_entry = ttk.Entry(frame, width=30)
        middle_name_entry.grid(row=2, column=1, pady=5)
        
        ttk.Label(frame, text="Last Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        last_name_entry = ttk.Entry(frame, width=30)
        last_name_entry.grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Street Address:").grid(row=4, column=0, sticky=tk.W, pady=5)
        street_entry = ttk.Entry(frame, width=30)
        street_entry.grid(row=4, column=1, pady=5)
        
        ttk.Label(frame, text="City:").grid(row=5, column=0, sticky=tk.W, pady=5)
        city_entry = ttk.Entry(frame, width=30)
        city_entry.grid(row=5, column=1, pady=5)
        
        ttk.Label(frame, text="State:").grid(row=6, column=0, sticky=tk.W, pady=5)
        state_entry = ttk.Entry(frame, width=30)
        state_entry.grid(row=6, column=1, pady=5)
        
        ttk.Label(frame, text="Zip Code:").grid(row=7, column=0, sticky=tk.W, pady=5)
        zip_entry = ttk.Entry(frame, width=30)
        zip_entry.grid(row=7, column=1, pady=5)
        
        ttk.Label(frame, text="Phone:").grid(row=8, column=0, sticky=tk.W, pady=5)
        phone_entry = ttk.Entry(frame, width=30)
        phone_entry.grid(row=8, column=1, pady=5)
        
        ttk.Label(frame, text="Email:").grid(row=9, column=0, sticky=tk.W, pady=5)
        email_entry = ttk.Entry(frame, width=30)
        email_entry.grid(row=9, column=1, pady=5)
        
        ttk.Label(frame, text="Hourly Rate ($):").grid(row=10, column=0, sticky=tk.W, pady=5)
        rate_entry = ttk.Entry(frame, width=30)
        rate_entry.grid(row=10, column=1, pady=5)
        
        ttk.Label(frame, text="Overtime Rate ($):").grid(row=11, column=0, sticky=tk.W, pady=5)
        overtime_entry = ttk.Entry(frame, width=30)
        overtime_entry.grid(row=11, column=1, pady=5)
        
        ttk.Label(frame, text="Department:").grid(row=12, column=0, sticky=tk.W, pady=5)
        department_combo = ttk.Combobox(frame, width=28, state='readonly')
        department_combo.grid(row=12, column=1, pady=5)
        departments = self.data_manager.data.get("departments", ["Administration", "Operations", "Sales", "IT", "HR"])
        department_combo['values'] = departments
        if departments:
            department_combo.current(0)
        
        ttk.Label(frame, text="Job Title:").grid(row=13, column=0, sticky=tk.W, pady=5)
        job_title_entry = ttk.Entry(frame, width=30)
        job_title_entry.grid(row=13, column=1, pady=5)
        
        ttk.Label(frame, text="Employee Type:").grid(row=14, column=0, sticky=tk.W, pady=5)
        emp_type_combo = ttk.Combobox(frame, width=28, state='readonly', values=["Full-Time", "Part-Time", "Contract", "Temporary"])
        emp_type_combo.grid(row=14, column=1, pady=5)
        emp_type_combo.current(0)
        
        ttk.Label(frame, text="Hire Date:").grid(row=15, column=0, sticky=tk.W, pady=5)
        hire_date_picker = DateEntry(frame, width=27, background='darkblue', foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy', firstweekday='sunday')
        hire_date_picker.grid(row=15, column=1, pady=5)
        
        def save_employee():
            try:
                emp_id = id_entry.get().strip()
                first_name = first_name_entry.get().strip()
                middle_name = middle_name_entry.get().strip()
                last_name = last_name_entry.get().strip()
                email = email_entry.get().strip()
                street = street_entry.get().strip()
                city = city_entry.get().strip()
                state = state_entry.get().strip()
                zip_code = zip_entry.get().strip()
                phone = phone_entry.get().strip()
                rate = float(rate_entry.get().strip())
                overtime = float(overtime_entry.get().strip()) if overtime_entry.get().strip() else 0.0
                department = department_combo.get()
                job_title = job_title_entry.get().strip()
                emp_type = emp_type_combo.get()
                hire_date = hire_date_picker.get_date().strftime('%m/%d/%Y')
                
                if not emp_id or not first_name or not last_name:
                    messagebox.showerror("Error", "Please fill in Employee ID, First Name, and Last Name.")
                    return
                
                success, message = self.data_manager.add_employee(emp_id, first_name, middle_name, last_name, rate, overtime, street, city, state, zip_code, phone, email, department, job_title, emp_type, hire_date)
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
            except ValueError:
                messagebox.showerror("Error", "Invalid hourly rate or overtime rate!")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=17, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Save", command=save_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Add close button at top right
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=510, y=10)
    
    def edit_employee_dialog(self):
        """Open dialog to edit an employee"""
        # Try to get selection from Time Clock tab first, then Employees tab
        selection = self.employee_combo.get()
        if not selection and hasattr(self, 'employee_mgmt_combo'):
            selection = self.employee_mgmt_combo.get()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        emp_id = selection.split(' - ')[0]
        employee = self.data_manager.get_employee(emp_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Employee")
        
        # Calculate center position
        window_width = 550
        window_height = 950
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"Edit Employee: {emp_id}", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        ttk.Label(frame, text="Employee ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        id_label = ttk.Label(frame, text=emp_id, foreground=self.accent_color)
        id_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="First Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        first_name_entry = ttk.Entry(frame, width=30)
        first_name_entry.grid(row=2, column=1, pady=5)
        first_name_entry.insert(0, employee.get('first_name', ''))
        
        ttk.Label(frame, text="Middle Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        middle_name_entry = ttk.Entry(frame, width=30)
        middle_name_entry.grid(row=3, column=1, pady=5)
        middle_name_entry.insert(0, employee.get('middle_name', ''))
        
        ttk.Label(frame, text="Last Name:").grid(row=4, column=0, sticky=tk.W, pady=5)
        last_name_entry = ttk.Entry(frame, width=30)
        last_name_entry.grid(row=4, column=1, pady=5)
        last_name_entry.insert(0, employee.get('last_name', ''))
        
        ttk.Label(frame, text="Street Address:").grid(row=5, column=0, sticky=tk.W, pady=5)
        street_entry = ttk.Entry(frame, width=30)
        street_entry.grid(row=5, column=1, pady=5)
        street_entry.insert(0, employee.get('street', ''))
        
        ttk.Label(frame, text="City:").grid(row=6, column=0, sticky=tk.W, pady=5)
        city_entry = ttk.Entry(frame, width=30)
        city_entry.grid(row=6, column=1, pady=5)
        city_entry.insert(0, employee.get('city', ''))
        
        ttk.Label(frame, text="State:").grid(row=7, column=0, sticky=tk.W, pady=5)
        state_entry = ttk.Entry(frame, width=30)
        state_entry.grid(row=7, column=1, pady=5)
        state_entry.insert(0, employee.get('state', ''))
        
        ttk.Label(frame, text="Zip Code:").grid(row=8, column=0, sticky=tk.W, pady=5)
        zip_entry = ttk.Entry(frame, width=30)
        zip_entry.grid(row=8, column=1, pady=5)
        zip_entry.insert(0, employee.get('zip_code', ''))
        
        ttk.Label(frame, text="Phone:").grid(row=9, column=0, sticky=tk.W, pady=5)
        phone_entry = ttk.Entry(frame, width=30)
        phone_entry.grid(row=9, column=1, pady=5)
        phone_entry.insert(0, employee.get('phone', ''))
        
        ttk.Label(frame, text="Email:").grid(row=10, column=0, sticky=tk.W, pady=5)
        email_entry = ttk.Entry(frame, width=30)
        email_entry.grid(row=10, column=1, pady=5)
        email_entry.insert(0, employee.get('email', ''))
        
        ttk.Label(frame, text="Hourly Rate ($):").grid(row=11, column=0, sticky=tk.W, pady=5)
        rate_entry = ttk.Entry(frame, width=30)
        rate_entry.grid(row=11, column=1, pady=5)
        rate_entry.insert(0, str(employee['hourly_rate']))
        
        ttk.Label(frame, text="Overtime Rate ($):").grid(row=12, column=0, sticky=tk.W, pady=5)
        overtime_entry = ttk.Entry(frame, width=30)
        overtime_entry.grid(row=12, column=1, pady=5)
        overtime_entry.insert(0, str(employee.get('overtime_rate', 0.0)))
        
        ttk.Label(frame, text="Department:").grid(row=13, column=0, sticky=tk.W, pady=5)
        department_combo = ttk.Combobox(frame, width=28, state='readonly')
        department_combo.grid(row=13, column=1, pady=5)
        departments = self.data_manager.data.get("departments", ["Administration", "Operations", "Sales", "IT", "HR"])
        department_combo['values'] = departments
        current_dept = employee.get('department', '')
        if current_dept and current_dept in departments:
            department_combo.set(current_dept)
        elif departments:
            department_combo.current(0)
        
        ttk.Label(frame, text="Job Title:").grid(row=14, column=0, sticky=tk.W, pady=5)
        job_title_entry = ttk.Entry(frame, width=30)
        job_title_entry.grid(row=14, column=1, pady=5)
        job_title_entry.insert(0, employee.get('job_title', ''))
        
        ttk.Label(frame, text="Employee Type:").grid(row=15, column=0, sticky=tk.W, pady=5)
        emp_type_combo = ttk.Combobox(frame, width=28, state='readonly', values=["Full-Time", "Part-Time", "Contract", "Temporary"])
        emp_type_combo.grid(row=15, column=1, pady=5)
        current_type = employee.get('employee_type', 'Full-Time')
        if current_type in ["Full-Time", "Part-Time", "Contract", "Temporary"]:
            emp_type_combo.set(current_type)
        else:
            emp_type_combo.current(0)
        
        ttk.Label(frame, text="Hire Date:").grid(row=16, column=0, sticky=tk.W, pady=5)
        hire_date_picker = DateEntry(frame, width=27, background='darkblue', foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy', firstweekday='sunday')
        hire_date_picker.grid(row=16, column=1, pady=5)
        # Set current hire date if exists
        if employee.get('hire_date'):
            try:
                hire_date_obj = datetime.strptime(employee['hire_date'], '%m/%d/%Y')
                hire_date_picker.set_date(hire_date_obj)
            except:
                pass
        
        def save_changes():
            try:
                first_name = first_name_entry.get().strip()
                middle_name = middle_name_entry.get().strip()
                last_name = last_name_entry.get().strip()
                email = email_entry.get().strip()
                street = street_entry.get().strip()
                city = city_entry.get().strip()
                state = state_entry.get().strip()
                zip_code = zip_entry.get().strip()
                phone = phone_entry.get().strip()
                new_rate = float(rate_entry.get().strip())
                overtime = float(overtime_entry.get().strip()) if overtime_entry.get().strip() else 0.0
                department = department_combo.get()
                job_title = job_title_entry.get().strip()
                emp_type = emp_type_combo.get()
                hire_date = hire_date_picker.get_date().strftime('%m/%d/%Y')
                
                if not first_name or not last_name:
                    messagebox.showerror("Error", "First Name and Last Name cannot be empty.")
                    return
                
                success, message = self.data_manager.edit_employee(emp_id, first_name, middle_name, last_name, new_rate, overtime, street, city, state, zip_code, phone, email, department, job_title, emp_type, hire_date)
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
            except ValueError:
                messagebox.showerror("Error", "Invalid hourly rate or overtime rate!")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=18, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Add close button at top right
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=510, y=10)
    
    def delete_employee_dialog(self):
        """Open dialog to delete an employee"""
        # Try to get selection from Time Clock tab first, then Employees tab
        selection = self.employee_combo.get()
        if not selection and hasattr(self, 'employee_mgmt_combo'):
            selection = self.employee_mgmt_combo.get()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        emp_id = selection.split(' - ')[0]
        employee = self.data_manager.get_employee(emp_id)
        
        # Check if employee has time entries
        entries = self.data_manager.get_time_entries(emp_id)
        has_entries = len(entries) > 0
        
        if has_entries:
            # Ask what to do with time entries
            dialog = tk.Toplevel(self.root)
            dialog.title("Delete Employee")
            
            # Calculate center position
            window_width = 500
            window_height = 300
            screen_width = dialog.winfo_screenwidth()
            screen_height = dialog.winfo_screenheight()
            center_x = int(screen_width/2 - window_width/2)
            center_y = int(screen_height/2 - window_height/2)
            
            dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
            dialog.configure(bg=self.bg_color)
            dialog.transient(self.root)
            dialog.grab_set()
            
            frame = ttk.Frame(dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text=f"Delete Employee: {employee['name']}", style='Header.TLabel').pack(pady=(0, 10))
            
            message = f"This employee has {len(entries)} time entry/entries.\n\n"
            message += "What would you like to do?"
            
            msg_label = ttk.Label(frame, text=message, justify=tk.CENTER)
            msg_label.pack(pady=20)
            
            def delete_keep_entries():
                success, msg = self.data_manager.delete_employee(emp_id)
                if success:
                    messagebox.showinfo("Success", msg + "\nTime entries have been kept.")
                    dialog.destroy()
                    self.employee_combo.set('')
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", msg)
            
            def delete_with_entries():
                confirm_msg = f"Are you sure you want to delete {employee['name']} and ALL their time entries?\n\nThis cannot be undone!"
                if messagebox.askyesno("Confirm Delete", confirm_msg):
                    success, msg = self.data_manager.delete_employee_with_entries(emp_id)
                    if success:
                        messagebox.showinfo("Success", msg)
                        dialog.destroy()
                        self.employee_combo.set('')
                        self.refresh_all()
                    else:
                        messagebox.showerror("Error", msg)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(pady=(20, 0))
            
            ttk.Button(btn_frame, text="Delete Employee Only\n(Keep Time Entries)", 
                      command=delete_keep_entries).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Delete Employee\n& All Time Entries", 
                      command=delete_with_entries).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Add close button at top right
            close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                                 bg=self.danger_color, fg='white', relief=tk.FLAT,
                                 command=dialog.destroy, cursor='hand2', width=3)
            close_btn.place(x=410, y=10)
        else:
            # No entries, just confirm deletion
            confirm_msg = f"Are you sure you want to delete {employee['name']}?\n\nThis employee has no time entries."
            if messagebox.askyesno("Confirm Delete", confirm_msg):
                success, msg = self.data_manager.delete_employee(emp_id)
                if success:
                    messagebox.showinfo("Success", msg)
                    self.employee_combo.set('')
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", msg)
    
    def update_rate_dialog(self):
        """Open dialog to update hourly rate"""
        # Try to get selection from Time Clock tab first, then Employees tab
        selection = self.employee_combo.get()
        if not selection and hasattr(self, 'employee_mgmt_combo'):
            selection = self.employee_mgmt_combo.get()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        emp_id = selection.split(' - ')[0]
        employee = self.data_manager.get_employee(emp_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Hourly Rate")
        
        # Calculate center position
        window_width = 500
        window_height = 320
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"Employee: {employee['name']}", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text=f"Current Hourly Rate: ${employee['hourly_rate']:.2f}").grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Label(frame, text=f"Current Overtime Rate: ${employee.get('overtime_rate', 0.0):.2f}").grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Label(frame, text="New Hourly Rate ($):").grid(row=3, column=0, sticky=tk.W, pady=5)
        rate_entry = ttk.Entry(frame, width=20)
        rate_entry.grid(row=3, column=1, pady=5)
        rate_entry.insert(0, str(employee['hourly_rate']))
        
        ttk.Label(frame, text="New Overtime Rate ($):").grid(row=4, column=0, sticky=tk.W, pady=5)
        overtime_entry = ttk.Entry(frame, width=20)
        overtime_entry.grid(row=4, column=1, pady=5)
        overtime_entry.insert(0, str(employee.get('overtime_rate', 0.0)))
        
        def save_rate():
            try:
                new_rate = float(rate_entry.get().strip())
                new_overtime = float(overtime_entry.get().strip()) if overtime_entry.get().strip() else 0.0
                
                # Update both rates
                employee['hourly_rate'] = new_rate
                employee['overtime_rate'] = new_overtime
                self.data_manager.save_data()
                
                message = f"Rates updated successfully!\nHourly Rate: ${new_rate:.2f}\nOvertime Rate: ${new_overtime:.2f}"
                messagebox.showinfo("Success", message)
                dialog.destroy()
                self.refresh_all()
            except ValueError:
                messagebox.showerror("Error", "Invalid hourly rate or overtime rate!")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Save", command=save_rate).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Add close button at top right
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=460, y=10)
    
    def log_past_hours_dialog(self):
        """Open dialog to log past hours worked"""
        selection = self.employee_combo.get()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        emp_id = selection.split(' - ')[0]
        employee = self.data_manager.get_employee(emp_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Log Past Hours")
        
        # Calculate center position
        window_width = 550
        window_height = 500
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"Employee: {employee['name']}", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 10))
        ttk.Label(frame, text=f"Current Rate: ${employee['hourly_rate']:.2f}/hr").grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Date selection
        ttk.Label(frame, text="Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
        date_picker = DateEntry(frame, width=18, date_pattern='mm/dd/yyyy', firstweekday='sunday')
        date_picker.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Project selection
        ttk.Label(frame, text="Project:").grid(row=3, column=0, sticky=tk.W, pady=5)
        project_combo = ttk.Combobox(frame, state='readonly', width=20)
        project_combo['values'] = self.data_manager.data.get("projects", ["General"])
        if project_combo['values']:
            project_combo.current(0)
        project_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Clock In Time
        ttk.Label(frame, text="Clock In Time:").grid(row=4, column=0, sticky=tk.W, pady=5)
        clock_in_frame = ttk.Frame(frame)
        clock_in_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        in_hour_var = tk.StringVar(value="9")
        in_minute_var = tk.StringVar(value="00")
        in_ampm_var = tk.StringVar(value="AM")
        
        hours = [str(h) for h in range(1, 13)]
        minutes = [f"{m:02d}" for m in range(0, 60)]
        
        ttk.Combobox(clock_in_frame, textvariable=in_hour_var, values=hours, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        ttk.Label(clock_in_frame, text=":").pack(side=tk.LEFT)
        ttk.Combobox(clock_in_frame, textvariable=in_minute_var, values=minutes, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        ttk.Combobox(clock_in_frame, textvariable=in_ampm_var, values=["AM", "PM"], width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        
        # Clock Out Time
        ttk.Label(frame, text="Clock Out Time:").grid(row=5, column=0, sticky=tk.W, pady=5)
        clock_out_frame = ttk.Frame(frame)
        clock_out_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        out_hour_var = tk.StringVar(value="5")
        out_minute_var = tk.StringVar(value="00")
        out_ampm_var = tk.StringVar(value="PM")
        
        ttk.Combobox(clock_out_frame, textvariable=out_hour_var, values=hours, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        ttk.Label(clock_out_frame, text=":").pack(side=tk.LEFT)
        ttk.Combobox(clock_out_frame, textvariable=out_minute_var, values=minutes, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        ttk.Combobox(clock_out_frame, textvariable=out_ampm_var, values=["AM", "PM"], width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        
        # Preview
        preview_label = ttk.Label(frame, text="", foreground=self.accent_color, wraplength=350)
        preview_label.grid(row=6, column=0, columnspan=2, pady=15)
        
        def update_preview(*args):
            try:
                selected_date = date_picker.get_date()
                year = selected_date.year
                month = selected_date.month
                day = selected_date.day
                
                in_hour = int(in_hour_var.get())
                in_minute = int(in_minute_var.get())
                if in_ampm_var.get() == "PM" and in_hour != 12:
                    in_hour += 12
                elif in_ampm_var.get() == "AM" and in_hour == 12:
                    in_hour = 0
                
                out_hour = int(out_hour_var.get())
                out_minute = int(out_minute_var.get())
                if out_ampm_var.get() == "PM" and out_hour != 12:
                    out_hour += 12
                elif out_ampm_var.get() == "AM" and out_hour == 12:
                    out_hour = 0
                
                clock_in = datetime(year, month, day, in_hour, in_minute)
                clock_out = datetime(year, month, day, out_hour, out_minute)
                
                # Handle overnight shifts
                if clock_out <= clock_in:
                    clock_out = datetime(year, month, day + 1, out_hour, out_minute)
                
                hours = (clock_out - clock_in).total_seconds() / 3600
                wages = hours * employee['hourly_rate']
                
                preview_text = f"Hours: {hours:.2f} | Wages: ${wages:.2f}"
                preview_label.config(text=preview_text)
            except:
                preview_label.config(text="")
        
        # Bind all variables to update preview
        for var in [in_hour_var, in_minute_var, in_ampm_var, 
                    out_hour_var, out_minute_var, out_ampm_var]:
            var.trace('w', update_preview)
        
        update_preview()
        
        def save_entry():
            try:
                selected_date = date_picker.get_date()
                year = selected_date.year
                month = selected_date.month
                day = selected_date.day
                
                in_hour = int(in_hour_var.get())
                in_minute = int(in_minute_var.get())
                if in_ampm_var.get() == "PM" and in_hour != 12:
                    in_hour += 12
                elif in_ampm_var.get() == "AM" and in_hour == 12:
                    in_hour = 0
                
                out_hour = int(out_hour_var.get())
                out_minute = int(out_minute_var.get())
                if out_ampm_var.get() == "PM" and out_hour != 12:
                    out_hour += 12
                elif out_ampm_var.get() == "AM" and out_hour == 12:
                    out_hour = 0
                
                clock_in = datetime(year, month, day, in_hour, in_minute)
                clock_out = datetime(year, month, day, out_hour, out_minute)
                
                # Handle overnight shifts
                if clock_out <= clock_in:
                    clock_out = datetime(year, month, day + 1, out_hour, out_minute)
                
                project = project_combo.get()
                if not project:
                    messagebox.showerror("Error", "Please select a project.")
                    return
                
                success, message = self.data_manager.add_manual_entry(emp_id, clock_in, clock_out, project)
                
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid date or time: {str(e)}")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Save Entry", command=save_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Add close button at top right
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=510, y=10)
    
    def edit_entry_dialog(self):
        """Open dialog to edit a time entry"""
        all_entries = [
            (i, e)
            for i, e in enumerate(self.data_manager.data["time_entries"])
        ]
        
        if not all_entries:
            messagebox.showinfo("No Entries", "No time entries to edit.")
            return
        
        # Entry selection dialog
        select_dialog = tk.Toplevel(self.root)
        select_dialog.title("Select Entry to Edit")
        
        # Calculate center position
        window_width = 650
        window_height = 450
        screen_width = select_dialog.winfo_screenwidth()
        screen_height = select_dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        select_dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        select_dialog.configure(bg=self.bg_color)
        select_dialog.transient(self.root)
        select_dialog.grab_set()
        
        frame = ttk.Frame(select_dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Entry to Edit", style='Header.TLabel').pack(pady=(0, 10))
        ttk.Label(frame, text="Active shifts are shown by default.").pack(pady=(0, 10))

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(filter_frame, text="Show:").pack(side=tk.LEFT, padx=(0, 8))
        status_filter_var = ttk.Combobox(filter_frame, state='readonly', width=12, values=["Active", "Closed", "All"])
        status_filter_var.set("Active")
        status_filter_var.pack(side=tk.LEFT)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color,
                            selectmode=tk.SINGLE, yscrollcommand=scrollbar.set, height=15)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        filtered_entries = []

        def get_entry_status(entry):
            return "Active" if entry.get("clock_out") is None else "Closed"

        def refresh_entries(*_):
            nonlocal filtered_entries
            listbox.delete(0, tk.END)
            filtered_entries = []
            selected_filter = status_filter_var.get()

            for global_idx, entry in all_entries:
                status = get_entry_status(entry)
                if selected_filter != "All" and status != selected_filter:
                    continue

                clock_in = datetime.fromisoformat(entry["clock_in"]).strftime('%m/%d/%Y %I:%M %p')
                if entry.get("clock_out"):
                    clock_out = datetime.fromisoformat(entry["clock_out"]).strftime('%m/%d/%Y %I:%M %p')
                else:
                    clock_out = "---"

                display = f"{entry['name']} | {clock_in} - {clock_out} | {entry['hours_worked']:.2f}h | ${entry['wages']:.2f} | {status}"
                listbox.insert(tk.END, display)
                filtered_entries.append((global_idx, entry))

            if not filtered_entries:
                listbox.insert(tk.END, "No entries match the selected filter.")

        status_filter_var.bind('<<ComboboxSelected>>', refresh_entries)
        refresh_entries()
        
        def edit_selected():
            if not filtered_entries:
                messagebox.showinfo("No Entries", "No time entries match the selected filter.")
                return

            if not listbox.curselection():
                messagebox.showwarning("No Selection", "Please select an entry to edit.")
                return
            
            selected_idx = listbox.curselection()[0]
            global_idx, entry = filtered_entries[selected_idx]
            select_dialog.destroy()
            self.show_edit_entry_form(global_idx, entry)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))
        
        ttk.Button(btn_frame, text="Edit Selected", command=edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=select_dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Add close button at top right
        close_btn = tk.Button(select_dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=select_dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=610, y=10)
    
    def show_edit_entry_form(self, entry_index, entry):
        """Show form to edit the selected entry"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Time Entry")
        
        # Calculate center position
        window_width = 760
        window_height = 760
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"Edit Entry - {entry['name']}", style='Header.TLabel').grid(row=0, column=0, columnspan=3, pady=(0, 10))
        ttk.Label(frame, text=f"Rate: ${entry['hourly_rate']:.2f}/hr").grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Parse existing times
        clock_in_dt = datetime.fromisoformat(entry["clock_in"])
        clock_out_dt = datetime.fromisoformat(entry["clock_out"]) if entry.get("clock_out") else datetime.now()
        entry_is_open = entry.get("clock_out") is None
        
        clock_out_active_var = tk.BooleanVar(value=not entry_is_open)
        
        # Project selection
        ttk.Label(frame, text="Project:").grid(row=2, column=0, sticky=tk.W, pady=5)
        projects = self.data_manager.data.get("projects", [])
        project_var = ttk.Combobox(frame, values=projects, state='readonly', font=('Segoe UI', 10))
        project_var.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))
        
        # Set current project if exists
        current_project = entry.get('project', '')
        if current_project and current_project in projects:
            project_var.set(current_project)
        elif projects:
            project_var.current(0)
        
        # Date selection
        ttk.Label(frame, text="Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
        date_frame = ttk.Frame(frame)
        date_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        year_var = tk.StringVar(value=str(clock_in_dt.year))
        month_var = tk.StringVar(value=str(clock_in_dt.month))
        day_var = tk.StringVar(value=str(clock_in_dt.day))
        
        current_date = datetime.now()
        years = [str(y) for y in range(current_date.year - 5, current_date.year + 1)]
        months = [str(m) for m in range(1, 13)]
        days = [str(d) for d in range(1, 32)]
        
        ttk.Label(date_frame, text="Month:").pack(side=tk.LEFT)
        month_combo = ttk.Combobox(date_frame, textvariable=month_var, values=months, width=4, state='readonly')
        month_combo.pack(side=tk.LEFT, padx=(2, 5))
        
        ttk.Label(date_frame, text="Day:").pack(side=tk.LEFT)
        day_combo = ttk.Combobox(date_frame, textvariable=day_var, values=days, width=4, state='readonly')
        day_combo.pack(side=tk.LEFT, padx=(2, 5))
        
        ttk.Label(date_frame, text="Year:").pack(side=tk.LEFT)
        year_combo = ttk.Combobox(date_frame, textvariable=year_var, values=years, width=6, state='readonly')
        year_combo.pack(side=tk.LEFT, padx=2)
        
        # Day of week display (moved to the right in column 2)
        day_of_week_label = ttk.Label(frame, text="", foreground=self.accent_color, font=('Segoe UI', 10, 'bold'))
        day_of_week_label.grid(row=3, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        
        def update_day_of_week(*args):
            try:
                year = int(year_var.get())
                month = int(month_var.get())
                day = int(day_var.get())
                date_obj = datetime(year, month, day)
                day_name = date_obj.strftime('%A')
                day_of_week_label.config(text=day_name)
            except:
                day_of_week_label.config(text="")
        
        # Bind date changes to update day of week
        year_var.trace('w', update_day_of_week)
        month_var.trace('w', update_day_of_week)
        day_var.trace('w', update_day_of_week)
        update_day_of_week()
        
        # Clock In Time
        ttk.Label(frame, text="Clock In Time:").grid(row=4, column=0, sticky=tk.W, pady=5)
        clock_in_frame = ttk.Frame(frame)
        clock_in_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        in_hour = clock_in_dt.hour
        in_ampm = "AM"
        if in_hour >= 12:
            in_ampm = "PM"
            if in_hour > 12:
                in_hour -= 12
        elif in_hour == 0:
            in_hour = 12
        
        in_hour_var = tk.StringVar(value=str(in_hour))
        in_minute_var = tk.StringVar(value=f"{clock_in_dt.minute:02d}")
        in_ampm_var = tk.StringVar(value=in_ampm)
        
        hours = [str(h) for h in range(1, 13)]
        minutes = [f"{m:02d}" for m in range(0, 60)]
        
        ttk.Combobox(clock_in_frame, textvariable=in_hour_var, values=hours, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        ttk.Label(clock_in_frame, text=":").pack(side=tk.LEFT)
        ttk.Combobox(clock_in_frame, textvariable=in_minute_var, values=minutes, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        ttk.Combobox(clock_in_frame, textvariable=in_ampm_var, values=["AM", "PM"], width=4, state='readonly').pack(side=tk.LEFT, padx=2)
        
        # Clock Out Time
        ttk.Label(frame, text="Clock Out Time:").grid(row=5, column=0, sticky=tk.W, pady=5)
        clock_out_frame = ttk.Frame(frame)
        clock_out_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        clock_out_frame.columnconfigure(0, weight=1)
        clock_out_frame.columnconfigure(1, weight=1)
        clock_out_frame.columnconfigure(2, weight=1)
        clock_out_widgets = []

        active_check = ttk.Checkbutton(
            frame,
            text="Entry is still open",
            variable=clock_out_active_var
        )
        active_check.grid(row=5, column=2, sticky=tk.W, padx=(10, 0))
        
        out_hour = clock_out_dt.hour
        out_ampm = "AM"
        if out_hour >= 12:
            out_ampm = "PM"
            if out_hour > 12:
                out_hour -= 12
        elif out_hour == 0:
            out_hour = 12
        
        out_hour_var = tk.StringVar(value=str(out_hour))
        out_minute_var = tk.StringVar(value=f"{clock_out_dt.minute:02d}")
        out_ampm_var = tk.StringVar(value=out_ampm)
        
        out_hour_combo = ttk.Combobox(clock_out_frame, textvariable=out_hour_var, values=hours, width=4, state='readonly')
        out_hour_combo.pack(side=tk.LEFT, padx=2)
        clock_out_widgets.append(out_hour_combo)
        out_colon = ttk.Label(clock_out_frame, text=":")
        out_colon.pack(side=tk.LEFT)
        clock_out_widgets.append(out_colon)
        out_minute_combo = ttk.Combobox(clock_out_frame, textvariable=out_minute_var, values=minutes, width=4, state='readonly')
        out_minute_combo.pack(side=tk.LEFT, padx=2)
        clock_out_widgets.append(out_minute_combo)
        out_ampm_combo = ttk.Combobox(clock_out_frame, textvariable=out_ampm_var, values=["AM", "PM"], width=4, state='readonly')
        out_ampm_combo.pack(side=tk.LEFT, padx=2)
        clock_out_widgets.append(out_ampm_combo)

        def set_clock_out_state(*_):
            if clock_out_active_var.get():
                for widget in clock_out_widgets:
                    try:
                        widget.configure(state='readonly')
                    except tk.TclError:
                        widget.configure(state='normal')
            else:
                for widget in clock_out_widgets:
                    try:
                        widget.configure(state='disabled')
                    except tk.TclError:
                        pass

        clock_out_active_var.trace_add('write', set_clock_out_state)
        set_clock_out_state()
        
        # Break management
        ttk.Label(frame, text="Breaks:").grid(row=6, column=0, sticky=tk.NW, pady=5)
        breaks_frame = ttk.Frame(frame)
        breaks_frame.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        breaks_frame.columnconfigure(0, weight=1)
        breaks_frame.rowconfigure(0, weight=1)

        breaks_listbox = tk.Listbox(breaks_frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color, selectmode=tk.SINGLE, height=8)
        breaks_scrollbar = ttk.Scrollbar(breaks_frame, orient=tk.VERTICAL, command=breaks_listbox.yview)
        breaks_listbox.configure(yscrollcommand=breaks_scrollbar.set)
        breaks_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        breaks_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        break_records = []
        for break_entry in entry.get("breaks", []):
            normalized_break = self.data_manager.normalize_break_record(break_entry)
            if normalized_break:
                break_records.append(normalized_break)

        def refresh_breaks_list():
            breaks_listbox.delete(0, tk.END)
            for break_entry in break_records:
                break_start = datetime.fromisoformat(break_entry["start_time"])
                break_end = datetime.fromisoformat(break_entry["end_time"])
                breaks_listbox.insert(
                    tk.END,
                    f"{break_entry['break_type']} | {break_start.strftime('%m/%d/%Y %I:%M %p')} - {break_end.strftime('%I:%M %p')} | {break_entry['duration']:.2f}h"
                )

        def open_break_editor(selected_break_index=None):
            break_dialog = tk.Toplevel(dialog)
            break_dialog.title("Edit Break" if selected_break_index is not None else "Add Break")
            break_dialog.geometry("460x320")
            break_dialog.configure(bg=self.bg_color)
            break_dialog.transient(dialog)
            break_dialog.grab_set()

            break_frame = ttk.Frame(break_dialog, padding="20")
            break_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(break_frame, text="Break Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
            selected_break = break_records[selected_break_index] if selected_break_index is not None else None
            break_type_var = tk.StringVar(value=(selected_break or {}).get("break_type", "Unpaid"))
            ttk.Combobox(break_frame, textvariable=break_type_var, values=["Paid", "Unpaid"], state='readonly', width=20).grid(row=0, column=1, sticky=tk.W, pady=5)

            start_dt = datetime.fromisoformat(selected_break["start_time"]) if selected_break else clock_in_dt
            end_dt = datetime.fromisoformat(selected_break["end_time"]) if selected_break else (start_dt + timedelta(minutes=15))

            ttk.Label(break_frame, text="Start Date:").grid(row=1, column=0, sticky=tk.W, pady=5)
            break_start_date = DateEntry(break_frame, width=18, date_pattern='mm/dd/yyyy', firstweekday='sunday')
            break_start_date.grid(row=1, column=1, sticky=tk.W, pady=5)
            break_start_date.set_date(start_dt)

            ttk.Label(break_frame, text="Start Time:").grid(row=2, column=0, sticky=tk.W, pady=5)
            break_start_hour = tk.StringVar(value=str(start_dt.hour % 12 or 12))
            break_start_minute = tk.StringVar(value=f"{start_dt.minute:02d}")
            break_start_ampm = tk.StringVar(value="PM" if start_dt.hour >= 12 else "AM")
            start_time_frame = ttk.Frame(break_frame)
            start_time_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
            ttk.Combobox(start_time_frame, textvariable=break_start_hour, values=hours, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
            ttk.Label(start_time_frame, text=":").pack(side=tk.LEFT)
            ttk.Combobox(start_time_frame, textvariable=break_start_minute, values=minutes, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
            ttk.Combobox(start_time_frame, textvariable=break_start_ampm, values=["AM", "PM"], width=4, state='readonly').pack(side=tk.LEFT, padx=2)

            ttk.Label(break_frame, text="End Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
            break_end_date = DateEntry(break_frame, width=18, date_pattern='mm/dd/yyyy', firstweekday='sunday')
            break_end_date.grid(row=3, column=1, sticky=tk.W, pady=5)
            break_end_date.set_date(end_dt)

            ttk.Label(break_frame, text="End Time:").grid(row=4, column=0, sticky=tk.W, pady=5)
            break_end_hour = tk.StringVar(value=str(end_dt.hour % 12 or 12))
            break_end_minute = tk.StringVar(value=f"{end_dt.minute:02d}")
            break_end_ampm = tk.StringVar(value="PM" if end_dt.hour >= 12 else "AM")
            end_time_frame = ttk.Frame(break_frame)
            end_time_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
            ttk.Combobox(end_time_frame, textvariable=break_end_hour, values=hours, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
            ttk.Label(end_time_frame, text=":").pack(side=tk.LEFT)
            ttk.Combobox(end_time_frame, textvariable=break_end_minute, values=minutes, width=4, state='readonly').pack(side=tk.LEFT, padx=2)
            ttk.Combobox(end_time_frame, textvariable=break_end_ampm, values=["AM", "PM"], width=4, state='readonly').pack(side=tk.LEFT, padx=2)

            def save_break():
                try:
                    start_date_value = break_start_date.get_date()
                    end_date_value = break_end_date.get_date()

                    start_hour = int(break_start_hour.get())
                    start_minute = int(break_start_minute.get())
                    if break_start_ampm.get() == "PM" and start_hour != 12:
                        start_hour += 12
                    elif break_start_ampm.get() == "AM" and start_hour == 12:
                        start_hour = 0

                    end_hour = int(break_end_hour.get())
                    end_minute = int(break_end_minute.get())
                    if break_end_ampm.get() == "PM" and end_hour != 12:
                        end_hour += 12
                    elif break_end_ampm.get() == "AM" and end_hour == 12:
                        end_hour = 0

                    start_dt_value = datetime(
                        start_date_value.year,
                        start_date_value.month,
                        start_date_value.day,
                        start_hour,
                        start_minute,
                    )
                    end_dt_value = datetime(
                        end_date_value.year,
                        end_date_value.month,
                        end_date_value.day,
                        end_hour,
                        end_minute,
                    )

                    if end_dt_value <= start_dt_value:
                        messagebox.showerror("Error", "Break end time must be after break start time.")
                        return

                    normalized_break = self.data_manager.normalize_break_record({
                        "start_time": start_dt_value.isoformat(),
                        "end_time": end_dt_value.isoformat(),
                        "break_type": break_type_var.get(),
                    })

                    if selected_break_index is None:
                        break_records.append(normalized_break)
                    else:
                        break_records[selected_break_index] = normalized_break

                    refresh_breaks_list()
                    break_dialog.destroy()
                except ValueError as exc:
                    messagebox.showerror("Error", f"Invalid break date or time: {exc}")

            btn_frame = ttk.Frame(break_frame)
            btn_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0))
            ttk.Button(btn_frame, text="Save Break", command=save_break).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=break_dialog.destroy).pack(side=tk.LEFT, padx=5)

        def add_break():
            open_break_editor()

        def edit_break():
            if not breaks_listbox.curselection():
                messagebox.showwarning("No Selection", "Please select a break to edit.")
                return
            selected_index = breaks_listbox.curselection()[0]
            open_break_editor(selected_index)

        def delete_break():
            if not breaks_listbox.curselection():
                messagebox.showwarning("No Selection", "Please select a break to delete.")
                return
            selected_index = breaks_listbox.curselection()[0]
            del break_records[selected_index]
            refresh_breaks_list()

        refresh_breaks_list()

        break_button_frame = ttk.Frame(frame)
        break_button_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)
        ttk.Button(break_button_frame, text="Add Break", command=add_break).pack(side=tk.LEFT, padx=5)
        ttk.Button(break_button_frame, text="Edit Break", command=edit_break).pack(side=tk.LEFT, padx=5)
        ttk.Button(break_button_frame, text="Delete Break", command=delete_break).pack(side=tk.LEFT, padx=5)
        
        # Preview
        preview_label = ttk.Label(frame, text="", foreground=self.accent_color, wraplength=350)
        preview_label.grid(row=8, column=0, columnspan=3, pady=15)
        
        def update_preview(*args):
            try:
                year = int(year_var.get())
                month = int(month_var.get())
                day = int(day_var.get())
                
                in_hour = int(in_hour_var.get())
                in_minute = int(in_minute_var.get())
                if in_ampm_var.get() == "PM" and in_hour != 12:
                    in_hour += 12
                elif in_ampm_var.get() == "AM" and in_hour == 12:
                    in_hour = 0
                
                if not clock_out_active_var.get():
                    preview_label.config(text="")
                    return

                out_hour = int(out_hour_var.get())
                out_minute = int(out_minute_var.get())
                if out_ampm_var.get() == "PM" and out_hour != 12:
                    out_hour += 12
                elif out_ampm_var.get() == "AM" and out_hour == 12:
                    out_hour = 0
                
                clock_in = datetime(year, month, day, in_hour, in_minute)
                clock_out = datetime(year, month, day, out_hour, out_minute)
                
                if clock_out <= clock_in:
                    clock_out = datetime(year, month, day + 1, out_hour, out_minute)
                
                hours = (clock_out - clock_in).total_seconds() / 3600
                wages = hours * entry['hourly_rate']
                
                preview_text = f"Hours: {hours:.2f} | Wages: ${wages:.2f}"
                preview_label.config(text=preview_text)
            except:
                preview_label.config(text="")
        
        for var in [year_var, month_var, day_var, in_hour_var, in_minute_var, in_ampm_var, 
                    out_hour_var, out_minute_var, out_ampm_var, clock_out_active_var]:
            var.trace('w', update_preview)
        
        update_preview()
        
        def save_changes():
            try:
                year = int(year_var.get())
                month = int(month_var.get())
                day = int(day_var.get())
                
                in_hour = int(in_hour_var.get())
                in_minute = int(in_minute_var.get())
                if in_ampm_var.get() == "PM" and in_hour != 12:
                    in_hour += 12
                elif in_ampm_var.get() == "AM" and in_hour == 12:
                    in_hour = 0
                
                clock_in = datetime(year, month, day, in_hour, in_minute)
                clock_out = None
                if clock_out_active_var.get():
                    out_hour = int(out_hour_var.get())
                    out_minute = int(out_minute_var.get())
                    if out_ampm_var.get() == "PM" and out_hour != 12:
                        out_hour += 12
                    elif out_ampm_var.get() == "AM" and out_hour == 12:
                        out_hour = 0
                    
                    clock_out = datetime(year, month, day, out_hour, out_minute)
                    
                    if clock_out <= clock_in:
                        clock_out = datetime(year, month, day + 1, out_hour, out_minute)
                
                # Update the time entry
                success, message = self.data_manager.update_entry(entry_index, clock_in, clock_out, breaks=break_records)
                
                # Update project if changed
                if success:
                    selected_project = project_var.get()
                    if selected_project:
                        self.data_manager.data["time_entries"][entry_index]["project"] = selected_project
                        self.data_manager.save_data()
                
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid date or time: {str(e)}")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=9, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=510, y=10)
    
    def delete_entry_dialog(self):
        """Open dialog to delete a time entry"""
        all_entries = [
            (i, e)
            for i, e in enumerate(self.data_manager.data["time_entries"])
        ]
        
        if not all_entries:
            messagebox.showinfo("No Entries", "No time entries to delete.")
            return
        
        # Entry selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Entry to Delete")
        
        # Calculate center position
        window_width = 650
        window_height = 450
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Entry to Delete", style='Header.TLabel').pack(pady=(0, 10))
        ttk.Label(frame, text="Active shifts are shown by default.").pack(pady=(0, 10))

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(filter_frame, text="Show:").pack(side=tk.LEFT, padx=(0, 8))
        status_filter_var = ttk.Combobox(filter_frame, state='readonly', width=12, values=["Active", "Closed", "All"])
        status_filter_var.set("Active")
        status_filter_var.pack(side=tk.LEFT)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color,
                            selectmode=tk.SINGLE, yscrollcommand=scrollbar.set, height=15)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        filtered_entries = []

        def get_entry_status(entry):
            return "Active" if entry.get("clock_out") is None else "Closed"

        def refresh_entries(*_):
            nonlocal filtered_entries
            listbox.delete(0, tk.END)
            filtered_entries = []
            selected_filter = status_filter_var.get()

            for global_idx, entry in all_entries:
                status = get_entry_status(entry)
                if selected_filter != "All" and status != selected_filter:
                    continue

                clock_in = datetime.fromisoformat(entry["clock_in"]).strftime('%m/%d/%Y %I:%M %p')
                if entry.get("clock_out"):
                    clock_out = datetime.fromisoformat(entry["clock_out"]).strftime('%m/%d/%Y %I:%M %p')
                else:
                    clock_out = "---"

                display = f"{entry['name']} | {clock_in} - {clock_out} | {entry['hours_worked']:.2f}h | ${entry['wages']:.2f} | {status}"
                listbox.insert(tk.END, display)
                filtered_entries.append((global_idx, entry))

            if not filtered_entries:
                listbox.insert(tk.END, "No entries match the selected filter.")

        status_filter_var.bind('<<ComboboxSelected>>', refresh_entries)
        refresh_entries()
        
        def delete_selected():
            if not filtered_entries:
                messagebox.showinfo("No Entries", "No time entries match the selected filter.")
                return

            if not listbox.curselection():
                messagebox.showwarning("No Selection", "Please select an entry to delete.")
                return
            
            selected_idx = listbox.curselection()[0]
            global_idx, entry = filtered_entries[selected_idx]
            
            # Confirm deletion
            clock_in = datetime.fromisoformat(entry["clock_in"]).strftime('%m/%d/%Y %I:%M %p')
            clock_out = datetime.fromisoformat(entry["clock_out"]).strftime('%m/%d/%Y %I:%M %p')
            confirm_msg = f"Delete this entry?\n\n{clock_in} - {clock_out}\n{entry['hours_worked']:.2f} hours | ${entry['wages']:.2f}"
            
            if messagebox.askyesno("Confirm Delete", confirm_msg):
                success, message = self.data_manager.delete_entry(global_idx)
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))
        
        ttk.Button(btn_frame, text="Delete Selected", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Add close button at top right
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=610, y=10)
    
    def view_reports(self):
        """View wage reports"""
        selection = self.employee_combo.get()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        emp_id = selection.split(' - ')[0]
        employee = self.data_manager.get_employee(emp_id)
        
        total_hours, total_wages, num_entries = self.data_manager.calculate_total_wages(emp_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Wage Report - {employee['name']}")
        
        # Calculate center position
        window_width = 600
        window_height = 500
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        report_text = scrolledtext.ScrolledText(frame, font=('Consolas', 10),
                                               bg='#34495e', fg=self.fg_color,
                                               relief=tk.FLAT, padx=15, pady=15)
        report_text.pack(fill=tk.BOTH, expand=True)
        
        report = f"{'='*50}\n"
        report += f"WAGE REPORT\n"
        report += f"{'='*50}\n\n"
        report += f"Employee:      {employee['name']}\n"
        report += f"Employee ID:   {emp_id}\n"
        report += f"Current Rate:  ${employee['hourly_rate']:.2f}/hr\n\n"
        report += f"{'='*50}\n"
        report += f"SUMMARY\n"
        report += f"{'='*50}\n\n"
        report += f"Total Entries:      {num_entries}\n"
        report += f"Total Hours:        {total_hours:.2f} hrs\n"
        report += f"Total Wages:        ${total_wages:.2f}\n"
        
        if num_entries > 0:
            avg_hours = total_hours / num_entries
            report += f"Avg Hours/Entry:    {avg_hours:.2f} hrs\n"
        
        report_text.insert('1.0', report)
        report_text.config(state=tk.DISABLED)
        
        ttk.Button(frame, text="Close", command=dialog.destroy).pack(pady=(10, 0))
        
        # Add close button at top right
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=560, y=10)
    
    def start_break_dialog(self):
        """Show dialog to select break type and start break"""
        selection = self.employee_combo.get()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        emp_id = selection.split(' - ')[0]
        
        # Ask for break type
        dialog = tk.Toplevel(self.root)
        dialog.title("Start Break")
        dialog.geometry("400x200")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Break Type:", style='Header.TLabel').pack(pady=(0, 10))
        
        break_type_var = tk.StringVar(value="Unpaid")
        ttk.Radiobutton(frame, text="Paid Break", variable=break_type_var, value="Paid").pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(frame, text="Unpaid Break", variable=break_type_var, value="Unpaid").pack(anchor=tk.W, pady=5)
        
        def confirm():
            success, message = self.data_manager.start_break(emp_id, break_type_var.get())
            if success:
                messagebox.showinfo("Success", message)
                dialog.destroy()
                self.refresh_all()
            else:
                messagebox.showerror("Error", message)
        
        ttk.Button(frame, text="Start Break", command=confirm).pack(pady=(15, 0))
    
    def end_break(self):
        """End a break for the selected employee"""
        selection = self.employee_combo.get()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee first.")
            return
        
        emp_id = selection.split(' - ')[0]
        success, message = self.data_manager.end_break(emp_id)
        
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_all()
        else:
            messagebox.showerror("Error", message)
    
    def generate_payroll_report(self):
        """Generate payroll report for date range"""
        try:
            start_date = self.payroll_start_date.get_date()
            end_date = self.payroll_end_date.get_date()
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.min.time())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format! Use MM/DD/YYYY")
            return
        
        report_data = self.data_manager.get_payroll_report(start_date, end_date)
        
        self.payroll_text.delete('1.0', tk.END)
        
        if not report_data:
            self.payroll_text.insert('1.0', "No entries found for the specified date range.")
            return
        
        # Header
        report = f"{'='*120}\n"
        report += f"PAYROLL REPORT - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n"
        report += f"{'='*120}\n\n"
        
        # Column headers
        report += f"{'Name':<20} {'Date':<12} {'Type':<10} {'Total Hrs':<10} {'Reg Hrs':<10} {'OT Hrs':<10} {'Reg Pay':<12} {'OT Pay':<12} {'Gross':<12}\n"
        report += f"{'-'*130}\n"
        
        total_reg_hours = 0
        total_ot_hours = 0
        total_reg_pay = 0
        total_ot_pay = 0
        total_gross = 0
        
        for entry in report_data:
            entry_type = entry.get('leave_type', 'Work') if entry.get('entry_type') == 'leave' else 'Work'
            report += f"{entry['name']:<20} {entry['date']:<12} {entry_type:<10} {entry['total_hours']:<10.2f} {entry['regular_hours']:<10.2f} {entry['overtime_hours']:<10.2f} ${entry['regular_pay']:<11.2f} ${entry['overtime_pay']:<11.2f} ${entry['gross_pay']:<11.2f}\n"
            total_reg_hours += entry['regular_hours']
            total_ot_hours += entry['overtime_hours']
            total_reg_pay += entry['regular_pay']
            total_ot_pay += entry['overtime_pay']
            total_gross += entry['gross_pay']
        
        report += f"{'-'*130}\n"
        report += f"{'TOTALS':<20} {'':<12} {'':<10} {total_reg_hours + total_ot_hours:<10.2f} {total_reg_hours:<10.2f} {total_ot_hours:<10.2f} ${total_reg_pay:<11.2f} ${total_ot_pay:<11.2f} ${total_gross:<11.2f}\n"
        report += f"{'='*130}\n"
        
        self.payroll_text.insert('1.0', report)
    
    def export_payroll_csv(self):
        """Export payroll report to CSV file"""
        try:
            start_date = self.payroll_start_date.get_date()
            end_date = self.payroll_end_date.get_date()
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.min.time())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format! Use MM/DD/YYYY")
            return
        
        report_data = self.data_manager.get_payroll_report(start_date, end_date)
        
        if not report_data:
            messagebox.showwarning("No Data", "No entries found for the specified date range.")
            return
        
        import csv
        filename = f"payroll_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Name', 'Date', 'Total Hours', 'Regular Hours', 'Overtime Hours', 
                         'Hourly Rate', 'OT Rate', 'Regular Pay', 'Overtime Pay', 'Gross Pay']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in report_data:
                writer.writerow({
                    'Name': entry['name'],
                    'Date': entry['date'],
                    'Total Hours': entry['total_hours'],
                    'Regular Hours': entry['regular_hours'],
                    'Overtime Hours': entry['overtime_hours'],
                    'Hourly Rate': entry['hourly_rate'],
                    'OT Rate': entry['overtime_rate'],
                    'Regular Pay': entry['regular_pay'],
                    'Overtime Pay': entry['overtime_pay'],
                    'Gross Pay': entry['gross_pay']
                })
        
        messagebox.showinfo("Success", f"Payroll report exported to {filename}")
    
    def submit_leave_request(self):
        """Submit a leave request"""
        selection = self.leave_employee_combo.get()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee.")
            return
        
        emp_id = selection.split(' - ')[0]
        leave_type = self.leave_type_combo.get()
        start_date = self.leave_start_date.get_date().strftime('%m/%d/%Y')
        end_date = self.leave_end_date.get_date().strftime('%m/%d/%Y')
        
        try:
            hours = float(self.leave_hours.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for hours.")
            return
        
        reason = self.leave_reason.get('1.0', tk.END).strip()
        
        success, message = self.data_manager.request_leave(emp_id, leave_type, start_date, end_date, hours, reason)
        
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_leave_requests()
            # Reset form while keeping valid dates
            self.leave_start_date.set_date(datetime.now())
            self.leave_end_date.set_date(datetime.now())
            self.leave_hours.delete(0, tk.END)
            self.leave_reason.delete('1.0', tk.END)
        else:
            messagebox.showerror("Error", message)
    
    def refresh_leave_requests(self):
        """Refresh leave requests display"""
        self.leave_requests_text.delete('1.0', tk.END)
        
        # Refresh employee combo
        employees = self.data_manager.get_all_employees()
        employee_list = [f"{emp_id} - {emp['name']}" for emp_id, emp in employees.items()]
        self.leave_employee_combo['values'] = employee_list
        
        # Display pending requests
        pending = [r for r in self.data_manager.data.get("leave_requests", []) if r['status'] == 'Pending']
        
        if not pending:
            self.leave_requests_text.insert('1.0', "No pending leave requests.")
            return
        
        report = f"{'='*80}\n"
        report += "PENDING LEAVE REQUESTS\n"
        report += f"{'='*80}\n\n"
        
        for req in pending:
            report += f"Request ID: {req['request_id']}\n"
            report += f"Employee:   {req['employee_name']}\n"
            report += f"Type:       {req['leave_type']}\n"
            report += f"Dates:      {req['start_date']} to {req['end_date']}\n"
            report += f"Hours:      {req['hours']}\n"
            report += f"Reason:     {req['reason']}\n"
            report += f"Submitted:  {req['submitted_date']}\n"
            report += f"{'-'*80}\n\n"
        
        self.leave_requests_text.insert('1.0', report)
    
    def update_leave_balance(self, event=None):
        """Update the leave balance display when employee or leave type changes"""
        selection = self.leave_employee_combo.get()
        if not selection:
            self.leave_balance_label.config(text="Balance: 0.0 hrs")
            return
        
        emp_id = selection.split(' - ')[0]
        employee = self.data_manager.get_employee(emp_id)
        if not employee:
            self.leave_balance_label.config(text="Balance: 0.0 hrs")
            return
        
        leave_type = self.leave_type_combo.get()
        balance_key = f"{leave_type.lower()}_balance"
        balance = employee.get(balance_key, 0)
        
        self.leave_balance_label.config(text=f"Balance: {balance:.1f} hrs")
    
    def approve_leave(self):
        """Approve a leave request"""
        # Get pending requests
        pending = [r for r in self.data_manager.data.get("leave_requests", []) if r['status'] == 'Pending']
        
        if not pending:
            messagebox.showinfo("No Requests", "There are no pending leave requests.")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Approve Leave Request")
        dialog.geometry("700x500")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Leave Request to Approve:", style='Header.TLabel').pack(pady=(0, 10))
        
        # Create listbox with requests
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=('Consolas', 9),
                            bg='#34495e', fg=self.fg_color, selectmode=tk.SINGLE)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for req in pending:
            display_text = f"ID: {req['request_id']} - {req['employee_name']} - {req['leave_type']} ({req['start_date']} to {req['end_date']}) - {req['hours']} hrs"
            listbox.insert(tk.END, display_text)
        
        ttk.Label(frame, text="Approver Name:").pack(anchor=tk.W, pady=(5, 0))
        approver_entry = ttk.Entry(frame, width=40)
        approver_entry.pack(fill=tk.X, pady=(0, 10))
        
        def do_approve():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a request to approve.")
                return
            
            approver = approver_entry.get().strip()
            if not approver:
                messagebox.showwarning("No Approver", "Please enter your name.")
                return
            
            request_id = pending[selection[0]]['request_id']
            success, message = self.data_manager.approve_leave_request(request_id, approver)
            
            if success:
                messagebox.showinfo("Success", message)
                dialog.destroy()
                self.refresh_leave_requests()
            else:
                messagebox.showerror("Error", message)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="✅ Approve", command=do_approve).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def deny_leave(self):
        """Deny a leave request"""
        # Get pending requests
        pending = [r for r in self.data_manager.data.get("leave_requests", []) if r['status'] == 'Pending']
        
        if not pending:
            messagebox.showinfo("No Requests", "There are no pending leave requests.")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Deny Leave Request")
        dialog.geometry("700x550")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Leave Request to Deny:", style='Header.TLabel').pack(pady=(0, 10))
        
        # Create listbox with requests
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=('Consolas', 9),
                            bg='#34495e', fg=self.fg_color, selectmode=tk.SINGLE)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for req in pending:
            display_text = f"ID: {req['request_id']} - {req['employee_name']} - {req['leave_type']} ({req['start_date']} to {req['end_date']}) - {req['hours']} hrs"
            listbox.insert(tk.END, display_text)
        
        ttk.Label(frame, text="Approver Name:").pack(anchor=tk.W, pady=(5, 0))
        approver_entry = ttk.Entry(frame, width=40)
        approver_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Denial Reason (optional):").pack(anchor=tk.W, pady=(5, 0))
        reason_entry = ttk.Entry(frame, width=40)
        reason_entry.pack(fill=tk.X, pady=(0, 10))
        
        def do_deny():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a request to deny.")
                return
            
            approver = approver_entry.get().strip()
            if not approver:
                messagebox.showwarning("No Approver", "Please enter your name.")
                return
            
            reason = reason_entry.get().strip()
            request_id = pending[selection[0]]['request_id']
            success, message = self.data_manager.deny_leave_request(request_id, approver, reason)
            
            if success:
                messagebox.showinfo("Success", message)
                dialog.destroy()
                self.refresh_leave_requests()
            else:
                messagebox.showerror("Error", message)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="❌ Deny", command=do_deny).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def adjust_pto_dialog(self):
        """Dialog to manually adjust PTO balance"""
        selection = self.leave_employee_combo.get()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an employee.")
            return
        
        emp_id = selection.split(' - ')[0]
        employee = self.data_manager.get_employee(emp_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Adjust PTO Balance")
        dialog.geometry("500x400")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"Employee: {employee['name']}", style='Header.TLabel').pack(pady=(0, 15))
        
        ttk.Label(frame, text="Leave Type:").pack(anchor=tk.W)
        leave_type_var = ttk.Combobox(frame, state='readonly', values=["PTO", "Sick", "Vacation"])
        leave_type_var.pack(fill=tk.X, pady=(0, 10))
        leave_type_var.current(0)
        
        ttk.Label(frame, text="Hours to Add (use negative to subtract):").pack(anchor=tk.W)
        hours_entry = ttk.Entry(frame)
        hours_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Reason:").pack(anchor=tk.W)
        reason_entry = ttk.Entry(frame)
        reason_entry.pack(fill=tk.X, pady=(0, 15))
        
        def save_adjustment():
            try:
                hours = float(hours_entry.get())
                leave_type = leave_type_var.get()
                reason = reason_entry.get()
                
                success, message = self.data_manager.adjust_pto_balance(emp_id, leave_type, hours, reason)
                
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", message)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for hours.")
        
        ttk.Button(frame, text="Save Adjustment", command=save_adjustment).pack()
    
    def on_report_type_changed(self, event=None):
        """Show/hide employee selector based on report type"""
        report_type = self.report_type_combo.get()
        if report_type in ["Wage Report", "Attendance Report"]:
            self.emp_select_frame.grid()
            self.refresh_report_employee_list()
        else:
            self.emp_select_frame.grid_remove()
    
    def refresh_report_employee_list(self):
        """Refresh the employee list in the reports tab"""
        employees = self.data_manager.get_all_employees()
        employee_list = [f"{emp_id} - {emp['name']}" for emp_id, emp in employees.items()]
        self.report_employee_combo['values'] = employee_list
        if employee_list:
            self.report_employee_combo.current(0)
    
    def view_employee_report(self):
        """View employee reports"""
        report_type = self.report_type_combo.get()
        
        # For Wage Report and Attendance Report, use report_employee_combo
        if report_type in ["Wage Report", "Attendance Report"]:
            # Ensure employee list is populated
            if not self.report_employee_combo.get():
                self.refresh_report_employee_list()
            
            selection = self.report_employee_combo.get()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an employee first.")
                return
            
            try:
                emp_id = selection.split(' - ')[0]
                if report_type == "Wage Report":
                    self.view_wage_report_for_employee(emp_id)
                else:  # Attendance Report
                    self.view_attendance_report_for_employee(emp_id)
            except Exception as e:
                messagebox.showerror("Error", f"Error generating report: {str(e)}")
            return
        
        # For other reports, show all employees
        selection = self.employee_combo.get()
        if not selection:
            # Show all employees report
            employees = self.data_manager.get_all_employees()
        else:
            emp_id = selection.split(' - ')[0]
            employees = {emp_id: self.data_manager.get_employee(emp_id)}
        
        report_type = self.report_type_combo.get()
        self.report_text.delete('1.0', tk.END)
        
        if report_type == "Employee Hours Summary":
            report = f"{'='*100}\n"
            report += "EMPLOYEE HOURS SUMMARY\n"
            report += f"{'='*100}\n\n"
            report += f"{'Name':<25} {'Total Hrs':<12} {'Total Wages':<15} {'Entries':<10} {'Avg Hrs/Entry':<15}\n"
            report += f"{'-'*100}\n"
            
            for emp_id, emp in employees.items():
                total_hours, total_wages, num_entries = self.data_manager.calculate_total_wages(emp_id)
                avg_hours = total_hours / num_entries if num_entries > 0 else 0
                report += f"{emp['name']:<25} {total_hours:<12.2f} ${total_wages:<14.2f} {num_entries:<10} {avg_hours:<15.2f}\n"
            
            self.report_text.insert('1.0', report)
    
    def view_wage_report_for_employee(self, emp_id):
        """View wage report for a specific employee"""
        employee = self.data_manager.get_employee(emp_id)
        total_hours, total_wages, num_entries = self.data_manager.calculate_total_wages(emp_id)
        
        self.report_text.delete('1.0', tk.END)
        
        report = f"{'='*80}\n"
        report += f"WAGE REPORT\n"
        report += f"{'='*80}\n\n"
        report += f"Employee:      {employee['name']}\n"
        report += f"Employee ID:   {emp_id}\n"
        report += f"Department:    {employee.get('department', 'N/A')}\n"
        report += f"Job Title:     {employee.get('job_title', 'N/A')}\n"
        report += f"Current Rate:  ${employee['hourly_rate']:.2f}/hr\n\n"
        report += f"{'='*80}\n"
        report += f"SUMMARY\n"
        report += f"{'='*80}\n\n"
        report += f"Total Hours Worked:    {total_hours:.2f}\n"
        report += f"Total Wages Earned:    ${total_wages:.2f}\n"
        report += f"Number of Entries:     {num_entries}\n"
        report += f"Average Hours/Entry:   {total_hours/num_entries if num_entries > 0 else 0:.2f}\n\n"
        
        # Get time entries
        entries = [entry for entry in self.data_manager.data["time_entries"] if entry['employee_id'] == emp_id and entry.get('clock_out')]
        if entries:
            report += f"{'='*80}\n"
            report += f"TIME ENTRIES\n"
            report += f"{'='*80}\n\n"
            report += f"{'Date':<12} {'Clock In':<10} {'Clock Out':<10} {'Hours':<8} {'Wages':<10}\n"
            report += f"{'-'*80}\n"
            
            for entry in sorted(entries, key=lambda x: x['clock_in'], reverse=True):
                clock_in = datetime.fromisoformat(entry['clock_in'])
                clock_out = datetime.fromisoformat(entry['clock_out'])
                hours = entry.get('hours_worked', 0)
                wages = hours * employee['hourly_rate']
                report += f"{clock_in.strftime('%m/%d/%Y'):<12} {clock_in.strftime('%I:%M %p'):<10} {clock_out.strftime('%I:%M %p'):<10} {hours:<8.2f} ${wages:<9.2f}\n"
        
        self.report_text.insert('1.0', report)
    
    def view_attendance_report_for_employee(self, emp_id):
        """View attendance report for a specific employee"""
        employee = self.data_manager.get_employee(emp_id)
        
        self.report_text.delete('1.0', tk.END)
        
        report = f"{'='*120}\n"
        report += f"ATTENDANCE REPORT - {employee['name']}\n"
        report += f"{'='*120}\n\n"
        report += f"Employee ID:   {emp_id}\n"
        report += f"Department:    {employee.get('department', 'N/A')}\n"
        report += f"Job Title:     {employee.get('job_title', 'N/A')}\n\n"
        report += f"{'='*120}\n"
        report += f"{'Date':<12} {'Clock In':<12} {'Clock Out':<12} {'Hours':<8} {'Break Time':<12} {'Status':<10}\n"
        report += f"{'-'*120}\n"
        
        # Get time entries for this employee sorted by date (newest first)
        entries = [entry for entry in self.data_manager.data["time_entries"] if entry['employee_id'] == emp_id]
        entries = sorted(entries, key=lambda x: x.get('clock_in', ''), reverse=True)
        
        total_hours = 0
        total_break_time = 0
        
        for entry in entries:
            clock_in = datetime.fromisoformat(entry['clock_in'])
            date_str = clock_in.strftime('%m/%d/%Y')
            clock_in_str = clock_in.strftime('%I:%M %p')
            
            if entry.get('clock_out'):
                clock_out = datetime.fromisoformat(entry['clock_out'])
                clock_out_str = clock_out.strftime('%I:%M %p')
                hours = entry.get('hours_worked', 0)
                total_hours += hours
                status = "Complete"
            else:
                clock_out_str = "---"
                hours = 0
                status = "Clocked In"
            
            # Calculate total break time
            break_time = self.data_manager.calculate_break_hours(entry)
            total_break_time += break_time
            
            break_str = f"{break_time:.2f} hrs" if break_time > 0 else "None"
            
            report += f"{date_str:<12} {clock_in_str:<12} {clock_out_str:<12} {hours:<8.2f} {break_str:<12} {status:<10}\n"
        
        if not entries:
            report += "\nNo attendance records found for this employee.\n"
        else:
            report += f"{'-'*120}\n"
            report += f"{'TOTALS':<12} {'':<12} {'':<12} {total_hours:<8.2f} {total_break_time:<12.2f}\n"
        
        # Add leave requests section (Approved and Denied)
        leave_requests = [r for r in self.data_manager.data.get("leave_requests", []) 
                         if r['employee_id'] == emp_id and r['status'] in ['Approved', 'Denied']]
        
        if leave_requests:
            report += f"\n{'='*120}\n"
            report += f"LEAVE REQUESTS\n"
            report += f"{'='*120}\n\n"
            report += f"{'Type':<12} {'Start Date':<12} {'End Date':<12} {'Hours':<8} {'Status':<12} {'Approved By':<20} {'Date':<12}\n"
            report += f"{'-'*120}\n"
            
            for req in sorted(leave_requests, key=lambda x: x.get('start_date', ''), reverse=True):
                status_display = req['status']
                if req['status'] == 'Denied' and req.get('denial_reason'):
                    status_display = f"Denied*"
                
                report += f"{req['leave_type']:<12} {req['start_date']:<12} {req['end_date']:<12} {req['hours']:<8.1f} {status_display:<12} {req.get('approved_by', 'N/A'):<20} {req.get('approved_date', 'N/A'):<12}\n"
                
                if req['status'] == 'Denied' and req.get('denial_reason'):
                    report += f"  Reason: {req['denial_reason']}\n"
            
            report += f"\n* Denied requests do not deduct from leave balance\n"
        
        self.report_text.insert('1.0', report)
    
    def refresh_all(self):
        """Refresh all displays"""
        self.refresh_employee_list()
        self.on_employee_selected(None)
    
    # ============= FILE MENU METHODS =============
    
    def print_report(self):
        """Print current report"""
        # Get the current active tab
        current_tab = self.notebook.index(self.notebook.select())
        tab_names = ["Time Clock", "Payroll", "Leave Management", "Reports", "Employees"]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Print Report")
        dialog.geometry("600x500")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Print Report", style='Header.TLabel').pack(pady=(0, 20))
        
        ttk.Label(frame, text=f"Current Tab: {tab_names[current_tab]}", font=('Segoe UI', 11, 'bold')).pack(pady=10)
        
        # Print options
        ttk.Label(frame, text="Select what to print:").pack(anchor=tk.W, pady=(10, 5))
        
        print_var = tk.StringVar(value="current")
        ttk.Radiobutton(frame, text="Current visible report", variable=print_var, value="current").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(frame, text="Payroll report (current period)", variable=print_var, value="payroll").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(frame, text="All employee time entries", variable=print_var, value="all_entries").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(frame, text="Employee summary", variable=print_var, value="summary").pack(anchor=tk.W, padx=20)
        
        def do_print():
            selection = print_var.get()
            
            # Get content to print based on selection
            content = ""
            if selection == "current":
                if current_tab == 0:  # Time Clock
                    content = self.entries_text.get('1.0', tk.END)
                elif current_tab == 1:  # Payroll
                    content = self.payroll_text.get('1.0', tk.END)
                elif current_tab == 2:  # Leave Management
                    content = self.leave_requests_text.get('1.0', tk.END)
                elif current_tab == 3:  # Reports
                    content = self.report_text.get('1.0', tk.END)
            elif selection == "payroll":
                self.generate_payroll_report()
                content = self.payroll_text.get('1.0', tk.END)
            elif selection == "all_entries":
                content = "All Time Entries Report\n" + "="*80 + "\n\n"
                for emp_id, emp in self.data_manager.get_all_employees().items():
                    content += f"\n{emp['name']} ({emp_id})\n" + "-"*40 + "\n"
                    entries = [e for e in self.data_manager.data["time_entries"] if e['employee_id'] == emp_id and e.get('clock_out')]
                    for entry in sorted(entries, key=lambda x: x['clock_in'], reverse=True)[:10]:
                        clock_in = datetime.fromisoformat(entry['clock_in'])
                        clock_out = datetime.fromisoformat(entry['clock_out'])
                        content += f"{clock_in.strftime('%m/%d/%Y %I:%M %p')} - {clock_out.strftime('%I:%M %p')}: {entry.get('hours_worked', 0):.2f} hrs\n"
            elif selection == "summary":
                content = "Employee Summary Report\n" + "="*80 + "\n\n"
                for emp_id, emp in self.data_manager.get_all_employees().items():
                    hours, wages, entries = self.data_manager.calculate_total_wages(emp_id)
                    content += f"{emp['name']:<30} Hours: {hours:>8.2f}  Wages: ${wages:>10.2f}  Entries: {entries:>5}\n"
            
            # Save to temporary text file for printing
            import tempfile
            import subprocess
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                f.write(content)
                temp_file = f.name
            
            # Try to open with Microsoft Word
            try:
                # Common Word installation paths
                word_paths = [
                    r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                    r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
                    r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
                    r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE",
                    r"C:\Program Files\Microsoft Office\root\Office15\WINWORD.EXE",
                    r"C:\Program Files (x86)\Microsoft Office\root\Office15\WINWORD.EXE",
                ]
                
                word_exe = None
                for path in word_paths:
                    if os.path.exists(path):
                        word_exe = path
                        break
                
                if word_exe:
                    subprocess.Popen([word_exe, temp_file])
                    messagebox.showinfo("Print", f"Report opened in Microsoft Word.\n\nYou can now print using File > Print in Word.\n\nFile: {temp_file}")
                else:
                    # Fallback to default editor if Word not found
                    os.startfile(temp_file)
                    messagebox.showinfo("Print", f"Microsoft Word not found.\n\nReport opened in default text editor.\n\nYou can now print using File > Print.\n\nFile: {temp_file}")
                
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open report:\n{str(e)}")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Print", command=do_print).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def backup_data(self):
        """Backup data to file"""
        backup_folder = get_backup_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_folder / f"time_clock_backup_{timestamp}.json"
        
        try:
            shutil.copy(self.data_manager.data_file, backup_file)
            messagebox.showinfo("Backup Successful", f"Data backed up to:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Failed to backup data:\n{str(e)}")
    
    def export_all_data(self):
        """Export all data to CSV or JSON"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Export All Data")
        dialog.geometry("600x450")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Export All Data", style='Header.TLabel').pack(pady=(0, 20))
        
        ttk.Label(frame, text="Choose export format and data:").pack(anchor=tk.W, pady=(0, 10))
        
        def export_json():
            import shutil
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"time_clock_export_{timestamp}.json"
            try:
                shutil.copy(self.data_manager.data_file, filename)
                messagebox.showinfo("Success", f"All data exported to JSON:\n\n{filename}\n\nLocation: {os.path.abspath(filename)}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{str(e)}")
        
        def export_csv_all():
            import csv
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            try:
                # Export employees
                emp_file = f"employees_{timestamp}.csv"
                with open(emp_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Employee ID', 'Name', 'Hourly Rate', 'Department', 'Job Title', 'Employee Type', 'PTO Balance', 'Sick Balance', 'Vacation Balance'])
                    for emp_id, emp in self.data_manager.get_all_employees().items():
                        writer.writerow([
                            emp_id, emp['name'], emp['hourly_rate'],
                            emp.get('department', 'N/A'), emp.get('job_title', 'N/A'),
                            emp.get('employee_type', 'N/A'),
                            emp.get('pto_balance', 0), emp.get('sick_balance', 0),
                            emp.get('vacation_balance', 0)
                        ])
                
                # Export time entries
                entries_file = f"time_entries_{timestamp}.csv"
                with open(entries_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Employee ID', 'Name', 'Clock In', 'Clock Out', 'Hours Worked', 'Hourly Rate'])
                    for entry in self.data_manager.data["time_entries"]:
                        if entry.get('clock_out'):
                            writer.writerow([
                                entry['employee_id'], entry['name'],
                                entry['clock_in'], entry['clock_out'],
                                entry.get('hours_worked', 0), entry['hourly_rate']
                            ])
                
                # Export leave requests
                leave_file = f"leave_requests_{timestamp}.csv"
                with open(leave_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Request ID', 'Employee ID', 'Employee Name', 'Leave Type', 'Start Date', 'End Date', 'Hours', 'Status', 'Approved By'])
                    for req in self.data_manager.data.get("leave_requests", []):
                        writer.writerow([
                            req['request_id'], req['employee_id'], req['employee_name'],
                            req['leave_type'], req['start_date'], req['end_date'],
                            req['hours'], req['status'], req.get('approved_by', 'N/A')
                        ])
                
                messagebox.showinfo("Success", f"Data exported to CSV files:\n\n{emp_file}\n{entries_file}\n{leave_file}\n\nLocation: {os.path.abspath(emp_file)}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{str(e)}")
        
        def export_payroll_csv():
            try:
                start_date = datetime.now().replace(day=1)
                end_date = datetime.now()
                report_data = self.data_manager.get_payroll_report(start_date, end_date)
                
                if not report_data:
                    messagebox.showwarning("No Data", "No payroll data for current period.")
                    return
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"payroll_export_{timestamp}.csv"
                
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Employee', 'Date', 'Type', 'Total Hours', 'Regular Hours', 'OT Hours', 'Hourly Rate', 'OT Rate', 'Regular Pay', 'Overtime Pay', 'Gross Pay'])
                    
                    for entry in report_data:
                        entry_type = entry.get('leave_type', 'Work') if entry.get('entry_type') == 'leave' else 'Work'
                        writer.writerow([
                            entry['name'], entry['date'], entry_type,
                            entry['total_hours'], entry['regular_hours'], entry['overtime_hours'],
                            entry['hourly_rate'], entry['overtime_rate'],
                            entry['regular_pay'], entry['overtime_pay'], entry['gross_pay']
                        ])
                
                messagebox.showinfo("Success", f"Payroll data exported:\n\n{filename}\n\nLocation: {os.path.abspath(filename)}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{str(e)}")
        
        ttk.Button(frame, text="📄 Export Complete Database (JSON)", command=export_json).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text="📊 Export All Data (Multiple CSV Files)", command=export_csv_all).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text="💰 Export Current Payroll Period (CSV)", command=export_payroll_csv).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text="Cancel", command=dialog.destroy).pack(pady=20, fill=tk.X)
    
    def import_data(self):
        """Import data from file"""
        from tkinter import filedialog
        
        response = messagebox.askyesno("Import Data", 
                                       "Importing data will merge with existing data.\n\n" +
                                       "Do you want to backup current data first?")
        if response:
            self.backup_data()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Import Data")
        dialog.geometry("600x500")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Import Data", style='Header.TLabel').pack(pady=(0, 20))
        
        selected_file = tk.StringVar(value="No file selected")
        
        ttk.Label(frame, text="Select import file:").pack(anchor=tk.W, pady=(0, 10))
        file_label = ttk.Label(frame, textvariable=selected_file, foreground=self.accent_color)
        file_label.pack(anchor=tk.W, pady=(0, 20))
        
        import_type = tk.StringVar(value="merge")
        
        ttk.Label(frame, text="Import mode:").pack(anchor=tk.W, pady=(10, 5))
        ttk.Radiobutton(frame, text="Merge with existing data (recommended)", variable=import_type, value="merge").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(frame, text="Replace all data (WARNING: Current data will be lost)", variable=import_type, value="replace").pack(anchor=tk.W, padx=20)
        
        selected_filepath: List[Optional[str]] = [None]
        
        def browse_file():
            filename = filedialog.askopenfilename(
                title="Select Time Clock Data File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                selected_filepath[0] = filename
                selected_file.set(os.path.basename(filename))
        
        def do_import():
            if not selected_filepath[0]:
                messagebox.showwarning("No File", "Please select a file to import.")
                return
            
            mode = import_type.get()
            
            if mode == "replace":
                confirm = messagebox.askyesno("Confirm Replace", 
                                             "This will DELETE all current data and replace it.\n\n" +
                                             "Are you absolutely sure?")
                if not confirm:
                    return
            
            try:
                with open(selected_filepath[0], 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                if mode == "replace":
                    self.data_manager.data = import_data
                else:  # merge
                    # Merge employees
                    for emp_id, emp in import_data.get("employees", {}).items():
                        if emp_id not in self.data_manager.data["employees"]:
                            self.data_manager.data["employees"][emp_id] = emp
                    
                    # Merge time entries
                    existing_entries = {(e['employee_id'], e['clock_in']) for e in self.data_manager.data["time_entries"]}
                    for entry in import_data.get("time_entries", []):
                        if (entry['employee_id'], entry['clock_in']) not in existing_entries:
                            self.data_manager.data["time_entries"].append(entry)
                    
                    # Merge leave requests
                    existing_req_ids = {r['request_id'] for r in self.data_manager.data.get("leave_requests", [])}
                    for req in import_data.get("leave_requests", []):
                        if req['request_id'] not in existing_req_ids:
                            self.data_manager.data.get("leave_requests", []).append(req)
                    
                    # Merge departments
                    for dept in import_data.get("departments", []):
                        if dept not in self.data_manager.data.get("departments", []):
                            self.data_manager.data.setdefault("departments", []).append(dept)
                
                self.data_manager.save_data()
                self.refresh_all()
                
                emp_count = len(import_data.get("employees", {}))
                entry_count = len(import_data.get("time_entries", []))
                
                messagebox.showinfo("Import Successful", 
                                   f"Data imported successfully!\n\n" +
                                   f"Employees: {emp_count}\n" +
                                   f"Time Entries: {entry_count}\n\n" +
                                   f"Mode: {mode.upper()}")
                dialog.destroy()
                
            except json.JSONDecodeError:
                messagebox.showerror("Invalid File", "The selected file is not a valid JSON file.")
            except Exception as e:
                messagebox.showerror("Import Failed", f"Failed to import data:\n\n{str(e)}")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Browse...", command=browse_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Import", command=do_import).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    # ============= REPORTS MENU METHODS =============
    
    def quick_payroll_report(self):
        """Quickly generate payroll report for current period"""
        self.notebook.select(1)  # Switch to Payroll tab
        self.generate_payroll_report()
    
    def quick_attendance_report(self):
        """Quickly generate attendance report"""
        self.notebook.select(3)  # Switch to Reports tab
        self.report_type_combo.set("Attendance Report")
        self.on_report_type_changed()
    
    def quick_hours_summary(self):
        """Quickly generate hours summary"""
        self.notebook.select(3)  # Switch to Reports tab
        self.report_type_combo.set("Employee Hours Summary")
        self.on_report_type_changed()
        self.view_employee_report()
    
    def leave_requests_summary(self):
        """Show summary of all leave requests"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Leave Requests Summary")
        dialog.geometry("800x600")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Leave Requests Summary", style='Header.TLabel').pack(pady=(0, 10))
        
        text = scrolledtext.ScrolledText(frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color)
        text.pack(fill=tk.BOTH, expand=True)
        
        leave_requests = self.data_manager.data.get("leave_requests", [])
        
        report = f"{'='*100}\n"
        report += "ALL LEAVE REQUESTS\n"
        report += f"{'='*100}\n\n"
        report += f"{'ID':<5} {'Employee':<20} {'Type':<10} {'Start':<12} {'End':<12} {'Hours':<8} {'Status':<10}\n"
        report += f"{'-'*100}\n"
        
        for req in sorted(leave_requests, key=lambda x: x.get('submitted_date', ''), reverse=True):
            report += f"{req['request_id']:<5} {req['employee_name']:<20} {req['leave_type']:<10} {req['start_date']:<12} {req['end_date']:<12} {req['hours']:<8.1f} {req['status']:<10}\n"
        
        text.insert('1.0', report)
        text.config(state='disabled')
    
    def department_report(self):
        """Show report by department"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Department Report")
        dialog.geometry("800x600")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Department Report", style='Header.TLabel').pack(pady=(0, 10))
        
        text = scrolledtext.ScrolledText(frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color)
        text.pack(fill=tk.BOTH, expand=True)
        
        employees = self.data_manager.get_all_employees()
        dept_data = {}
        
        for emp_id, emp in employees.items():
            dept = emp.get('department', 'No Department')
            if dept not in dept_data:
                dept_data[dept] = []
            dept_data[dept].append((emp['name'], emp.get('job_title', 'N/A')))
        
        report = f"{'='*80}\n"
        report += "DEPARTMENT REPORT\n"
        report += f"{'='*80}\n\n"
        
        for dept, emp_list in sorted(dept_data.items()):
            report += f"\n{dept} ({len(emp_list)} employees)\n"
            report += f"{'-'*40}\n"
            for name, title in sorted(emp_list):
                report += f"  {name:<30} {title}\n"
        
        text.insert('1.0', report)
        text.config(state='disabled')
    
    # ============= TOOLS MENU METHODS =============
    
    def application_settings(self):
        """Application settings dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Application Settings")
        dialog.geometry("750x850")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Application Settings", style='Header.TLabel').pack(pady=(0, 20))
        
        # Get current settings
        settings = self.data_manager.data.get("settings", {})
        company_info = settings.get("company_info", {})
        
        # Create scrollable frame for settings
        canvas = tk.Canvas(frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Company Information Section
        ttk.Label(scrollable_frame, text="Company Information (for Invoices):", font=('Segoe UI', 11, 'bold'), foreground=self.accent_color).pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Company Name:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        company_name_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_name_entry.insert(0, company_info.get("name", "YOUR COMPANY NAME"))
        company_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Street Address:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        company_street_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_street_entry.insert(0, company_info.get("street", "123 Business Street"))
        company_street_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Street Address 2 (optional):", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        company_street2_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_street2_entry.insert(0, company_info.get("street2", ""))
        company_street2_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="City:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        company_city_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_city_entry.insert(0, company_info.get("city", "City"))
        company_city_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="State:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        company_state_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_state_entry.insert(0, company_info.get("state", "State"))
        company_state_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="ZIP Code:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        company_zip_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_zip_entry.insert(0, company_info.get("zip", "12345"))
        company_zip_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Phone:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        company_phone_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_phone_entry.insert(0, company_info.get("phone", "(555) 123-4567"))
        company_phone_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Email:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        company_email_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_email_entry.insert(0, company_info.get("email", "email@company.com"))
        company_email_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Website:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        company_website_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        company_website_entry.insert(0, company_info.get("website", "www.company.com"))
        company_website_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Separator
        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Payroll Settings Section
        ttk.Label(scrollable_frame, text="Payroll Settings:", font=('Segoe UI', 11, 'bold'), foreground=self.accent_color).pack(anchor=tk.W, pady=(0, 10))
        
        # Overtime settings
        ttk.Label(scrollable_frame, text="Default Overtime Rate (multiplier):", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        ttk.Label(scrollable_frame, text="Default Overtime Rate (multiplier):", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        ot_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        ot_entry.insert(0, str(settings.get("overtime_rate", 1.5)))
        ot_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Overtime Hours Threshold:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        hours_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        hours_entry.insert(0, str(settings.get("overtime_threshold", 40)))
        hours_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Separator
        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Leave Management Settings Section
        ttk.Label(scrollable_frame, text="Leave Management Settings:", font=('Segoe UI', 11, 'bold'), foreground=self.accent_color).pack(anchor=tk.W, pady=(0, 10))
        
        # PTO accrual settings
        ttk.Label(scrollable_frame, text="Annual PTO Hours Accrual:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        pto_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        pto_entry.insert(0, str(settings.get("pto_accrual", 80)))
        pto_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Annual Sick Leave Hours:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        sick_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        sick_entry.insert(0, str(settings.get("sick_accrual", 40)))
        sick_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(scrollable_frame, text="Annual Vacation Hours:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        vac_entry = ttk.Entry(scrollable_frame, font=('Segoe UI', 10))
        vac_entry.insert(0, str(settings.get("vacation_accrual", 80)))
        vac_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Separator
        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Other Settings Section
        ttk.Label(scrollable_frame, text="Other Settings:", font=('Segoe UI', 11, 'bold'), foreground=self.accent_color).pack(anchor=tk.W, pady=(0, 10))
        
        # Auto-backup setting
        backup_var = tk.BooleanVar(value=settings.get("auto_backup", True))
        ttk.Checkbutton(scrollable_frame, text="Enable automatic daily backup", variable=backup_var, style='Accent.TCheckbutton').pack(anchor=tk.W, pady=10)
        
        def save_settings():
            try:
                # Validate numeric inputs
                ot_rate = float(ot_entry.get())
                ot_threshold = int(hours_entry.get())
                pto_hours = int(pto_entry.get())
                sick_hours = int(sick_entry.get())
                vac_hours = int(vac_entry.get())
                
                # Update settings with company info
                self.data_manager.data["settings"] = {
                    "overtime_rate": ot_rate,
                    "overtime_threshold": ot_threshold,
                    "pto_accrual": pto_hours,
                    "sick_accrual": sick_hours,
                    "vacation_accrual": vac_hours,
                    "auto_backup": backup_var.get(),
                    "company_info": {
                        "name": company_name_entry.get(),
                        "street": company_street_entry.get(),
                        "street2": company_street2_entry.get(),
                        "city": company_city_entry.get(),
                        "state": company_state_entry.get(),
                        "zip": company_zip_entry.get(),
                        "phone": company_phone_entry.get(),
                        "email": company_email_entry.get(),
                        "website": company_website_entry.get()
                    }
                }
                
                self.data_manager.save_data()
                messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values.")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Save Settings", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def backup_restore_db(self):
        """Backup and restore database"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Backup/Restore Database")
        dialog.geometry("700x550")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Backup/Restore Database", style='Header.TLabel').pack(pady=(0, 20))
        
        def create_backup():
            self.backup_data()
            update_backup_list()
        
        def restore_backup():
            file_path = filedialog.askopenfilename(
                title="Select Backup File",
                initialdir=str(get_backup_dir()),
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if file_path:
                do_restore(file_path)
        
        def restore_selected():
            selection = backup_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a backup file to restore.")
                return
            
            filename = backup_listbox.get(selection[0])
            file_path = get_backup_dir() / filename
            do_restore(file_path)
        
        def do_restore(file_path):
            if not os.path.exists(file_path):
                messagebox.showerror("File Not Found", f"Backup file not found:\n{file_path}")
                return
            
            response = messagebox.askyesno(
                "Confirm Restore",
                "This will replace all current data with the backup.\n\n" +
                "Current data will be backed up first.\n\nContinue?"
            )
            
            if response:
                try:
                    # Backup current data first
                    self.backup_data()
                    
                    # Load backup data
                    with open(file_path, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    # Validate backup data
                    if not isinstance(backup_data, dict):
                        raise ValueError("Invalid backup file format")
                    
                    # Restore data
                    self.data_manager.data = backup_data
                    self.data_manager.save_data()
                    
                    messagebox.showinfo(
                        "Restore Successful", 
                        "Database restored successfully!\n\n" +
                        f"Restored from: {os.path.basename(file_path)}\n\n" +
                        "Please restart the application for all changes to take effect."
                    )
                    dialog.destroy()
                except json.JSONDecodeError as e:
                    messagebox.showerror("Invalid Backup", f"Backup file is corrupted or invalid:\n\n{str(e)}")
                except Exception as e:
                    messagebox.showerror("Restore Failed", f"Failed to restore backup:\n\n{str(e)}")
        
        def update_backup_list():
            backup_listbox.delete(0, tk.END)
            backup_dir = get_backup_dir()
            if backup_dir.exists():
                backups = sorted(backup_dir.glob("*.json"), reverse=True)
                for backup in backups:
                    backup_listbox.insert(tk.END, backup.name)
        
        ttk.Button(frame, text="Create New Backup", command=create_backup).pack(pady=10, fill=tk.X)
        ttk.Button(frame, text="Browse for Backup...", command=restore_backup).pack(pady=10, fill=tk.X)
        
        ttk.Label(frame, text="Available Backups:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        backup_listbox = tk.Listbox(frame, font=('Segoe UI', 9), bg='#34495e', fg=self.fg_color, height=8)
        backup_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        update_backup_list()
        
        btn_frame2 = ttk.Frame(frame)
        btn_frame2.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame2, text="Restore Selected", command=restore_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Refresh List", command=update_backup_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def clear_old_data(self):
        """Clear old time entries"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Clear Old Data")
        dialog.geometry("600x450")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Clear Old Data", style='Header.TLabel').pack(pady=(0, 20))
        
        ttk.Label(frame, text="Remove data older than (days):", font=('Segoe UI', 10)).pack(anchor=tk.W, pady=5)
        days_entry = ttk.Entry(frame, font=('Segoe UI', 10))
        days_entry.insert(0, "365")
        days_entry.pack(fill=tk.X, pady=(0, 10))
        
        info_label = ttk.Label(frame, text="", font=('Segoe UI', 9), foreground='#95a5a6')
        info_label.pack(pady=10)
        
        def count_old_entries():
            try:
                days = int(days_entry.get())
                cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                time_entries = self.data_manager.data.get("time_entries", [])
                old_entries = [e for e in time_entries if e.get('date', '') < cutoff_date]
                
                info_label.config(text=f"Found {len(old_entries)} entries older than {days} days")
            except ValueError:
                info_label.config(text="Please enter a valid number of days")
        
        def clear_data():
            try:
                days = int(days_entry.get())
                cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                response = messagebox.askyesno(
                    "Confirm Clear",
                    f"This will permanently remove all time entries older than {days} days.\n\n" +
                    "A backup will be created first.\n\nContinue?"
                )
                
                if response:
                    # Create backup first
                    self.backup_data()
                    
                    # Remove old entries
                    time_entries = self.data_manager.data.get("time_entries", [])
                    original_count = len(time_entries)
                    self.data_manager.data["time_entries"] = [e for e in time_entries if e.get('date', '') >= cutoff_date]
                    removed_count = original_count - len(self.data_manager.data["time_entries"])
                    
                    self.data_manager.save_data()
                    
                    messagebox.showinfo(
                        "Data Cleared",
                        f"Successfully removed {removed_count} old time entries.\n\n" +
                        f"Backup created before deletion."
                    )
                    dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number of days.")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Count Old Entries", command=count_old_entries).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Data", command=clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def recalculate_balances(self):
        """Recalculate all PTO balances"""
        response = messagebox.askyesno(
            "Recalculate Balances",
            "This will recalculate all employee leave balances based on:\n\n" +
            "- Hire date\n" +
            "- Approved leave requests\n" +
            "- Current accrual settings\n\n" +
            "Continue?"
        )
        
        if response:
            settings = self.data_manager.data.get("settings", {})
            pto_accrual = settings.get("pto_accrual", 80)
            sick_accrual = settings.get("sick_accrual", 40)
            vacation_accrual = settings.get("vacation_accrual", 80)
            
            employees = self.data_manager.get_all_employees()
            leave_requests = self.data_manager.data.get("leave_requests", [])
            
            updated_count = 0
            
            for emp_id, emp in employees.items():
                # Calculate time employed (in years)
                hire_date_str = emp.get('hire_date', '')
                if hire_date_str:
                    try:
                        hire_date = datetime.strptime(hire_date_str, '%m/%d/%Y')
                        years_employed = (datetime.now() - hire_date).days / 365.25
                    except:
                        years_employed = 1
                else:
                    years_employed = 1
                
                # Set base balances based on accrual
                emp['pto_balance'] = pto_accrual * years_employed
                emp['sick_balance'] = sick_accrual * years_employed
                emp['vacation_balance'] = vacation_accrual * years_employed
                
                # Subtract approved leave
                for req in leave_requests:
                    if req['employee_id'] == emp_id and req['status'] == 'Approved':
                        leave_type = req['leave_type']
                        hours = req['hours']
                        
                        if leave_type == 'PTO':
                            emp['pto_balance'] -= hours
                        elif leave_type == 'Sick Leave':
                            emp['sick_balance'] -= hours
                        elif leave_type == 'Vacation':
                            emp['vacation_balance'] -= hours
                
                # Ensure balances aren't negative
                emp['pto_balance'] = max(0, emp['pto_balance'])
                emp['sick_balance'] = max(0, emp['sick_balance'])
                emp['vacation_balance'] = max(0, emp['vacation_balance'])
                
                updated_count += 1
            
            self.data_manager.save_data()
            messagebox.showinfo(
                "Recalculation Complete",
                f"Successfully recalculated balances for {updated_count} employees.\n\n" +
                f"PTO Accrual: {pto_accrual} hours/year\n" +
                f"Sick Leave: {sick_accrual} hours/year\n" +
                f"Vacation: {vacation_accrual} hours/year"
            )
    
    def manage_departments(self):
        """Manage department list"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Departments")
        dialog.geometry("650x550")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Manage Departments", style='Header.TLabel').pack(pady=(0, 10))
        
        # Ensure departments list exists
        if "departments" not in self.data_manager.data:
            self.data_manager.data["departments"] = ["Administration", "Operations", "Sales", "IT", "HR"]
            self.data_manager.save_data()
        
        listbox = tk.Listbox(frame, font=('Segoe UI', 10), bg='#34495e', fg=self.fg_color, selectmode=tk.SINGLE)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        def refresh_list():
            listbox.delete(0, tk.END)
            for dept in self.data_manager.data.get("departments", []):
                listbox.insert(tk.END, dept)
        
        def add_department():
            dept_name = simpledialog.askstring("Add Department", "Enter department name:", parent=dialog)
            if dept_name:
                dept_name = dept_name.strip()
                if dept_name:
                    if dept_name not in self.data_manager.data["departments"]:
                        self.data_manager.data["departments"].append(dept_name)
                        self.data_manager.data["departments"].sort()
                        self.data_manager.save_data()
                        refresh_list()
                        messagebox.showinfo("Success", f"Department '{dept_name}' added successfully.")
                    else:
                        messagebox.showwarning("Duplicate", "This department already exists.")
        
        def edit_department():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a department to edit.")
                return
            
            old_name = listbox.get(selection[0])
            new_name = simpledialog.askstring("Edit Department", "Enter new department name:", 
                                             initialvalue=old_name, parent=dialog)
            
            if new_name and new_name != old_name:
                new_name = new_name.strip()
                if new_name:
                    if new_name not in self.data_manager.data["departments"]:
                        # Update department in list
                        idx = self.data_manager.data["departments"].index(old_name)
                        self.data_manager.data["departments"][idx] = new_name
                        self.data_manager.data["departments"].sort()
                        
                        # Update all employees with this department
                        employees = self.data_manager.get_all_employees()
                        for emp_id, emp in employees.items():
                            if emp.get('department') == old_name:
                                emp['department'] = new_name
                        
                        self.data_manager.save_data()
                        refresh_list()
                        messagebox.showinfo("Success", f"Department renamed to '{new_name}'.")
                    else:
                        messagebox.showwarning("Duplicate", "This department name already exists.")
        
        def remove_department():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a department to remove.")
                return
            
            dept_name = listbox.get(selection[0])
            
            # Check if any employees use this department
            employees = self.data_manager.get_all_employees()
            emp_count = sum(1 for emp in employees.values() if emp.get('department') == dept_name)
            
            if emp_count > 0:
                response = messagebox.askyesno(
                    "Department In Use",
                    f"This department is assigned to {emp_count} employee(s).\n\n" +
                    "Their department will be set to 'No Department'.\n\nContinue?"
                )
                if not response:
                    return
                
                # Update employees
                for emp in employees.values():
                    if emp.get('department') == dept_name:
                        emp['department'] = 'No Department'
            
            self.data_manager.data["departments"].remove(dept_name)
            self.data_manager.save_data()
            refresh_list()
            messagebox.showinfo("Success", f"Department '{dept_name}' removed.")
        
        refresh_list()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add", command=add_department).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit", command=edit_department).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove", command=remove_department).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    # ============= ADMIN MENU METHODS =============
    
    def user_management(self):
        """Manage users and permissions"""
        dialog = tk.Toplevel(self.root)
        dialog.title("User Management")
        dialog.geometry("800x600")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="User Management System", style='Header.TLabel').pack(pady=(0, 10))
        
        # Initialize users if not exists
        if "users" not in self.data_manager.data:
            self.data_manager.data["users"] = [
                {"username": "admin", "role": "Administrator", "email": "admin@timeclock.com", "active": True},
                {"username": "manager", "role": "Manager", "email": "manager@timeclock.com", "active": True}
            ]
            self.data_manager.save_data()
        
        # User list
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        listbox = tk.Listbox(list_frame, font=('Segoe UI', 10), bg='#34495e', fg=self.fg_color, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        def refresh_users():
            listbox.delete(0, tk.END)
            for user in self.data_manager.data.get("users", []):
                status = "✓" if user.get("active", True) else "✗"
                listbox.insert(tk.END, f"{status} {user['username']:<20} {user['role']:<15} {user.get('email', '')}")
        
        def add_user():
            username = simpledialog.askstring("Add User", "Enter username:", parent=dialog)
            if username:
                username = username.strip()
                if any(u['username'] == username for u in self.data_manager.data["users"]):
                    messagebox.showerror("Error", "Username already exists.")
                    return
                
                email = simpledialog.askstring("Add User", "Enter email:", parent=dialog)
                role_dialog = tk.Toplevel(dialog)
                role_dialog.title("Select Role")
                role_dialog.geometry("300x200")
                role_dialog.configure(bg=self.bg_color)
                role_dialog.transient(dialog)
                
                role_var = tk.StringVar(value="Employee")
                ttk.Label(role_dialog, text="Select Role:").pack(pady=10)
                for role in ["Administrator", "Manager", "Employee"]:
                    ttk.Radiobutton(role_dialog, text=role, variable=role_var, value=role).pack(anchor=tk.W, padx=20)
                
                def save_user():
                    self.data_manager.data["users"].append({
                        "username": username,
                        "role": role_var.get(),
                        "email": email or "",
                        "active": True
                    })
                    self.data_manager.save_data()
                    refresh_users()
                    role_dialog.destroy()
                    messagebox.showinfo("Success", f"User '{username}' added successfully.")
                
                ttk.Button(role_dialog, text="Save", command=save_user).pack(pady=10)
        
        def toggle_status():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a user.")
                return
            
            user = self.data_manager.data["users"][selection[0]]
            user["active"] = not user.get("active", True)
            self.data_manager.save_data()
            refresh_users()
            status = "activated" if user["active"] else "deactivated"
            messagebox.showinfo("Success", f"User '{user['username']}' {status}.")
        
        def remove_user():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a user.")
                return
            
            user = self.data_manager.data["users"][selection[0]]
            if messagebox.askyesno("Confirm", f"Remove user '{user['username']}'?"):
                self.data_manager.data["users"].pop(selection[0])
                self.data_manager.save_data()
                refresh_users()
                messagebox.showinfo("Success", "User removed.")
        
        refresh_users()
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Add User", command=add_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Toggle Active/Inactive", command=toggle_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove User", command=remove_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def audit_log(self):
        """View system audit log"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Audit Log")
        dialog.geometry("1200x750")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="System Audit Log", style='Header.TLabel').pack(pady=(0, 10))
        
        # Filter frame
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
        filter_var = ttk.Combobox(filter_frame, state='readonly', width=20, values=["All Events", "Clock In/Out", "Employee Changes", "Leave Requests", "System Changes"])
        filter_var.pack(side=tk.LEFT, padx=5)
        filter_var.current(0)
        
        ttk.Label(filter_frame, text="Show:").pack(side=tk.LEFT, padx=(20, 5))
        limit_var = ttk.Combobox(filter_frame, state='readonly', width=10, values=["50", "100", "200", "500", "All"])
        limit_var.pack(side=tk.LEFT, padx=5)
        limit_var.current(1)
        
        text = scrolledtext.ScrolledText(frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Add horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(text, orient=tk.HORIZONTAL, command=text.xview)
        text.configure(xscrollcommand=h_scrollbar.set)
        
        def parse_datetime(dt_string):
            """Parse datetime string to datetime object"""
            try:
                # Try ISO format first (from clock_in/clock_out)
                return datetime.fromisoformat(dt_string)
            except:
                try:
                    # Try standard format
                    return datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
                except:
                    # Return current time if parsing fails
                    return datetime.now()
        
        def generate_log():
            text.delete('1.0', tk.END)
            filter_type = filter_var.get()
            limit = limit_var.get()
            
            # Collect all log entries with timestamps
            log_entries = []
            
            # System startup
            log_entries.append({
                'timestamp': datetime.now(),
                'type': 'SYSTEM',
                'message': 'System accessed',
                'category': 'System Changes'
            })
            
            # Clock events
            time_entries = self.data_manager.data.get("time_entries", [])
            for entry in time_entries:
                emp_id = entry.get("employee_id")
                emp = self.data_manager.get_employee(emp_id)
                if emp:
                    # Clock in event
                    clock_in_time = parse_datetime(entry['clock_in'])
                    log_entries.append({
                        'timestamp': clock_in_time,
                        'type': 'CLOCK_IN',
                        'message': f"{emp['name']} (ID: {emp_id}) clocked in",
                        'category': 'Clock In/Out'
                    })
                    
                    # Clock out event
                    if entry.get('clock_out'):
                        clock_out_time = parse_datetime(entry['clock_out'])
                        log_entries.append({
                            'timestamp': clock_out_time,
                            'type': 'CLOCK_OUT',
                            'message': f"{emp['name']} (ID: {emp_id}) clocked out - {entry.get('hours_worked', 0):.2f} hours worked",
                            'category': 'Clock In/Out'
                        })
            
            # Leave requests
            leave_requests = self.data_manager.data.get("leave_requests", [])
            for req in leave_requests:
                submitted_time = parse_datetime(req.get('submitted_date', datetime.now().isoformat()))
                log_entries.append({
                    'timestamp': submitted_time,
                    'type': 'LEAVE_REQUEST',
                    'message': f"{req['employee_name']} requested {req['leave_type']} leave from {req['start_date']} to {req['end_date']} - Status: {req['status']}",
                    'category': 'Leave Requests'
                })
            
            # Employee changes (from data)
            employees = self.data_manager.get_all_employees()
            for emp_id, emp in employees.items():
                if emp.get('hire_date'):
                    try:
                        hire_time = datetime.strptime(emp['hire_date'], '%m/%d/%Y')
                        log_entries.append({
                            'timestamp': hire_time,
                            'type': 'EMPLOYEE_ADDED',
                            'message': f"Employee {emp['name']} (ID: {emp_id}) hired - Department: {emp.get('department', 'N/A')}",
                            'category': 'Employee Changes'
                        })
                    except:
                        pass
            
            # User management events
            users = self.data_manager.data.get("users", [])
            for user in users:
                log_entries.append({
                    'timestamp': datetime.now() - timedelta(days=30),  # Simulated date
                    'type': 'USER_CREATED',
                    'message': f"User '{user['username']}' created with role: {user['role']} - Active: {user.get('active', True)}",
                    'category': 'System Changes'
                })
            
            # Apply filter
            if filter_type != "All Events":
                log_entries = [e for e in log_entries if e['category'] == filter_type]
            
            # Sort by timestamp (most recent first)
            log_entries.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Apply limit
            if limit != "All":
                log_entries = log_entries[:int(limit)]
            
            # Display header
            header = f"{'TIMESTAMP':<20} {'TYPE':<20} {'EVENT DESCRIPTION'}\n"
            header += "=" * 120 + "\n"
            text.insert('1.0', header)
            
            # Display entries
            for entry in log_entries:
                timestamp_str = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                line = f"{timestamp_str:<20} {entry['type']:<20} {entry['message']}\n"
                text.insert(tk.END, line)
            
            # Summary
            summary = f"\n{'=' * 120}\n"
            summary += f"Total Events: {len(log_entries)}"
            if filter_type != "All Events":
                summary += f" (Filtered by: {filter_type})"
            summary += "\n"
            text.insert(tk.END, summary)
        
        def apply_filter(event=None):
            generate_log()
        
        filter_var.bind('<<ComboboxSelected>>', apply_filter)
        limit_var.bind('<<ComboboxSelected>>', apply_filter)
        
        def export_log():
            try:
                filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w') as f:
                    f.write(text.get('1.0', tk.END))
                messagebox.showinfo("Export Successful", f"Audit log exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export log:\n\n{str(e)}")
        
        generate_log()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Refresh", command=generate_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export Log", command=export_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Filters", command=lambda: (filter_var.current(0), limit_var.current(1), generate_log())).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def system_configuration(self):
        """System configuration settings"""
        dialog = tk.Toplevel(self.root)
        dialog.title("System Configuration")
        dialog.geometry("700x600")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="System Configuration", style='Header.TLabel').pack(pady=(0, 20))
        
        # Initialize system config if not exists
        if "system_config" not in self.data_manager.data:
            self.data_manager.data["system_config"] = {
                "company_name": "My Company",
                "time_zone": "Eastern",
                "date_format": "MM/DD/YYYY",
                "currency": "USD",
                "rounding_method": "15 minutes",
                "email_notifications": True,
                "backup_frequency": "Daily"
            }
            self.data_manager.save_data()
        
        config = self.data_manager.data["system_config"]
        
        # Company Name
        ttk.Label(frame, text="Company Name:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        company_entry = ttk.Entry(frame, width=40, font=('Segoe UI', 10))
        company_entry.insert(0, config.get("company_name", ""))
        company_entry.pack(anchor=tk.W, pady=(0, 10))
        
        # Time Zone
        ttk.Label(frame, text="Time Zone:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        tz_combo = ttk.Combobox(frame, state='readonly', width=38, values=["Eastern", "Central", "Mountain", "Pacific", "Alaska", "Hawaii"])
        tz_combo.set(config.get("time_zone", "Eastern"))
        tz_combo.pack(anchor=tk.W, pady=(0, 10))
        
        # Date Format
        ttk.Label(frame, text="Date Format:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        date_combo = ttk.Combobox(frame, state='readonly', width=38, values=["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        date_combo.set(config.get("date_format", "MM/DD/YYYY"))
        date_combo.pack(anchor=tk.W, pady=(0, 10))
        
        # Currency
        ttk.Label(frame, text="Currency:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        curr_combo = ttk.Combobox(frame, state='readonly', width=38, values=["USD", "EUR", "GBP", "CAD", "AUD"])
        curr_combo.set(config.get("currency", "USD"))
        curr_combo.pack(anchor=tk.W, pady=(0, 10))
        
        # Time Rounding
        ttk.Label(frame, text="Time Rounding:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        round_combo = ttk.Combobox(frame, state='readonly', width=38, values=["No rounding", "5 minutes", "10 minutes", "15 minutes", "30 minutes"])
        round_combo.set(config.get("rounding_method", "15 minutes"))
        round_combo.pack(anchor=tk.W, pady=(0, 10))
        
        # Email Notifications
        email_var = tk.BooleanVar(value=config.get("email_notifications", True))
        ttk.Checkbutton(frame, text="Enable Email Notifications", variable=email_var).pack(anchor=tk.W, pady=10)
        
        # Backup Frequency
        ttk.Label(frame, text="Backup Frequency:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        backup_combo = ttk.Combobox(frame, state='readonly', width=38, values=["Hourly", "Daily", "Weekly", "Manual"])
        backup_combo.set(config.get("backup_frequency", "Daily"))
        backup_combo.pack(anchor=tk.W, pady=(0, 10))
        
        def save_config():
            self.data_manager.data["system_config"] = {
                "company_name": company_entry.get().strip(),
                "time_zone": tz_combo.get(),
                "date_format": date_combo.get(),
                "currency": curr_combo.get(),
                "rounding_method": round_combo.get(),
                "email_notifications": email_var.get(),
                "backup_frequency": backup_combo.get()
            }
            self.data_manager.save_data()
            messagebox.showinfo("Success", "System configuration saved successfully.")
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Save Configuration", command=save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def holiday_calendar(self):
        """Manage company holidays"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Holiday Calendar")
        dialog.geometry("800x650")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Company Holiday Calendar", style='Header.TLabel').pack(pady=(0, 10))
        
        # Initialize holidays if not exists
        if "holidays" not in self.data_manager.data:
            self.data_manager.data["holidays"] = [
                {"date": "01/01/2025", "name": "New Year's Day"},
                {"date": "05/26/2025", "name": "Memorial Day"},
                {"date": "07/04/2025", "name": "Independence Day"},
                {"date": "09/01/2025", "name": "Labor Day"},
                {"date": "11/27/2025", "name": "Thanksgiving"},
                {"date": "12/25/2025", "name": "Christmas Day"}
            ]
            self.data_manager.save_data()
        
        listbox = tk.Listbox(frame, font=('Segoe UI', 10), bg='#34495e', fg=self.fg_color, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        def refresh_holidays():
            listbox.delete(0, tk.END)
            holidays = sorted(self.data_manager.data.get("holidays", []), key=lambda x: x['date'])
            for holiday in holidays:
                listbox.insert(tk.END, f"{holiday['date']:<15} {holiday['name']}")
        
        def add_holiday():
            add_dialog = tk.Toplevel(dialog)
            add_dialog.title("Add Holiday")
            add_dialog.geometry("400x250")
            add_dialog.configure(bg=self.bg_color)
            add_dialog.transient(dialog)
            
            add_frame = ttk.Frame(add_dialog, padding="20")
            add_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(add_frame, text="Holiday Name:").pack(anchor=tk.W, pady=5)
            name_entry = ttk.Entry(add_frame, width=30)
            name_entry.pack(pady=(0, 10))
            
            ttk.Label(add_frame, text="Date:").pack(anchor=tk.W, pady=5)
            date_picker = DateEntry(add_frame, width=28, background='darkblue', foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy', firstweekday='sunday')
            date_picker.pack(pady=(0, 10))
            
            def save_holiday():
                name = name_entry.get().strip()
                date = date_picker.get_date().strftime('%m/%d/%Y')
                
                if not name:
                    messagebox.showerror("Error", "Please enter a holiday name.")
                    return
                
                self.data_manager.data["holidays"].append({"date": date, "name": name})
                self.data_manager.save_data()
                refresh_holidays()
                add_dialog.destroy()
                messagebox.showinfo("Success", f"Holiday '{name}' added.")
            
            ttk.Button(add_frame, text="Save", command=save_holiday).pack(pady=10)
        
        def remove_holiday():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a holiday to remove.")
                return
            
            holidays = sorted(self.data_manager.data.get("holidays", []), key=lambda x: x['date'])
            holiday = holidays[selection[0]]
            
            if messagebox.askyesno("Confirm", f"Remove '{holiday['name']}' on {holiday['date']}?"):
                self.data_manager.data["holidays"].remove(holiday)
                self.data_manager.save_data()
                refresh_holidays()
                messagebox.showinfo("Success", "Holiday removed.")
        
        def edit_holiday():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a holiday to edit.")
                return
            
            holidays = sorted(self.data_manager.data.get("holidays", []), key=lambda x: x['date'])
            holiday = holidays[selection[0]]
            
            new_name = simpledialog.askstring("Edit Holiday", "Enter new name:", initialvalue=holiday['name'], parent=dialog)
            if new_name:
                holiday['name'] = new_name.strip()
                self.data_manager.save_data()
                refresh_holidays()
                messagebox.showinfo("Success", "Holiday updated.")
        
        refresh_holidays()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Add Holiday", command=add_holiday).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Holiday", command=edit_holiday).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove Holiday", command=remove_holiday).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    # ============= HELP MENU METHODS =============
    
    def user_guide(self):
        """Show user guide"""
        dialog = tk.Toplevel(self.root)
        dialog.title("User Guide")
        dialog.geometry("900x700")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Time Clock System - User Guide", style='Header.TLabel').pack(pady=(0, 10))
        
        text = scrolledtext.ScrolledText(frame, font=('Segoe UI', 10), bg='#34495e', fg=self.fg_color, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        guide = """
TIME CLOCK SYSTEM USER GUIDE

1. CLOCKING IN/OUT
   - Select your name from the dropdown
   - Click "CLOCK IN" to start your shift
   - Click "CLOCK OUT" to end your shift

2. BREAKS
   - Click "START BREAK" to begin a break
   - Select Paid or Unpaid break type
   - Click "END BREAK" when done

3. PAYROLL
   - Select date range
   - Click "Generate Report" to view payroll
   - Click "Export to CSV" to save report

4. LEAVE MANAGEMENT
   - Select employee and leave type
   - Choose dates and enter hours
   - Submit request for approval
   - Managers can approve/deny requests

5. REPORTS
   - View various reports from Reports tab
   - Select report type and employee
   - Export reports as needed

6. EMPLOYEE MANAGEMENT
   - Add new employees
   - Update employee information
   - Adjust pay rates and PTO balances
        """
        
        text.insert('1.0', guide)
        text.config(state='disabled')
    
    def keyboard_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts = """
KEYBOARD SHORTCUTS

F1  - Help
F5  - Refresh Data
F12 - Quick Clock In/Out

Ctrl+P - Print Report
Ctrl+E - Export Data
Ctrl+B - Backup Data
Ctrl+Q - Exit Program

Alt+1 - Time Clock Tab
Alt+2 - Payroll Tab
Alt+3 - Leave Management Tab
Alt+4 - Reports Tab
Alt+5 - Employee Management Tab
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def check_updates(self):
        """Check for software updates"""
        repo = GITHUB_REPO.strip()
        if not repo or "/" not in repo:
            messagebox.showinfo(
                "Check for Updates",
                f"{APP_NAME} v{APP_VERSION}\n\n"
                "Automatic updates are not configured yet.\n\n"
                "Set GITHUB_REPO in time_clock_version.py to owner/repo\n"
                "to enable update checks from GitHub Releases."
            )
            return

        release_page = f"https://github.com/{repo}/releases"
        release_candidates = []

        for release_api in (
            f"https://api.github.com/repos/{repo}/releases/latest",
            f"https://api.github.com/repos/{repo}/releases?per_page=100",
        ):
            request = urllib.request.Request(
                release_api,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "TimeClockUpdateChecker"
                }
            )

            try:
                with urllib.request.urlopen(request, timeout=8) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError:
                continue
            except (urllib.error.URLError, TimeoutError):
                break
            except json.JSONDecodeError:
                break

            if isinstance(payload, list):
                release_candidates = [
                    release for release in payload
                    if not release.get("draft") and not release.get("prerelease")
                ]
                if release_candidates:
                    release_data = release_candidates[0]
                    break
            else:
                release_data = payload
                break
        else:
            release_data = None

        if not release_data:
            open_page = messagebox.askyesno(
                "Check for Updates",
                "GitHub did not return a published release for this repository.\n\n"
                "Open the GitHub Releases page instead?"
            )
            if open_page:
                webbrowser.open(release_page)
            return

        latest_tag = (release_data.get("tag_name") or "").strip()
        latest_version = latest_tag.lstrip("vV")
        release_url = release_data.get("html_url", f"https://github.com/{repo}/releases")

        if not latest_version:
            messagebox.showerror("Check for Updates", "Latest release is missing a version tag.")
            return

        if is_newer_version(latest_version, APP_VERSION):
            assets = release_data.get("assets") or []
            installer_asset = next(
                (
                    asset for asset in assets
                    if (asset.get("name") or "").lower().endswith(".exe")
                    and "setup" in (asset.get("name") or "").lower()
                ),
                None,
            )
            if installer_asset is None:
                installer_asset = next(
                    (asset for asset in assets if (asset.get("name") or "").lower().endswith(".exe")),
                    None,
                )

            action = messagebox.askyesnocancel(
                "Update Available",
                f"Current version: {APP_VERSION}\n"
                f"Latest version:  {latest_version}\n\n"
                "Yes: Download installer now\n"
                "No: Open release page\n"
                "Cancel: Do nothing"
            )

            if action is True:
                if installer_asset:
                    self.download_release_asset(installer_asset)
                else:
                    should_open = messagebox.askyesno(
                        "Installer Not Found",
                        "No installer (.exe) asset was found in this release.\n\n"
                        "Open the release page instead?"
                    )
                    if should_open:
                        webbrowser.open(release_url)
            elif action is False:
                webbrowser.open(release_url)
            return

        messagebox.showinfo(
            "Check for Updates",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "You are running the latest version."
        )

    def download_release_asset(self, asset: Dict):
        """Download a release asset to a user-selected location."""
        asset_name = asset.get("name") or "TimeClockSetup.exe"
        asset_url = asset.get("browser_download_url")
        if not asset_url:
            messagebox.showerror("Download Update", "The selected release asset has no download URL.")
            return

        default_dir = Path.home() / "Downloads"
        save_path = filedialog.asksaveasfilename(
            title="Save Installer As",
            initialdir=str(default_dir),
            initialfile=asset_name,
            defaultextension=".exe",
            filetypes=[("Installer", "*.exe"), ("All Files", "*.*")],
        )
        if not save_path:
            return

        request = urllib.request.Request(
            asset_url,
            headers={
                "Accept": "application/octet-stream",
                "User-Agent": "TimeClockUpdateChecker"
            }
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response, open(save_path, "wb") as output_file:
                shutil.copyfileobj(response, output_file)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            messagebox.showerror("Download Update", f"Could not download installer:\n{exc}")
            return

        should_run = messagebox.askyesno(
            "Download Complete",
            f"Installer downloaded to:\n{save_path}\n\nRun it now?"
        )
        if should_run:
            try:
                os.startfile(save_path)
            except OSError as exc:
                messagebox.showerror("Run Installer", f"Could not launch installer:\n{exc}")
    
    def about_dialog(self):
        """Show about dialog"""
        messagebox.showinfo("About Time Clock System", 
                           f"{APP_NAME} v{APP_VERSION}\n\n" +
                           "Enterprise Time and Attendance Management\n\n" +
                           "Features:\n" +
                           "• Employee Time Tracking\n" +
                           "• Payroll Management\n" +
                           "• Leave Request System\n" +
                           "• Comprehensive Reporting\n\n" +
                           "Created by:\n" +
                           "Judson M. Fitzpatrick\n" +
                           "Irish Coder Programming\n\n" +
                           "© 2025 Time Clock Systems")
    
    def exit_program(self):
        """Exit the application with option to backup data"""
        response = messagebox.askyesnocancel(
            "Exit Application",
            "Would you like to backup your data before exiting?\n\n" +
            "Yes - Backup and exit\n" +
            "No - Exit without backup\n" +
            "Cancel - Return to application"
        )
        
        if response is None:  # Cancel was clicked
            return
        elif response:  # Yes was clicked
            self.backup_data()
        
        # Exit the application (response is True or False, but not None)
        self.root.quit()
    
    # ============= PROJECT MANAGEMENT METHODS =============
    
    def refresh_project_list(self):
        """Refresh the projects list display"""
        self.project_list_text.delete('1.0', tk.END)
        
        projects = self.data_manager.data.get("projects", [])
        
        if not projects:
            self.project_list_text.insert('1.0', "No projects found.\n\nClick '➕ Add Project' to add your first project.")
            return
        
        # Get time tracking data for each project
        time_entries = self.data_manager.data.get("time_entries", [])
        project_stats = {}
        
        for entry in time_entries:
            if entry.get("clock_out") and entry.get("project"):
                project = entry["project"]
                if project not in project_stats:
                    project_stats[project] = {"total_hours": 0, "employees": set(), "entry_count": 0}
                
                project_stats[project]["total_hours"] += entry.get("hours_worked", 0)
                project_stats[project]["employees"].add(entry.get("employee_id"))
                project_stats[project]["entry_count"] += 1
        
        # Header
        self.project_list_text.insert(tk.END, f"{'='*100}\n")
        self.project_list_text.insert(tk.END, f"{'PROJECT DIRECTORY':^100}\n")
        self.project_list_text.insert(tk.END, f"{'='*100}\n\n")
        
        # Display each project
        for i, project in enumerate(projects, 1):
            self.project_list_text.insert(tk.END, f"{'─'*100}\n")
            self.project_list_text.insert(tk.END, f"{i}. {project}\n")
            self.project_list_text.insert(tk.END, f"{'─'*100}\n")
            
            if project in project_stats:
                stats = project_stats[project]
                self.project_list_text.insert(tk.END, f"   Total Hours Worked: {stats['total_hours']:.2f}\n")
                self.project_list_text.insert(tk.END, f"   Number of Employees: {len(stats['employees'])}\n")
                self.project_list_text.insert(tk.END, f"   Number of Entries: {stats['entry_count']}\n")
            else:
                self.project_list_text.insert(tk.END, f"   No time entries recorded yet\n")
            
            self.project_list_text.insert(tk.END, "\n")
        
        self.project_list_text.insert(tk.END, f"{'='*100}\n")
        self.project_list_text.insert(tk.END, f"Total Projects: {len(projects)}\n")
        self.project_list_text.insert(tk.END, f"{'='*100}\n")
    
    def add_project_dialog(self):
        """Add a new project"""
        project_name = simpledialog.askstring("Add Project", "Enter project name:", parent=self.root)
        
        if project_name:
            project_name = project_name.strip()
            if not project_name:
                messagebox.showerror("Error", "Project name cannot be empty.")
                return
            
            projects = self.data_manager.data.get("projects", [])
            
            if project_name in projects:
                messagebox.showerror("Error", "This project already exists.")
                return
            
            projects.append(project_name)
            self.data_manager.save_data()
            
            # Refresh project combo boxes
            self.project_combo['values'] = projects
            
            self.refresh_project_list()
            messagebox.showinfo("Success", f"Project '{project_name}' added successfully.")
    
    def edit_project_dialog(self):
        """Edit an existing project"""
        projects = self.data_manager.data.get("projects", [])
        
        if not projects:
            messagebox.showwarning("No Projects", "No projects to edit.")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Project")
        dialog.geometry("500x400")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Project to Edit:", style='Header.TLabel').pack(pady=(0, 10))
        
        listbox = tk.Listbox(frame, font=('Segoe UI', 10), bg='#34495e', fg=self.fg_color, height=10)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        for project in projects:
            listbox.insert(tk.END, project)
        
        def edit_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a project to edit.")
                return
            
            old_name = projects[selection[0]]
            new_name = simpledialog.askstring("Edit Project", "Enter new project name:", 
                                             initialvalue=old_name, parent=dialog)
            
            if new_name and new_name != old_name:
                new_name = new_name.strip()
                if new_name:
                    if new_name in projects:
                        messagebox.showerror("Error", "This project name already exists.")
                        return
                    
                    # Update project name in list
                    projects[selection[0]] = new_name
                    
                    # Update all time entries with this project
                    time_entries = self.data_manager.data.get("time_entries", [])
                    for entry in time_entries:
                        if entry.get("project") == old_name:
                            entry["project"] = new_name
                    
                    self.data_manager.save_data()
                    
                    # Refresh project combo boxes
                    self.project_combo['values'] = projects
                    
                    self.refresh_project_list()
                    messagebox.showinfo("Success", f"Project renamed to '{new_name}'.")
                    dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Edit", command=edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_project_dialog(self):
        """Delete a project"""
        projects = self.data_manager.data.get("projects", [])
        
        if not projects:
            messagebox.showwarning("No Projects", "No projects to delete.")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Project")
        dialog.geometry("500x450")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Project to Delete:", style='Header.TLabel').pack(pady=(0, 10))
        
        listbox = tk.Listbox(frame, font=('Segoe UI', 10), bg='#34495e', fg=self.fg_color, height=10)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        for project in projects:
            listbox.insert(tk.END, project)
        
        def delete_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a project to delete.")
                return
            
            project_name = projects[selection[0]]
            
            # Check if any time entries use this project
            time_entries = self.data_manager.data.get("time_entries", [])
            entry_count = sum(1 for e in time_entries if e.get("project") == project_name)
            
            if entry_count > 0:
                response = messagebox.askyesno(
                    "Project In Use",
                    f"This project has {entry_count} time entries.\\n\\n" +
                    "Time entries will be moved to 'General' project.\\n\\nContinue?"
                )
                if not response:
                    return
                
                # Move entries to General
                for entry in time_entries:
                    if entry.get("project") == project_name:
                        entry["project"] = "General"
            
            projects.remove(project_name)
            self.data_manager.save_data()
            
            # Refresh project combo boxes
            self.project_combo['values'] = projects
            if self.project_combo.get() == project_name:
                if projects:
                    self.project_combo.current(0)
            
            self.refresh_project_list()
            messagebox.showinfo("Success", f"Project '{project_name}' deleted.")
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Delete", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def view_project_report(self):
        """View detailed project time tracking report"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Project Time Report")
        dialog.geometry("1000x700")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Project Time Tracking Report", style='Header.TLabel').pack(pady=(0, 10))
        
        # Project selector
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(selector_frame, text="Select Project:").pack(side=tk.LEFT, padx=5)
        project_selector = ttk.Combobox(selector_frame, state='readonly', width=30)
        projects = self.data_manager.data.get("projects", [])
        project_selector['values'] = ["All Projects"] + projects
        project_selector.current(0)
        project_selector.pack(side=tk.LEFT, padx=5)
        
        text = scrolledtext.ScrolledText(frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color)
        text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        def generate_report():
            text.delete('1.0', tk.END)
            selected = project_selector.get()
            
            time_entries = self.data_manager.data.get("time_entries", [])
            
            # Save flag to track if we modified any entries
            modified = False
            
            # Filter entries - also check entries without project and assign default
            if selected == "All Projects":
                filtered_entries = []
                for e in time_entries:
                    if e.get("clock_out"):
                        # Assign default project if missing
                        if not e.get("project"):
                            e["project"] = "General"
                            modified = True
                        filtered_entries.append(e)
            else:
                filtered_entries = []
                for e in time_entries:
                    if e.get("clock_out"):
                        # Assign default project if missing
                        if not e.get("project"):
                            e["project"] = "General"
                            modified = True
                        if e.get("project") == selected:
                            filtered_entries.append(e)
            
            # Save if we modified entries
            if modified:
                self.data_manager.save_data()
            
            if not filtered_entries:
                text.insert(tk.END, f"No time entries found for selected project(s).\n\n")
                text.insert(tk.END, f"Debug Information:\n")
                text.insert(tk.END, f"{'='*50}\n")
                text.insert(tk.END, f"Total entries in database: {len(time_entries)}\n")
                text.insert(tk.END, f"Completed entries: {sum(1 for e in time_entries if e.get('clock_out'))}\n")
                text.insert(tk.END, f"Entries with project field: {sum(1 for e in time_entries if e.get('project'))}\n\n")
                
                # Show sample of what's in the database
                if time_entries:
                    text.insert(tk.END, f"Sample entry (most recent):\n")
                    latest = time_entries[-1]
                    text.insert(tk.END, f"  Employee: {latest.get('name', 'N/A')}\n")
                    text.insert(tk.END, f"  Clock In: {latest.get('clock_in', 'N/A')}\n")
                    text.insert(tk.END, f"  Clock Out: {latest.get('clock_out', 'N/A')}\n")
                    text.insert(tk.END, f"  Hours: {latest.get('hours_worked', 'N/A')}\n")
                    text.insert(tk.END, f"  Project: {latest.get('project', 'N/A')}\n")
                return
            
            # Group by project and employee
            project_data = {}
            for entry in filtered_entries:
                project = entry.get("project", "Unknown")
                emp_name = entry.get("name", "Unknown")
                
                if project not in project_data:
                    project_data[project] = {}
                
                if emp_name not in project_data[project]:
                    project_data[project][emp_name] = {"hours": 0, "wages": 0, "entries": 0}
                
                project_data[project][emp_name]["hours"] += entry.get("hours_worked", 0)
                project_data[project][emp_name]["wages"] += entry.get("wages", 0)
                project_data[project][emp_name]["entries"] += 1
            
            # Display report
            text.insert(tk.END, f"{'='*120}\n")
            text.insert(tk.END, f"PROJECT TIME TRACKING REPORT\n")
            text.insert(tk.END, f"{'='*120}\n\n")
            
            grand_total_hours = 0
            grand_total_wages = 0
            
            for project, employees in sorted(project_data.items()):
                text.insert(tk.END, f"\n{'─'*120}\n")
                text.insert(tk.END, f"PROJECT: {project}\n")
                text.insert(tk.END, f"{'─'*120}\n")
                text.insert(tk.END, f"{'Employee':<30} {'Hours':<15} {'Wages':<15} {'Entries'}\n")
                text.insert(tk.END, f"{'-'*120}\n")
                
                project_hours = 0
                project_wages = 0
                
                for emp_name, data in sorted(employees.items()):
                    text.insert(tk.END, f"{emp_name:<30} {data['hours']:<15.2f} ${data['wages']:<14.2f} {data['entries']}\n")
                    project_hours += data['hours']
                    project_wages += data['wages']
                
                text.insert(tk.END, f"{'-'*120}\n")
                text.insert(tk.END, f"{'SUBTOTAL:':<30} {project_hours:<15.2f} ${project_wages:<14.2f}\n")
                
                grand_total_hours += project_hours
                grand_total_wages += project_wages
            
            text.insert(tk.END, f"\n{'='*120}\n")
            text.insert(tk.END, f"{'GRAND TOTAL:':<30} {grand_total_hours:<15.2f} ${grand_total_wages:<14.2f}\n")
            text.insert(tk.END, f"{'='*120}\n")
        
        project_selector.bind('<<ComboboxSelected>>', lambda e: generate_report())
        generate_report()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Refresh", command=generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def manage_project_notes(self):
        """Manage project notes - view, add, edit, delete"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Project Progress Notes")
        dialog.geometry("1200x700")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Project Progress Notes", style='Header.TLabel').pack(pady=(0, 10))
        
        # Filter frame
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Project:").pack(side=tk.LEFT, padx=5)
        project_filter = ttk.Combobox(filter_frame, state='readonly', width=25)
        projects = self.data_manager.data.get("projects", [])
        project_filter['values'] = ["All Projects"] + projects
        project_filter.current(0)
        project_filter.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="Filter by Employee:").pack(side=tk.LEFT, padx=15)
        employee_filter = ttk.Combobox(filter_frame, state='readonly', width=25)
        employee_filter.pack(side=tk.LEFT, padx=5)
        
        # Notes display
        notes_text = scrolledtext.ScrolledText(frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color)
        notes_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        def refresh_notes():
            notes_text.delete('1.0', tk.END)
            
            project_notes = self.data_manager.data.get("project_notes", [])
            
            if not project_notes:
                notes_text.insert('1.0', "No project notes found.\n\nClick 'Add Note' to create your first progress note.")
                return
            
            # Filter notes
            filtered_notes = project_notes.copy()
            
            selected_project = project_filter.get()
            if selected_project != "All Projects":
                filtered_notes = [n for n in filtered_notes if n.get("project") == selected_project]
            
            selected_employee = employee_filter.get()
            if selected_employee != "All Employees":
                filtered_notes = [n for n in filtered_notes if n.get("employee_name") == selected_employee]
            
            if not filtered_notes:
                notes_text.insert('1.0', "No notes match the selected filters.")
                return
            
            # Sort by timestamp (most recent first)
            filtered_notes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Display notes
            notes_text.insert(tk.END, f"{'='*140}\n")
            notes_text.insert(tk.END, f"{'PROJECT PROGRESS NOTES':^140}\n")
            notes_text.insert(tk.END, f"{'='*140}\n\n")
            
            for i, note in enumerate(filtered_notes, 1):
                notes_text.insert(tk.END, f"{'─'*140}\n")
                notes_text.insert(tk.END, f"Note #{note.get('id', i)}\n")
                notes_text.insert(tk.END, f"{'─'*140}\n")
                notes_text.insert(tk.END, f"Project:       {note.get('project', 'Unknown')}\n")
                notes_text.insert(tk.END, f"Employee:      {note.get('employee_name', 'Unknown')}\n")
                notes_text.insert(tk.END, f"Date/Time:     {note.get('timestamp', 'Unknown')}\n")
                notes_text.insert(tk.END, f"{'─'*140}\n")
                notes_text.insert(tk.END, f"{note.get('note', '')}\n")
                notes_text.insert(tk.END, f"{'─'*140}\n\n")
            
            notes_text.insert(tk.END, f"{'='*140}\n")
            notes_text.insert(tk.END, f"Total Notes Displayed: {len(filtered_notes)}\n")
            notes_text.insert(tk.END, f"{'='*140}\n")
        
        def update_employee_filter():
            # Get unique employee names from notes
            project_notes = self.data_manager.data.get("project_notes", [])
            employees = sorted(set(n.get("employee_name", "Unknown") for n in project_notes))
            employee_filter['values'] = ["All Employees"] + employees
            employee_filter.current(0)
        
        def add_note():
            add_dialog = tk.Toplevel(dialog)
            add_dialog.title("Add Project Note")
            add_dialog.geometry("600x500")
            add_dialog.configure(bg=self.bg_color)
            add_dialog.transient(dialog)
            
            add_frame = ttk.Frame(add_dialog, padding="20")
            add_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(add_frame, text="Add Progress Note", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))
            
            ttk.Label(add_frame, text="Employee:").grid(row=1, column=0, sticky=tk.W, pady=5)
            emp_combo = ttk.Combobox(add_frame, state='readonly', width=30)
            employees = self.data_manager.data.get("employees", {})
            emp_combo['values'] = sorted([emp_data["name"] for emp_data in employees.values()])
            if emp_combo['values']:
                emp_combo.current(0)
            emp_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
            
            ttk.Label(add_frame, text="Project:").grid(row=2, column=0, sticky=tk.W, pady=5)
            proj_combo = ttk.Combobox(add_frame, state='readonly', width=30)
            proj_combo['values'] = projects
            if proj_combo['values']:
                proj_combo.current(0)
            proj_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
            
            ttk.Label(add_frame, text="Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
            date_picker = DateEntry(add_frame, width=28, date_pattern='mm/dd/yyyy', firstweekday='sunday')
            date_picker.grid(row=3, column=1, sticky=tk.W, pady=5)
            
            ttk.Label(add_frame, text="Progress Note:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=5)
            note_text = tk.Text(add_frame, height=15, width=50, font=('Segoe UI', 10), bg='#34495e', fg=self.fg_color)
            note_text.grid(row=4, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
            
            add_frame.columnconfigure(1, weight=1)
            add_frame.rowconfigure(4, weight=1)
            
            def save_note():
                employee_name = emp_combo.get()
                project_name = proj_combo.get()
                note_content = note_text.get('1.0', tk.END).strip()
                
                if not employee_name or not project_name or not note_content:
                    messagebox.showerror("Error", "All fields are required.")
                    return
                
                # Find employee ID
                emp_id = None
                for eid, emp_data in employees.items():
                    if emp_data["name"] == employee_name:
                        emp_id = eid
                        break
                
                # Get selected date and combine with current time
                selected_date = date_picker.get_date()
                current_time = datetime.now().time()
                note_datetime = datetime.combine(selected_date, current_time)
                
                project_notes = self.data_manager.data.get("project_notes", [])
                note_id = max([n.get("id", 0) for n in project_notes], default=0) + 1
                
                new_note = {
                    "id": note_id,
                    "project": project_name,
                    "employee_id": emp_id,
                    "employee_name": employee_name,
                    "note": note_content,
                    "timestamp": note_datetime.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                project_notes.append(new_note)
                self.data_manager.save_data()
                
                update_employee_filter()
                refresh_notes()
                messagebox.showinfo("Success", "Progress note added successfully.")
                add_dialog.destroy()
            
            btn_frame = ttk.Frame(add_frame)
            btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
            ttk.Button(btn_frame, text="Save Note", command=save_note).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=add_dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        def edit_note():
            project_notes = self.data_manager.data.get("project_notes", [])
            
            if not project_notes:
                messagebox.showwarning("No Notes", "No notes to edit.")
                return
            
            # Selection dialog
            select_dialog = tk.Toplevel(dialog)
            select_dialog.title("Select Note to Edit")
            select_dialog.geometry("800x500")
            select_dialog.configure(bg=self.bg_color)
            select_dialog.transient(dialog)
            
            select_frame = ttk.Frame(select_dialog, padding="20")
            select_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(select_frame, text="Select Note to Edit:", style='Header.TLabel').pack(pady=(0, 10))
            
            listbox = tk.Listbox(select_frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color, height=20)
            listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            for note in project_notes:
                display_text = f"#{note.get('id', 0)} | {note.get('project', 'Unknown')} | {note.get('employee_name', 'Unknown')} | {note.get('timestamp', 'Unknown')}"
                listbox.insert(tk.END, display_text)
            
            def edit_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("No Selection", "Please select a note to edit.")
                    return
                
                note = project_notes[selection[0]]
                
                edit_dialog = tk.Toplevel(select_dialog)
                edit_dialog.title("Edit Project Note")
                edit_dialog.geometry("600x500")
                edit_dialog.configure(bg=self.bg_color)
                edit_dialog.transient(select_dialog)
                
                edit_frame = ttk.Frame(edit_dialog, padding="20")
                edit_frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(edit_frame, text="Edit Progress Note", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))
                
                ttk.Label(edit_frame, text="Employee:").grid(row=1, column=0, sticky=tk.W, pady=5)
                emp_label = ttk.Label(edit_frame, text=note.get('employee_name', 'Unknown'))
                emp_label.grid(row=1, column=1, sticky=tk.W, pady=5)
                
                ttk.Label(edit_frame, text="Project:").grid(row=2, column=0, sticky=tk.W, pady=5)
                proj_label = ttk.Label(edit_frame, text=note.get('project', 'Unknown'))
                proj_label.grid(row=2, column=1, sticky=tk.W, pady=5)
                
                ttk.Label(edit_frame, text="Original Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
                time_label = ttk.Label(edit_frame, text=note.get('timestamp', 'Unknown'))
                time_label.grid(row=3, column=1, sticky=tk.W, pady=5)
                
                ttk.Label(edit_frame, text="New Date:").grid(row=4, column=0, sticky=tk.W, pady=5)
                edit_date_picker = DateEntry(edit_frame, width=28, date_pattern='mm/dd/yyyy', firstweekday='sunday')
                edit_date_picker.grid(row=4, column=1, sticky=tk.W, pady=5)
                
                ttk.Label(edit_frame, text="Progress Note:").grid(row=5, column=0, sticky=(tk.W, tk.N), pady=5)
                note_text = tk.Text(edit_frame, height=15, width=50, font=('Segoe UI', 10), bg='#34495e', fg=self.fg_color)
                note_text.grid(row=5, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
                note_text.insert('1.0', note.get('note', ''))
                
                edit_frame.columnconfigure(1, weight=1)
                edit_frame.rowconfigure(5, weight=1)
                
                def update_note():
                    note_content = note_text.get('1.0', tk.END).strip()
                    
                    if not note_content:
                        messagebox.showerror("Error", "Note content cannot be empty.")
                        return
                    
                    # Get selected date and combine with current time
                    selected_date = edit_date_picker.get_date()
                    current_time = datetime.now().time()
                    note_datetime = datetime.combine(selected_date, current_time)
                    
                    note['note'] = note_content
                    note['timestamp'] = note_datetime.strftime('%Y-%m-%d %H:%M:%S') + " (edited)"
                    
                    self.data_manager.save_data()
                    refresh_notes()
                    messagebox.showinfo("Success", "Note updated successfully.")
                    edit_dialog.destroy()
                    select_dialog.destroy()
                
                btn_frame = ttk.Frame(edit_frame)
                btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
                ttk.Button(btn_frame, text="Update Note", command=update_note).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_frame, text="Cancel", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            btn_frame = ttk.Frame(select_frame)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text="Edit", command=edit_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=select_dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        def delete_note():
            project_notes = self.data_manager.data.get("project_notes", [])
            
            if not project_notes:
                messagebox.showwarning("No Notes", "No notes to delete.")
                return
            
            # Selection dialog
            select_dialog = tk.Toplevel(dialog)
            select_dialog.title("Select Note to Delete")
            select_dialog.geometry("800x500")
            select_dialog.configure(bg=self.bg_color)
            select_dialog.transient(dialog)
            
            select_frame = ttk.Frame(select_dialog, padding="20")
            select_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(select_frame, text="Select Note to Delete:", style='Header.TLabel').pack(pady=(0, 10))
            
            listbox = tk.Listbox(select_frame, font=('Consolas', 9), bg='#34495e', fg=self.fg_color, height=20)
            listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            for note in project_notes:
                display_text = f"#{note.get('id', 0)} | {note.get('project', 'Unknown')} | {note.get('employee_name', 'Unknown')} | {note.get('timestamp', 'Unknown')}"
                listbox.insert(tk.END, display_text)
            
            def delete_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("No Selection", "Please select a note to delete.")
                    return
                
                note = project_notes[selection[0]]
                
                response = messagebox.askyesno(
                    "Confirm Delete",
                    f"Are you sure you want to delete this note?\n\nProject: {note.get('project', 'Unknown')}\nEmployee: {note.get('employee_name', 'Unknown')}\nDate: {note.get('timestamp', 'Unknown')}"
                )
                
                if response:
                    project_notes.remove(note)
                    self.data_manager.save_data()
                    
                    update_employee_filter()
                    refresh_notes()
                    messagebox.showinfo("Success", "Note deleted successfully.")
                    select_dialog.destroy()
            
            btn_frame = ttk.Frame(select_frame)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text="Delete", command=delete_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=select_dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Initialize and refresh
        update_employee_filter()
        project_filter.bind('<<ComboboxSelected>>', lambda e: refresh_notes())
        employee_filter.bind('<<ComboboxSelected>>', lambda e: refresh_notes())
        refresh_notes()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Add Note", command=add_note).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Note", command=edit_note).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Note", command=delete_note).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh", command=refresh_notes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    # ============= INVOICE MANAGEMENT METHODS =============
    
    def refresh_invoice_list(self):
        """Refresh the invoice list display"""
        self.invoice_list_text.delete('1.0', tk.END)
        
        invoices = self.data_manager.data.get("invoices", [])
        
        if not invoices:
            self.invoice_list_text.insert('1.0', "No invoices created yet.\\n\\nClick 'Generate Invoice' to create an invoice for a project.")
            return
        
        report = f"{'='*140}\\n"
        report += "INVOICES\\n"
        report += f"{'='*140}\\n\\n"
        report += f"{'ID':<8} {'Project':<25} {'Labor Hrs':<12} {'Labor Cost':<15} {'kWh Used':<12} {'$/kWh':<10} {'Elec Cost':<15} {'Total':<15} {'Date':<12}\\n"
        report += f"{'-'*140}\\n"
        
        total_labor_cost = 0
        total_electricity = 0
        total_amount = 0
        
        for invoice in sorted(invoices, key=lambda x: x.get('invoice_id', 0), reverse=True):
            inv_id = invoice.get('invoice_id', 'N/A')
            project = invoice.get('project_name', 'Unknown')
            labor_hours = invoice.get('labor_hours', 0)
            labor_cost = invoice.get('labor_cost', 0)
            kwh_used = invoice.get('kwh_used', 0)
            rate_per_kwh = invoice.get('rate_per_kwh', 0)
            electricity = invoice.get('electricity_cost', 0)
            total = invoice.get('total_cost', 0)
            date = invoice.get('date_created', 'N/A')
            
            total_labor_cost += labor_cost
            total_electricity += electricity
            total_amount += total
            
            report += f"{inv_id:<8} {project:<25} {labor_hours:<12.2f} ${labor_cost:<14.2f} {kwh_used:<12.2f} ${rate_per_kwh:<9.2f} ${electricity:<14.2f} ${total:<14.2f} {date:<12}\\n"
        
        report += f"{'-'*140}\\n"
        report += f"{'TOTALS':<8} {'':<25} {'':<12} ${total_labor_cost:<14.2f} {'':<12} {'':<10} ${total_electricity:<14.2f} ${total_amount:<14.2f}\\n"
        report += f"{'='*140}\\n"
        
        self.invoice_list_text.insert('1.0', report)
    
    def generate_invoice_dialog(self):
        """Generate a new invoice for a project"""
        projects = self.data_manager.data.get("projects", [])
        
        if not projects:
            messagebox.showwarning("No Projects", "No projects available. Please create a project first.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Generate Invoice")
        
        # Calculate center position
        window_width = 700
        window_height = 600
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Generate Invoice", style='Header.TLabel').pack(pady=(0, 20))
        
        # Project selection
        ttk.Label(frame, text="Select Project:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        project_var = ttk.Combobox(frame, state='readonly', values=projects, font=('Segoe UI', 10))
        project_var.pack(fill=tk.X, pady=(0, 10))
        if projects:
            project_var.current(0)
        
        # Company Info Section
        ttk.Label(frame, text="Company Information:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        company_frame = ttk.Frame(frame)
        company_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Get saved company info from settings
        settings = self.data_manager.data.get("settings", {})
        company_info = settings.get("company_info", {})
        
        ttk.Label(company_frame, text="Company Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        company_name_entry = ttk.Entry(company_frame, width=40)
        company_name_entry.insert(0, company_info.get("name", "YOUR COMPANY NAME"))
        company_name_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(company_frame, text="Street Address:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        company_street_entry = ttk.Entry(company_frame, width=40)
        company_street_entry.insert(0, company_info.get("street", "123 Business Street"))
        company_street_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(company_frame, text="Street Address 2:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        company_street2_entry = ttk.Entry(company_frame, width=40)
        company_street2_entry.insert(0, company_info.get("street2", ""))
        company_street2_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(company_frame, text="City:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        company_city_entry = ttk.Entry(company_frame, width=40)
        company_city_entry.insert(0, company_info.get("city", "City"))
        company_city_entry.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(company_frame, text="State:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5))
        company_state_entry = ttk.Entry(company_frame, width=40)
        company_state_entry.insert(0, company_info.get("state", "State"))
        company_state_entry.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(company_frame, text="ZIP Code:").grid(row=5, column=0, sticky=tk.W, padx=(0, 5))
        company_zip_entry = ttk.Entry(company_frame, width=40)
        company_zip_entry.insert(0, company_info.get("zip", "12345"))
        company_zip_entry.grid(row=5, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(company_frame, text="Phone:").grid(row=6, column=0, sticky=tk.W, padx=(0, 5))
        company_phone_entry = ttk.Entry(company_frame, width=40)
        company_phone_entry.insert(0, company_info.get("phone", "(555) 123-4567"))
        company_phone_entry.grid(row=6, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(company_frame, text="Email:").grid(row=7, column=0, sticky=tk.W, padx=(0, 5))
        company_email_entry = ttk.Entry(company_frame, width=40)
        company_email_entry.insert(0, company_info.get("email", "email@company.com"))
        company_email_entry.grid(row=7, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(company_frame, text="Website:").grid(row=8, column=0, sticky=tk.W, padx=(0, 5))
        company_website_entry = ttk.Entry(company_frame, width=40)
        company_website_entry.insert(0, company_info.get("website", "www.company.com"))
        company_website_entry.grid(row=8, column=1, sticky=tk.W, pady=2)
        
        # Bill To Section
        ttk.Label(frame, text="Bill To Information:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        billto_frame = ttk.Frame(frame)
        billto_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(billto_frame, text="Client Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        bill_to_name_entry = ttk.Entry(billto_frame, width=40)
        bill_to_name_entry.insert(0, "Client Name")
        bill_to_name_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(billto_frame, text="Address:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        bill_to_address_entry = ttk.Entry(billto_frame, width=40)
        bill_to_address_entry.insert(0, "Client Address")
        bill_to_address_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(billto_frame, text="City/State/Zip:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        bill_to_city_entry = ttk.Entry(billto_frame, width=40)
        bill_to_city_entry.insert(0, "City, State ZIP")
        bill_to_city_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Invoice details display
        details_label = ttk.Label(frame, text="", font=('Consolas', 9), foreground=self.accent_color, justify=tk.LEFT)
        details_label.pack(anchor=tk.W, pady=10, fill=tk.BOTH, expand=True)
        
        # kWh consumption rate setting
        kwh_rate_frame = ttk.Frame(frame)
        kwh_rate_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(kwh_rate_frame, text="kWh/Hour Rate:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        kwh_per_hour_entry = ttk.Entry(kwh_rate_frame, font=('Segoe UI', 10), width=10)
        kwh_per_hour_entry.insert(0, "5.0")  # Default 5 kWh per work hour
        kwh_per_hour_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(kwh_rate_frame, text="(Power consumption per work hour)", font=('Segoe UI', 8), foreground='#95a5a6').pack(side=tk.LEFT)
        
        # Electricity usage
        electricity_frame = ttk.Frame(frame)
        electricity_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(electricity_frame, text="kWh Used:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        kwh_entry = ttk.Entry(electricity_frame, font=('Segoe UI', 10), width=15)
        kwh_entry.insert(0, "0.00")
        kwh_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(electricity_frame, text="Rate ($/kWh):", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        rate_entry = ttk.Entry(electricity_frame, font=('Segoe UI', 10), width=15)
        rate_entry.insert(0, "0.00")
        rate_entry.pack(side=tk.LEFT)
        
        # Electricity cost display
        elec_cost_label = ttk.Label(frame, text="Electricity Cost: $0.00", font=('Segoe UI', 10), foreground=self.accent_color)
        elec_cost_label.pack(anchor=tk.W, pady=(5, 10))
        
        def update_electricity_cost(*args):
            try:
                kwh = float(kwh_entry.get())
                rate = float(rate_entry.get())
                cost = kwh * rate
                elec_cost_label.config(text=f"Electricity Cost: ${cost:.2f}")
            except ValueError:
                elec_cost_label.config(text="Electricity Cost: $0.00")
        
        def calculate_invoice(*args):
            """Calculate invoice details when project is selected"""
            selected_project = project_var.get()
            if not selected_project:
                return
            
            # Get all time entries for this project
            time_entries = self.data_manager.data.get("time_entries", [])
            project_entries = [e for e in time_entries if e.get('project') == selected_project and e.get('clock_out')]
            
            total_hours = 0
            total_cost = 0
            employee_hours = {}
            
            for entry in project_entries:
                emp_id = entry['employee_id']
                employee = self.data_manager.get_employee(emp_id)
                
                clock_in = datetime.fromisoformat(entry['clock_in'])
                clock_out = datetime.fromisoformat(entry['clock_out'])
                hours = (clock_out - clock_in).total_seconds() / 3600
                
                # Subtract break time
                hours -= self.data_manager.calculate_break_hours(entry, unpaid_only=True)
                
                hourly_rate = employee.get('hourly_rate', 0)
                cost = hours * hourly_rate
                
                total_hours += hours
                total_cost += cost
                
                emp_name = employee.get('name', emp_id)
                if emp_name not in employee_hours:
                    employee_hours[emp_name] = {'hours': 0, 'cost': 0, 'rate': hourly_rate}
                employee_hours[emp_name]['hours'] += hours
                employee_hours[emp_name]['cost'] += cost
            
            # Auto-calculate kWh based on hours worked
            try:
                kwh_per_hour = float(kwh_per_hour_entry.get())
                auto_kwh = total_hours * kwh_per_hour
                kwh_entry.delete(0, tk.END)
                kwh_entry.insert(0, f"{auto_kwh:.2f}")
                update_electricity_cost()
            except ValueError:
                pass
            
            # Display breakdown
            details = f"Project: {selected_project}\n"
            details += f"{'='*60}\n\n"
            details += f"Labor Breakdown:\n"
            details += f"{'-'*60}\n"
            details += f"{'Employee':<25} {'Hours':<12} {'Rate':<10} {'Cost':<10}\n"
            details += f"{'-'*60}\n"
            
            for emp_name, data in sorted(employee_hours.items()):
                details += f"{emp_name:<25} {data['hours']:<12.2f} ${data['rate']:<9.2f} ${data['cost']:<9.2f}\n"
            
            details += f"{'-'*60}\n"
            details += f"{'TOTAL LABOR':<25} {total_hours:<12.2f} {'':<10} ${total_cost:<9.2f}\n"
            details += f"\nTotal Entries: {len(project_entries)}\n"
            
            details_label.config(text=details)
            
            # Store calculated values for saving
            dialog.labor_hours = total_hours
            dialog.labor_cost = total_cost
            
            # Store company and bill-to info
            dialog.company_name = company_name_entry.get()
            dialog.company_street = company_street_entry.get()
            dialog.company_street2 = company_street2_entry.get()
            dialog.company_city = company_city_entry.get()
            dialog.company_state = company_state_entry.get()
            dialog.company_zip = company_zip_entry.get()
            dialog.company_phone = company_phone_entry.get()
            dialog.company_email = company_email_entry.get()
            dialog.company_website = company_website_entry.get()
            dialog.bill_to_name = bill_to_name_entry.get()
            dialog.bill_to_address = bill_to_address_entry.get()
            dialog.bill_to_city = bill_to_city_entry.get()
        
        project_var.bind('<<ComboboxSelected>>', calculate_invoice)
        kwh_per_hour_entry.bind('<KeyRelease>', calculate_invoice)
        kwh_entry.bind('<KeyRelease>', update_electricity_cost)
        rate_entry.bind('<KeyRelease>', update_electricity_cost)
        if projects:
            calculate_invoice()
        
        def save_invoice():
            selected_project = project_var.get()
            if not selected_project:
                messagebox.showwarning("No Project", "Please select a project.")
                return
            
            try:
                kwh_used = float(kwh_entry.get())
                rate_per_kwh = float(rate_entry.get())
                electricity_cost = kwh_used * rate_per_kwh
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values for electricity.")
                return
            
            # Generate invoice ID
            invoices = self.data_manager.data.get("invoices", [])
            if invoices:
                invoice_id = max([inv.get('invoice_id', 0) for inv in invoices]) + 1
            else:
                invoice_id = 1
            
            total_cost = dialog.labor_cost + electricity_cost
            
            # Get company and bill-to info from dialog
            invoice = {
                'invoice_id': invoice_id,
                'project_name': selected_project,
                'labor_hours': dialog.labor_hours,
                'labor_cost': dialog.labor_cost,
                'kwh_used': kwh_used,
                'rate_per_kwh': rate_per_kwh,
                'electricity_cost': electricity_cost,
                'total_cost': total_cost,
                'date_created': datetime.now().strftime('%m/%d/%Y'),
                'company_name': dialog.company_name,
                'company_street': dialog.company_street,
                'company_street2': dialog.company_street2,
                'company_city': dialog.company_city,
                'company_state': dialog.company_state,
                'company_zip': dialog.company_zip,
                'company_phone': dialog.company_phone,
                'company_email': dialog.company_email,
                'company_website': dialog.company_website,
                'bill_to_name': dialog.bill_to_name,
                'bill_to_address': dialog.bill_to_address,
                'bill_to_city': dialog.bill_to_city
            }
            
            self.data_manager.data["invoices"].append(invoice)
            self.data_manager.save_data()
            
            messagebox.showinfo(
                "Invoice Generated",
                f"Invoice #{invoice_id} created successfully!\\n\\n"
                f"Project: {selected_project}\\n"
                f"Labor Hours: {dialog.labor_hours:.2f}\\n"
                f"Labor Cost: ${dialog.labor_cost:.2f}\\n"
                f"kWh Used: {kwh_used:.2f}\\n"
                f"Rate: ${rate_per_kwh:.2f}/kWh\\n"
                f"Electricity: ${electricity_cost:.2f}\\n"
                f"Total: ${total_cost:.2f}"
            )
            
            self.refresh_invoice_list()
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Generate Invoice", command=save_invoice).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=660, y=10)
    
    def view_print_invoice_dialog(self):
        """View and print a formatted invoice"""
        invoices = self.data_manager.data.get("invoices", [])
        
        if not invoices:
            messagebox.showwarning("No Invoices", "No invoices available. Please generate an invoice first.")
            return
        
        # Selection dialog
        select_dialog = tk.Toplevel(self.root)
        select_dialog.title("Select Invoice to View/Print")
        select_dialog.geometry("700x400")
        select_dialog.configure(bg=self.bg_color)
        select_dialog.transient(self.root)
        select_dialog.grab_set()
        
        frame = ttk.Frame(select_dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Invoice to View/Print", style='Header.TLabel').pack(pady=(0, 10))
        
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=('Consolas', 10),
                            bg='#34495e', fg=self.fg_color, selectmode=tk.SINGLE)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for inv in sorted(invoices, key=lambda x: x.get('invoice_id', 0), reverse=True):
            display_text = f"Invoice #{inv['invoice_id']:<5} - {inv['project_name']:<30} - ${inv.get('total_cost', 0):.2f} - {inv.get('date_created', 'N/A')}"
            listbox.insert(tk.END, display_text)
        
        def view_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an invoice to view.")
                return
            
            invoice = sorted(invoices, key=lambda x: x.get('invoice_id', 0), reverse=True)[selection[0]]
            select_dialog.destroy()
            self.show_formatted_invoice(invoice)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text="View/Print", command=view_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=select_dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_formatted_invoice(self, invoice):
        """Show a professionally formatted, printable invoice"""
        import tempfile
        import os
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Invoice #{invoice['invoice_id']}")
        
        # Calculate center position
        window_width = 1100
        window_height = 850
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        
        # Create canvas with scrollbar for scrolling
        canvas = tk.Canvas(dialog, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        dialog.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        # Create main frame with white background inside scrollable frame
        main_frame = tk.Frame(scrollable_frame, bg='white', padx=50, pady=40)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Company header
        header_frame = tk.Frame(main_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        # Get company info from settings as fallback
        settings = self.data_manager.data.get("settings", {})
        company_info = settings.get("company_info", {})
        
        # Use invoice data if available, otherwise fall back to settings
        company_name = invoice.get('company_name', company_info.get('name', 'YOUR COMPANY NAME'))
        company_street = invoice.get('company_street', company_info.get('street', '123 Business Street'))
        company_street2 = invoice.get('company_street2', company_info.get('street2', ''))
        company_city = invoice.get('company_city', company_info.get('city', 'City'))
        company_state = invoice.get('company_state', company_info.get('state', 'State'))
        company_zip = invoice.get('company_zip', company_info.get('zip', '12345'))
        company_phone = invoice.get('company_phone', company_info.get('phone', '(555) 123-4567'))
        company_email = invoice.get('company_email', company_info.get('email', 'email@company.com'))
        company_website = invoice.get('company_website', company_info.get('website', 'www.company.com'))
        
        # Build address line
        address_line1 = company_street
        if company_street2:
            address_line2 = f"{company_street2}, {company_city}, {company_state} {company_zip}"
        else:
            address_line2 = f"{company_city}, {company_state} {company_zip}"
        
        tk.Label(header_frame, text=company_name, font=('Arial', 32, 'bold'),
                bg='white', fg='#2c3e50').pack(anchor=tk.W)
        tk.Label(header_frame, text=address_line1, font=('Arial', 13),
                bg='white', fg='#7f8c8d').pack(anchor=tk.W, pady=(5, 0))
        if company_street2:
            tk.Label(header_frame, text=address_line2, font=('Arial', 13),
                    bg='white', fg='#7f8c8d').pack(anchor=tk.W)
        else:
            tk.Label(header_frame, text=address_line2, font=('Arial', 13),
                    bg='white', fg='#7f8c8d').pack(anchor=tk.W)
        tk.Label(header_frame, text=f"{company_phone} • {company_email} • {company_website}",
                font=('Arial', 13), bg='white', fg='#7f8c8d').pack(anchor=tk.W)
        
        # Separator line
        separator = tk.Frame(main_frame, height=3, bg='#3498db')
        separator.pack(fill=tk.X, pady=20)
        
        # Invoice title and info
        title_frame = tk.Frame(main_frame, bg='white')
        title_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(title_frame, text="INVOICE", font=('Arial', 36, 'bold'),
                bg='white', fg='#2c3e50').pack(side=tk.LEFT)
        
        info_right = tk.Frame(title_frame, bg='white')
        info_right.pack(side=tk.RIGHT)
        
        tk.Label(info_right, text=f"Invoice #: {invoice['invoice_id']}", font=('Arial', 14, 'bold'),
                bg='white', fg='#2c3e50').pack(anchor=tk.E, pady=2)
        tk.Label(info_right, text=f"Date: {invoice.get('date_created', 'N/A')}", font=('Arial', 14),
                bg='white', fg='#2c3e50').pack(anchor=tk.E)
        
        # Bill To section
        billto_frame = tk.Frame(main_frame, bg='white')
        billto_frame.pack(fill=tk.X, pady=(0, 30))
        
        bill_to_name = invoice.get('bill_to_name', 'Client Name')
        bill_to_address = invoice.get('bill_to_address', 'Client Address')
        bill_to_city = invoice.get('bill_to_city', 'City, State ZIP')
        
        tk.Label(billto_frame, text="BILL TO:", font=('Arial', 14, 'bold'),
                bg='white', fg='#2c3e50').pack(anchor=tk.W)
        tk.Label(billto_frame, text=bill_to_name, font=('Arial', 13),
                bg='white', fg='#34495e').pack(anchor=tk.W, padx=(0, 0), pady=(5, 0))
        tk.Label(billto_frame, text=bill_to_address, font=('Arial', 13),
                bg='white', fg='#34495e').pack(anchor=tk.W)
        tk.Label(billto_frame, text=bill_to_city, font=('Arial', 13),
                bg='white', fg='#34495e').pack(anchor=tk.W)
        
        # Project Info
        project_frame = tk.Frame(main_frame, bg='#ecf0f1', relief=tk.SOLID, borderwidth=2)
        project_frame.pack(fill=tk.X, pady=(0, 25), padx=0)
        
        proj_inner = tk.Frame(project_frame, bg='#ecf0f1', padx=20, pady=15)
        proj_inner.pack(fill=tk.BOTH)
        
        tk.Label(proj_inner, text="PROJECT:", font=('Arial', 13, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(anchor=tk.W)
        tk.Label(proj_inner, text=invoice.get('project_name', 'Unknown'), font=('Arial', 16, 'bold'),
                bg='#ecf0f1', fg='#3498db').pack(anchor=tk.W, pady=(5, 0))
        
        # Invoice details table
        table_frame = tk.Frame(main_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 25))
        
        # Table header
        header_bg = '#34495e'
        header_fg = 'white'
        
        headers = [("Description", 40), ("Quantity", 15), ("Rate", 15), ("Amount", 15)]
        header_row = tk.Frame(table_frame, bg=header_bg)
        header_row.pack(fill=tk.X)
        
        for header, width in headers:
            tk.Label(header_row, text=header, font=('Arial', 13, 'bold'),
                    bg=header_bg, fg=header_fg, width=width, anchor=tk.W,
                    padx=15, pady=12).pack(side=tk.LEFT)
        
        # Table rows
        row_bg1 = 'white'
        row_bg2 = '#f8f9fa'
        
        # Labor row
        labor_row = tk.Frame(table_frame, bg=row_bg1, relief=tk.SOLID, borderwidth=1)
        labor_row.pack(fill=tk.X)
        
        labor_hours = invoice.get('labor_hours', 0)
        labor_cost = invoice.get('labor_cost', 0)
        labor_rate = labor_cost / labor_hours if labor_hours > 0 else 0
        
        tk.Label(labor_row, text="Labor - Employee Time", font=('Arial', 13),
                bg=row_bg1, fg='#2c3e50', width=40, anchor=tk.W, padx=15, pady=15).pack(side=tk.LEFT)
        tk.Label(labor_row, text=f"{labor_hours:.2f} hrs", font=('Arial', 13),
                bg=row_bg1, fg='#2c3e50', width=15, anchor=tk.W, padx=15, pady=15).pack(side=tk.LEFT)
        tk.Label(labor_row, text=f"${labor_rate:.2f}/hr", font=('Arial', 13),
                bg=row_bg1, fg='#2c3e50', width=15, anchor=tk.W, padx=15, pady=15).pack(side=tk.LEFT)
        tk.Label(labor_row, text=f"${labor_cost:.2f}", font=('Arial', 13, 'bold'),
                bg=row_bg1, fg='#27ae60', width=15, anchor=tk.W, padx=15, pady=15).pack(side=tk.LEFT)
        
        # Electricity row
        elec_row = tk.Frame(table_frame, bg=row_bg2, relief=tk.SOLID, borderwidth=1)
        elec_row.pack(fill=tk.X)
        
        kwh_used = invoice.get('kwh_used', 0)
        rate_per_kwh = invoice.get('rate_per_kwh', 0)
        electricity_cost = invoice.get('electricity_cost', 0)
        
        tk.Label(elec_row, text="Electricity - Power Consumption", font=('Arial', 13),
                bg=row_bg2, fg='#2c3e50', width=40, anchor=tk.W, padx=15, pady=15).pack(side=tk.LEFT)
        tk.Label(elec_row, text=f"{kwh_used:.2f} kWh", font=('Arial', 13),
                bg=row_bg2, fg='#2c3e50', width=15, anchor=tk.W, padx=15, pady=15).pack(side=tk.LEFT)
        tk.Label(elec_row, text=f"${rate_per_kwh:.2f}/kWh", font=('Arial', 13),
                bg=row_bg2, fg='#2c3e50', width=15, anchor=tk.W, padx=15, pady=15).pack(side=tk.LEFT)
        tk.Label(elec_row, text=f"${electricity_cost:.2f}", font=('Arial', 13, 'bold'),
                bg=row_bg2, fg='#27ae60', width=15, anchor=tk.W, padx=15, pady=15).pack(side=tk.LEFT)
        
        # Totals section
        totals_frame = tk.Frame(main_frame, bg='white')
        totals_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Spacer
        tk.Frame(totals_frame, bg='white', width=500).pack(side=tk.LEFT)
        
        totals_right = tk.Frame(totals_frame, bg='white')
        totals_right.pack(side=tk.RIGHT)
        
        # Subtotal
        subtotal_frame = tk.Frame(totals_right, bg='white')
        subtotal_frame.pack(fill=tk.X, pady=5)
        tk.Label(subtotal_frame, text="Subtotal:", font=('Arial', 14),
                bg='white', fg='#2c3e50', width=20, anchor=tk.E).pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(subtotal_frame, text=f"${invoice.get('total_cost', 0):.2f}", font=('Arial', 14),
                bg='white', fg='#2c3e50', width=15, anchor=tk.E).pack(side=tk.LEFT)
        
        # Separator
        tk.Frame(totals_right, height=2, bg='#bdc3c7').pack(fill=tk.X, pady=8)
        
        # Total
        total_frame = tk.Frame(totals_right, bg='#3498db', padx=15, pady=12)
        total_frame.pack(fill=tk.X)
        tk.Label(total_frame, text="TOTAL:", font=('Arial', 18, 'bold'),
                bg='#3498db', fg='white', width=20, anchor=tk.E).pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(total_frame, text=f"${invoice.get('total_cost', 0):.2f}", font=('Arial', 18, 'bold'),
                bg='#3498db', fg='white', width=15, anchor=tk.E).pack(side=tk.LEFT)
        
        # Footer
        footer_frame = tk.Frame(main_frame, bg='white')
        footer_frame.pack(fill=tk.X, pady=(35, 0))
        
        tk.Label(footer_frame, text="Thank you for your business!", font=('Arial', 14, 'italic'),
                bg='white', fg='#7f8c8d').pack(pady=(0, 5))
        tk.Label(footer_frame, text="Payment due within 30 days", font=('Arial', 12),
                bg='white', fg='#95a5a6').pack()
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='#ecf0f1', pady=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        def print_invoice():
            """Print the invoice"""
            # Generate formatted text version
            invoice_text = self.generate_invoice_text(invoice)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                f.write(invoice_text)
                temp_file = f.name
            
            try:
                # Open with default text editor for printing
                os.startfile(temp_file, 'print')
                messagebox.showinfo("Print", "Invoice sent to printer!")
            except Exception as e:
                try:
                    # Alternative: open with notepad
                    os.system(f'notepad /p "{temp_file}"')
                except:
                    messagebox.showinfo("Print File", f"Invoice saved to:\n{temp_file}\n\nPlease open and print manually.")
        
        def save_invoice_pdf():
            """Save invoice as text file (simulated PDF)"""
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"Invoice_{invoice['invoice_id']}_{invoice.get('project_name', 'project').replace(' ', '_')}.txt"
            )
            
            if filename:
                invoice_text = self.generate_invoice_text(invoice)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(invoice_text)
                messagebox.showinfo("Success", f"Invoice saved to:\n{filename}")
        
        ttk.Button(btn_frame, text="🖨️ Print", command=print_invoice).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Save As", command=save_invoice_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def generate_invoice_text(self, invoice):
        """Generate formatted text version of invoice for printing"""
        company_name = invoice.get('company_name', 'YOUR COMPANY NAME')
        company_street = invoice.get('company_street', '123 Business Street')
        company_street2 = invoice.get('company_street2', '')
        company_city = invoice.get('company_city', 'City')
        company_state = invoice.get('company_state', 'State')
        company_zip = invoice.get('company_zip', '12345')
        company_phone = invoice.get('company_phone', '(555) 123-4567')
        company_email = invoice.get('company_email', 'email@company.com')
        bill_to_name = invoice.get('bill_to_name', 'Client Name')
        bill_to_address = invoice.get('bill_to_address', 'Client Address')
        bill_to_city = invoice.get('bill_to_city', 'City, State ZIP')
        
        # Build address lines
        if company_street2:
            company_addr_line = f"{company_street}, {company_street2}, {company_city}, {company_state} {company_zip}"
        else:
            company_addr_line = f"{company_street}, {company_city}, {company_state} {company_zip}"
        
        text = "="*80 + "\n"
        text += " " * int((80 - len(company_name)) / 2) + company_name + "\n"
        text += " " * int((80 - len(company_addr_line)) / 2) + company_addr_line + "\n"
        text += " " * int((80 - len(f"{company_phone} • {company_email}")) / 2) + f"{company_phone} • {company_email}\n"
        text += "="*80 + "\n\n"
        
        text += " " * 32 + "I N V O I C E\n\n"
        text += f"Invoice #: {invoice['invoice_id']:<20}              Date: {invoice.get('date_created', 'N/A')}\n"
        text += "-"*80 + "\n\n"
        
        text += "BILL TO:\n"
        text += bill_to_name + "\n"
        text += bill_to_address + "\n"
        text += bill_to_city + "\n\n"
        
        text += f"PROJECT: {invoice.get('project_name', 'Unknown')}\n"
        text += "-"*80 + "\n\n"
        
        text += f"{'Description':<40} {'Quantity':>12} {'Rate':>12} {'Amount':>15}\n"
        text += "-"*80 + "\n"
        
        # Labor
        labor_hours = invoice.get('labor_hours', 0)
        labor_cost = invoice.get('labor_cost', 0)
        labor_rate = labor_cost / labor_hours if labor_hours > 0 else 0
        
        text += f"{'Labor - Employee Time':<40} {labor_hours:>10.2f} hrs ${labor_rate:>10.2f}/hr ${labor_cost:>12.2f}\n"
        
        # Electricity
        kwh_used = invoice.get('kwh_used', 0)
        rate_per_kwh = invoice.get('rate_per_kwh', 0)
        electricity_cost = invoice.get('electricity_cost', 0)
        
        text += f"{'Electricity - Power Consumption':<40} {kwh_used:>10.2f} kWh ${rate_per_kwh:>10.2f}/kWh ${electricity_cost:>12.2f}\n"
        
        text += "-"*80 + "\n\n"
        
        text += f"{' '*50} {'Subtotal:':>15} ${invoice.get('total_cost', 0):>12.2f}\n"
        text += f"{' '*50} {'-'*30}\n"
        text += f"{' '*50} {'TOTAL:':>15} ${invoice.get('total_cost', 0):>12.2f}\n\n"
        
        text += "="*80 + "\n"
        text += " " * 25 + "Thank you for your business!\n"
        text += " " * 25 + "Payment due within 30 days\n"
        text += "="*80 + "\n"
        
        return text
    
    def add_electricity_cost_dialog(self):
        """Add or update electricity cost for an existing invoice"""
        invoices = self.data_manager.data.get("invoices", [])
        
        if not invoices:
            messagebox.showwarning("No Invoices", "No invoices available. Please generate an invoice first.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Electricity Cost")
        
        # Calculate center position
        window_width = 600
        window_height = 400
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Add Electricity Cost", style='Header.TLabel').pack(pady=(0, 20))
        
        # Invoice selection
        ttk.Label(frame, text="Select Invoice:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        invoice_options = [f"#{inv['invoice_id']} - {inv['project_name']} (${inv.get('total_cost', 0):.2f})" for inv in invoices]
        invoice_var = ttk.Combobox(frame, state='readonly', values=invoice_options, font=('Segoe UI', 10))
        invoice_var.pack(fill=tk.X, pady=(0, 15))
        if invoice_options:
            invoice_var.current(0)
        
        # Current electricity info display
        current_label = ttk.Label(frame, text="", font=('Segoe UI', 10), foreground=self.accent_color)
        current_label.pack(anchor=tk.W, pady=(0, 10))
        
        # kWh Used
        ttk.Label(frame, text="kWh Used:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        kwh_entry = ttk.Entry(frame, font=('Segoe UI', 10))
        kwh_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Rate per kWh
        ttk.Label(frame, text="Rate ($/kWh):", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        rate_entry = ttk.Entry(frame, font=('Segoe UI', 10))
        rate_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Calculated cost display
        calc_label = ttk.Label(frame, text="Electricity Cost: $0.00", font=('Segoe UI', 10, 'bold'), foreground='#27ae60')
        calc_label.pack(anchor=tk.W, pady=(5, 15))
        
        def update_calculated_cost(*args):
            try:
                kwh = float(kwh_entry.get())
                rate = float(rate_entry.get())
                cost = kwh * rate
                calc_label.config(text=f"Electricity Cost: ${cost:.2f}")
            except ValueError:
                calc_label.config(text="Electricity Cost: $0.00")
        
        kwh_entry.bind('<KeyRelease>', update_calculated_cost)
        rate_entry.bind('<KeyRelease>', update_calculated_cost)
        
        def update_current_display(*args):
            selection = invoice_var.get()
            if selection:
                invoice_id = int(selection.split('#')[1].split(' - ')[0])
                invoice = next((inv for inv in invoices if inv['invoice_id'] == invoice_id), None)
                if invoice:
                    kwh_used = invoice.get('kwh_used', 0)
                    rate_per_kwh = invoice.get('rate_per_kwh', 0)
                    elec_cost = invoice.get('electricity_cost', 0)
                    current_label.config(text=f"Current: {kwh_used:.2f} kWh × ${rate_per_kwh:.2f}/kWh = ${elec_cost:.2f}")
                    
                    kwh_entry.delete(0, tk.END)
                    kwh_entry.insert(0, str(kwh_used))
                    
                    rate_entry.delete(0, tk.END)
                    rate_entry.insert(0, str(rate_per_kwh))
                    
                    update_calculated_cost()
        
        invoice_var.bind('<<ComboboxSelected>>', update_current_display)
        update_current_display()
        
        def save_electricity_cost():
            selection = invoice_var.get()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an invoice.")
                return
            
            try:
                kwh_used = float(kwh_entry.get())
                rate_per_kwh = float(rate_entry.get())
                new_cost = kwh_used * rate_per_kwh
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values.")
                return
            
            invoice_id = int(selection.split('#')[1].split(' - ')[0])
            
            for invoice in invoices:
                if invoice['invoice_id'] == invoice_id:
                    old_electricity = invoice.get('electricity_cost', 0)
                    invoice['kwh_used'] = kwh_used
                    invoice['rate_per_kwh'] = rate_per_kwh
                    invoice['electricity_cost'] = new_cost
                    invoice['total_cost'] = invoice['labor_cost'] + new_cost
                    
                    self.data_manager.save_data()
                    
                    messagebox.showinfo(
                        "Success",
                        f"Electricity cost updated for Invoice #{invoice_id}\\n\\n"
                        f"kWh Used: {kwh_used:.2f}\\n"
                        f"Rate: ${rate_per_kwh:.2f}/kWh\\n"
                        f"Old Cost: ${old_electricity:.2f}\\n"
                        f"New Cost: ${new_cost:.2f}\\n"
                        f"New Total: ${invoice['total_cost']:.2f}"
                    )
                    
                    self.refresh_invoice_list()
                    dialog.destroy()
                    return
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save", command=save_electricity_cost).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=560, y=10)
    
    def edit_invoice_dialog(self):
        """Edit an existing invoice"""
        invoices = self.data_manager.data.get("invoices", [])
        
        if not invoices:
            messagebox.showwarning("No Invoices", "No invoices available.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Invoice")
        
        # Calculate center position
        window_width = 600
        window_height = 500
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Edit Invoice", style='Header.TLabel').pack(pady=(0, 20))
        
        # Invoice selection
        ttk.Label(frame, text="Select Invoice:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        invoice_options = [f"#{inv['invoice_id']} - {inv['project_name']} (${inv.get('total_cost', 0):.2f})" for inv in invoices]
        invoice_var = ttk.Combobox(frame, state='readonly', values=invoice_options, font=('Segoe UI', 10))
        invoice_var.pack(fill=tk.X, pady=(0, 15))
        if invoice_options:
            invoice_var.current(0)
        
        # Invoice details
        ttk.Label(frame, text="Project Name:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        project_entry = ttk.Entry(frame, font=('Segoe UI', 10), state='readonly')
        project_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Labor Hours:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        labor_hours_entry = ttk.Entry(frame, font=('Segoe UI', 10), state='readonly')
        labor_hours_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Labor Cost ($):", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        labor_cost_entry = ttk.Entry(frame, font=('Segoe UI', 10), state='readonly')
        labor_cost_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="kWh Used:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        kwh_entry = ttk.Entry(frame, font=('Segoe UI', 10))
        kwh_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Rate ($/kWh):", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        rate_entry = ttk.Entry(frame, font=('Segoe UI', 10))
        rate_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Electricity Cost ($):", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        electricity_entry = ttk.Entry(frame, font=('Segoe UI', 10), state='readonly')
        electricity_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Total Cost ($):", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        total_entry = ttk.Entry(frame, font=('Segoe UI', 10), state='readonly')
        total_entry.pack(fill=tk.X, pady=(0, 15))
        
        def update_calculated_fields(*args):
            try:
                kwh = float(kwh_entry.get())
                rate = float(rate_entry.get())
                elec_cost = kwh * rate
                
                electricity_entry.config(state='normal')
                electricity_entry.delete(0, tk.END)
                electricity_entry.insert(0, f"{elec_cost:.2f}")
                electricity_entry.config(state='readonly')
                
                labor = float(labor_cost_entry.get())
                total = labor + elec_cost
                
                total_entry.config(state='normal')
                total_entry.delete(0, tk.END)
                total_entry.insert(0, f"{total:.2f}")
                total_entry.config(state='readonly')
            except ValueError:
                pass
        
        def load_invoice_details(*args):
            selection = invoice_var.get()
            if not selection:
                return
            
            invoice_id = int(selection.split('#')[1].split(' - ')[0])
            invoice = next((inv for inv in invoices if inv['invoice_id'] == invoice_id), None)
            
            if invoice:
                project_entry.config(state='normal')
                project_entry.delete(0, tk.END)
                project_entry.insert(0, invoice.get('project_name', ''))
                project_entry.config(state='readonly')
                
                labor_hours_entry.config(state='normal')
                labor_hours_entry.delete(0, tk.END)
                labor_hours_entry.insert(0, f"{invoice.get('labor_hours', 0):.2f}")
                labor_hours_entry.config(state='readonly')
                
                labor_cost_entry.config(state='normal')
                labor_cost_entry.delete(0, tk.END)
                labor_cost_entry.insert(0, f"{invoice.get('labor_cost', 0):.2f}")
                labor_cost_entry.config(state='readonly')
                
                kwh_entry.delete(0, tk.END)
                kwh_entry.insert(0, f"{invoice.get('kwh_used', 0):.2f}")
                
                rate_entry.delete(0, tk.END)
                rate_entry.insert(0, f"{invoice.get('rate_per_kwh', 0):.2f}")
                
                electricity_entry.config(state='normal')
                electricity_entry.delete(0, tk.END)
                electricity_entry.insert(0, f"{invoice.get('electricity_cost', 0):.2f}")
                electricity_entry.config(state='readonly')
                
                total_entry.config(state='normal')
                total_entry.delete(0, tk.END)
                total_entry.insert(0, f"{invoice.get('total_cost', 0):.2f}")
                total_entry.config(state='readonly')
        
        kwh_entry.bind('<KeyRelease>', update_calculated_fields)
        rate_entry.bind('<KeyRelease>', update_calculated_fields)
        invoice_var.bind('<<ComboboxSelected>>', load_invoice_details)
        load_invoice_details()
        
        def save_changes():
            selection = invoice_var.get()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an invoice.")
                return
            
            try:
                kwh_used = float(kwh_entry.get())
                rate_per_kwh = float(rate_entry.get())
                new_electricity = kwh_used * rate_per_kwh
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values.")
                return
            
            invoice_id = int(selection.split('#')[1].split(' - ')[0])
            
            for invoice in invoices:
                if invoice['invoice_id'] == invoice_id:
                    invoice['kwh_used'] = kwh_used
                    invoice['rate_per_kwh'] = rate_per_kwh
                    invoice['electricity_cost'] = new_electricity
                    invoice['total_cost'] = invoice['labor_cost'] + new_electricity
                    
                    self.data_manager.save_data()
                    
                    messagebox.showinfo("Success", f"Invoice #{invoice_id} updated successfully!")
                    self.refresh_invoice_list()
                    dialog.destroy()
                    return
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=560, y=10)
    
    def delete_invoice_dialog(self):
        """Delete an invoice"""
        invoices = self.data_manager.data.get("invoices", [])
        
        if not invoices:
            messagebox.showwarning("No Invoices", "No invoices available.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Invoice")
        
        # Calculate center position
        window_width = 600
        window_height = 400
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        dialog.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Delete Invoice", style='Header.TLabel').pack(pady=(0, 20))
        
        # Invoice selection with listbox
        ttk.Label(frame, text="Select Invoice to Delete:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(5, 5))
        
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=('Consolas', 9),
                            bg='#34495e', fg=self.fg_color, selectmode=tk.SINGLE)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for inv in invoices:
            display_text = f"#{inv['invoice_id']:<5} {inv['project_name']:<25} Labor: ${inv['labor_cost']:<10.2f} Elec: ${inv.get('electricity_cost', 0):<10.2f} Total: ${inv.get('total_cost', 0):.2f}"
            listbox.insert(tk.END, display_text)
        
        def delete_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an invoice to delete.")
                return
            
            invoice = invoices[selection[0]]
            
            response = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete this invoice?\n\n"
                f"Invoice ID: #{invoice['invoice_id']}\n"
                f"Project: {invoice['project_name']}\n"
                f"Total: ${invoice.get('total_cost', 0):.2f}"
            )
            
            if response:
                invoices.remove(invoice)
                self.data_manager.save_data()
                
                messagebox.showinfo("Success", f"Invoice #{invoice['invoice_id']} deleted successfully.")
                self.refresh_invoice_list()
                dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Delete", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(dialog, text="✕", font=('Segoe UI', 10, 'bold'),
                             bg=self.danger_color, fg='white', relief=tk.FLAT,
                             command=dialog.destroy, cursor='hand2', width=3)
        close_btn.place(x=560, y=10)


def main():
    root = tk.Tk()
    app = TimeClockGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
