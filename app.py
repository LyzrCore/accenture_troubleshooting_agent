import os
import uuid

import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# from agent import (
#     analyse_handwritten_data,
#     generate_corrosion_analysis,
#     generate_telemetry_analysis,
#     generate_ticket_history_analysis,
#     troubleshoot_issue,
# )
from graphs import (
    create_comparison_charts,
    create_telemetry_graphs,
    create_ticket_priority_chart,
)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4().hex)


# Streamlit UI
def main():
    st.title("Troubleshooter Agent")

    # Input VIN
    vin = st.text_input("Enter VIN Number:")
    issue_desc = st.text_area("Explain the issue:")

    # Corrosion image
    corrosion_uploaded_image = st.file_uploader("Corrosion image:", type=["jpg", "png"])
    CORROSION_FILE_PATH = os.path.join(BASE_DIR, "data/corrosion_upload.jpg")
    if corrosion_uploaded_image:
        with open(CORROSION_FILE_PATH, "wb") as f:
            f.write(corrosion_uploaded_image.read())

    # Handwriting Image
    handwriting_uploaded_image = st.file_uploader(
        "Handwriting image:", type=["jpg", "png"]
    )
    HANDWRITTEN_FILE_PATH = os.path.join(BASE_DIR, "data/handwritten_upload.jpg")
    if handwriting_uploaded_image:
        with open(HANDWRITTEN_FILE_PATH, "wb") as f:
            f.write(handwriting_uploaded_image.read())

    if st.button("Troubleshoot"):
        if not vin:
            st.error("Please enter a valid VinNumber.")

        if not issue_desc:
            st.error("Please enter the detailed issue description.")

        try:
            # Get telemetry data
            st.header("Step 1: Telemetry Data")
            telemetry_df = pd.read_csv("data/POC Telemetry Data.csv")
            if not telemetry_df.empty:
                # Display last known state
                last_state = telemetry_df.iloc[0]
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Engine Status", last_state["EngineStatus"])
                    st.metric("Alert Status", last_state["AlertStatus"])

                with col2:
                    st.metric("Health Alerts", last_state["HealthAlertCounts"])
                    st.metric("Service Alerts", last_state["ServiceAlertCounts"])

                with col3:
                    st.metric("Security Alerts", last_state["SecurityAlertCounts"])
                    st.metric(
                        "Utilization Alerts", last_state["UtilizationAlertCounts"]
                    )

                # Display telemetry graphs
                utilization_fig = create_telemetry_graphs(telemetry_df)
                if utilization_fig:
                    st.plotly_chart(utilization_fig)

                st.subheader("Fleet Comparison Analysis")
                # fleet_averages = get_fleet_averages(engine)
                fleet_averages = {
                    "avg_working_hours": telemetry_df["WorkingHours"].mean(),
                    "avg_fuel_rate": telemetry_df["FuelConsumptionRate"].mean(),
                    "avg_idle_hours": telemetry_df["EngineIdleHours"].mean(),
                    "avg_total_hours": telemetry_df["TotalMachineHours"].mean(),
                    "avg_fuel_used": telemetry_df["FuelUsed"].mean(),
                }
                # make a dataframe
                fleet_averages = pd.DataFrame(fleet_averages, index=[0])
                comparison_fig = create_comparison_charts(telemetry_df, fleet_averages)

                if comparison_fig:
                    st.plotly_chart(comparison_fig)

                telemetry_analysis = generate_telemetry_analysis(
                    st.session_state.session_id,
                    issue_desc,
                    telemetry_df,
                    fleet_averages,
                )
                st.subheader("Agent Analysis (Telemetry):")
                st.write(telemetry_analysis)
            else:
                st.write("No telemetry data found for this VIN")

            # st.header("Step 2: Vision Inspection Data")
            final_image_path, corrosion_analysis_result = generate_corrosion_analysis(
                st.session_state.session_id, issue_desc, CORROSION_FILE_PATH
            )
            st.image(final_image_path)
            st.write(corrosion_analysis_result)

            # Get ticket history
            st.header("Step 3: Ticket History")
            # ticket_df = get_ticketing_history(engine, vin)
            ticket_df = pd.read_csv("data/POC Ticketing Data_augmented.csv")
            # filter the ticket_df by vin (column name is VinNumber)
            ticket_df = ticket_df[ticket_df["VinNumber"] == vin]
            if not ticket_df.empty:
                st.dataframe(ticket_df)

                # Display ticket priority chart
                priority_chart, calltype_chart = create_ticket_priority_chart(ticket_df)
                if priority_chart and calltype_chart:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(priority_chart, use_container_width=True)
                    with col2:
                        st.plotly_chart(calltype_chart, use_container_width=True)

                ticket_analysis = generate_ticket_history_analysis(
                    st.session_state.session_id, issue_desc, ticket_df
                )
                st.subheader("Agent Analysis (Ticket History):")
                st.write(ticket_analysis)
            else:
                st.write("No ticket history found for this VIN")

            st.header("Step 4: Knowledge Graph Data")
            # kg_analysis_output = generate_knowledge_graph_analysis(
            #     st.session_state.session_id, vin, issue_desc
            # )
            kg_analysis_output = extract_steps_from_kg(
                st.session_state.session_id, issue_desc
            )
            # Print the analysis output
            st.write(kg_analysis_output)

            st.header("Step 5: Handwritten data analysis")
            handwritten_text, handwritten_analysis, image_path = (
                analyse_handwritten_data(
                    st.session_state.session_id,
                    issue_desc,
                    HANDWRITTEN_FILE_PATH,
                )
            )
            st.image(image_path)
            st.write(handwritten_analysis)

            # Troubleshoot
            if issue_desc:
                st.header("Solution: Next best actions")
                troubleshooting_steps = troubleshoot_issue(
                    st.session_state.session_id,
                    issue_desc,
                    telemetry_analysis,
                    corrosion_analysis_result,
                    ticket_analysis,
                    kg_analysis_output,
                    handwritten_analysis,
                )
                st.write(troubleshooting_steps)
            else:
                print("Skipping agent call")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")


