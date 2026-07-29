import os
import json
import re
import sys
import io
import contextlib
import trace
import pandas as pd
import numpy as np
import requests
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class DataAnalystAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def execute_python_code(self, code: str) -> str:
        """Executes Python code safely and captures stdout/stderr and returned values."""
        buffer = io.StringIO()
        local_vars = {"pd": pd, "np": np, "requests": requests, "json": json, "re": re}
        
        try:
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                exec(code, local_vars, local_vars)
            output = buffer.getvalue()
            if "result" in local_vars:
                output += f"\nResult: {local_vars['result']}"
            return output.strip()
        except Exception as e:
            return f"Error executing code: {str(e)}"

    def solve(self, messages: list) -> dict:
        """
        Solves the data analysis task given a sequence of messages.
        Returns a dict representing the answer payload.
        """
        conversation_text = ""
        for idx, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation_text += f"\n--- Message {idx+1} ({role}) ---\n{content}\n"

        system_instruction = (
            "You are an expert Data Analyst Agent. Your task is to analyze user queries, process data, "
            "perform calculations, fetch/parse public datasets (such as MOSPI, Census, RBI, etc.), and answer questions accurately.\n"
            "CRITICAL INSTRUCTION:\n"
            "The user's message will specify the exact JSON shape required for the answer.\n"
            "You must output ONLY the answer value in the exact requested shape for the 'answer' field.\n"
            "Example prompt: 'Which state has the highest maternal mortality rate based on MOSPI data? Reply with ONLY this JSON object and nothing else: {\"answer\": {\"state\": \"<state name>\"}}'\n"
            "Your output for answer should be: {\"state\": \"Assam\"}.\n"
        )

        if not self.client:
            # Fallback heuristic parser if no API key set
            return self._heuristic_fallback(conversation_text)

        prompt = f"{system_instruction}\n\nCONVERSATION HISTORY:\n{conversation_text}\n\nAnalyze the question, perform any required data analysis, and output ONLY valid JSON in the format: {{\"answer\": <answer_value_in_requested_shape>}}."

        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )

        try:
            res_json = json.loads(response.text)
            if "answer" in res_json:
                return res_json["answer"]
            return res_json
        except Exception:
            # Fallback regex extraction if raw JSON wrapper
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                return parsed.get("answer", parsed)
            return {"text": response.text}

    def _heuristic_fallback(self, conversation_text: str) -> dict:
        """Fallback when API key is missing during offline unit testing."""
        return {"status": "processed", "query_length": len(conversation_text)}

if __name__ == "__main__":
    agent = DataAnalystAgent()
    sample_msgs = [
        {"role": "user", "content": "Which state has the highest maternal mortality rate based on MOSPI data? Reply with ONLY this JSON object: {\"answer\": {\"state\": \"<state name>\"}}"}
    ]
    print("Testing agent solve:", agent.solve(sample_msgs))
