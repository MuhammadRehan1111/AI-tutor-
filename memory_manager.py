import json
import os
from typing import Dict, List, Any

class MemoryManager:
    def __init__(self, storage_path: str = "memory.json"):
        self.storage_path = storage_path
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                return json.load(f)
        return {
            "name": "Student",
            "subjects": [],
            "weak_topics": [],
            "completed_topics": [],
            "history": []
        }

    def save_memory(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.memory, f, indent=4)

    def update_profile(self, name: str = None, subjects: List[str] = None):
        if name:
            self.memory["name"] = name
        if subjects:
            self.memory["subjects"] = list(set(self.memory["subjects"] + subjects))
        self.save_memory()

    def add_weak_topic(self, topic: str):
        if topic not in self.memory["weak_topics"]:
            self.memory["weak_topics"].append(topic)
            self.save_memory()

    def mark_topic_completed(self, topic: str):
        if topic in self.memory["weak_topics"]:
            self.memory["weak_topics"].remove(topic)
        if topic not in self.memory["completed_topics"]:
            self.memory["completed_topics"].append(topic)
        self.save_memory()

    def add_to_history(self, question: str, answer: str):
        self.memory["history"].append({"q": question, "a": answer})
        # Keep last 10 for context window efficiency
        if len(self.memory["history"]) > 10:
            self.memory["history"] = self.memory["history"][-10:]
        self.save_memory()

    def get_context_summary(self) -> str:
        return f"""
Student Name: {self.memory['name']}
Current Subjects: {', '.join(self.memory['subjects'])}
Weak Topics: {', '.join(self.memory['weak_topics'])}
Completed Topics: {', '.join(self.memory['completed_topics'])}
"""
