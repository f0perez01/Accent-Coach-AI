from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import streamlit as st
import extra_streamlit_components as stx


class SessionManager:
    """Manages authentication UI, session state, and history loading.
    
    Responsibilities:
    - Handle login/register forms and validation
    - Restore session from cookies
    - Load user analysis history
    - Manage session-level state
    """

    def __init__(self, login_callback, register_callback, get_history_callback):
        """
        Args:
            login_callback: Function(email, password) -> dict with 'error' or 'idToken'
            register_callback: Function(email, password) -> dict with 'error' or 'idToken'
            get_history_callback: Function(user_id) -> list of history dicts
        """
        self.login_callback = login_callback
        self.register_callback = register_callback
        self.get_history_callback = get_history_callback
        self.cookie_manager = stx.CookieManager(key="auth_cookies_accent")

    def restore_session_from_cookie(self):
        """Try to restore user from saved auth token. Returns user dict or None."""
        token = self.cookie_manager.get(cookie="auth_token")
        if token:
            try:
                # For now, return a minimal user dict; in real Firebase you'd verify the token
                return {"token": token}
            except Exception:
                pass
        return None

    def render_login_ui(self) -> Tuple[bool, Optional[dict]]:
        """Render login/register tabs and return (should_return, user_data).
        
        Returns:
            (True, user_dict) if login successful
            (True, None) if auth UI shown and user should not proceed
            (False, None) if user already authenticated
        """
        if st.session_state.user:
            return False, None  # User already authenticated

        st.title("🔐 Accent Coach AI - Login")
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    data = self.login_callback(email, password)
                    if "error" in data:
                        st.error(data["error"])
                    else:
                        st.session_state.user = data
                        self.cookie_manager.set(
                            "auth_token",
                            data["idToken"],
                            expires_at=datetime.now() + timedelta(days=7)
                        )
                        st.success("Login successful!")
                        st.rerun()
            return True, None

        with tab2:
            with st.form("register_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                password_confirm = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Register"):
                    if password != password_confirm:
                        st.error("Passwords don't match!")
                    else:
                        data = self.register_callback(email, password)
                        if "error" in data:
                            st.error(data["error"])
                        else:
                            st.success("Registration successful! Please login.")
        return True, None

    def render_user_info_and_history(self, user: dict) -> Tuple[str, str]:
        """Render user info in sidebar and handle history selection.
        
        Returns:
            (reference_text, selected_history_label)
        """
        st.write(f"👤 **{user['email']}**")
        st.divider()

        # --- HISTORY LOADER ---
        st.header("📜 History")
        history = self.get_history_callback(user.get('localId', ''))

        # Create options for selectbox
        history_options = {}
        if history:
            for h in history:
                timestamp_str = (
                    h.get('timestamp').strftime('%d/%m %H:%M')
                    if h.get('timestamp')
                    else 'Unknown'
                )
                text_preview = (
                    h.get('original_text', '')[:30] + "..."
                    if len(h.get('original_text', '')) > 30
                    else h.get('original_text', '')
                )
                label = f"{timestamp_str} - {text_preview}"
                history_options[label] = h

        selected_history = st.selectbox(
            "Select from history or start new",
            ["📝 New Practice Session"] + list(history_options.keys())
        )

        # Load selected history or start new session
        reference_text = ""
        if selected_history != "📝 New Practice Session":
            doc = history_options[selected_history]
            reference_text = doc.get('original_text', '')

            # Reset current_doc_id since we're loading a writing practice text
            if st.session_state.get("current_doc_id") != doc['id']:
                st.session_state.current_doc_id = doc['id']
                st.session_state.pop("previous_result", None)
                st.session_state.current_result = None
                st.rerun()

            st.info("📖 Practice pronunciation for this text from your writing history!")
            st.caption(
                f"**Text:** {reference_text[:50]}{'...' if len(reference_text) > 50 else ''}"
            )
        else:
            # New session - reset
            if st.session_state.get("current_doc_id"):
                st.session_state.current_doc_id = None
                st.session_state.pop("previous_result", None)
                st.session_state.current_result = None
                st.rerun()

        return reference_text, selected_history

    def render_logout_button(self) -> bool:
        """Render logout button. Returns True if user clicked logout."""
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            self.cookie_manager.delete("auth_token")
            st.rerun()
            return True
        return False
