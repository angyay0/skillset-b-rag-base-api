# RAG Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Application                         │
│                    (Flask App / WhatsApp Bot)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Question
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VertexAIService                            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Initialization                         │ │
│  │  • Load corpus_name from env or parameter                │ │
│  │  • Initialize Vertex AI client                           │ │
│  │  • Get or create RAG corpus                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              generate_response(use_rag=True)             │ │
│  │                                                           │ │
│  │  Step 1: Retrieve Contexts                               │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  retrieve_relevant_contexts(question, top_k=5)      │ │ │
│  │  │                                                       │ │ │
│  │  │  • Query RAG corpus with user question              │ │ │
│  │  │  • Get top-k most relevant chunks                   │ │ │
│  │  │  • Return contexts with metadata                    │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                             │                             │ │
│  │                             ▼                             │ │
│  │  Step 2: Build Enhanced Prompt                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  • System prompt (Blinky personality)               │ │ │
│  │  │  • Conversation context                             │ │ │
│  │  │  • Retrieved RAG contexts                           │ │ │
│  │  │  • User question                                    │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                             │                             │ │
│  │                             ▼                             │ │
│  │  Step 3: Generate Response                               │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  model.generate_content(enhanced_prompt)            │ │ │
│  │  │                                                       │ │ │
│  │  │  • Gemini 1.5 Pro processes prompt                  │ │ │
│  │  │  • Uses retrieved contexts                          │ │ │
│  │  │  • Generates contextual response                    │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Response
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                            User                                 │
└─────────────────────────────────────────────────────────────────┘
```

## RAG Corpus Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG Corpus                              │
│                   (Vertex AI RAG Engine)                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Document Store                         │ │
│  │                                                           │ │
│  │  Document 1 (policy.pdf)                                 │ │
│  │  ├─ Chunk 1: "Refund policy allows..."                   │ │
│  │  ├─ Chunk 2: "Returns accepted within..."                │ │
│  │  └─ Chunk 3: "Contact support for..."                    │ │
│  │                                                           │ │
│  │  Document 2 (faq.txt)                                     │ │
│  │  ├─ Chunk 1: "Q: How to reset password?"                 │ │
│  │  ├─ Chunk 2: "Q: What are business hours?"               │ │
│  │  └─ Chunk 3: "Q: How to contact support?"                │ │
│  │                                                           │ │
│  │  Document 3 (product_info.md)                            │ │
│  │  ├─ Chunk 1: "Product X specifications..."               │ │
│  │  ├─ Chunk 2: "Product X features..."                     │ │
│  │  └─ Chunk 3: "Product X pricing..."                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   Vector Index                            │ │
│  │              (Semantic Embeddings)                        │ │
│  │                                                           │ │
│  │  • Each chunk converted to vector embedding              │ │
│  │  • Enables semantic similarity search                    │ │
│  │  • Fast retrieval using vector similarity                │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Document Import Flow

```
┌──────────────┐
│   GCS Bucket │
│              │
│  ├─ doc1.pdf │
│  ├─ doc2.txt │
│  └─ doc3.md  │
└──────┬───────┘
       │
       │ import_files_to_corpus()
       ▼
┌──────────────────────────────────┐
│   Document Processing            │
│                                  │
│  1. Extract text from documents  │
│  2. Split into chunks            │
│     • chunk_size: 512 tokens     │
│     • chunk_overlap: 100 tokens  │
│  3. Generate embeddings          │
│  4. Store in vector index        │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│   RAG Corpus                     │
│   (Ready for retrieval)          │
└──────────────────────────────────┘
```

### 2. Query Flow

```
┌──────────────────┐
│  User Question   │
│  "What is your   │
│  refund policy?" │
└────────┬─────────┘
         │
         │ retrieve_relevant_contexts()
         ▼
┌────────────────────────────────────┐
│  Query Processing                  │
│                                    │
│  1. Convert question to embedding  │
│  2. Search vector index            │
│  3. Find top-k similar chunks      │
│  4. Rank by similarity score       │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Retrieved Contexts                │
│                                    │
│  [1] "Refund policy allows..."     │
│      Source: policy.pdf            │
│      Distance: 0.92                │
│                                    │
│  [2] "Returns accepted within..."  │
│      Source: policy.pdf            │
│      Distance: 0.88                │
│                                    │
│  [3] "Contact support for..."      │
│      Source: faq.txt               │
│      Distance: 0.85                │
└────────┬───────────────────────────┘
         │
         │ generate_response()
         ▼
