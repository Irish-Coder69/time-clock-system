"""
Time Clock Program with Hourly Wage Tracking
Tracks employee clock in/out times and calculates wages
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from time_clock_paths import get_data_file_path


class TimeClock:
    def __init__(self, data_file: str = None):
        self.data_file = data_file if data_file is not None else get_data_file_path()
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        """Load time clock data from JSON file"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {"employees": {}, "time_entries": []}
    
    def save_data(self):
        """Save time clock data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_employee(self, employee_id: str, name: str, hourly_rate: float):
        """Add a new employee to the system"""
        if employee_id in self.data["employees"]:
            print(f"Employee {employee_id} already exists!")
            return False
        
        self.data["employees"][employee_id] = {
            "name": name,
            "hourly_rate": hourly_rate,
            "clocked_in": False,
            "current_entry": None
        }
        self.save_data()
        print(f"Employee {name} added successfully with hourly rate: ${hourly_rate:.2f}")
        return True
    
    def update_hourly_rate(self, employee_id: str, new_rate: float):
        """Update an employee's hourly rate"""
        if employee_id not in self.data["employees"]:
            print(f"Employee {employee_id} not found!")
            return False
        
        old_rate = self.data["employees"][employee_id]["hourly_rate"]
        self.data["employees"][employee_id]["hourly_rate"] = new_rate
        self.save_data()
        print(f"Hourly rate updated from ${old_rate:.2f} to ${new_rate:.2f}")
        return True
    
    def clock_in(self, employee_id: str):
        """Clock in an employee"""
        if employee_id not in self.data["employees"]:
            print(f"Employee {employee_id} not found!")
            return False
        
        employee = self.data["employees"][employee_id]
        
        if employee["clocked_in"]:
            print(f"{employee['name']} is already clocked in!")
            return False
        
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
            "wages": 0
        }
        
        self.data["time_entries"].append(entry)
        self.save_data()
        
        print(f"{employee['name']} clocked in at {datetime.fromisoformat(clock_in_time).strftime('%Y-%m-%d %I:%M:%S %p')}")
        return True
    
    def clock_out(self, employee_id: str):
        """Clock out an employee and calculate wages"""
        if employee_id not in self.data["employees"]:
            print(f"Employee {employee_id} not found!")
            return False
        
        employee = self.data["employees"][employee_id]
        
        if not employee["clocked_in"]:
            print(f"{employee['name']} is not clocked in!")
            return False
        
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
        
        print(f"\n{employee['name']} clocked out at {clock_out_dt.strftime('%Y-%m-%d %I:%M:%S %p')}")
        print(f"Hours worked: {entry['hours_worked']:.2f}")
        print(f"Hourly rate: ${entry['hourly_rate']:.2f}")
        print(f"Wages earned: ${entry['wages']:.2f}\n")
        return True
    
    def view_employee_status(self, employee_id: str):
        """View current status of an employee"""
        if employee_id not in self.data["employees"]:
            print(f"Employee {employee_id} not found!")
            return
        
        employee = self.data["employees"][employee_id]
        print(f"\n--- Employee Status ---")
        print(f"Name: {employee['name']}")
        print(f"ID: {employee_id}")
        print(f"Hourly Rate: ${employee['hourly_rate']:.2f}")
        print(f"Status: {'CLOCKED IN' if employee['clocked_in'] else 'CLOCKED OUT'}")
        
        if employee['clocked_in']:
            entry = self.data["time_entries"][employee["current_entry"]]
            clock_in_dt = datetime.fromisoformat(entry["clock_in"])
            print(f"Clocked in at: {clock_in_dt.strftime('%Y-%m-%d %I:%M:%S %p')}")
        print()
    
    def list_employees(self):
        """List all employees"""
        if not self.data["employees"]:
            print("No employees in the system.")
            return
        
        print("\n--- All Employees ---")
        for emp_id, emp in self.data["employees"].items():
            status = "CLOCKED IN" if emp["clocked_in"] else "CLOCKED OUT"
            print(f"{emp_id}: {emp['name']} - ${emp['hourly_rate']:.2f}/hr - {status}")
        print()
    
    def view_time_entries(self, employee_id: Optional[str] = None):
        """View time entries, optionally filtered by employee"""
        entries = self.data["time_entries"]
        
        if employee_id:
            entries = [e for e in entries if e["employee_id"] == employee_id]
            if not entries:
                print(f"No time entries found for employee {employee_id}")
                return
        
        if not entries:
            print("No time entries found.")
            return
        
        print("\n--- Time Entries ---")
        for i, entry in enumerate(entries, 1):
            print(f"\nEntry #{i}")
            print(f"Employee: {entry['name']} ({entry['employee_id']})")
            
            clock_in_dt = datetime.fromisoformat(entry["clock_in"])
            print(f"Clock In: {clock_in_dt.strftime('%Y-%m-%d %I:%M:%S %p')}")
            
            if entry["clock_out"]:
                clock_out_dt = datetime.fromisoformat(entry["clock_out"])
                print(f"Clock Out: {clock_out_dt.strftime('%Y-%m-%d %I:%M:%S %p')}")
                print(f"Hours Worked: {entry['hours_worked']:.2f}")
                print(f"Hourly Rate: ${entry['hourly_rate']:.2f}")
                print(f"Wages Earned: ${entry['wages']:.2f}")
            else:
                print(f"Clock Out: Still clocked in")
        print()
    
    def calculate_total_wages(self, employee_id: Optional[str] = None):
        """Calculate total wages, optionally for a specific employee"""
        entries = self.data["time_entries"]
        
        if employee_id:
            entries = [e for e in entries if e["employee_id"] == employee_id]
            employee_name = self.data["employees"].get(employee_id, {}).get("name", "Unknown")
        
        completed_entries = [e for e in entries if e["clock_out"] is not None]
        
        if not completed_entries:
            print("No completed time entries found.")
            return
        
        total_hours = sum(e["hours_worked"] for e in completed_entries)
        total_wages = sum(e["wages"] for e in completed_entries)
        
        print("\n--- Wage Summary ---")
        if employee_id:
            print(f"Employee: {employee_name} ({employee_id})")
        else:
            print("All Employees")
        print(f"Total Hours Worked: {total_hours:.2f}")
        print(f"Total Wages: ${total_wages:.2f}\n")


