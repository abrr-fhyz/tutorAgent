from typing import Dict, Any
from lib.tools.agent import Agent

class SyllabusAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Syllabus Agent",
            description="Specialized agent for answering questions using only syllabus materials and course content"
        )
        self.syllabus_tool = SyllabusTool()
    
    def can_handle(self, question: str) -> bool:
        return True  # Can attempt to handle any question using syllabus materials
    
    def process(self, question: str, mode: str = "on-syllabus") -> Dict[str, Any]:
        result = self.syllabus_tool.process(question)
        return {
            "answer": result["answer"],
            "agent_used": self.name,
            "tools_used": [self.syllabus_tool.name],
            "sources": result.get("sources", [])
        }

class SyllabusTool(Agent):
    def __init__(self):
        super().__init__(
            name="Syllabus Tool",
            description="Tool for processing questions using syllabus materials and course content"
        )
    
    def can_handle(self, question: str) -> bool:
        return True  # Can attempt to process any question using syllabus materials
    
    def process(self, question: str) -> Dict[str, Any]:
        # Search for relevant documents for syllabus-based questions
        relevant_docs = self._search_documents(question)
        
        if not relevant_docs:
            return {
                "answer": "I couldn't find any relevant content in the syllabus materials to answer your question. Please check if the topic is covered in your course materials or try the off-syllabus mode for general knowledge.",
                "sources": []
            }
        
        # Create context from relevant documents
        doc_context = "\n\n".join([
            f"From {doc['file']}:\n{doc['content']}"
            for doc in relevant_docs
        ])
        
        prompt = f"""
        You are a knowledgeable tutor. Answer this question using ONLY the information provided from the syllabus materials below. Do not use external knowledge.
        
        Question: {question}
        
        Syllabus Materials:
        {doc_context}
        
        Instructions:
        - Answer based ONLY on the provided syllabus materials
        - If the answer isn't fully covered in the materials, clearly state what information is missing
        - Break down complex topics as explained in the materials
        - Reference specific sections or examples from the materials
        - Make your explanation suitable for a student following the syllabus
        """
        
        sources = [doc['file'] for doc in relevant_docs]
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "answer": response.text,
                "sources": sources
            }
        except Exception as e:
            return {
                "answer": f"I encountered an error processing your question: {str(e)}",
                "sources": sources
            }