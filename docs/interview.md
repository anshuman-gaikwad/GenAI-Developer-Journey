# GrahakNyay — Interview Preparation

## 1. My 60-Second Project Pitch

GrahakNyay is a full-stack Generative AI application I built to help Indian consumers understand their rights and navigate consumer complaints.

Consumer-protection laws can be difficult to interpret, especially when people need to identify the correct Consumer Commission or understand complaint-filing procedures.

I built a Streamlit frontend connected to a FastAPI backend. The application uses Retrieval-Augmented Generation (RAG) to retrieve relevant legal provisions and Groq to generate understandable answers with source citations.

I also implemented a LangGraph agent that can use legal-search tools or a Consumer Commission and filing-fee calculator, with a human-approval step before calculator execution.

The knowledge base contains 36 structured legal records, and I developed a separate semantic-search pipeline with 152 document chunks.

For reliability, I added automated testing, GitHub Actions CI, Docker, API latency and token logging, input validation, and response caching. The project has 41 passing automated tests.

The hardest challenge was handling legal rules that changed over time. I had to distinguish older figures in the Consumer Protection Act from later jurisdiction rules and fee amendments.

The application is deployed using Streamlit Community Cloud and Render.

## 2. Ten Likely Interview Questions and Answers

### Q1. What problem does GrahakNyay solve?

Many Indian consumers do not know their legal rights, the correct Consumer Commission, or the steps involved in filing complaints.

GrahakNyay helps them retrieve relevant consumer-protection information, understand legal provisions in simpler language, and explore complaint-filing guidance.

It provides general information, not professional legal advice.

### Q2. Why did you choose Retrieval-Augmented Generation (RAG)?

A general LLM may answer from its training data without showing where the information came from.

RAG first retrieves relevant legal records, then includes them as context for the LLM. This helps ground answers in available documents and allows the application to provide citations.

However, RAG does not guarantee that every answer is legally correct.

### Q3. How does your RAG pipeline work?

A user submits a question through Streamlit.

FastAPI receives the request, retrieves relevant consumer-law records using the configured retrieval method, builds a prompt containing the retrieved legal context, and sends it to the Groq LLM.

The application returns the generated answer with citations.

Production uses TF-IDF retrieval to reduce memory requirements. The project also supports semantic retrieval locally.

### Q4. Why did you use TF-IDF in production instead of embeddings?

The backend runs on a memory-limited Render deployment.

Semantic retrieval requires additional model-loading and memory resources. TF-IDF provides a lightweight retrieval method suitable for the production environment.

The tradeoff is that TF-IDF depends more on matching terms, while semantic retrieval can capture similarities in meaning.

### Q5. What is the role of LangGraph in your project?

LangGraph coordinates the agent workflow.

The agent can use legal retrieval or a calculator for Consumer Commission, filing-fee, and indicative deadline questions.

Calculator execution includes a human-approval step. The application uses a thread ID to resume a paused workflow after the user approves or rejects it.

### Q6. How did you handle legal rules that changed over time?

This was one of the hardest problems in the project.

The original Consumer Protection Act, 2019, included a ₹1 crore District Commission threshold, but the 2021 Jurisdiction Rules introduced a ₹50 lakh threshold.

The filing-fee table was substituted in 2022 and then substituted again by the Consumer Protection (Consumer Disputes Redressal Commissions) (Amendment) Rules, 2023 (G.S.R. 606(E)). The fee amounts in the two notifications are the same.

I implemented the updated jurisdiction thresholds in the calculator and documented the applicable rule sources instead of relying only on the original Act's figures.

An important limitation is that the rules are currently coded into the application. Future legal changes require verification and a code or data update.

### Q7. How did you test the application?

I used pytest to test API endpoints, input validation, retrieval-related behavior, calculator logic, cache behavior, and error handling.

I also added tests that verify prompt-injection precautions are included in the constructed RAG prompt.

The project currently has 41 passing automated tests, including tests for jurisdiction boundaries. GitHub Actions runs CI checks.

### Q8. How did you improve performance?

I added API and LLM latency logging, input/output token logging, and a five-minute in-memory cache for a small allowlist of general questions.

In one local two-request test, the uncached API request took 1,004.23 milliseconds, while the cached request took 1.22 milliseconds.

This demonstrated the benefit of avoiding a repeated LLM call, but it is not a statistically representative production benchmark.

### Q9. How did you address security and reliability?