# TO REMOVE
import json

import requests

from corrosion_detection import detect_corrosion
from ocr_extraction import extract_text
from settings import settings

base_url = settings.AGENT_STUDIO_CHAT_URL


def chat_with_agent(user_id, agent_id, session_id, message):
    url = base_url
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.LYZR_API_KEY,
    }

    payload = json.dumps(
        {
            "user_id": user_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "message": message,
        }
    )
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        print(f"Other error occurred: {err}")
        return None


def troubleshoot_issue(
    session_id,
    issue_desc,
    telemetry_analysis,
    corrosion_analysis_result,
    ticket_analysis,
    kg_analysis_output,
    handwritten_analysis,
):
    message = (
        "Issue Description: "
        + issue_desc
        + "\nTelemetry Analysis: "
        + telemetry_analysis
        + "\nCorrosion Analysis: "
        + corrosion_analysis_result
        + "\nTicket Analysis: "
        + ticket_analysis
        + "\nHandwritten Analysis: "
        + handwritten_analysis
        + "\nKnowledge Graph Analysis: "
        + str(kg_analysis_output)
    )

    troubleshooting_agent_output = chat_with_agent(
        user_id="default",
        agent_id=settings.TROUBLESHOOTING_AGENT_ID,
        session_id=session_id,
        message=message,
    )

    if troubleshooting_agent_output:
        final_output = troubleshooting_agent_output["response"]
        return final_output
    else:
        return "Error: Unable to troubleshoot."


