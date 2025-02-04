import json
from datetime import datetime
from typing import Dict, List, Optional

import networkx as nx
import pandas as pd


class DataManager:
    def __init__(self):
        self.G = nx.Graph()
        self.telemetry_history = {}
        self.ticket_history = {}

    def add_telemetry_batch(self, telemetry_df: pd.DataFrame) -> Dict[str, int]:
        """
        Add multiple telemetry records with tracking
        Returns statistics about the ingestion
        """
        stats = {"processed": 0, "errors": 0, "updated": 0}

        for _, row in telemetry_df.iterrows():
            try:
                vin = row["VinNumber"]
                timestamp = pd.to_datetime(row["LastSynchDateTime"])

                # Create unique telemetry ID
                telemetry_id = f"TLM_{vin}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

                # Store telemetry data
                telemetry_data = {
                    "engine_status": row["EngineStatus"],
                    "temperature": row["EngineCoolantTemperture"],
                    "pressure": row["EngineOilPressure"],
                    "hours": row["TotalMachineHours"],
                    "fuel_level": row["FuelLevelPercentage"],
                    "timestamp": timestamp,
                }

                # Add to graph
                self.G.add_node(telemetry_id, type="telemetry", **telemetry_data)

                # Link to machine
                if vin not in self.G:
                    self.G.add_node(
                        vin,
                        type="machine",
                        machine_number=row["MachineNumber"],
                        install_date=row["InstallDate"],
                    )

                self.G.add_edge(vin, telemetry_id, relation="has_telemetry")

                # Update history
                if vin not in self.telemetry_history:
                    self.telemetry_history[vin] = []
                self.telemetry_history[vin].append(telemetry_id)

                stats["processed"] += 1

            except Exception as e:
                print(f"Error processing telemetry for row: {e}")
                stats["errors"] += 1

        return stats

    def add_ticket_batch(self, tickets_df: pd.DataFrame) -> Dict[str, int]:
        """
        Add multiple service tickets with tracking
        Returns statistics about the ingestion
        """
        stats = {"processed": 0, "errors": 0, "linked": 0}

        for _, row in tickets_df.iterrows():
            try:
                vin = row["VinNumber"]
                call_id = str(row["CallId"])

                ticket_data = {
                    "call_type": row["CallType"],
                    "priority": row["Priority"],
                    "created_by": row["CreatedBy"],
                    "assigned_to": row["CallAssigned"],
                    "call_date": pd.to_datetime(row["CallPlaced"]),
                    "serial_number": row["SerialNumber"],
                }

                # Add ticket node
                self.G.add_node(call_id, type="ticket", **ticket_data)

                # Link to machine
                if vin in self.G:
                    self.G.add_edge(vin, call_id, relation="has_ticket")
                    stats["linked"] += 1

                # Update history
                if vin not in self.ticket_history:
                    self.ticket_history[vin] = []
                self.ticket_history[vin].append(call_id)

                stats["processed"] += 1

            except Exception as e:
                print(f"Error processing ticket for row: {e}")
                stats["errors"] += 1

        return stats

    def get_machine_history(self, vin: str) -> Dict:
        """
        Get complete history for a machine including telemetry and tickets
        """
        if vin not in self.G:
            return None

        history = {
            "telemetry": [],
            "tickets": [],
            "machine_info": dict(self.G.nodes[vin]),
        }

        # Get telemetry history
        if vin in self.telemetry_history:
            telemetry_nodes = self.telemetry_history[vin]
            history["telemetry"] = [
                dict(self.G.nodes[t]) for t in telemetry_nodes if t in self.G
            ]

        # Get ticket history
        if vin in self.ticket_history:
            ticket_nodes = self.ticket_history[vin]
            history["tickets"] = [
                dict(self.G.nodes[t]) for t in ticket_nodes if t in self.G
            ]

        return history

    def get_latest_telemetry(self, vin: str) -> Optional[Dict]:
        """Get the most recent telemetry reading for a machine"""
        if vin not in self.telemetry_history:
            return None

        telemetry_nodes = self.telemetry_history[vin]
        if not telemetry_nodes:
            return None

        latest = max(
            telemetry_nodes,
            key=lambda x: (
                self.G.nodes[x]["timestamp"] if x in self.G else pd.Timestamp.min
            ),
        )

        return dict(self.G.nodes[latest]) if latest in self.G else None

    def get_open_tickets(self, vin: str = None) -> List[Dict]:
        """Get all open tickets, optionally filtered by machine"""
        open_tickets = []

        if vin:
            if vin in self.ticket_history:
                ticket_nodes = self.ticket_history[vin]
            else:
                return []
        else:
            ticket_nodes = [
                n for n, d in self.G.nodes(data=True) if d.get("type") == "ticket"
            ]

        for ticket_id in ticket_nodes:
            if ticket_id in self.G:
                ticket_data = dict(self.G.nodes[ticket_id])
                if ticket_data.get("status") != "Closed":
                    open_tickets.append(ticket_data)

        return open_tickets


