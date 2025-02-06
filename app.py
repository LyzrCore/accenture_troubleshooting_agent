import uuid

import pandas as pd
import streamlit as st

from agent import (
    analyse_handwritten_data,
    generate_corrosion_analysis,
    generate_telemetry_analysis,
    generate_ticket_history_analysis,
    troubleshoot_issue,
)
from graphs import (
    create_comparison_charts,
    create_telemetry_graphs,
    create_ticket_priority_chart,
)
from knowledge_graph import extract_steps_from_kg

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4().hex)
    st.header("Session ID:")
    st.header(st.session_state.session_id)


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
                    "33f7bdd5-e988-445b-b014-412217ffb94a",
                    issue_desc,
                    telemetry_df,
                    fleet_averages,
                )
                st.subheader("Agent Analysis (Telemetry):")
                st.write(telemetry_analysis)
            else:
                st.write("No telemetry data found for this VIN")

            st.header("Step 2: Vision Inspection Data")
            final_image_path, corrosion_analysis_result = generate_corrosion_analysis(
                st.session_state.session_id, issue_desc, "data/corrosion_upload.jpg"
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
                    "data/handwriting_upload.jpg",
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


if __name__ == "__main__":
    main()