┌────────────────────────────────────┐
│  Enhanced Prompt                   │
│                                    │
│  System: "You are Blinky..."       │
│  Context: "Previous conversation"  │
│  Retrieved: "[1] Refund policy..." │
│  Question: "What is your refund    │
│            policy?"                │
└────────┬───────────────────────────┘
         │
         │ Gemini 1.5 Pro
         ▼
┌────────────────────────────────────┐
│  Generated Response                │
│                                    │
│  "Our refund policy allows you to  │
│  return items within 30 days of    │
│  purchase. Simply contact our      │
│  support team to initiate the      │
│  return process."                  │
└────────────────────────────────────┘
```

## Component Interactions

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Flask App   │  │ WhatsApp Bot │  │  CLI Tools   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
└───────────────────────────┼────────────────────────────────────┘
                            │
                            │ Uses
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer                                │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              VertexAIService                              │ │
│  │                                                           │ │
│  │  • generate_response()                                   │ │
│  │  • retrieve_relevant_contexts()                          │ │
│  │  • import_files_to_corpus()                              │ │
│  │  • get_corpus_info()                                     │ │
│  └───────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Calls
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                        │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Vertex AI       │  │  RAG Engine      │  │  GCS         │ │
│  │  (Gemini 1.5)    │  │  (Retrieval)     │  │  (Storage)   │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Retrieval Strategy

### Semantic Search Process

```
1. Query Embedding
   ┌────────────────────────────────────┐
   │ "What is your refund policy?"      │
   └────────────┬───────────────────────┘
                │
                │ Embedding Model
                ▼
   ┌────────────────────────────────────┐
   │ [0.23, -0.45, 0.67, ..., 0.12]     │
   │ (768-dimensional vector)           │
   └────────────┬───────────────────────┘
                │
                │
2. Vector Similarity Search
   ┌────────────▼───────────────────────┐
   │  Compare with all chunk vectors    │
   │                                    │
   │  Chunk 1: similarity = 0.92 ✓      │
   │  Chunk 2: similarity = 0.88 ✓      │
   │  Chunk 3: similarity = 0.85 ✓      │
   │  Chunk 4: similarity = 0.45        │
   │  Chunk 5: similarity = 0.32        │
   │  ...                               │
   └────────────┬───────────────────────┘
                │
                │
3. Ranking & Filtering
   ┌────────────▼───────────────────────┐
   │  • Sort by similarity score        │
   │  • Take top-k results (k=5)        │
   │  • Include metadata (source, etc)  │
   └────────────┬───────────────────────┘
                │
                ▼
   ┌────────────────────────────────────┐
   │  Top 5 Most Relevant Contexts      │
   └────────────────────────────────────┘
```

## Configuration Options

### Chunk Configuration

```
Document: "Lorem ipsum dolor sit amet, consectetur adipiscing elit..."

┌─────────────────────────────────────────────────────────────────┐
│                     Chunking Strategy                           │
│                                                                 │
│  chunk_size = 512 tokens                                        │
│  chunk_overlap = 100 tokens                                     │
│                                                                 │
│  ┌────────────────────────────────────────────┐                │
│  │ Chunk 1 (tokens 0-512)                     │                │
│  │ "Lorem ipsum dolor sit amet..."            │                │
│  └────────────────────────────────────────────┘                │
│                    ▼ overlap (100 tokens)                       │
│  ┌────────────────────────────────────────────┐                │
│  │ Chunk 2 (tokens 412-924)                   │                │
│  │ "...consectetur adipiscing elit..."        │                │
│  └────────────────────────────────────────────┘                │
│                    ▼ overlap (100 tokens)                       │
│  ┌────────────────────────────────────────────┐                │
│  │ Chunk 3 (tokens 824-1336)                  │                │
│  │ "...sed do eiusmod tempor..."              │                │
│  └────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘

Benefits of Overlap:
• Preserves context across chunk boundaries
• Improves retrieval accuracy
• Prevents information loss at edges
```

### Retrieval Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│                  Retrieval Parameters                           │
│                                                                 │
│  top_k = 5                                                      │
│  ├─ Number of contexts to retrieve                             │
│  └─ Trade-off: More contexts = more info but slower            │
│                                                                 │
│  similarity_threshold (optional)                                │
│  ├─ Minimum similarity score to include                        │
│  └─ Filter out low-quality matches                             │
│                                                                 │
│  max_distance (optional)                                        │
│  ├─ Maximum distance in vector space                           │
│  └─ Alternative to similarity threshold                        │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Latency Breakdown

```
Total Response Time: ~1-2 seconds (first query)
                    ~300-500ms (subsequent queries)

