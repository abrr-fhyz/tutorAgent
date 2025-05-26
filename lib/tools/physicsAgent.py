from lib.tools.util import CalculatorTool
from lib.tools.agent import Agent
from typing import Dict, Any

class PhysicsAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Physics Agent",
            description="Handles physics questions, problems, concepts, and scientific principles related to mechanics, thermodynamics, electromagnetism, and quantum physics",
            tools=[CalculatorTool()]
        )
    
    def can_handle(self, question: str) -> bool:
        """Use AI to determine if this is a physics question"""
        classification_prompt = f"""
        Analyze this question and determine if it's primarily a physics question.
        
        Question: "{question}"
        
        A physics question includes:
        - Mechanics (motion, forces, energy, momentum)
        - Thermodynamics (heat, temperature, entropy)
        - Electromagnetism (electricity, magnetism, waves)
        - Quantum physics and atomic structure
        - Optics, acoustics, fluid dynamics
        - Physics concepts, laws, theories, or principles
        - Physics problem-solving with calculations
        
        Respond with only "YES" if this is primarily a physics question, or "NO" if it's not.
        """
        
        try:
            response = self.classifier_model.generate_content(classification_prompt)
            return response.text.strip().upper() == "YES"
        except Exception:
            # Fallback to basic keyword matching if AI fails
            physics_indicators = ['physics', 'force', 'energy', 'velocity', 'acceleration', 'newton', 'gravity', 'mass', 'momentum', 'wave', 'quantum']
            return any(indicator in question.lower() for indicator in physics_indicators)
    
    def process(self, question: str, mode: str = "off-syllabus") -> Dict[str, Any]:
        calculations, tools_used = self._extract_and_calculate(question)
        
        if mode == "on-syllabus":
            # Search for relevant documents
            relevant_docs = self._search_documents(question, "physics")
            
            if not relevant_docs:
                return {
                    "answer": "I couldn't find any relevant physics content in the syllabus materials to answer your question. Please check if the topic is covered in your course materials.",
                    "tools_used": tools_used,
                    "sources": []
                }
            
            # Create context from relevant documents
            doc_context = "\n\n".join([
                f"From {doc['file']}:\n{doc['content']}"
                for doc in relevant_docs
            ])
            
            prompt = f"""
            You are a physics tutor. Answer this question using ONLY the information provided from the syllabus materials below. Do not use external knowledge.
            
            Question: {question}
            
            Syllabus Materials:
            {doc_context}
            
            {f"Pre-computed calculations: {calculations}" if calculations else ""}
            
            Instructions:
            - Answer based ONLY on the provided syllabus materials
            - If the answer isn't fully covered in the materials, clearly state what information is missing
            - Reference specific laws, principles, or examples from the materials
            - Show step-by-step problem solving as demonstrated in the materials
            - Use proper scientific units as shown in the materials
            """
            
            sources = [doc['file'] for doc in relevant_docs]
        else:
            # Off-syllabus mode - enhanced prompt with physics-specific context
            prompt = f"""
            You are an expert physics tutor. Answer this question with clear, scientific explanations.
            
            Question: {question}
            
            {f"Pre-computed calculations: {calculations}" if calculations else ""}
            
            Instructions:
            - Explain relevant physics principles and laws
            - Show step-by-step problem solving when applicable
            - Include relevant formulas and their meanings
            - Use proper scientific units
            - Connect concepts to real-world applications
            - Make explanations accessible to students
            - If solving physics problems, clearly show the approach
            """
            sources = []
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "answer": response.text,
                "tools_used": tools_used,
                "sources": sources
            }
        except Exception as e:
            return {
                "answer": f"I encountered an error processing your physics question: {str(e)}",
                "tools_used": tools_used,
                "sources": sources if mode == "on-syllabus" else []
            }