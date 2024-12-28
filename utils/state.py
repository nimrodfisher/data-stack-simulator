import streamlit as st
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class AppState:
    """Class to manage application state"""
    step: int = 1
    infrastructure: Dict = None
    selected_sources: List[str] = None
    volume_estimates: Dict = None
    visualization_seats: int = 1
    excluded_components: List[str] = None

def init_session_state():
    """Initialize or reset the session state"""
    if 'state' not in st.session_state:
        st.session_state.state = AppState()
        st.session_state.state.infrastructure = {}
        st.session_state.state.selected_sources = []
        st.session_state.state.volume_estimates = {}
        st.session_state.state.excluded_components = []

def get_state() -> AppState:
    """Get the current application state"""
    return st.session_state.state

def update_state(**kwargs):
    """Update specific state attributes"""
    for key, value in kwargs.items():
        if hasattr(st.session_state.state, key):
            setattr(st.session_state.state, key, value)
