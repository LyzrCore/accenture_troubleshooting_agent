import json
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

import networkx as nx

from agent import analyse_knowledge_graph_data


class MachineErrorSystem:
    """
    Machine Error System with OpenAI-based semantic search.
    Searches by machine type and symptoms/description, returns troubleshooting steps.
    """

    MACHINE_TYPES = {
        "EX": {
            "name": "Excavator",
            "code": "EX",
            "aliases": ["excavator", "digger", "EX machine"],
            "common_errors": {
                "H1234": {
                    "description": "Hydraulic Pressure Too Low",
                    "symptoms": [
                        "Slow or unresponsive hydraulic operations",
                        "Unusual noises from the hydraulic pump",
                        "Visible leaks in the hydraulic lines or connections",
                        "Reduced lifting capacity",
                    ],
                    "steps": [
                        "Inspect Hydraulic Fluid Levels",
                        "Check for Leaks",
                        "Test Hydraulic Pump",
                        "Inspect Relief Valves",
                        "Check Hydraulic Filters",
                        "Clear the DTC Code",
                    ],
                },
                "E5678": {
                    "description": "Engine Overheating",
                    "symptoms": [
                        "Temperature gauge reading consistently high",
                        "Engine warning light activated",
                        "Loss of power or stalling",
                        "Steam or coolant leaks from the engine compartment",
                    ],
                    "steps": [
                        "Inspect Coolant Levels",
                        "Check for Coolant Leaks",
                        "Examine the Radiator Fan",
                        "Inspect the Thermostat",
                        "Check the Water Pump",
                        "Clear the DTC Code",
                    ],
                },
                "M8910": {
                    "description": "Motor Stalling Under Load",
                    "symptoms": [
                        "Motor stalls or hesitates during operation",
                        "Reduced power output",
                        "Unusual vibrations or noises from the motor",
                    ],
                    "steps": [
                        "Inspect Electrical Connections",
                        "Test the Motor Windings",
                        "Examine the Load",
                        "Inspect the Drive Belt or Coupling",
                        "Test the Motor Controller",
                        "Clear the DTC Code",
                    ],
                },
                "H9012": {
                    "description": "Hydraulic Cylinder Malfunction",
                    "symptoms": [
                        "Erratic or uneven cylinder movement",
                        "Hydraulic fluid seeping from the cylinder seals",
                        "Reduced load capacity or failure to extend/retract properly",
                    ],
                    "steps": [
                        "Inspect Cylinder Seals",
                        "Check Hydraulic Lines",
                        "Test Cylinder Operation",
                        "Inspect Control Valves",
                        "Perform System Calibration",
                        "Clear the DTC Code",
                    ],
                },
            },
        }
    }

    def __init__(self):
        self.graph = nx.Graph()
        self.error_index = defaultdict(set)
        self.name_index = {}
        self._initialize_system()

    def _initialize_system(self):
        """Initialize system with machines, errors, and relationships"""
        for machine_code, machine_data in self.MACHINE_TYPES.items():
            self.name_index[machine_data["name"].lower()] = machine_code
            for alias in machine_data["aliases"]:
                self.name_index[alias.lower()] = machine_code

            machine_node = f"machine_{machine_code}"
            self.graph.add_node(machine_node, type="machine", name=machine_data["name"])

            for error_code, error_data in machine_data["common_errors"].items():
                error_node = f"error_{error_code}"
                self.graph.add_node(
                    error_node,
                    type="error",
                    code=error_code,
                    description=error_data["description"],
                    symptoms=error_data["symptoms"],
                    steps=error_data["steps"],
                )
                self.graph.add_edge(machine_node, error_node, relation="has_error")
                self.error_index[error_code].add(machine_code)

    def find_machine_code(self, machine_name: str) -> str:
        """Find the machine type code based on machine name or alias"""
        machine_name = machine_name.lower()
        return self.name_index.get(machine_name, None)

    def search_by_machine_and_error_code(
        self, machine_name: str, error_code: str
    ) -> Dict[str, Any]:
        """Search for a specific error within a machine type"""
        machine_code = self.find_machine_code(machine_name)
        if not machine_code:
            return {"error": f"Machine '{machine_name}' not found."}

        if (
            error_code not in self.error_index
            or machine_code not in self.error_index[error_code]
        ):
            return {
                "error": f"Error code '{error_code}' not found for machine '{machine_name}'."
            }

        return self.get_error_details(error_code)

    def search_by_machine_and_symptoms(
        self, machine_name: str, search_text: str, session_id: str
    ) -> List[Dict[str, Any]]:
        """Search for errors within a machine type based on symptoms or description"""
        machine_code = self.find_machine_code(machine_name)
        if not machine_code:
            return [{"error": f"Machine '{machine_name}' not found."}]

        matching_errors = []
        for error_code, data in self.MACHINE_TYPES[machine_code][
            "common_errors"
        ].items():
            # Combine description and symptoms for searching
            search_content = (
                f"{data['description']} - Symptoms: {'; '.join(data['symptoms'])}"
            )
            matching_errors.append({"id": error_code, "text": search_content})

        if not matching_errors:
            return [{"error": f"No errors found for machine '{machine_name}'."}]

        return self.semantic_search(search_text, matching_errors, session_id)

    def semantic_search(
        self, query: str, items_to_search: List[Dict[str, str]], session_id: str
    ) -> List[Dict[str, Any]]:
        """Perform semantic search within a limited scope (machine-specific errors)."""
        if not items_to_search:
            return [{"error": "No relevant errors found to perform search."}]

        description_to_code = {item["text"]: item["id"] for item in items_to_search}
        valid_error_codes = list(description_to_code.values())

        prompt = f"Given the search text: '{query}', rank the following errors by relevance (0-100). "

        for item in items_to_search:
            prompt += f"- {item['id']}: {item['text']}\n"

        # prompt += (
        #     '\nReturn JSON in the format: {"results": [{"id": "H1234", "score": 85}]}. '
        #     "Only use the error codes provided."
        # )

        try:
            agent_output = analyse_knowledge_graph_data(session_id, prompt)
            raw_content = agent_output.strip()
            cleaned_json = re.sub(r"```json\n|\n```", "", raw_content)

            try:
                results = json.loads(cleaned_json)
            except json.JSONDecodeError:
                return [{"error": f"Invalid JSON response from OpenAI: {cleaned_json}"}]

            if "results" not in results:
                return [{"error": f"Unexpected response format: {results}"}]

            matches = []
            for item in results["results"]:
                error_code = item["id"]
                if error_code not in valid_error_codes:
                    print(f"⚠ Warning: Ignoring unexpected error code '{error_code}'")
                    continue

                error_info = self.get_error_details(error_code, item["score"] / 100)
                if "error" not in error_info:
                    matches.append(error_info)

            if not matches:
                return [
                    {"error": "No relevant matches found based on search criteria."}
                ]

            return matches

        except Exception as e:
            return [{"error": f"Semantic search failed: {str(e)}"}]

    def get_error_details(
        self, error_code: str, similarity: float = None
    ) -> Dict[str, Any]:
        """Retrieve details of a specific error"""
        error_node = f"error_{error_code}"
        if error_node not in self.graph:
            return {"error": f"Error code '{error_code}' not found."}

        error_data = self.graph.nodes[error_node]
        machines = [
            self.graph.nodes[m]["name"]
            for m in self.graph.neighbors(error_node)
            if self.graph.nodes[m]["type"] == "machine"
        ]

        result = {
            "code": error_data["code"],
            "description": error_data["description"],
            "symptoms": error_data["symptoms"],
            "steps": error_data["steps"],
            "machines": machines,
        }
        if similarity:
            result["similarity"] = similarity

        return result


def extract_steps_from_kg(
    session_id, issue_desc: str, machine_name: str = "Excavator"
) -> List[Dict[str, Any]]:
    system = MachineErrorSystem()
    results = system.search_by_machine_and_symptoms(
        machine_name, issue_desc, session_id
    )
    return results[:3]