def generate_telemetry_analysis(session_id, issue_desc, telemetry_df, fleet_averages):
    message = (
        "Telemetry Data: "
        + str(telemetry_df)
        + "\nFleet Averages: "
        + str(fleet_averages)
        + "\nIssue Description: "
        + issue_desc
    )
    telemetry_anlysis_agent_output = chat_with_agent(
        user_id="default",
        agent_id=settings.TELEMETRY_AGENT_ID,
        session_id=session_id,
        message=message,
    )

    if telemetry_anlysis_agent_output:
        final_output = telemetry_anlysis_agent_output["response"]
        return final_output
    else:
        return "Error: Unable to analyze telemetry data."

    # return "[Performance Insights]\n- Working hours are 31.6% below the fleet average, indicating underutilization.\n- Fuel consumption rate is 39.5% above the fleet average, suggesting potential inefficiency.\n- Engine idle hours are slightly above the fleet average, which may indicate unnecessary idling.\n\n[System Health]\n- Notable anomaly: Unusual vibrations may indicate underlying mechanical issues, correlating with high fuel consumption.\n- Resource usage: Current fuel level at 21.5% signals potential need for refueling during operation.\n\n[Additional Context]\n- The significant increase in fuel consumption coincides with the onset of the reported vibrations.\n- Total machine hours are significantly lower than the fleet average, potentially impacting overall productivity."


def generate_ticket_history_analysis(session_id, issue_desc, ticket_df):
    message = "Ticket History: " + str(ticket_df) + "\nIssue Description: " + issue_desc

    ticket_analysis_agent_output = chat_with_agent(
        user_id="default",
        agent_id=settings.TICKET_AGENT_ID,
        session_id=session_id,
        message=message,
    )

    if ticket_analysis_agent_output:
        final_output = ticket_analysis_agent_output["response"]
        return final_output
    else:
        return "Error: Unable to analyze ticket history."
    # return "[Service Patterns]\n- An immediate operational call was placed recently due to mechanical noises, indicating urgency in addressing potential motor issues.\n- Multiple related technical and maintenance tickets created on the same day suggest a coordinated effort to resolve related issues promptly.\n- Priority trend indicates that most recent ticket responses fall within 4-10 hour windows, reflecting priority handling.\n\n[Issue History]\n- Similar incidents involving unusual noises reported recently with multiple ticket categories tied to mechanical concerns.\n- Resolution patterns indicate a quick turnaround for response, typically within 4-10 hours for high-priority calls.\n- Previous issues frequently lead to cascading tickets, suggesting a systematic approach to resolving multi-faceted mechanical problems.\n\n[Additional Context]\n- Notable trend: Increased frequency of urgent calls related to motor performance, potentially signaling underlying systemic issues.\n- Supporting observation: Close correlation between operational distress signals and prompt service response times, implying reliability in addressing critical concerns."


