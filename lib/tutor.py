from typing import Dict, Any

from lib.tools.agent import Agent
from lib.tools.mathAgent import MathTool
from lib.tools.physicsAgent import PhysicsTool

class TutorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Tutor Agent",
            description="Main orchestrator that intelligently routes questions to specialized tools"
        )
        self.specialized_tools = [
            MathTool(),
            PhysicsTool()
        ]
    
    def can_handle(self, question: str) -> bool:
        return True  # Tutor can handle any question
    
    def find_best_agent(self, question: str) -> Agent:
        """Intelligently find the most suitable agent using AI classification"""
        
        # Check each specialized agent's capability
        agent_scores = []
        for agent in self.specialized_tools:
            try:
                if agent.can_handle(question):
                    # Get confidence score for better routing
                    confidence_prompt = f"""
                    Rate how well suited the "{agent.name}" is for this question on a scale of 1-10.
                    
                    Question: "{question}"
                    Agent specialty: {agent.description}
                    
                    Consider:
                    - How closely the question matches the agent's expertise
                    - Whether the question requires specialized knowledge in this domain
                    - If this agent would provide the most accurate and helpful answer
                    
                    Respond with only a number from 1-10.
                    """
                    
                    confidence_response = self.classifier_model.generate_content(confidence_prompt)
                    try:
                        score = float(confidence_response.text.strip())
                        agent_scores.append((agent, score))
                    except ValueError:
                        agent_scores.append((agent, 5.0))  # Default score
            except Exception:
                continue
        
        # Return agent with highest confidence score
        if agent_scores:
            best_agent = max(agent_scores, key=lambda x: x[1])[0]
            return best_agent
        
        return self  # Default to tutor agent if no specialist matches
    
    def process(self, question: str, mode: str = "off-syllabus") -> Dict[str, Any]:
        # Find the best agent for this question
        best_agent = self.find_best_agent(question)
        
        if best_agent != self:
            # Delegate to specialized agent
            result = best_agent.process(question, mode)
            return {
                "answer": result["answer"],
                "agent_used": best_agent.name,
                "tools_used": result.get("tools_used", []),
                "sources": result.get("sources", [])
            }
        else:
            # Handle general questions with enhanced Tutor Agent
            if mode == "on-syllabus":
                # Search for relevant documents for general questions
                relevant_docs = self._search_documents(question)
                
                if not relevant_docs:
                    return {
                        "answer": "I couldn't find any relevant content in the syllabus materials to answer your question. Please check if the topic is covered in your course materials or try the off-syllabus mode for general knowledge.",
                        "agent_used": self.name,
                        "tools_used": [],
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
            else:
                # Off-syllabus mode
                prompt = f"""
                You are a knowledgeable and helpful tutor. Answer this question clearly and educationally.
                
                Question: {question}
                
                Instructions:
                - Provide comprehensive but accessible explanations
                - Break down complex topics into understandable parts
                - Use examples to illustrate concepts when helpful
                - Encourage learning and curiosity
                - If the question spans multiple subjects, address each aspect appropriately
                - Make your explanation suitable for a student seeking to learn
                """
                sources = []
            
            try:
                response = self.model.generate_content(prompt)
                return {
                    "answer": response.text,
                    "agent_used": self.name,
                    "tools_used": [],
                    "sources": sources
                }
            except Exception as e:
                return {
                    "answer": f"I encountered an error processing your question: {str(e)}",
                    "agent_used": self.name,
                    "tools_used": [],
                    "sources": sources if mode == "on-syllabus" else []
                }