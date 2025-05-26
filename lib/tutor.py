from typing import Dict, Any

from lib.tools.agent import Agent
from lib.tools.mathTool import MathTool
from lib.tools.physicsTool import PhysicsTool
from lib.tools.syllabusTool import SyllabusAgent

class TutorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Tutor Agent",
            description="Main orchestrator that intelligently routes questions to specialized tools and agents"
        )
        self.specialized_tools = [
            MathTool(),
            PhysicsTool()
        ]
        self.syllabus_agent = SyllabusAgent()
    
    def can_handle(self, question: str) -> bool:
        return True  # Tutor can handle any question by routing appropriately
    
    def find_best_agent(self, question: str, mode: str) -> Agent:
        """Intelligently find the most suitable agent using AI classification"""
        
        # If mode is on-syllabus, use syllabus agent
        if mode == "on-syllabus":
            return self.syllabus_agent
        
        # For off-syllabus mode, check specialized tools first
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
        
        # Return specialized agent with highest confidence score (if score is high enough)
        if agent_scores:
            best_agent, best_score = max(agent_scores, key=lambda x: x[1])
            # Only use specialized agent if confidence is reasonably high
            if best_score >= 6.0:
                return best_agent
        
        # Default to tutor agent for general off-syllabus questions
        return self
    
    def process(self, question: str, mode: str = "off-syllabus") -> Dict[str, Any]:
        # Find the best agent for this question
        best_agent = self.find_best_agent(question, mode)
        
        if best_agent != self:
            # Delegate to specialized agent
            result = best_agent.process(question, mode)
            return {
                "answer": result["answer"],
                "agent_used": result["agent_used"],
                "tools_used": result.get("tools_used", []),
                "sources": result.get("sources", []),
                "routed_by": self.name
            }
        else:
            # Handle general off-syllabus questions directly
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
            
            try:
                response = self.model.generate_content(prompt)
                return {
                    "answer": response.text,
                    "agent_used": self.name,
                    "tools_used": [],
                    "sources": []
                }
            except Exception as e:
                return {
                    "answer": f"I encountered an error processing your question: {str(e)}",
                    "agent_used": self.name,
                    "tools_used": [],
                    "sources": []
                }