I added question-length validation, generic error responses for LLM failures, and prompt instructions that tell the model to treat user questions and retrieved content as untrusted.

I used environment variables for API keys rather than placing them in source code, and added automated tests and CI.

Prompt-injection defenses are not foolproof, and the existing tests validate prompt construction rather than complete resistance to adversarial attacks.

### Q10. What would you improve if you had more time?

I would add automated legal-rule version tracking using official notifications, expand the legal-answer evaluation dataset, test prompt-injection behavior against live models, and introduce a shared persistent cache.

I would also improve production monitoring and make the agent's approval state durable across server restarts.

## 3. Hardest Problem — Versioned Consumer-Protection Rules

### Situation

While building the Consumer Commission calculator, I encountered legal provisions that had changed after the original Consumer Protection Act, 2019.

A system relying on the original Act alone could show outdated jurisdiction thresholds.

### Task

I needed the calculator to identify the appropriate Consumer Commission using the later applicable rules and provide filing-fee guidance without silently mixing old and updated provisions.

### Action

I separated jurisdiction, fee, and limitation calculations.

For jurisdiction, I implemented the thresholds specified in the 2021 Jurisdiction Rules:

- District Commission: up to ₹50 lakh.
- State Commission: above ₹50 lakh and up to ₹2 crore.
- National Commission: above ₹2 crore.

I implemented the filing-fee table under Rule 7(2), using the 2023 amendment (G.S.R. 606(E)), which replaced the 2022 table while retaining the same fee amounts.

I also calculated an indicative two-year filing deadline under Section 69 of the Consumer Protection Act, 2019.

The calculator returns references to the legal sources used.

### Result

The calculator applies the coded 2021 jurisdiction thresholds rather than the original Act's older monetary limits.

I added boundary tests for ₹50 lakh and ₹2 crore to verify that the calculator selects the intended commission at and immediately above those thresholds.

This taught me that legal AI systems need explicit source-version awareness. Retrieving a relevant provision is not enough if a later notification changes how that provision operates.

### Limitation and Future Improvement

The current implementation does not automatically discover new legal amendments.

A stronger production system would store each rule's notification date, effective date, source URL, and supersession status, then select the applicable version for the relevant date.

The RAG component would also need evaluation to ensure that it explains why a later rule takes precedence when older documents are retrieved.

## 4. Demo Rehearsal Checklist

### Rehearsal 1

- [x] Open the deployed Streamlit application.
- [x] Confirm that the FastAPI backend is reachable.
- [x] Ask a consumer-rights question.
- [x] Check that the answer includes source citations.
- [x] Demonstrate the Consumer Commission calculator.
- [x] Explain the jurisdiction-rule versioning challenge aloud.
- [x] Record the citation inconsistency discovered during the demo and its resolution.

### Rehearsal 2

- [ ] Repeat the complete demonstration.
- [ ] Practice the 60-second pitch aloud.
- [ ] Explain the architecture without reading notes.
- [ ] Explain the hardest technical problem clearly.
- [ ] Confirm that the application is working.
- [x] Record any remaining issues — none observed during Rehearsal 2.

## 5. Project Links

- **GitHub:** https://github.com/anshuman-gaikwad/GenAI-Developer-Journey
- **Live App:** https://genai-developer-journey-jowf6tq3safp6mu9dmzaey.streamlit.app/
- **Backend API:** https://grahaknyay-api.onrender.com
- **Swagger Docs:** https://grahaknyay-api.onrender.com/docs

## 6. Legal and Technical Limitations

GrahakNyay is an educational project that provides general consumer-rights information, not legal advice.

The calculator's thresholds and fees require periodic verification against official government notifications. Generated answers and citations should be checked against the underlying sources before being relied upon.

The agent uses in-memory development state, and the response cache is also process-local.

## 7. Official Legal References

- **Consumer Protection Act, 2019:** Section 69 (limitation period).
- **Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021:** G.S.R. 912(E).
- **Consumer Protection (Consumer Disputes Redressal Commissions) Amendment Rules, 2022:** G.S.R. 892(E), dated 20 December 2022.
- **Consumer Protection (Consumer Disputes Redressal Commissions) (Amendment) Rules, 2023:** G.S.R. 606(E), dated 17 August 2023. This notification replaced the Rule 7(2) filing-fee table again.

The calculator implements specific rule versions in code. It does not automatically detect future amendments. Legal rules and fees should be rechecked against current official notifications before real-world use.