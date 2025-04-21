import os
import uuid

import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from agent import (
    analyse_handwritten_data,
    generate_corrosion_analysis,
    generate_manager_analysis,
    generate_telemetry_analysis,
    generate_ticket_history_analysis,
    troubleshoot_issue,
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
    if corrosion_uploaded_image:
        with open(f"data/corrosion_upload.jpg", "wb") as f:
            f.write(corrosion_uploaded_image.read())

    # Handwriting Image
    handwriting_uploaded_image = st.file_uploader(
        "Handwriting image:", type=["jpg", "png"]
    )
    if handwriting_uploaded_image:
        with open(f"data/handwriting_upload.jpg", "wb") as f:
            f.write(handwriting_uploaded_image.read())

    if st.button("Troubleshoot"):
        if not vin:
            st.error("Please enter a valid VinNumber.")

        if not issue_desc:
            st.error("Please enter the detailed issue description.")

        try:
            # Get telemetry data
            st.header("Step 1: Telemetry Data")
            telemetry_analysis = generate_telemetry_analysis(
                st.session_state.session_id,
                vin,
                issue_desc,
            )
            st.subheader("Agent Analysis (Telemetry):")
            st.write(telemetry_analysis)

            st.header("Step 2: Vision Inspection Data")
            final_image_path, corrosion_analysis_result = generate_corrosion_analysis(
                st.session_state.session_id, issue_desc, "data/corrosion_upload.jpg"
            )
            st.image(final_image_path)
            st.write(corrosion_analysis_result)

            # Get ticket history
            st.header("Step 3: Ticket History")
            ticket_analysis = generate_ticket_history_analysis(
                st.session_state.session_id, issue_desc, vin
            )
            st.subheader("Agent Analysis (Ticket History):")
            st.write(ticket_analysis)

            # st.header("Step 4: Knowledge Graph Data")
            # kg_analysis_output = extract_steps_from_kg(
            #     st.session_state.session_id, issue_desc
            # )
            # # Print the analysis output
            # st.write(kg_analysis_output)

            st.header("Step 5: Handwritten data analysis")
            handwritten_text, handwritten_analysis, image_path = (
                analyse_handwritten_data(
                    st.session_state.session_id,
                    issue_desc,
                    "data/handwriting_upload.jpg",
                )
            )
            st.image(image_path)
            st.write(handwritten_analysis)

            # Troubleshoot
            kg_analysis_output = "Knowledge Graph analysis not available"
            st.header("Step 6: Troubleshooting Steps")
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

            st.header("Step 7: Manager Analysis")
            manager_analysis = generate_manager_analysis(
                st.session_state.session_id,
                issue_desc,
                troubleshooting_steps,
                vin,
            )
            st.write(manager_analysis)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
