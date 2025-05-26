
# PlinyTheElder - Multi-Agent AI Tutoring System

## Overview

PlinyTheElder is an AI-powered tutoring system built on multi-agent architecture principles inspired by Google's Agent Development Kit (ADK). The system features a central Tutor Agent that intelligently routes questions to specialized sub-agents and tools, each equipped with domain-specific tools to provide accurate, detailed explanations.

## Key Architecture

- **Main Tutor Agent**: Acts as orchestrator, analyzing questions and routing to appropriate specialists
- **Specialist Sub-Agents**: Domain-specific agents (Mathematics, Physics, etc.)
- **Tool Integration**: Sub-agents utilize tools (calculators, data lookups, etc.) for precise solutions
- **Gemini API**: Powers the language model capabilities throughout the system
- **Document Processing Engine**: Parses and indexes uploaded syllabus materials

## Features

- **Intelligent Routing**: Questions automatically directed to the most appropriate specialist agent
- **Multi-Domain Expertise**: Specialized knowledge across Mathematics, Physics, Chemistry, Literature
- **Two Modes of Operation**:
  - **On-Syllabus Mode**: Tailored answers based on your defined curriculum
  - **Off-Syllabus Mode**: Broad knowledge for any academic question
- **Interactive Learning**: Follow-up questions and step-by-step explanations
- **Syllabus-Locked Responses**: Unique ability to constrain answers exclusively to user-uploaded syllabus materials
- **Citation Generation**: Automatically references specific pages from provided textbooks
- **Strict Boundary Enforcement**: Politely declines questions outside syllabus scope

## Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/abrr-fhyz/tutorAgent.git
   cd tutorAgent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file with your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

4. Run the application:
   ```bash
   python server.py
   ```

5. Access the web interface at `http://localhost:8000/`

## Usage Instructions

1. Select your mode:
   - **On-Syllabus**: For curriculum-aligned questions
   - **Off-Syllabus**: For general academic questions

2. Enter your question in the chat interface

3. The system will:
   - Analyze and route to appropriate specialist agent
   - Use necessary tools for accurate solutions
   - Provide step-by-step explanations

4. Ask follow-up questions to deepen understanding

5. **NOTE:** On-Syllabus Mode is currently Rate-limited, and may not be able to answer questions based on large (>20 pages) documents.

## Deployment

The application can be deployed to:
- Railway

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or contributions, please contact:
Abrar Fahyaz- fahyaz.abrar@gmail.com