from lib.tools.util import CalculatorTool
from lib.tools.agent import Agent
from typing import Dict, Any

class MathTool(Agent):
    def __init__(self):
        super().__init__(
            name="Math Agent",
            description="Handles mathematical questions, equations, calculations, algebra, geometry, calculus, and all mathematical concepts",
            tools=[CalculatorTool()]
        )
    
    def can_handle(self, question: str) -> bool:
        """Use AI to determine if this is a math question"""
        classification_prompt = f"""
        Analyze this question and determine if it's primarily a mathematics question.
        
        Question: "{question}"
        
        A mathematics question includes:
        - Arithmetic calculations, algebra, geometry, trigonometry, calculus
        - Mathematical concepts, formulas, equations, proofs
        - Statistical problems, probability questions
        - Mathematical word problems
        - Questions about mathematical theories or methods
        
        Respond with only "YES" if this is primarily a mathematics question, or "NO" if it's not.
        """
        
        try:
            response = self.classifier_model.generate_content(classification_prompt)
            return response.text.strip().upper() == "YES"
        except Exception:
            # Fallback to basic keyword matching if AI fails
            math_indicators = ['calculate', 'solve', 'equation', 'math', 'formula', 'derivative', 'integral', '+', '-', '*', '/', '=']
            return any(indicator in question.lower() for indicator in math_indicators)
    
    def process(self, question: str, mode: str = "off-syllabus") -> Dict[str, Any]:
        calculations, tools_used = self._extract_and_calculate(question)
        
        if mode == "on-syllabus":
            # Search for relevant documents
            relevant_docs = self._search_documents(question, "math")
            
            if not relevant_docs:
                return {
                    "answer": "I couldn't find any relevant mathematical content in the syllabus materials to answer your question. Please check if the topic is covered in your course materials.",
                    "tools_used": tools_used,
                    "sources": []
                }
            
            # Create context from relevant documents
            doc_context = "\n\n".join([
                f"From {doc['file']}:\n{doc['content']}"
                for doc in relevant_docs
            ])
            
            prompt = f"""
            You are a mathematics tutor. Answer this question using ONLY the information provided from the syllabus materials below. Do not use external knowledge.
            
            Question: {question}
            
            Syllabus Materials:
            {doc_context}
            
            {f"Pre-computed calculations: {calculations}" if calculations else ""}
            
            Instructions:
            - Answer based ONLY on the provided syllabus materials
            - If the answer isn't fully covered in the materials, clearly state what information is missing
            - Provide step-by-step solutions when the materials show examples
            - Reference specific sections or examples from the materials
            - Use proper mathematical notation as shown in the materials
            """
            
            sources = [doc['file'] for doc in relevant_docs]
        else:
            # Off-syllabus mode - enhanced prompt with better context
            prompt = f"""
            You are an expert mathematics tutor. Answer this question with clear, educational explanations.
            
            Question: {question}
            
            {f"Pre-computed calculations: {calculations}" if calculations else ""}
            
            Instructions:
            - Provide step-by-step solutions when applicable
            - Explain mathematical concepts clearly
            - Use proper mathematical notation
            - Make explanations suitable for students
            - If solving equations, show each step
            - Include relevant formulas when helpful
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
                "answer": f"I encountered an error processing your math question: {str(e)}",
                "tools_used": tools_used,
                "sources": sources if mode == "on-syllabus" else []
            }