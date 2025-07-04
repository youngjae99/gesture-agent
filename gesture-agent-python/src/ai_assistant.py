import os
import json
import time
from typing import Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class AIAssistant:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = os.getenv('ASSISTANT_ID')
        self.thread_id = None
        self.conversation_history = []
        
        if not self.assistant_id:
            self.assistant_id = self._create_default_assistant()
    
    def _create_default_assistant(self) -> str:
        assistant = self.client.beta.assistants.create(
            name="GestureAgent Assistant",
            instructions="""You are a helpful AI assistant activated by hand gestures. 
            When users interact with you through gestures, provide concise, helpful responses.
            If a screenshot is mentioned, acknowledge it and provide relevant assistance based on screen content.
            Keep responses brief but informative, as they'll be displayed in a popup window.""",
            model="gpt-4",
            tools=[]
        )
        return assistant.id
    
    def _create_thread(self) -> str:
        thread = self.client.beta.threads.create()
        return thread.id
    
    def _get_or_create_thread(self) -> str:
        if not self.thread_id:
            self.thread_id = self._create_thread()
        return self.thread_id
    
    def send_message(self, content: str, screenshot_path: Optional[str] = None) -> str:
        try:
            thread_id = self._get_or_create_thread()
            
            message_content = content
            if screenshot_path and os.path.exists(screenshot_path):
                message_content += f"\n\nA screenshot was captured at: {screenshot_path}"
            
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message_content
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            while run.status in ['queued', 'in_progress', 'cancelling']:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                
                for message in messages.data:
                    if message.role == "assistant":
                        response_text = ""
                        for content_block in message.content:
                            if content_block.type == "text":
                                response_text += content_block.text.value
                        
                        self.conversation_history.append({
                            "user": content,
                            "assistant": response_text,
                            "timestamp": time.time(),
                            "screenshot": screenshot_path
                        })
                        
                        return response_text
            else:
                return f"Error: Run failed with status {run.status}"
                
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"
    
    def get_conversation_history(self) -> list:
        return self.conversation_history
    
    def clear_conversation(self):
        self.thread_id = None
        self.conversation_history.clear()
    
    def save_conversation(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
    
    def load_conversation(self, filepath: str):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.conversation_history = json.load(f)