dm = DataManager()

telemetry_data = pd.read_csv("data/POC Telemetry Data.csv")

ticket_data = pd.read_csv("data/POC Ticketing Data.csv")

telemetry_stats = dm.add_telemetry_batch(telemetry_data)
ticket_stats = dm.add_ticket_batch(ticket_data)


def get_latest_data_from_graph(vin_number):
    latest_telemetry = dm.get_latest_telemetry(vin_number)
    machine_history = dm.get_machine_history(vin_number)
    return latest_telemetry, machine_history

# import networkx as nx
# from fuzzywuzzy import process

# manuals_data = {
#     "H1234": {
#         "description": "Hydraulic Pressure Too Low",
#         "symptoms": [
#             "Slow or unresponsive hydraulic operations",
#             "Unusual noises from the hydraulic pump",
#             "Visible leaks in the hydraulic lines or connections",
#             "Reduced lifting capacity",
#         ],
#         "steps": [
#             "Inspect Hydraulic Fluid Levels",
#             "Check for Leaks",
#             "Test Hydraulic Pump",
#             "Inspect Relief Valves",
#             "Check Hydraulic Filters",
#             "Clear the DTC Code",
#         ],
#     },
#     "E5678": {
#         "description": "Engine Overheating",
#         "symptoms": [
#             "Temperature gauge reading consistently high",
#             "Engine warning light activated",
#             "Loss of power or stalling",
#             "Steam or coolant leaks from the engine compartment",
#         ],
#         "steps": [
#             "Inspect Coolant Levels",
#             "Check for Coolant Leaks",
#             "Examine the Radiator Fan",
#             "Inspect the Thermostat",
#             "Check the Water Pump",
#             "Clear the DTC Code",
#         ],
#     },
#     "M8910": {
#         "description": "Motor Stalling Under Load",
#         "symptoms": [
#             "Motor stalls or hesitates during operation",
#             "Reduced power output",
#             "Unusual vibrations or noises from the motor",
#         ],
#         "steps": [
#             "Inspect Electrical Connections",
#             "Test the Motor Windings",
#             "Examine the Load",
#             "Inspect the Drive Belt or Coupling",
#             "Test the Motor Controller",
#             "Clear the DTC Code",
#         ],
#     },
#     "H9012": {
#         "description": "Hydraulic Cylinder Malfunction",
#         "symptoms": [
#             "Erratic or uneven cylinder movement",
#             "Hydraulic fluid seeping from the cylinder seals",
#             "Reduced load capacity or failure to extend/retract properly",
#         ],
#         "steps": [
#             "Inspect Cylinder Seals",
#             "Check Hydraulic Lines",
#             "Test Cylinder Operation",
#             "Inspect Control Valves",
#             "Perform System Calibration",
#             "Clear the DTC Code",
#         ],
#     },
# }


# G = nx.DiGraph()

# # Add edges from symptoms to steps
# for dtc, data in manuals_data.items():
#     for symptom in data["symptoms"]:
#         for step in data["steps"]:
#             G.add_edge(symptom, step)


# def find_closest_symptom(user_input, symptoms_list, threshold=70):
#     """
#     Finds the closest symptom from the graph using fuzzy matching.
#     :param user_input: Natural language input from the user
#     :param symptoms_list: List of known symptoms in the graph
#     :param threshold: Minimum match score to consider as a match
#     :return: Best matching symptom or None if no match found
#     """
#     match, score = process.extractOne(user_input, symptoms_list)
#     return match if score >= threshold else None

# # Function to get resolution steps for a given symptom
# def get_resolution_steps(user_input):
#     # Extract symptoms from the graph nodes
#     symptoms_list = [node for node in G.nodes if any(step not in node for step in ["Inspect", "Check", "Test", "Clear"])]
    
#     # Find the closest matching symptom
#     closest_symptom = find_closest_symptom(user_input, symptoms_list)
    
#     if closest_symptom:
#         return closest_symptom, list(G.successors(closest_symptom))
#     return None, []

# # Example Query with Natural Language Input
# user_input = "low power output"
# closest_symptom, resolution_steps = get_resolution_steps(user_input)
# if closest_symptom:
#     print(f"Matched Symptom: {closest_symptom}")
#     print(f"Resolution steps: {resolution_steps}")
# else:
#     print("No matching symptom found.")