┌─────────────────────────────────────────────────────────────────┐
│                    Latency Components                           │
│                                                                 │
│  ┌────────────────────────────────────────┐                    │
│  │ 1. Corpus Initialization (first time)  │ ~500-1000ms        │
│  └────────────────────────────────────────┘                    │
│                                                                 │
│  ┌────────────────────────────────────────┐                    │
│  │ 2. Query Embedding                     │ ~50-100ms          │
│  └────────────────────────────────────────┘                    │
│                                                                 │
│  ┌────────────────────────────────────────┐                    │
│  │ 3. Vector Search                       │ ~100-200ms         │
│  └────────────────────────────────────────┘                    │
│                                                                 │
│  ┌────────────────────────────────────────┐                    │
│  │ 4. Context Retrieval                   │ ~50-100ms          │
│  └────────────────────────────────────────┘                    │
│                                                                 │
│  ┌────────────────────────────────────────┐                    │
│  │ 5. LLM Generation (Gemini 1.5 Pro)     │ ~500-1000ms        │
│  └────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Scalability

```
┌─────────────────────────────────────────────────────────────────┐
│                    Corpus Size vs Performance                   │
│                                                                 │
│  Documents    Chunks      Retrieval Time    Storage            │
│  ──────────   ────────    ──────────────    ───────            │
│  10           ~200        ~100ms            ~1 MB              │
│  100          ~2,000      ~150ms            ~10 MB             │
│  1,000        ~20,000     ~200ms            ~100 MB            │
│  10,000       ~200,000    ~300ms            ~1 GB              │
│  100,000      ~2,000,000  ~500ms            ~10 GB             │
│                                                                 │
│  Note: Retrieval time scales logarithmically                   │
└─────────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Layers                              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 1. Authentication                                         │ │
│  │    • Service Account credentials                         │ │
│  │    • Application Default Credentials                     │ │
│  │    • No hardcoded API keys                               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 2. Authorization (IAM)                                    │ │
│  │    • Vertex AI User role                                 │ │
│  │    • Storage Object Viewer role                          │ │
│  │    • Least privilege principle                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 3. Data Encryption                                        │ │
│  │    • At rest: GCS encryption                             │ │
│  │    • In transit: TLS/HTTPS                               │ │
│  │    • Corpus data encrypted                               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 4. Access Control                                         │ │
│  │    • Project-level isolation                             │ │
│  │    • Corpus-level permissions                            │ │
│  │    • Audit logging enabled                               │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

### Document Organization

```
Recommended Structure:
gs://your-bucket/
├── knowledge-base/
│   ├── policies/
│   │   ├── refund-policy.pdf
│   │   ├── privacy-policy.pdf
│   │   └── terms-of-service.pdf
│   ├── faqs/
│   │   ├── general-faq.txt
│   │   ├── technical-faq.txt
│   │   └── billing-faq.txt
│   └── products/
│       ├── product-catalog.pdf
│       ├── specifications.md
│       └── pricing.xlsx
```

### Corpus Strategy

```
Option 1: Single Corpus (Simple)
┌────────────────────────────────┐
│     "company-knowledge"        │
│  • All documents in one corpus │
│  • Easier to manage            │
│  • Good for small datasets     │
└────────────────────────────────┘

Option 2: Multiple Corpora (Advanced)
┌────────────────────────────────┐
│    "customer-support"          │
│  • FAQs, policies, guides      │
└────────────────────────────────┘
┌────────────────────────────────┐
│    "product-information"       │
│  • Specs, features, pricing    │
└────────────────────────────────┘
┌────────────────────────────────┐
│    "internal-docs"             │
│  • Employee handbook, etc      │
└────────────────────────────────┘
```

## Monitoring & Observability

```
Key Metrics to Track:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. Retrieval Quality                                           │
│     • Relevance of retrieved contexts                           │
│     • Average similarity scores                                 │
│     • Context usage in responses                                │
│                                                                 │
│  2. Performance                                                 │
│     • Query latency (p50, p95, p99)                            │
│     • Retrieval time                                            │
│     • Generation time                                           │
│                                                                 │
│  3. Usage                                                       │
│     • Queries per minute                                        │
│     • RAG vs non-RAG ratio                                      │
│     • Top queried topics                                        │
│                                                                 │
│  4. Costs                                                       │
│     • Storage costs                                             │
│     • Retrieval API calls                                       │
│     • Generation API calls                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

For implementation details, see [RAG_IMPLEMENTATION_SUMMARY.md](RAG_IMPLEMENTATION_SUMMARY.md)