def generate_corrosion_analysis(session_id, issue_desc, image_path=None):
    if not image_path:
        image_path = "data/shutterstock_1667846680-scaled.jpg"
    st.header("Image path:")
    st.write(image_path)
    corrosion_analysis_file_path = detect_corrosion(image_path)
    st.header("Corrosion Detection:")
    st.write(corrosion_analysis_file_path)
    st.image(corrosion_analysis_file_path)
    corrosion_text = extract_text(corrosion_analysis_file_path)
    st.header("Corrosion Text:")
    st.write(corrosion_text)

    input_message = (
        "Corrosion Analysis: "
        + str(corrosion_text)
        + "\nIssue Description: "
        + str(issue_desc)
    )
    if corrosion_text:
        corrosion_analysis = chat_with_agent(
            user_id="default",
            agent_id=settings.CORROSION_AGENT_ID,
            session_id=session_id,
            message=input_message,
        )
    if corrosion_analysis:
        final_output = corrosion_analysis["response"]
        return corrosion_analysis_file_path, final_output
    else:
        return "Error: Unable to process image"
    # return (
    #     "detected_corrosion.png",
    #     "### Corrosion Metrics Assessment\n\n1. **Atmospheric Corrosion Level: 58.58%**\n   - **Severity:** Moderate\n   - **Potential Causes:** The elevated atmospheric corrosion suggests exposure to environmental factors such as humidity, temperature fluctuations, or industrial pollutants. These conditions can lead to the breakdown of protective coatings and subsequent corrosion.\n   - **Monitoring/Mitigation Strategies:** Implement regular inspections to monitor the corrosion progression, and consider applying anti-corrosive coatings after cleaning the affected areas.\n\n2. **Crevice Corrosion Level: 29.11%**\n   - **Severity:** Low\n   - **Potential Causes:** This lower level indicates minor issues, possibly due to water or contaminants being trapped in crevices without sufficient ventilation. It may not be a current concern but warrants attention in future maintenance.\n   - **Monitoring/Mitigation Strategies:** Ensure crevices are cleaned regularly and consider redesigning any components that may trap debris or water.\n\n3. **Pitting Corrosion Level: 12.51%**\n   - **Severity:** Low\n   - **Potential Causes:** The minimal presence of pitting suggests localized corrosion, likely resulting from localized attacks due to poor water drainage or absence of protective barrier in specific areas.\n   - **Monitoring/Mitigation Strategies:** Regular inspections focusing on points where water can accumulate, along with routine cleaning, can help mitigate this issue.\n\n4. **Degradation Index: 46.82%**\n   - **Severity:** Moderate\n   - **Overview:** This index reflects an overall moderate level of degradation which may indicate that while corrosion is not yet critical, it needs to be monitored closely to prevent escalation.\n   - **Monitoring/Mitigation Strategies:** Develop a schedule for more frequent assessments and timely maintenance interventions to address any emerging corrosion.\n\n### Correlation Analysis\nThe presence of moderate atmospheric corrosion may be contributing to the unusual vibrations or noises from the motor. Corrosion can affect tightness in joints and fasteners leading to mechanical looseness, resulting in operational anomalies like vibrations. Additionally, while crevice and pitting corrosion levels are low, they could also be localized factors contributing to wear and tear in critical components, possibly amplifying operational noise due to improper fitment or alignment.\n\n### Overall Assessment\nThe machine exhibits moderate corrosion levels with specific areas of concern that may affect its operation. It is essential to address these issues proactively to ensure safe and efficient functioning.\n\n### Recommendations\n1. **Immediate Action:** Schedule an inspection to determine if the noises and vibrations are directly linked to the corrosion metrics. Focus particularly on joints, fasteners, and areas with atmospheric exposure.\n   \n2. **Routine Maintenance:** Develop a maintenance plan that includes regular inspection intervals and cleaning protocols to mitigate atmospheric and crevice corrosion.\n\n3. **Urgency for Intervention:** The maintenance priority should be set as medium. If issues are not addressed, the machine's performance could degrade further, leading to potential operational failures or safety hazards.\n\n4. **Long-Term Strategy:** Consider investing in more advanced corrosion-resistance materials or coatings when refurbishing or replacing components to enhance durability against atmospheric elements.\n\nFailure to adequately address these corrosion-related issues could escalate into critical failures, increasing downtime and maintenance costs while potentially risking safety.",
    # )


def analyse_knowledge_graph_data(session_id, prompt):
    if prompt:
        kg_analysis = chat_with_agent(
            user_id="default",
            agent_id=settings.KG_AGENT,
            session_id=session_id,
            message=prompt,
        )
    if kg_analysis:
        final_output = kg_analysis["response"]
        return final_output
    else:
        return "Error: Unable to process KG data"


