import streamlit as st
import websockets
import asyncio
import json
import threading
import time
import queue
from datetime import datetime

# Create a thread-safe queue for message passing
if 'message_queue' not in st.session_state:
    st.session_state.message_queue = queue.Queue()

# Initialize session state variables
if 'connected' not in st.session_state:
    st.session_state.connected = False

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'thread_running' not in st.session_state:
    st.session_state.thread_running = False

# Set page configuration
st.set_page_config(page_title="Agent Metrics", page_icon="📊")

# App title
st.title("Agent Metrics Monitor")

# Single page layout
session_id = st.text_input("Enter Session ID", placeholder="temp_session_id_123")

# Connection controls in a row
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    connect_button = st.button("Connect", type="primary", use_container_width=True)
with col2:
    disconnect_button = st.button("Disconnect", type="secondary", use_container_width=True)
with col3:
    status_text = "Connected" if st.session_state.connected else "Disconnected"
    st.write(f"Status: {status_text}")

# Message display area
st.subheader("Messages")
message_container = st.empty()

# Function to display messages
def update_message_display():
    if st.session_state.messages:
        messages_text = "\n\n".join(st.session_state.messages)
        message_container.code(messages_text)
    else:
        message_container.write("No messages received yet.")

# Define global variables for thread communication
stop_thread = False

# Process for receiving websocket messages
async def websocket_receiver(websocket, message_queue):
    global stop_thread
    try:
        while not stop_thread:
            try:
                # Set timeout to check connection state periodically
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                
                # Process the message
                try:
                    # Try to parse as JSON for prettier display
                    parsed_message = json.loads(message)
                    message_content = json.dumps(parsed_message, indent=2)
                except json.JSONDecodeError:
                    message_content = message
                
                # Add to message queue for main thread to process
                message_queue.put(message_content)
                
            except asyncio.TimeoutError:
                # Just a timeout to check connection state
                pass
    except Exception as e:
        message_queue.put(f"Error: {str(e)}")
        return

# WebSocket connection function
def websocket_thread(session_id, message_queue):
    global stop_thread
    stop_thread = False
    
    async def connect_websocket():
        url = f"wss://metrics.studio.lyzr.ai/ws/{session_id}"
        
        try:
            async with websockets.connect(url) as websocket:
                # Add connection message to queue
                message_queue.put(f"Connected to {url}")
                
                # Start receiving messages
                await websocket_receiver(websocket, message_queue)
                
        except websockets.exceptions.ConnectionClosedError:
            message_queue.put("Connection closed by server")
        except Exception as e:
            message_queue.put(f"Error: {str(e)}")

    # Run the async function in the thread
    asyncio.run(connect_websocket())

# Handle connection/disconnection
if connect_button and not st.session_state.connected and session_id:
    st.session_state.connected = True
    st.session_state.messages = []  # Clear messages on new connection
    
    # Start WebSocket connection in a separate thread if not already running
    if not st.session_state.thread_running:
        thread = threading.Thread(
            target=websocket_thread, 
            args=(session_id, st.session_state.message_queue)
        )
        thread.daemon = True
        thread.start()
        st.session_state.thread_running = True
    
    st.rerun()

if disconnect_button and st.session_state.connected:
    st.session_state.connected = False
    stop_thread = True
    st.session_state.thread_running = False
    st.session_state.messages.append("Disconnected by user")
    st.rerun()

# Clear messages button
if st.button("Clear Messages"):
    st.session_state.messages = []
    st.rerun()

# Process messages from the queue
if st.session_state.connected:
    # Check for new messages
    try:
        while not st.session_state.message_queue.empty():
            message = st.session_state.message_queue.get(block=False)
            st.session_state.messages.append(message)
    except Exception:
        pass

# Display messages
update_message_display()

# Auto-refresh for live updates
if st.session_state.connected:
    refresh_placeholder = st.empty()
    refresh_placeholder.write("Connection active... (auto-refreshing)")
    
    # Set auto-refresh timer (every 2 seconds)
    time.sleep(2)
    st.rerun()