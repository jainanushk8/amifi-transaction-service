# AI Assistance Disclosure

## Declaration
This project was developed with AI assistance as permitted by the AmiFi assessment guidelines. This disclosure is provided in full compliance with the requirement for transparency about external help.

**Confirmation Statement**: "I understand that Amifi reserves the right to disqualify or blacklist candidates in case of fraudulent practices or non-disclosure."

## AI Assistance Details

### Tool Used
- **Primary AI Assistant**: Perplexity AI
- **Usage Period**: September 26-27, 2025
- **Purpose**: Code generation, architecture guidance, documentation

### Specific AI Contributions

#### Code Generation (Tagged with # @ai perplexity)
- **Database Models** (`src/database.py`) - SQLAlchemy models and connection logic
- **Parser Implementation** (`src/parsers.py`) - Regex patterns and parsing logic  
- **Classification System** (`src/classifier.py`) - TF-Lite interface and rule-based classifier
- **Goal Impact Logic** (`src/goal_impact.py`) - Financial goal calculations
- **FastAPI Application** (`src/main.py`) - API endpoints and request handling
- **Unit Tests** (`tests/test_basic.py`) - Test cases and assertions
- **Documentation** (README.md, this file) - Structure and content

#### Architecture Decisions (Human-Led)
- **Database schema design** - Chosen based on assignment requirements
- **Parsing strategy** - Regex patterns for Indian banking SMS/email formats
- **Classification categories** - Selected for Indian fintech context
- **Goal impact scoring** - Custom algorithms for financial goal tracking
- **API endpoint design** - REST API structure and response formats

### Human Contributions

#### Core Decisions
- Project structure and component organization
- Business logic for transaction classification
- Goal impact calculation algorithms  
- Error handling and validation strategies
- Test case selection and assertions
- Security considerations (PII masking, input validation)

#### Implementation Control
- All code reviewed and understood before integration
- Custom modifications to AI-generated code
- Integration testing and debugging
- Performance optimization decisions
- Documentation review and accuracy verification

### Development Process
1. **Requirements Analysis** - Human interpretation of assignment
2. **Architecture Design** - Human decisions on system structure  
3. **Code Generation** - AI assistance for implementation
4. **Integration & Testing** - Human validation and debugging
5. **Documentation** - AI assistance with human review and modification

## Flutter UI Decision
The assignment specifies "APIs (Python backend) OR Flutter UI". We chose the Python backend route with interactive API documentation, which provides superior functionality compared to a basic Flutter UI. The Swagger interface at `/docs` offers complete transaction visualization and testing capabilities.

## Transparency Statement
- **AI was used as a development tool**, similar to Stack Overflow or documentation
- **All generated code was reviewed, understood, and modified** as needed
- **Core architectural and business logic decisions were made by the human developer**
- **Final responsibility for all code quality and functionality** lies with the human developer

## Compliance
This disclosure ensures full transparency as required by the AmiFi assessment guidelines. The use of AI assistance was limited to code generation and documentation support, with all critical decisions, testing, and validation performed by the human candidate.

---
**Author**: Amit Singh  
**Date**: September 27, 2025  
**Assessment**: AmiFi Fintech Labs AI/ML Intern Take Home Assignment
