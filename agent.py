import json

import requests

from corrosion_detection import detect_corrosion
from ocr_extraction import extract_text
from settings import settings

base_url = settings.AGENT_STUDIO_CHAT_URL
feedback_url = settings.AGENT_LEARNING_FEEDBACK_URL
feedback_rag_config_id = settings.FEEDBACK_RAG_ID


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
    
def send_feedback(user_input, agent_output, feedback, agent_id):
    url = feedback_url + "?feedback_rag_config_id=" + feedback_rag_config_id + "&agent_id=" + agent_id
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.LYZR_API_KEY,
    }
    payload = json.dumps(
        {
            "feedback": feedback,
            "user_input": user_input,
            "agent_output": agent_output,
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


def generate_telemetry_analysis(session_id, vin, issue_desc):
    message = "Issue Description: " + issue_desc + "\nVIN: " + vin
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


def generate_ticket_history_analysis(session_id, issue_desc, vin):
    message = "Issue Description: " + issue_desc + "\nVIN: " + vin

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


def generate_corrosion_analysis(session_id, issue_desc, image_path=None):

    corrosion_analysis_file_path = detect_corrosion(image_path)
    corrosion_text = extract_text(corrosion_analysis_file_path)

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


def generate_manager_analysis(session_id, issue_desc, troubleshooting_steps, vin):
    message = (
        "Issue Description: "
        + issue_desc
        + "\nTroubleshooting Steps: "
        + troubleshooting_steps
        + "\nVIN: "
        + vin
    )
    manager_analysis = chat_with_agent(
        user_id="default",
        agent_id=settings.MANAGER_AGENT_ID,
        session_id=session_id,
        message=message,
    )
    if manager_analysis:
        final_output = manager_analysis["response"]
        return final_output
    else:
        return "Error: Unable to process manager analysis"

def send_feedback(user_input, agent_output, feedback, agent_id):
    url = feedback_url + "?feedback_rag_config_id=" + feedback_rag_config_id + "&agent_id=" + agent_id
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.LYZR_API_KEY,
    }
    payload = json.dumps(
        {
            "feedback": feedback,
            "user_input": user_input,
            "agent_output": agent_output,
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