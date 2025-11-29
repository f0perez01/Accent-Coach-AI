#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Writing Coach Manager
Handles writing evaluation, feedback generation, and interview question management.
"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime


class WritingCoachManager:
    """
    Manages writing evaluation workflow for interview practice.

    Responsibilities:
    - Analyze writing with LLM (Groq)
    - Calculate metrics (CEFR level, variety score)
    - Generate polished versions
    - Provide improvement suggestions
    - Extract vocabulary expansions
    """

    # Interview Question Topics
    TOPICS = {
        "Behavioral Questions": [
            {"id": "beh_1", "title": "Tell me about yourself", "category": "Intro",
             "desc": "Craft a compelling professional summary highlighting your experience.", "difficulty": "easy"},
            {"id": "beh_2", "title": "Conflict Resolution", "category": "Teamwork",
             "desc": "Describe a time you had a disagreement with a colleague.", "difficulty": "medium"},
            {"id": "beh_3", "title": "Greatest Weakness", "category": "Self-Awareness",
             "desc": "Discuss a real weakness and steps to improve it.", "difficulty": "medium"}
        ],
        "Technical Experience": [
            {"id": "tech_1", "title": "Project Deep Dive", "category": "System Design",
             "desc": "Explain a complex project focusing on architecture.", "difficulty": "hard"},
            {"id": "tech_2", "title": "Scaling Challenges", "category": "Performance",
             "desc": "Optimize code or infrastructure for scale.", "difficulty": "hard"},
            {"id": "tech_3", "title": "Tech Stack Choice", "category": "Decision Making",
             "desc": "Why did you choose a specific technology? Pros/Cons.", "difficulty": "medium"}
        ],
        "Remote Work & Soft Skills": [
            {"id": "rem_1", "title": "Remote Collaboration", "category": "Communication",
             "desc": "Ensuring effective communication in distributed teams.", "difficulty": "easy"},
            {"id": "rem_2", "title": "Time Management", "category": "Productivity",
             "desc": "Prioritizing tasks without supervision.", "difficulty": "easy"}
        ]
    }

    DIFFICULTY_XP = {"easy": 10, "medium": 20, "hard": 40}

    def __init__(self, groq_manager):
        """
        Initialize WritingCoachManager.

        Args:
            groq_manager: Instance of GroqManager for LLM interactions
        """
        self.groq_manager = groq_manager

    @staticmethod
    def compute_variety_score(text: str) -> int:
        """
        Calculate vocabulary variety score (1-10).

        Args:
            text: Input text to analyze

        Returns:
            Integer score from 1 to 10
        """
        words = re.findall(r"\w+", text.lower())
        if not words:
            return 0
        unique = len(set(words))
        score = int(round(1 + (unique / len(words)) * 9))
        return max(1, min(score, 10))

    @staticmethod
    def _parse_json_safe(raw: str) -> dict:
        """
        Safely parse JSON from LLM response (handles markdown wrappers).

        Args:
            raw: Raw string from LLM

        Returns:
            Parsed dict or empty dict if parsing fails
        """
        try:
            start = raw.index('{')
            end = raw.rindex('}')
            return json.loads(raw[start:end+1])
        except Exception:
            return {}

    def analyze_writing(self, text: str) -> Dict:
        """
        Analyze writing with LLM and return comprehensive feedback.

        Args:
            text: Student's written answer

        Returns:
            Dict with keys:
            - corrected: Polished version
            - improvements: List of improvement suggestions
            - questions: Follow-up interview questions
            - expansion_words: List of vocabulary improvements
            - metrics: {cefr_level, variety_score}
        """
        default_result = {
            "corrected": text,
            "improvements": [],
            "questions": [],
            "expansion_words": [],
            "metrics": {
                "cefr_level": "N/A",
                "variety_score": self.compute_variety_score(text)
            }
        }

        if not self.groq_manager or not self.groq_manager.api_key:
            return default_result

        try:
            from groq import Groq
            client = Groq(api_key=self.groq_manager.api_key)

            prompt = f"""
Role: Senior Tech Recruiter & Communication Coach for US Companies.
Goal: Optimize the candidate's answer for clarity, professionalism, and impact in a remote software engineering interview context.
Input Text: "{text}"

INSTRUCTIONS:
Analyze the text and return a valid JSON object.

REQUIRED JSON STRUCTURE (Do not deviate):
{{
    "metrics": {{
        "cefr_level": "String (e.g., B2, C1, C2)",
        "variety_score": Integer (1-10 based on professional vocabulary)
    }},
    "corrected": "String (Polished, professional version suitable for a job interview)",
    "improvements": ["String (Specific advice on tone, clarity, or STAR method)", "String", "String"],
    "questions": ["String (Follow-up interview question)", "String (Technical or behavioral probe)"],
    "expansion_words": [
        {{
            "word": "String (Power verb or industry term)",
            "ipa": "String (IPA pronunciation)",
            "replaces_simple_word": "String (The weaker word used)",
            "meaning_context": "String (Why this word is better for interviews)"
        }},
        ... (Total 3 items)
    ]
}}
"""

            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You represent a backend API. Output ONLY valid JSON. No markdown."},
                    {"role": "user", "content": prompt}
                ],
                model=self.groq_manager.model or "llama-3.1-8b-instant",
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            data = self._parse_json_safe(completion.choices[0].message.content)
            return {**default_result, **data} if data else default_result

        except Exception as e:
            print(f"Writing analysis error: {e}")
            return default_result

    def generate_teacher_feedback(self, analysis: dict, original_text: str) -> str:
        """
        Generate warm, teacher-style feedback email.

        Args:
            analysis: Analysis result from analyze_writing()
            original_text: Student's original answer

        Returns:
            Friendly feedback email body
        """
        if not self.groq_manager or not self.groq_manager.api_key:
            return "Your feedback is ready, but the AI model is offline."

        try:
            from groq import Groq
            client = Groq(api_key=self.groq_manager.api_key)

            prompt = f"""
You are a friendly English teacher who helps ESL students.
Rewrite the following analysis as warm, constructive feedback.
Tone: kind, supportive, motivating.
Format: an email addressed directly to the student.

Student's original answer:
{original_text}

Analysis data:
{json.dumps(analysis, indent=2)}

Produce ONLY the email body. No JSON, no explanation, no greeting lines like "Here is your email".
"""

            chat = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You write clear, warm English teacher feedback."},
                    {"role": "user", "content": prompt}
                ],
                model=self.groq_manager.model or "llama-3.1-8b-instant",
                temperature=0.4
            )

            return chat.choices[0].message.content.strip()

        except Exception as e:
            print(f"Teacher feedback generation error: {e}")
            return "We couldn't generate feedback due to an AI issue."

    @classmethod
    def calculate_xp_potential(cls, question_ids: List[str]) -> int:
        """
        Calculate potential XP from selected questions.

        Args:
            question_ids: List of question IDs

        Returns:
            Total XP points
        """
        total = 0
        for qid in question_ids:
            for group in cls.TOPICS.values():
                for q in group:
                    if q["id"] == qid:
                        total += cls.DIFFICULTY_XP.get(q.get("difficulty", "easy"), 10)
        return total

    @classmethod
    def get_question_by_id(cls, question_id: str) -> Optional[Dict]:
        """
        Get question details by ID.

        Args:
            question_id: Question identifier

        Returns:
            Question dict or None
        """
        for group in cls.TOPICS.values():
            for q in group:
                if q["id"] == question_id:
                    return q
        return None
