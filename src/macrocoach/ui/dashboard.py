"""
Streamlit dashboard for MacroCoach.
Simple UI for viewing progress and interacting with the system.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configuration
API_BASE_URL = os.getenv("MACROCOACH_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MacroCoach Dashboard",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main dashboard application."""
    
    st.title("🏃‍♂️ MacroCoach Dashboard")
    st.markdown("Your personal nutrition and fitness companion")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        user_id = st.text_input("User ID", value="demo_user")
        
        st.header("🎯 Quick Actions")
        if st.button("📊 Refresh Data"):
            st.experimental_rerun()
        
        if st.button("💬 Open Chat"):
            st.session_state.show_chat = True
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_dashboard(user_id)
    
    with col2:
        show_chat_interface(user_id)

def show_dashboard(user_id: str):
    """Display the main dashboard."""
    
    st.header("📊 Today's Overview")
    
    try:
        # Get user status
        response = requests.get(f"{API_BASE_URL}/api/status/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            daily_summary = data.get("daily_summary", {})
            profile = data.get("profile")
            progress = data.get("progress")
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                kcal_in = daily_summary.get("kcal_in", 0)
                st.metric("🔥 Calories In", f"{kcal_in:.0f}")
            
            with col2:
                kcal_out = daily_summary.get("kcal_out", 0)
                st.metric("🏃 Calories Out", f"{kcal_out:.0f}")
            
            with col3:
                balance = daily_summary.get("kcal_balance", 0)
                st.metric("⚖️ Balance", f"{balance:+.0f}")
            
            with col4:
                steps = daily_summary.get("steps", 0)
                st.metric("👟 Steps", f"{steps:,}")
            
            # Macros chart
            if any([daily_summary.get("protein_g"), daily_summary.get("carbs_g"), daily_summary.get("fat_g")]):
                st.subheader("🥗 Macronutrients")
                
                macros_data = {
                    "Nutrient": ["Protein", "Carbs", "Fat"],
                    "Grams": [
                        daily_summary.get("protein_g", 0),
                        daily_summary.get("carbs_g", 0),
                        daily_summary.get("fat_g", 0)
                    ],
                    "Calories": [
                        daily_summary.get("protein_g", 0) * 4,
                        daily_summary.get("carbs_g", 0) * 4,
                        daily_summary.get("fat_g", 0) * 9
                    ]
                }
                
                df_macros = pd.DataFrame(macros_data)
                
                fig = px.pie(
                    df_macros, 
                    values="Calories", 
                    names="Nutrient",
                    title="Calorie Distribution by Macronutrient",
                    color_discrete_map={
                        "Protein": "#ff6b6b",
                        "Carbs": "#4ecdc4", 
                        "Fat": "#45b7d1"
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Progress section
            if progress:
                st.subheader("📈 7-Day Progress")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Avg Calories/Day", 
                        f"{progress.get('avg_kcal_in', 0):.0f}"
                    )
                
                with col2:
                    st.metric(
                        "Avg Steps/Day", 
                        f"{progress.get('avg_steps', 0):,.0f}"
                    )
                
                with col3:
                    workout_rate = progress.get('workout_days', 0) / progress.get('total_days', 1) * 100
                    st.metric(
                        "Workout Rate", 
                        f"{workout_rate:.0f}%"
                    )
                
                # Weight trend
                weight_trend = progress.get('weight_trend', 'stable')
                trend_emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}
                st.info(f"Weight trend: {trend_emoji.get(weight_trend, '➡️')} {weight_trend}")
            
        else:
            st.error(f"Failed to load data: {response.status_code}")
            st.info("Make sure the MacroCoach API is running on http://localhost:8000")
    
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to MacroCoach API")
        st.info("Please start the API server first: `poetry run uvicorn src.macrocoach.main:app --reload`")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def show_chat_interface(user_id: str):
    """Display the chat interface."""
    
    st.header("💬 Chat with MacroCoach")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm MacroCoach. Ask me about your progress or nutrition plan! 🏃‍♂️"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from API
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={"message": prompt, "user_id": user_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get("response", "Sorry, I couldn't process that.")
            else:
                bot_response = f"Error: {response.status_code}"
        
        except Exception as e:
            bot_response = f"Connection error: {str(e)}"
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        
        with st.chat_message("assistant"):
            st.markdown(bot_response)
    
    # Quick action buttons
    st.markdown("**Quick Commands:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Status", key="quick_status"):
            send_quick_message("/status", user_id)
    
    with col2:
        if st.button("📅 Plan", key="quick_plan"):
            send_quick_message("/plan", user_id)

def send_quick_message(message: str, user_id: str):
    """Send a quick message and display response."""
    
    st.session_state.messages.append({"role": "user", "content": message})
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": message, "user_id": user_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get("response", "Sorry, I couldn't process that.")
        else:
            bot_response = f"Error: {response.status_code}"
    
    except Exception as e:
        bot_response = f"Connection error: {str(e)}"
    
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    st.experimental_rerun()

def show_data_entry():
    """Show manual data entry form."""
    
    st.header("📝 Log Data")
    
    with st.form("data_entry"):
        col1, col2 = st.columns(2)
        
        with col1:
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, step=0.1)
            steps = st.number_input("Steps", min_value=0, max_value=50000, step=100)
            calories = st.number_input("Calories consumed", min_value=0, max_value=5000, step=50)
        
        with col2:
            protein = st.number_input("Protein (g)", min_value=0.0, max_value=300.0, step=1.0)
            workout_type = st.selectbox("Workout Type", ["None", "Strength", "Cardio", "Walking", "Running"])
            rpe = st.slider("RPE (Rate of Perceived Exertion)", 1, 10, 5)
        
        submitted = st.form_submit_button("💾 Log Data")
        
        if submitted:
            # Format data for the /add command
            data_parts = []
            
            if weight > 0:
                data_parts.append(f"weight {weight} kg")
            if steps > 0:
                data_parts.append(f"{steps} steps")
            if calories > 0:
                data_parts.append(f"{calories} calories")
            if protein > 0:
                data_parts.append(f"{protein}g protein")
            if workout_type != "None":
                data_parts.append(f"{workout_type.lower()} workout, rpe {rpe}")
            
            if data_parts:
                message = "/add " + ", ".join(data_parts)
                st.success(f"Logged: {message}")
                # You could auto-send this message to the chat here
            else:
                st.warning("Please enter at least one data point")

if __name__ == "__main__":
    main()
