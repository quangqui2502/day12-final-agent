class MockLLM:
    """Mock LLM for development and testing without real API keys."""

    RESPONSES = {
        "docker": "Docker is a containerization platform that packages apps with their dependencies into isolated containers.",
        "kubernetes": "Kubernetes (K8s) is an orchestration system for automating deployment, scaling, and management of containers.",
        "redis": "Redis is an in-memory data store used for caching, session management, and real-time data processing.",
        "api": "An API (Application Programming Interface) defines how software components communicate with each other.",
        "deploy": "Deployment means releasing your application to a server where users can access it.",
        "cloud": "Cloud computing provides on-demand computing resources over the internet, enabling scalability and flexibility.",
    }

    def chat(self, question: str, history: list | None = None) -> str:
        q_lower = question.lower()
        for keyword, response in self.RESPONSES.items():
            if keyword in q_lower:
                if history:
                    return f"[Turn {len(history)//2 + 1}] {response}"
                return response
        turns = len(history) // 2 + 1 if history else 1
        return f"[Turn {turns}] I received your question: '{question}'. This is a mock response from QuangQui AI Agent."