def analyse_handwritten_data(session_id, issue_desc, image_path=None):
    if not image_path:
        image_path = "data/handwritten.jpg"

    handwritten_text = extract_text(image_path)
    if handwritten_text:
        ocr_analysis = chat_with_agent(
            user_id="default",
            agent_id=settings.OCR_AGENT_ID,
            session_id=session_id,
            message=str(handwritten_text) + str(issue_desc),
        )
    if ocr_analysis:
        final_output = ocr_analysis["response"]
        return handwritten_text, final_output, image_path
    else:
        return "Error: Unable to process image"
    # return (
    #     "Physical The machine appeavs to be in stable condition with no visible signs of extevnal damage ov Indicator Light: The ved indicator light suggests the machine is cur vently offline ov in a standby mode. 3, Ouvvoundings: The avea avound the machine is of debvis ov ob- stvuctions. Vo sions of tampeving ov unauthovized access weve observed. 4. Factors: [he ambient is velatively high which may impact Wind speed is modevate Recommendations’ | Immediate Action: Investigate the cause of the ved light and bving the machine back online if safe To do so 2. Maintenance Check: a maintenance inspection to addvess efficiency issues and enevgy loss. 3, Envivonmental Monitoving: Consider implementing cooling ov adjustments to mitigate the impact of high ambient tempevatuves. 4. Opevational Review: Analyze histovical data to identify patterns in enevo loss and",
    #     "**Analysis of Handwritten Maintenance Notes**\n\n**Issue Description:**\nThe machine appears to be in stable condition with no visible signs of external damage. However, the red indicator light suggests the machine is currently offline or in standby mode.\n\n**Handwritten Text:**\n1. The machine is stable, no visible external damage noted.\n2. Red indicator light indicates machine offline or in standby mode.\n3. Surroundings are cluttered with debris and obstructions.\n4. No signs of tampering or unauthorized access observed.\n5. Ambient conditions are relatively high which may impact machine performance.\n6. Wind speed is moderate.\n7. Recommendations for action:\n   - **Immediate Action**: Investigate the cause of the red light and bring the machine back online safely.\n   - **Maintenance Check**: Conduct a maintenance inspection to address efficiency issues and energy loss.\n   - **Environmental Monitoring**: Implement cooling measures to mitigate the impact of high ambient temperatures.\n   - **Operational Review**: Analyze historical data to identify patterns in energy loss.\n8. Unusual vibrations or noises from the motor have been noted.\n\n**Key Findings:**\n- The machine shows signs of operational issues indicated by the red light, despite its stable physical condition.\n- The presence of debris suggests possible operational hazards that could affect performance.\n- Environmental factors, particularly high ambient temperatures, may adversely impact machine efficiency and performance.\n- Unusual vibrations or noises from the motor indicate a potential underlying problem requiring immediate attention.\n\n**Critical Insights:**\n- The handwritten notes highlight concerns about both operational efficacy and environmental conditions, which are not detailed in the formal issue description.\n- The cluttered surroundings raise alarms about safety and potential impacts on machinery operation.\n- The urgency indicated in the recommendations suggests that delayed action could exacerbate current inefficiencies.\n\n**Conflicts/Discrepancies:**\n- While the formal description does not mention the environmental conditions or the clutter around the machine, these factors could significantly impact maintenance and operational strategy.\n- The unusual noises mentioned do not appear in the formal description, hinting at additional insights from field personnel that require further exploration.\n\n**Patterns/Recurring Themes:**\n- Maintenance checks and environmental considerations are recurring themes, suggesting a history of similar issues in this context.\n- Energy loss appears to be a persistent issue based on the recommendation for operational review.\n\n**Contextual Understanding:**\n- The level of expertise and experience of field personnel is apparent in their identification of both immediate and systemic issues.\n- The notes demonstrate a comprehensive understanding of the operational environment affecting machine performance.\n\n**Effectiveness of Documented Actions:**\n- Recommendations for immediate action and maintenance checks indicate a proactive approach to managing both current machine status and potential future hazards.\n- Implementing environmental monitoring measures is crucial, given the noted high ambient temperatures.\n\n**Areas Needing Further Investigation:**\n- Detailed investigation into the cause of the red indicator light to determine if it is linked to the motor's unusual vibrations or operational inefficiencies.\n- Further assessment of the work environment to address clutter which may impact machine functionality and safety protocols.",
    #     "data/handwritten.jpg",
    # )


import json
import re
from collections import defaultdict
from typing import Any, Dict, List

import networkx as nx


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


if __name__ == "__main__":
    main()
