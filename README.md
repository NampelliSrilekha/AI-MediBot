**AI-MediBot – AI-Powered Skin Health Assistant**

AI-MediBot is a multi-modal AI assistant designed to provide personalized, non-diagnostic guidance for users managing skin-related concerns. The system integrates vision-language modeling for skin image understanding with a large language model for intelligent response generation, delivering safe, context-aware insights while emphasizing responsible AI usage.

**Key Features**

- Secure User Authentication – Protects user access and consultation data
- Guided Patient Onboarding – Collects background details for personalization
- Natural Language Interaction – Users describe symptoms conversationally
- Skin Image Analysis – AI-powered visual understanding using BiomedCLIP(Vision Transformer)
- LLM-Orchestrated Responses – Context-aware guidance using Groq LLM
- Consultation Management – Session-based chat history and state management
- Non-Diagnostic & Safety-Driven – Promotes responsible AI and medical consultation

**System Overview**

AI-MediBot follows a modular, layered architecture:
Presentation Layer: Streamlit-based web interface
Application Layer: Orchestration, session management, and workflow control
AI Services Layer:
- BiomedCLIP for skin image embedding and similarity matching
- Groq LLM for reasoning and response generation
Data Layer: User authentication store, onboarding profiles, consultation history
The system takes image predictions, user symptoms, onboarding context, and conversational memory into structured prompts for the LLM to generate safe, non-diagnostic outputs.



<img width="936" height="662" alt="Sequence Diagram" src="https://github.com/user-attachments/assets/46511e72-d3e9-4c8b-aa9c-e17ed995651f" />



**Model Architecture**

BiomedCLIP (Vision-Language Model)

.........................................

BiomedCLIP-based skin appearance detector

Model: Microsoft BiomedCLIP (Fine-tuned on 15M+ medical images)

Paper: https://arxiv.org/abs/2303.00915

.............................................

- Encodes skin images into embeddings
- Matches them with medical text embeddings
- Returns top-K visually similar skin conditions using cosine similarity

Groq LLM (Transformer-based LLM)
- Receives structured prompts containing all contextual data
- Generates personalized, coherent, and non-diagnostic guidance
- Enforces safety constraints and medical boundaries

**Evaluation Approach**

AI-MediBot does not use a single “accuracy” metric, as it is not a diagnostic classifier.
- Vision Model: Evaluated using Top-K similarity matching
- System Level: Scenario-based testing for relevance and consistency
- Safety: Verified for non-diagnostic compliance and escalation guidance


**Future Enhancements**

- Cloud-based microservices deployment
- Integration with telemedicine platforms
- Secure database (PostgreSQL / Firebase)
- Human feedback and continuous evaluation
- Advanced dermatology datasets for benchmarking



