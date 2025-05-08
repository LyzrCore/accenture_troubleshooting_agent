import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from settings import settings

from agent import (
    analyse_handwritten_data,
    generate_corrosion_analysis,
    generate_manager_analysis,
    generate_telemetry_analysis,
    generate_ticket_history_analysis,
    troubleshoot_issue,
    send_feedback
)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache to store analysis results
analysis_cache: Dict[str, Dict[str, Any]] = {}

# Models
class FeedbackRequest(BaseModel):
    vinNumber: str
    issueDescription: str
    agent_output: str
    feedback: str
    stepNumber: int

class FeedbackResponse(BaseModel):
    stepNumber: int
    feedbackReceived: bool
    timestamp: str

# Helper function to save uploaded images
async def save_uploaded_file(file: UploadFile, path: str):
    if file:
        with open(path, "wb") as f:
            f.write(await file.read())
        return path
    return None

# Step 1: Telemetry Analysis
@app.post("/api/steps/1")
async def telemetry_analysis(
    vinNumber: str = Form(...),
    issueDescription: str = Form(...),
    corrosionImage: Optional[UploadFile] = File(None),
    handwritingImage: Optional[UploadFile] = File(None)
):
    try:
        # Save images if uploaded
        if corrosionImage:
            await save_uploaded_file(corrosionImage, f"data/corrosion_upload.jpg")
        if handwritingImage:
            await save_uploaded_file(handwritingImage, f"data/handwriting_upload.jpg")
        
        # Use VIN number as session ID
        session_id = vinNumber
        
        # Generate telemetry analysis
        telemetry_analysis = generate_telemetry_analysis(session_id, vinNumber, issueDescription)
        # telemetry_analysis = "Based on the telemetry data analysis for VIN MAR3DXS4E03123318:\n\nCRITICAL FINDINGS:\n- Engine Oil Pressure reading is at 59, which is within normal operating range, showing no immediate indication of oil clogging.\n- The machine currently shows 'Green' AlertStatus, suggesting no critical system warnings.\n- Last system synchronization occurred on 14-Mar-2024 with the engine currently in 'Off' state.\n\nHEALTH INDICATORS:\n- System has logged 6 Health Alerts and 2 Service Alerts, indicating some historical maintenance needs.\n- The combination of alerts and current oil pressure readings suggests monitoring may be required, despite current 'Green' status.\n\nNote: While the current telemetry data shows stable readings, the presence of multiple health alerts warrants attention to the engine oil system."
        
        # Store in cache
        if session_id not in analysis_cache:
            analysis_cache[session_id] = {}
        analysis_cache[session_id]['telemetry_analysis'] = telemetry_analysis
        analysis_cache[session_id]['issue_description'] = issueDescription
        
        return {
            "stepNumber": 1,
            "output": telemetry_analysis,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "websocket_url": f"wss://metrics.studio.lyzr.ai/ws/{session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Step 2: Vision Inspection (corrosion)
@app.post("/api/steps/2")
async def vision_inspection(
    vinNumber: str = Form(...),
    issueDescription: str = Form(...),
    corrosionImage: Optional[UploadFile] = File(None),
    handwritingImage: Optional[UploadFile] = File(None)
):
    try:
        # Save corrosion image if uploaded
        corrosion_path = "data/corrosion_upload.jpg"
        if corrosionImage:
            await save_uploaded_file(corrosionImage, corrosion_path)
        
        # Use VIN number as session ID
        session_id = vinNumber
        
        # Generate corrosion analysis
        final_image_path, corrosion_analysis = generate_corrosion_analysis(
            session_id, issueDescription, corrosion_path
        )
        # corrosion_analysis = "**Corrosion Metric Assessment:**\n\n1. **Atmospheric Corrosion Level: 63.40% (Moderate Severity)**\n   - The atmospheric corrosion level indicates a moderate degree of corrosion risk. Potential causes could include prolonged exposure to moisture, chemical pollutants, or high humidity environments. This level of corrosion could be contributing to the overall degradation of protective coatings on the machine.\n\n2. **Pitting Corrosion Level: 11.79% (Low Severity)**\n   - The low severity of pitting corrosion suggests minimal localized corrosion activity. Potential causes may include intermittent exposure to aggressive materials or irregular surface conditions. While currently low, it indicates that conditions favoring pitting may be present and should be monitored.\n\n3. **Degradation Index: 23.52% (Low Severity)**\n   - The degradation index at this level indicates a relatively low overall deterioration of the machine's materials. This suggests that, while there are issues, the machine is in a stable condition overall. Potential causes could include normal wear and tear, coupled with low exposure to corrosive environments.\n\n**Analysis of Correlation Between Corrosion Types:**\nThe moderate atmospheric corrosion may be affecting the machine's condition by compromising protective coatings, leading to the development of conditions that could promote pitting corrosion in the future. However, as pitting corrosion currently presents a low severity, it is less likely to be a direct contributor to the immediate issue of clogged engine oil. The degradation index supports this view, indicating that the machine's overall structural integrity has not been significantly compromised at this stage.\n\nThe presence of atmospheric corrosion might indirectly influence oil flow through the potential disruption of machinery components, surface finishes, or seals that could allow for debris accumulation, further contributing to the clogged engine oil issue.\n\n**Overall Assessment:**\nThe machine exhibits a moderate risk of atmospheric corrosion, with minimal pitting and degradation. The clogging of engine oil might be more related to operational factors or the cleanliness of the environment rather than severe corrosion. However, attention to atmospheric corrosion levels is warranted to prevent future complications.\n\n**Priority Level for Maintenance/Intervention:**\nGiven the current corrosion metrics and the issue described, priority for intervention is moderate. While immediate severe corrosion issues are not present, regular monitoring and maintenance will be necessary to ensure atmospheric corrosion does not increase and to address any operational factors leading to the oil clogging."
        
        # Store in cache
        if session_id not in analysis_cache:
            analysis_cache[session_id] = {}
        analysis_cache[session_id]['corrosion_analysis'] = corrosion_analysis
        analysis_cache[session_id]['issue_description'] = issueDescription
        
        return {
            "stepNumber": 2,
            "output": corrosion_analysis,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Step 3: Ticket History Analysis
@app.post("/api/steps/3")
async def ticket_history(
    vinNumber: str = Form(...),
    issueDescription: str = Form(...),
    corrosionImage: Optional[UploadFile] = File(None),
    handwritingImage: Optional[UploadFile] = File(None)
):
    try:
        # Use VIN number as session ID
        session_id = vinNumber
        
        # Generate ticket history analysis
        ticket_analysis = generate_ticket_history_analysis(session_id, issueDescription, vinNumber)
        # ticket_analysis = "1. **Historical Pattern Review**: The VIN MAR3DXS4E03123318 shows multiple ticket entries related to maintenance and technical issues, with varying priorities. The recurring nature of maintenance and technical calls suggests the machine may have ongoing operational challenges.\n\n2. **Issue-Specific Analysis**: There is no past record specifically mentioning engine oil clogs; however, the presence of technical and maintenance calls indicates that operational issues have been addressed. The resolution timeline for technical issues in the past varied between 4-6 hours to 8-10 hours, showing responsiveness in handling critical problems."
        
        # Store in cache
        if session_id not in analysis_cache:
            analysis_cache[session_id] = {}
        analysis_cache[session_id]['ticket_analysis'] = ticket_analysis
        analysis_cache[session_id]['issue_description'] = issueDescription
        
        return {
            "stepNumber": 3,
            "output": ticket_analysis,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Step 4: Handwritten Data Analysis
@app.post("/api/steps/4")
async def handwritten_analysis(
    vinNumber: str = Form(...),
    issueDescription: str = Form(...),
    corrosionImage: Optional[UploadFile] = File(None),
    handwritingImage: Optional[UploadFile] = File(None)
):
    try:
        # Save handwriting image if uploaded
        handwriting_path = "data/handwriting_upload.jpg"
        if handwritingImage:
            await save_uploaded_file(handwritingImage, handwriting_path)
        
        # Use VIN number as session ID
        session_id = vinNumber
        
        # Generate handwritten data analysis
        handwritten_text, handwritten_analysis, image_path = analyse_handwritten_data(
            session_id, issueDescription, handwriting_path
        )
        # handwritten_analysis = "**Key Findings:**\n\n1. **Machine Condition:** The machine is reported to be in stable condition with no visible external damage.\n   \n2. **Indicator Light Status:** A red indicator light is noted, suggesting that the machine is currently offline or in standby mode.\n\n3. **Surroundings:** The area around the machine has debris and obstructions. There are no signs of tampering or unauthorized access.\n\n4. **Environmental Factors:** The ambient temperature is described as relatively high, which may potentially impact machine performance. Wind speed is moderate.\n\n5. **Urgent Recommendations:**\n   - Investigate the cause of the red light and attempt to bring the machine back online if it is safe to do so.\n   - Conduct a maintenance inspection focused on addressing efficiency issues and energy loss.\n   - Consider implementing cooling adjustments to alleviate the impact of high ambient temperatures.\n   - Analyze historical data to identify patterns in energy loss.\n\n6. **Additional Observations:** There is a mention that engine oil is clogged, indicating a potential maintenance issue that needs to be addressed.\n\n**Contextual Understanding:**\nThe maintenance notes provide a comprehensive view of the machine's current status, highlighting both operational concerns and environmental conditions that require attention. The urgency surrounding the red indicator light suggests immediate action is needed to restore functionality. Additionally, the presence of debris may point to an ongoing maintenance concern that could lead to further issues if not resolved. The need for a deeper inspection into efficiency and historical energy loss is critical for long-term machine health."
        
        # Store in cache
        if session_id not in analysis_cache:
            analysis_cache[session_id] = {}
        analysis_cache[session_id]['handwritten_analysis'] = handwritten_analysis
        analysis_cache[session_id]['issue_description'] = issueDescription
        
        return {
            "stepNumber": 4,
            "output": handwritten_analysis,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Step 5: Troubleshooting Steps
@app.post("/api/steps/5")
async def troubleshooting_steps(
    vinNumber: str = Form(...),
    issueDescription: str = Form(...),
    corrosionImage: Optional[UploadFile] = File(None),
    handwritingImage: Optional[UploadFile] = File(None)
):
    try:
        # Use VIN number as session ID
        session_id = vinNumber
        
        # Initialize or update cache entry
        if session_id not in analysis_cache:
            analysis_cache[session_id] = {}
        analysis_cache[session_id]['issue_description'] = issueDescription
        
        # Retrieve data from cache or regenerate if not available
        telemetry_analysis = analysis_cache.get(session_id, {}).get('telemetry_analysis')
        if not telemetry_analysis:
            telemetry_analysis = generate_telemetry_analysis(session_id, vinNumber, issueDescription)
            analysis_cache[session_id]['telemetry_analysis'] = telemetry_analysis
            
        corrosion_analysis = analysis_cache.get(session_id, {}).get('corrosion_analysis')
        if not corrosion_analysis:
            corrosion_path = "data/corrosion_upload.jpg"
            _, corrosion_analysis = generate_corrosion_analysis(session_id, issueDescription, corrosion_path)
            analysis_cache[session_id]['corrosion_analysis'] = corrosion_analysis
            
        ticket_analysis = analysis_cache.get(session_id, {}).get('ticket_analysis')
        if not ticket_analysis:
            ticket_analysis = generate_ticket_history_analysis(session_id, issueDescription, vinNumber)
            analysis_cache[session_id]['ticket_analysis'] = ticket_analysis
            
        handwritten_analysis = analysis_cache.get(session_id, {}).get('handwritten_analysis')
        if not handwritten_analysis:
            handwriting_path = "data/handwriting_upload.jpg"
            _, handwritten_analysis, _ = analyse_handwritten_data(session_id, issueDescription, handwriting_path)
            analysis_cache[session_id]['handwritten_analysis'] = handwritten_analysis
        
        # Placeholder for knowledge graph analysis
        kg_analysis_output = "Knowledge Graph analysis not available"
        
        # Generate troubleshooting steps
        troubleshooting_result = troubleshoot_issue(
            session_id,
            issueDescription,
            telemetry_analysis,
            corrosion_analysis,
            ticket_analysis,
            kg_analysis_output,
            handwritten_analysis,
        ) 
        # troubleshooting_result = "UNRESOLVED\n\nThe issue of clogged engine oil for VIN MAR3DXS4E03123318 cannot be resolved at this time due to the unavailability of the Knowledge Graph analysis. The Knowledge Graph is necessary to provide specific resolution steps, and without it, we cannot retrieve the appropriate measures to address the clogging issue. Additionally, while telemetry and corrosion analyses indicate some contributing factors, the precise corrective actions require a completed Knowledge Graph analysis."
        
        # Store the troubleshooting result in cache
        analysis_cache[session_id]['troubleshooting_result'] = troubleshooting_result
        
        return {
            "stepNumber": 5,
            "output": troubleshooting_result,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Step 6: RCA (Manager) Analysis
@app.post("/api/steps/6")
async def rca_analysis(
    vinNumber: str = Form(...),
    issueDescription: str = Form(...),
    corrosionImage: Optional[UploadFile] = File(None),
    handwritingImage: Optional[UploadFile] = File(None)
):
    try:
        # Use VIN number as session ID
        session_id = vinNumber
        
        # Update cache with latest issue description
        if session_id not in analysis_cache:
            analysis_cache[session_id] = {}
        analysis_cache[session_id]['issue_description'] = issueDescription
        
        # Get troubleshooting result from cache or generate it if missing
        troubleshooting_result = analysis_cache.get(session_id, {}).get('troubleshooting_result')
        if not troubleshooting_result:
            # We need to generate the troubleshooting result
            telemetry_analysis = analysis_cache.get(session_id, {}).get('telemetry_analysis')
            if not telemetry_analysis:
                telemetry_analysis = generate_telemetry_analysis(session_id, vinNumber, issueDescription)
                
            corrosion_analysis = analysis_cache.get(session_id, {}).get('corrosion_analysis')
            if not corrosion_analysis:
                corrosion_path = "data/corrosion_upload.jpg"
                _, corrosion_analysis = generate_corrosion_analysis(session_id, issueDescription, corrosion_path)
                
            ticket_analysis = analysis_cache.get(session_id, {}).get('ticket_analysis')
            if not ticket_analysis:
                ticket_analysis = generate_ticket_history_analysis(session_id, issueDescription, vinNumber)
                
            handwritten_analysis = analysis_cache.get(session_id, {}).get('handwritten_analysis')
            if not handwritten_analysis:
                handwriting_path = "data/handwriting_upload.jpg"
                _, handwritten_analysis, _ = analyse_handwritten_data(session_id, issueDescription, handwriting_path)
            
            kg_analysis_output = "Knowledge Graph analysis not available"
            
            troubleshooting_result = troubleshoot_issue(
                session_id,
                issueDescription,
                telemetry_analysis or "Telemetry data not available",
                corrosion_analysis or "Corrosion analysis not available",
                ticket_analysis or "Ticket history not available",
                kg_analysis_output,
                handwritten_analysis or "Handwritten analysis not available",
            )
            analysis_cache[session_id]['troubleshooting_result'] = troubleshooting_result
        
        # Generate manager analysis
        manager_analysis = generate_manager_analysis(
            session_id,
            issueDescription,
            troubleshooting_result,
            vinNumber,
        )
        # manager_analysis = "VIN: MAR3DXS4E03123318  \nIssue: Engine oil is clogged  \n\nAdvanced Troubleshooting Steps:  \n1. Check and top up the engine oil level, using the correct oil grade.  \n2. Replace the oil filter to restore proper oil flow.  \n3. Inspect engine seals and gaskets for leaks; repair or replace any damaged parts.  \n4. Test oil pump performance with a pressure gauge; replace the pump if it fails to meet specifications.  \n5. Clean internal oil passages to remove sludge or debris buildup.  \n6. Verify the accuracy of the oil pressure sensor and replace it if readings are out of tolerance."
        
        # Store the manager analysis in cache
        analysis_cache[session_id]['manager_analysis'] = manager_analysis
        
        return {
            "stepNumber": 6,
            "output": manager_analysis,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
step_agent_id_mapping = {
    0: settings.TELEMETRY_AGENT_ID,
    1: settings.CORROSION_AGENT_ID,
    2: settings.TICKET_AGENT_ID,
    3: settings.OCR_AGENT_ID,
    4: settings.TROUBLESHOOTING_AGENT_ID,
    5: settings.MANAGER_AGENT_ID
}

# Feedback Submission
@app.post("/api/steps/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback_request: FeedbackRequest):
    try:
        user_input = "VIN: " + feedback_request.vinNumber + " " + "Issue: " + feedback_request.issueDescription
        feedback_response = send_feedback(user_input, feedback_request.agent_output, feedback_request.feedback, step_agent_id_mapping[feedback_request.stepNumber])
        return FeedbackResponse(
            stepNumber=feedback_request.stepNumber,
            feedbackReceived=True,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Troubleshooter Agent API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 