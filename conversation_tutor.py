#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversation Tutor Module
ESL/L2 Voice-based Conversation Practice with AI Feedback
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


class ConversationTutor:
    """
    Main class for managing ESL conversation practice sessions.
    Handles the flow: STT → LLM Analysis → TTS Response
    """

    def __init__(self, groq_manager, asr_manager, audio_processor):
        """
        Initialize ConversationTutor with required managers.

        Args:
            groq_manager: Instance of GroqManager for LLM interactions
            asr_manager: Instance of ASRModelManager for speech-to-text
            audio_processor: AudioProcessor class for audio handling
        """
        self.groq_manager = groq_manager
        self.asr_manager = asr_manager
        self.audio_processor = audio_processor

    def process_user_speech(
        self,
        audio_data: bytes,
        conversation_history: List[Dict],
        user_level: str = "B1-B2"
    ) -> Dict:
        """
        Process user's speech input and generate tutor response.

        Args:
            audio_data: Raw audio bytes from user recording
            conversation_history: List of previous conversation turns
            user_level: User's language proficiency level

        Returns:
            Dict with keys:
                - user_transcript: What the user said (STT output)
                - correction: Corrected version of user's speech
                - explanation: Brief grammar/vocab explanation
                - improved_version: Natural reformulation
                - follow_up_question: Question to continue conversation
                - assistant_response: Full response text
                - audio_response: TTS audio bytes for response
                - errors_detected: List of specific errors found
                - timestamp: When this turn occurred
        """

        # Step 1: Speech-to-Text
        try:
            user_transcript = self._transcribe_audio(audio_data)

            if not user_transcript or user_transcript.strip() == "":
                return {
                    "error": "Could not transcribe audio. Please try again.",
                    "timestamp": datetime.now()
                }
        except Exception as e:
            return {
                "error": f"Transcription failed: {str(e)}",
                "timestamp": datetime.now()
            }

        # Step 2: LLM Analysis & Feedback
        try:
            llm_response = self._get_llm_feedback(
                user_transcript,
                conversation_history,
                user_level
            )
        except Exception as e:
            return {
                "error": f"LLM analysis failed: {str(e)}",
                "user_transcript": user_transcript,
                "timestamp": datetime.now()
            }

        # Step 3: Text-to-Speech for response
        try:
            from audio_processor import TTSGenerator

            # Generate audio for full response (for exam mode)
            audio_response = TTSGenerator.generate_audio(
                llm_response['assistant_response']
            )

            # Also generate audio specifically for follow-up question (clearer for practice mode)
            follow_up_audio = None
            if llm_response.get('follow_up_question'):
                follow_up_audio = TTSGenerator.generate_audio(
                    llm_response['follow_up_question']
                )

        except Exception as e:
            audio_response = None
            follow_up_audio = None
            # Non-fatal: user can still read the text response

        # Compile full result
        result = {
            "user_transcript": user_transcript,
            "correction": llm_response.get('correction', ''),
            "explanation": llm_response.get('explanation', ''),
            "improved_version": llm_response.get('improved_version', ''),
            "follow_up_question": llm_response.get('follow_up_question', ''),
            "assistant_response": llm_response.get('assistant_response', ''),
            "errors_detected": llm_response.get('errors_detected', []),
            "audio_response": audio_response,
            "follow_up_audio": follow_up_audio,  # NEW: Dedicated audio for question
            "timestamp": datetime.now()
        }

        return result

    def _transcribe_audio(self, audio_data: bytes) -> str:
        """
        Convert audio bytes to text using ASR model.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Transcribed text
        """
        import io
        import soundfile as sf

        # Load audio
        audio_file = io.BytesIO(audio_data)
        waveform, sr = sf.read(audio_file, dtype='float32')

        # Resample if needed (ASR expects 16kHz)
        if sr != 16000:
            import librosa
            waveform = librosa.resample(waveform, orig_sr=sr, target_sr=16000)
            sr = 16000

        # Transcribe using loaded ASR model
        # Note: transcribe() returns a tuple (decoded_text, phoneme_str)
        result = self.asr_manager.transcribe(waveform, sr, use_g2p=False)

        # Handle tuple or string return
        if isinstance(result, tuple):
            transcript = result[0]  # Get the text part
        else:
            transcript = result

        return transcript.strip() if transcript else ""

    def _get_llm_feedback(
        self,
        user_transcript: str,
        conversation_history: List[Dict],
        user_level: str
    ) -> Dict:
        """
        Get LLM feedback on user's speech with corrections and follow-up.

        Args:
            user_transcript: What the user said
            conversation_history: Previous conversation turns
            user_level: User's proficiency level (e.g., "B1-B2")

        Returns:
            Dict with correction, explanation, improved version, and follow-up question
        """
        from prompt_templates import ConversationPromptTemplate

        # Build prompt with conversation context
        prompt = ConversationPromptTemplate.build_tutor_prompt(
            user_transcript=user_transcript,
            conversation_history=conversation_history,
            user_level=user_level
        )

        # Call Groq LLM
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_manager.api_key)

            response = client.chat.completions.create(
                model=self.groq_manager.model or "llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                temperature=self.groq_manager.temperature or 0.3,
                max_tokens=500
            )

            llm_output = response.choices[0].message.content

            # Parse structured output
            parsed = self._parse_llm_output(llm_output)

            return parsed

        except Exception as e:
            # Fallback: return basic structure
            return {
                "correction": "",
                "explanation": f"Error getting feedback: {str(e)}",
                "improved_version": user_transcript,
                "follow_up_question": "Could you tell me more about that?",
                "assistant_response": f"I heard: '{user_transcript}'. Could you tell me more?",
                "errors_detected": []
            }

    def _parse_llm_output(self, llm_text: str) -> Dict:
        """
        Parse LLM output into structured fields.

        Expected format:
        [CORRECTION]: ...
        [EXPLANATION]: ...
        [IMPROVED VERSION]: ...
        [FOLLOW UP QUESTION]: ...

        Args:
            llm_text: Raw LLM output

        Returns:
            Parsed dict with structured fields
        """
        result = {
            "correction": "",
            "explanation": "",
            "improved_version": "",
            "follow_up_question": "",
            "assistant_response": "",
            "errors_detected": []
        }

        # Parse structured sections
        sections = {
            "[CORRECTION]": "correction",
            "[EXPLANATION]": "explanation",
            "[IMPROVED VERSION]": "improved_version",
            "[FOLLOW UP QUESTION]": "follow_up_question"
        }

        for marker, key in sections.items():
            if marker in llm_text:
                # Extract text after marker until next marker or end
                start = llm_text.find(marker) + len(marker)
                end = len(llm_text)

                # Find next marker
                for other_marker in sections.keys():
                    if other_marker != marker:
                        next_pos = llm_text.find(other_marker, start)
                        if next_pos != -1 and next_pos < end:
                            end = next_pos

                value = llm_text[start:end].strip()
                result[key] = value

        # Build full assistant response
        response_parts = []

        if result['correction']:
            response_parts.append(result['correction'])

        if result['explanation']:
            response_parts.append(result['explanation'])

        if result['improved_version']:
            response_parts.append(f"Better way: {result['improved_version']}")

        if result['follow_up_question']:
            response_parts.append(result['follow_up_question'])

        result['assistant_response'] = "\n\n".join(response_parts)

        # Extract errors if mentioned
        if "error" in result['correction'].lower() or "mistake" in result['correction'].lower():
            result['errors_detected'].append(result['correction'])

        return result


