import pandas as pd
from sqlalchemy import text


# Query functions
def get_ticketing_history(engine, vin):
    query = """
    SELECT 
        "CallId",
        "CallPlaced",
        "CallType",
        "Priority",
        "CreatedBy",
        "CallAssigned"
    FROM "POC Ticketing Data"
    WHERE "VinNumber" = :vin
    ORDER BY "CallPlaced" DESC
    """
    return pd.read_sql_query(text(query), engine, params={"vin": vin})


def get_telemetry_data(engine, vin):
    query = """
    SELECT 
        "EngineStatus",
        "AlertStatus",
        "TotalMachineHours",
        "FuelLevelPercentage",
        "LastSynchDateTime",
        "HealthAlertCounts",
        "ServiceAlertCounts",
        "SecurityAlertCounts",
        "UtilizationAlertCounts",
        "EngineCoolantTemperture",
        "EngineOilPressure",
        "MachineBattery",
        "OperatingHours",
        "WorkingHours",
        "EngineIdleHours",
        "FuelUsed",
        "FuelConsumptionRate"
    FROM "POC Telemetry Data"
    WHERE "VinNumber" = :vin
    """
    return pd.read_sql_query(text(query), engine, params={"vin": vin})


def get_fleet_averages(engine):
    """Get average metrics for the entire fleet"""
    query = """
    SELECT 
        AVG("WorkingHours") as avg_working_hours,
        AVG("FuelConsumptionRate") as avg_fuel_rate,
        AVG("EngineIdleHours") as avg_idle_hours,
        AVG("TotalMachineHours") as avg_total_hours,
        AVG("FuelUsed") as avg_fuel_used
    FROM "POC Telemetry Data"
    WHERE 
        "WorkingHours" IS NOT NULL 
        AND "FuelConsumptionRate" IS NOT NULL
    """
    return pd.read_sql_query(text(query), engine)
