import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Visualization functions
def create_ticket_priority_chart(df):
    if df.empty:
        return None, None

    # Create Priority chart
    priority_counts = df["Priority"].value_counts()
    priority_fig = px.pie(
        values=priority_counts.values,
        names=priority_counts.index,
        title="Ticket Priority Distribution",
    )

    # Create Call Type chart
    calltype_counts = df["CallType"].value_counts()
    calltype_fig = px.pie(
        values=calltype_counts.values,
        names=calltype_counts.index,
        title="Call Type Distribution",
    )

    return priority_fig, calltype_fig


def create_telemetry_graphs(df):
    if df.empty:
        return None, None

    # Convert relevant columns to numeric
    df["FuelLevelPercentage"] = pd.to_numeric(
        df["FuelLevelPercentage"], errors="coerce"
    )
    df["LastSynchDateTime"] = pd.to_datetime(df["LastSynchDateTime"], errors="coerce")

    # Create utilization graph
    utilization_fig = go.Figure()
    utilization_fig.add_trace(
        go.Bar(
            x=["Total Hours", "Working Hours", "Idle Hours"],
            y=[
                df["TotalMachineHours"].iloc[0],
                df["WorkingHours"].iloc[0],
                df["EngineIdleHours"].iloc[0],
            ],
            name="Hours",
        )
    )
    utilization_fig.update_layout(title="Machine Utilization")

    return utilization_fig


def create_comparison_charts(individual_data, fleet_averages):
    if individual_data.empty or fleet_averages.empty:
        return None

    # Create comparison bar chart
    comparison_fig = go.Figure()

    # Working Hours Comparison
    comparison_fig.add_trace(
        go.Bar(
            name="This Machine",
            x=["Working Hours", "Fuel Consumption Rate", "Idle Hours"],
            y=[
                individual_data["WorkingHours"].iloc[0],
                individual_data["FuelConsumptionRate"].iloc[0],
                individual_data["EngineIdleHours"].iloc[0],
            ],
            marker_color="blue",
        )
    )

    comparison_fig.add_trace(
        go.Bar(
            name="Fleet Average",
            x=["Working Hours", "Fuel Consumption Rate", "Idle Hours"],
            y=[
                fleet_averages["avg_working_hours"].iloc[0],
                fleet_averages["avg_fuel_rate"].iloc[0],
                fleet_averages["avg_idle_hours"].iloc[0],
            ],
            marker_color="gray",
        )
    )

    comparison_fig.update_layout(
        title="Machine vs Fleet Average Comparison",
        barmode="group",
        yaxis_title="Hours / Rate",
    )

    return comparison_fig