def main():
    """Main program loop"""
    clock = TimeClock()
    
    while True:
        print("\n========== TIME CLOCK SYSTEM ==========")
        print("1. Add Employee")
        print("2. Update Hourly Rate")
        print("3. Clock In")
        print("4. Clock Out")
        print("5. View Employee Status")
        print("6. List All Employees")
        print("7. View Time Entries")
        print("8. Calculate Total Wages")
        print("9. Exit")
        print("=======================================")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == "1":
            emp_id = input("Enter employee ID: ").strip()
            name = input("Enter employee name: ").strip()
            try:
                rate = float(input("Enter hourly rate: $").strip())
                clock.add_employee(emp_id, name, rate)
            except ValueError:
                print("Invalid hourly rate!")
        
        elif choice == "2":
            emp_id = input("Enter employee ID: ").strip()
            try:
                rate = float(input("Enter new hourly rate: $").strip())
                clock.update_hourly_rate(emp_id, rate)
            except ValueError:
                print("Invalid hourly rate!")
        
        elif choice == "3":
            emp_id = input("Enter employee ID: ").strip()
            clock.clock_in(emp_id)
        
        elif choice == "4":
            emp_id = input("Enter employee ID: ").strip()
            clock.clock_out(emp_id)
        
        elif choice == "5":
            emp_id = input("Enter employee ID: ").strip()
            clock.view_employee_status(emp_id)
        
        elif choice == "6":
            clock.list_employees()
        
        elif choice == "7":
            emp_id = input("Enter employee ID (or press Enter for all): ").strip()
            clock.view_time_entries(emp_id if emp_id else None)
        
        elif choice == "8":
            emp_id = input("Enter employee ID (or press Enter for all): ").strip()
            clock.calculate_total_wages(emp_id if emp_id else None)
        
        elif choice == "9":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice! Please try again.")


if __name__ == "__main__":
    main()
