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
    # if not image_path:
    #     image_path = "data/shutterstock_1667846680-scaled.jpg"

    # corrosion_analysis_file_path = detect_corrosion(image_path)
    # corrosion_text = extract_text(corrosion_analysis_file_path)

    # input_message = (
    #     "Corrosion Analysis: "
    #     + str(corrosion_text)
    #     + "\nIssue Description: "
    #     + str(issue_desc)
    # )
    # if corrosion_text:
    #     corrosion_analysis = chat_with_agent(
    #         user_id="default",
    #         agent_id=settings.CORROSION_AGENT_ID,
    #         session_id=session_id,
    #         message=input_message,
    #     )
    # if corrosion_analysis:
    #     final_output = corrosion_analysis["response"]
    #     return corrosion_analysis_file_path, final_output
    # else:
    #     return "Error: Unable to process image"
    return (
        "detected_corrosion.png",
        "### Corrosion Metrics Assessment\n\n1. **Atmospheric Corrosion Level: 58.58%**\n   - **Severity:** Moderate\n   - **Potential Causes:** The elevated atmospheric corrosion suggests exposure to environmental factors such as humidity, temperature fluctuations, or industrial pollutants. These conditions can lead to the breakdown of protective coatings and subsequent corrosion.\n   - **Monitoring/Mitigation Strategies:** Implement regular inspections to monitor the corrosion progression, and consider applying anti-corrosive coatings after cleaning the affected areas.\n\n2. **Crevice Corrosion Level: 29.11%**\n   - **Severity:** Low\n   - **Potential Causes:** This lower level indicates minor issues, possibly due to water or contaminants being trapped in crevices without sufficient ventilation. It may not be a current concern but warrants attention in future maintenance.\n   - **Monitoring/Mitigation Strategies:** Ensure crevices are cleaned regularly and consider redesigning any components that may trap debris or water.\n\n3. **Pitting Corrosion Level: 12.51%**\n   - **Severity:** Low\n   - **Potential Causes:** The minimal presence of pitting suggests localized corrosion, likely resulting from localized attacks due to poor water drainage or absence of protective barrier in specific areas.\n   - **Monitoring/Mitigation Strategies:** Regular inspections focusing on points where water can accumulate, along with routine cleaning, can help mitigate this issue.\n\n4. **Degradation Index: 46.82%**\n   - **Severity:** Moderate\n   - **Overview:** This index reflects an overall moderate level of degradation which may indicate that while corrosion is not yet critical, it needs to be monitored closely to prevent escalation.\n   - **Monitoring/Mitigation Strategies:** Develop a schedule for more frequent assessments and timely maintenance interventions to address any emerging corrosion.\n\n### Correlation Analysis\nThe presence of moderate atmospheric corrosion may be contributing to the unusual vibrations or noises from the motor. Corrosion can affect tightness in joints and fasteners leading to mechanical looseness, resulting in operational anomalies like vibrations. Additionally, while crevice and pitting corrosion levels are low, they could also be localized factors contributing to wear and tear in critical components, possibly amplifying operational noise due to improper fitment or alignment.\n\n### Overall Assessment\nThe machine exhibits moderate corrosion levels with specific areas of concern that may affect its operation. It is essential to address these issues proactively to ensure safe and efficient functioning.\n\n### Recommendations\n1. **Immediate Action:** Schedule an inspection to determine if the noises and vibrations are directly linked to the corrosion metrics. Focus particularly on joints, fasteners, and areas with atmospheric exposure.\n   \n2. **Routine Maintenance:** Develop a maintenance plan that includes regular inspection intervals and cleaning protocols to mitigate atmospheric and crevice corrosion.\n\n3. **Urgency for Intervention:** The maintenance priority should be set as medium. If issues are not addressed, the machine's performance could degrade further, leading to potential operational failures or safety hazards.\n\n4. **Long-Term Strategy:** Consider investing in more advanced corrosion-resistance materials or coatings when refurbishing or replacing components to enhance durability against atmospheric elements.\n\nFailure to adequately address these corrosion-related issues could escalate into critical failures, increasing downtime and maintenance costs while potentially risking safety.",
    )


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
    # if not image_path:
    #     image_path = "data/handwritten.jpg"

    # handwritten_text = extract_text(image_path)
    # if handwritten_text:
    #     ocr_analysis = chat_with_agent(
    #         user_id="default",
    #         agent_id=settings.OCR_AGENT_ID,
    #         session_id=session_id,
    #         message=str(handwritten_text) + str(issue_desc),
    #     )
    # if ocr_analysis:
    #     final_output = ocr_analysis["response"]
    #     return handwritten_text, final_output, image_path
    # else:
    #     return "Error: Unable to process image"
    return (
        "Physical The machine appeavs to be in stable condition with no visible signs of extevnal damage ov Indicator Light: The ved indicator light suggests the machine is cur vently offline ov in a standby mode. 3, Ouvvoundings: The avea avound the machine is of debvis ov ob- stvuctions. Vo sions of tampeving ov unauthovized access weve observed. 4. Factors: [he ambient is velatively high which may impact Wind speed is modevate Recommendations’ | Immediate Action: Investigate the cause of the ved light and bving the machine back online if safe To do so 2. Maintenance Check: a maintenance inspection to addvess efficiency issues and enevgy loss. 3, Envivonmental Monitoving: Consider implementing cooling ov adjustments to mitigate the impact of high ambient tempevatuves. 4. Opevational Review: Analyze histovical data to identify patterns in enevo loss and",
        "**Analysis of Handwritten Maintenance Notes**\n\n**Issue Description:**\nThe machine appears to be in stable condition with no visible signs of external damage. However, the red indicator light suggests the machine is currently offline or in standby mode.\n\n**Handwritten Text:**\n1. The machine is stable, no visible external damage noted.\n2. Red indicator light indicates machine offline or in standby mode.\n3. Surroundings are cluttered with debris and obstructions.\n4. No signs of tampering or unauthorized access observed.\n5. Ambient conditions are relatively high which may impact machine performance.\n6. Wind speed is moderate.\n7. Recommendations for action:\n   - **Immediate Action**: Investigate the cause of the red light and bring the machine back online safely.\n   - **Maintenance Check**: Conduct a maintenance inspection to address efficiency issues and energy loss.\n   - **Environmental Monitoring**: Implement cooling measures to mitigate the impact of high ambient temperatures.\n   - **Operational Review**: Analyze historical data to identify patterns in energy loss.\n8. Unusual vibrations or noises from the motor have been noted.\n\n**Key Findings:**\n- The machine shows signs of operational issues indicated by the red light, despite its stable physical condition.\n- The presence of debris suggests possible operational hazards that could affect performance.\n- Environmental factors, particularly high ambient temperatures, may adversely impact machine efficiency and performance.\n- Unusual vibrations or noises from the motor indicate a potential underlying problem requiring immediate attention.\n\n**Critical Insights:**\n- The handwritten notes highlight concerns about both operational efficacy and environmental conditions, which are not detailed in the formal issue description.\n- The cluttered surroundings raise alarms about safety and potential impacts on machinery operation.\n- The urgency indicated in the recommendations suggests that delayed action could exacerbate current inefficiencies.\n\n**Conflicts/Discrepancies:**\n- While the formal description does not mention the environmental conditions or the clutter around the machine, these factors could significantly impact maintenance and operational strategy.\n- The unusual noises mentioned do not appear in the formal description, hinting at additional insights from field personnel that require further exploration.\n\n**Patterns/Recurring Themes:**\n- Maintenance checks and environmental considerations are recurring themes, suggesting a history of similar issues in this context.\n- Energy loss appears to be a persistent issue based on the recommendation for operational review.\n\n**Contextual Understanding:**\n- The level of expertise and experience of field personnel is apparent in their identification of both immediate and systemic issues.\n- The notes demonstrate a comprehensive understanding of the operational environment affecting machine performance.\n\n**Effectiveness of Documented Actions:**\n- Recommendations for immediate action and maintenance checks indicate a proactive approach to managing both current machine status and potential future hazards.\n- Implementing environmental monitoring measures is crucial, given the noted high ambient temperatures.\n\n**Areas Needing Further Investigation:**\n- Detailed investigation into the cause of the red indicator light to determine if it is linked to the motor's unusual vibrations or operational inefficiencies.\n- Further assessment of the work environment to address clutter which may impact machine functionality and safety protocols.",
        "data/handwritten.jpg",
    )