class ConversationSession:
    """
    Manages a single conversation practice session.
    Tracks history, context, and session metadata.
    """

    def __init__(self, session_id: str, user_id: str, topic: Optional[str] = None):
        """
        Initialize a new conversation session.

        Args:
            session_id: Unique identifier for this session
            user_id: User ID from authentication
            topic: Optional conversation topic/theme
        """
        self.session_id = session_id
        self.user_id = user_id
        self.topic = topic or "General conversation practice"
        self.history: List[Dict] = []
        self.started_at = datetime.now()
        self.last_activity = datetime.now()

    def add_turn(self, turn_data: Dict):
        """
        Add a conversation turn to history.

        Args:
            turn_data: Result from ConversationTutor.process_user_speech()
        """
        self.history.append(turn_data)
        self.last_activity = datetime.now()

    def get_history_summary(self, max_turns: int = 5) -> List[Dict]:
        """
        Get recent conversation history for context.

        Args:
            max_turns: Maximum number of recent turns to return

        Returns:
            List of recent conversation turns
        """
        return self.history[-max_turns:] if len(self.history) > max_turns else self.history

    def get_session_stats(self) -> Dict:
        """
        Calculate session statistics.

        Returns:
            Dict with session metrics:
                - total_turns: Number of conversation turns
                - total_errors: Total errors detected
                - duration: Session duration in minutes
                - topics_covered: List of topics discussed
        """
        total_errors = sum(
            len(turn.get('errors_detected', []))
            for turn in self.history
        )

        duration = (self.last_activity - self.started_at).total_seconds() / 60

        return {
            "total_turns": len(self.history),
            "total_errors": total_errors,
            "duration_minutes": round(duration, 1),
            "started_at": self.started_at.isoformat(),
            "topic": self.topic
        }

    def export_to_dict(self) -> Dict:
        """
        Export session to dictionary for storage.

        Returns:
            Dict representation of session
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "topic": self.topic,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "history": [
                {
                    "user_transcript": turn.get('user_transcript', ''),
                    "correction": turn.get('correction', ''),
                    "explanation": turn.get('explanation', ''),
                    "improved_version": turn.get('improved_version', ''),
                    "follow_up_question": turn.get('follow_up_question', ''),
                    "timestamp": turn.get('timestamp', datetime.now()).isoformat(),
                    "errors_count": len(turn.get('errors_detected', []))
                }
                for turn in self.history
            ],
            "stats": self.get_session_stats()
        }
