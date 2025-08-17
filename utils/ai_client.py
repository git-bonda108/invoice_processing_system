"""
Mock AI Client for generating conversational responses.
This is a placeholder to simulate a generative AI model (like GPT, Claude, etc.)
without requiring an actual API key. It allows for development and testing
of the conversational features of the agents.
"""
import random
import logging

class MockAIClient:
    def __init__(self):
        self.logger = logging.getLogger("MockAIClient")
        self.logger.info("Mock AI Client initialized. Using static responses.")

    def generate_conversation_response(self, user_message: str, agent_type: str, context: dict) -> dict:
        """
        Simulates generating a conversational response from an AI model.
        """
        try:
            self.logger.debug(f"Generating response for agent '{agent_type}' with context: {context}")
            
            # Generic fallback response
            response_text = f"As the {agent_type.replace('_', ' ').title()} Agent, I have processed your query regarding '{user_message[:30]}...'. Based on my expertise in {context.get('agent_expertise', ['my domain'])}, I can provide some initial information."

            # Agent-specific logic
            if agent_type == "learning":
                response_text = self._get_learning_agent_response(user_message, context)
            elif agent_type in ["extraction", "contract", "msa", "leasing", "fixed_assets"]:
                response_text = self._get_domain_agent_response(user_message, agent_type, context)

            return {
                "status": "success",
                "response": response_text,
                "confidence": random.uniform(0.85, 0.98),
                "model_used": "mock-ai-v1"
            }
        except Exception as e:
            self.logger.error(f"Error in mock AI client: {e}")
            return {
                "status": "error",
                "message": "Failed to generate mock AI response."
            }

    def _get_learning_agent_response(self, user_message: str, context: dict) -> str:
        """Generates a response for the Learning Agent."""
        user_message_lower = user_message.lower()
        
        if any(keyword in user_message_lower for keyword in ["thank", "great", "awesome"]):
            return "You're welcome! I'm glad I could help. Is there anything else you need assistance with?"
            
        if "how" in user_message_lower and "work" in user_message_lower:
            return "The system works by orchestrating a team of specialized AI agents. Each agent handles a specific document type, like invoices or contracts. The Manager Agent oversees their work, and I, the Learning Agent, help facilitate communication and learn from your feedback to improve the system continuously."
            
        return f"I've received your message: '{user_message}'. I am analyzing it to provide the best possible assistance. How can I help you further with our document processing system?"

    def _get_domain_agent_response(self, user_message: str, agent_type: str, context: dict) -> str:
        """Generates a response for a domain-specific agent."""
        user_message_lower = user_message.lower()
        expertise = context.get('agent_expertise', ['my domain'])
        
        if "accuracy" in user_message_lower:
            return f"As the {agent_type.replace('_', ' ').title()} Agent, I prioritize accuracy. My models are trained to achieve over 95% accuracy on key fields within my domain of {', '.join(expertise)}. Confidence scores are provided for every extraction to ensure transparency."
            
        if "anomaly" in user_message_lower:
            return f"I am trained to detect anomalies specific to {', '.join(expertise)}. For example, I can flag unusual payment terms in contracts or discrepancies in asset depreciation schedules. What specific anomaly are you interested in?"
            
        return f"As the {agent_type.replace('_', ' ').title()} Agent, my expertise is in {', '.join(expertise)}. I have analyzed your query and am ready to assist. What specific details are you looking for?"

# Create a singleton instance of the client
ai_client = MockAIClient()