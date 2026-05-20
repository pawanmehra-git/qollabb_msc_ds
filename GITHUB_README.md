# 📚 Ansira - NLP-Powered Book Shop Chatbot

An intelligent, NLP-based automated customer service chatbot for online bookstores. Built with **Streamlit** and **Ollama (Mistral LLM)**, Ansira handles FAQ queries, book catalog browsing, order management, and general customer inquiries with a conversational AI approach.

**Status:** Fully functional | **Python:** 3.x | **License:** MIT

---

## ✨ Features

- **📖 Smart Intent Routing** - Automatically detects user intent: FAQ, book search, orders, order status, cancellation, or general queries
- **🤖 Local LLM Integration** - Uses Ollama with Mistral for context-aware, grounded responses
- **🔍 Intelligent FAQ Search** - Keyword matching + fuzzy scoring with LLM fallback for no-match scenarios
- **📚 Book Catalog Management** - Browse, filter by genre/author/price range, check stock availability
- **🛒 Order Management** - Place orders with automatic stock checks, lookup order status, cancel orders with stock restoration
- **💾 JSON-Based Persistence** - Lightweight, file-based data storage (no external database required)
- **📊 Activity Logging** - Tracks all conversations, queries, searches, and orders in `chat_logs.json`
- **💬 Conversation History** - Full message history passed to LLM for context-aware responses
- **🎨 Beautiful UI** - Clean Streamlit interface with sidebar analytics, customer name input, and chat preview
- **🎁 Smart Recommendations** - "You may also like..." suggestions based on book genre

---

## 📋 Project Structure

```
msc/
├── app/                          # Main application modules
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Streamlit app entry point
│   ├── chatbot.py               # Intent detection & routing logic
│   ├── llm.py                   # Ollama API integration
│   ├── faq.py                   # FAQ search & matching
│   ├── books.py                 # Book catalog & search functions
│   ├── orders.py                # Order management (create, status, cancel)
│   ├── logger.py                # Conversation & activity logging
│   └── utils.py                 # JSON file helpers & utilities
├── data/                        # JSON data files
│   ├── faq.json                 # FAQ database
│   ├── books.json               # Book catalog
│   ├── orders.json              # Order records
│   └── chat_logs.json           # Conversation history & analytics
├── ollama/                      # Ollama model configurations
│   └── AnsiraMistralDeterministic/
│       └── Modelfile            # Deterministic sampling config
├── requirements.txt             # Python dependencies
├── README.md                    # Original documentation
└── GITHUB_README.md             # This file
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.8+**
- **Ollama** (for local LLM inference)
- **pip** (Python package manager)

### Step 1: Clone & Navigate
```bash
# Clone or extract the project
cd c:\Users\HP\Desktop\msc
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv msc_env
msc_env\Scripts\activate

# macOS/Linux
python3 -m venv msc_env
source msc_env/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install & Configure Ollama

1. **Download Ollama** from [https://ollama.com](https://ollama.com)
2. **Install** and ensure the Ollama service is running
3. **Pull the Mistral model:**
   ```bash
   ollama pull mistral
   ```

### Step 5: (Optional) Create Deterministic Model
For consistent, reproducible answers:
```bash
ollama create ansira-mistral-deterministic -f ollama/AnsiraMistralDeterministic/Modelfile
```

### Step 6: Launch the Application
```bash
streamlit run app/main.py
```

The app will open automatically at `http://localhost:8501`

---

## ⚙️ Configuration

### Environment Variables
Control behavior via environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `mistral` | Model name to use |
| `OLLAMA_TEMPERATURE` | `0.0` | Response randomness (0=deterministic, 1=creative) |
| `OLLAMA_TOP_K` | `1` | Top-K sampling parameter |
| `OLLAMA_TOP_P` | `1.0` | Nucleus sampling parameter |
| `OLLAMA_SEED` | `42` | Random seed for reproducibility |

### Setting Environment Variables

**Windows (PowerShell):**
```powershell
$env:OLLAMA_MODEL = "ansira-mistral-deterministic"
$env:OLLAMA_TEMPERATURE = "0.0"
streamlit run app/main.py
```

**Windows (Command Prompt):**
```cmd
set OLLAMA_MODEL=ansira-mistral-deterministic
set OLLAMA_TEMPERATURE=0.0
streamlit run app/main.py
```

**macOS/Linux:**
```bash
export OLLAMA_MODEL=ansira-mistral-deterministic
export OLLAMA_TEMPERATURE=0.0
streamlit run app/main.py
```

---

## 📦 Project Functions & Modules

### Core Modules

#### **app/main.py** - Streamlit Application
The main entry point. Provides:
- Web UI with chat interface
- Sidebar for customer name input
- Session history preview
- Analytics dashboard
- Chat message rendering
- Admin JSON viewer

**Key Functions:**
- `init_session()` - Initialize chat session state
- `history_for_bot()` - Format message history for LLM context
- `render_sidebar()` - Display sidebar controls and analytics

---

#### **app/chatbot.py** - Intent Detection & Routing
Intelligent message routing engine that determines user intent.

**Intents Supported:**
- `FAQ` - Frequently asked questions
- `BOOK_SEARCH` - Browse/search catalog
- `ORDER_PLACEMENT` - Place new order
- `ORDER_STATUS` - Check order status
- `CANCEL_ORDER` - Cancel existing order
- `GENERAL` - General questions (LLM fallback)

**Key Functions:**
- `process_message(user_msg, history, customer_name)` - Route user message to appropriate handler
- `detect_intent(text)` - Identify intent from text patterns
- `extract_entities(text, intent)` - Extract parameters (book title, quantity, order ID, etc.)

**Entity Extraction:**
- Book title, author, quantity
- Order ID, customer name
- Genre, price range filters

---

#### **app/llm.py** - Ollama Integration
Handles all communication with Ollama LLM.

**Key Functions:**
- `generate_response(prompt, context, model, temperature, top_k, top_p, seed)` - Generate LLM response
- `extract_entities_llm(text, intent)` - Use LLM to intelligently extract entities from messy input

**Features:**
- HTTP-based API calls to Ollama
- Context injection for grounded responses
- Configurable sampling parameters
- Conversation history support

---

#### **app/faq.py** - FAQ Search & Matching
Intelligent FAQ retrieval system.

**Key Functions:**
- `search_faq(query, threshold=0.3)` - Find relevant FAQ entries
- `keyword_overlap_score(query, faq_entry)` - Calculate relevance score
- `fuzzy_match_score(query, candidate)` - Fuzzy string matching for typo tolerance

**Features:**
- Keyword-based matching
- Fuzzy string matching (handles typos)
- LLM fallback when no strong match found
- Ranked results with confidence scores

---

#### **app/books.py** - Book Catalog Management
Manages book inventory and search.

**Key Functions:**
- `get_all_books()` - Retrieve entire catalog
- `search_books(query, genre=None, author=None, price_range=None)` - Advanced search with filters
- `get_recommendations(genre)` - Get "you may also like" suggestions
- `check_stock(book_id)` - Verify availability
- `update_stock(book_id, quantity)` - Adjust inventory

**Supported Filters:**
- Genre (Fiction, Non-Fiction, Self-Help, etc.)
- Author name
- Price range (min/max)
- Keyword search

---

#### **app/orders.py** - Order Management
Full order lifecycle management.

**Key Functions:**
- `create_order(customer_name, items)` - Create new order
  - Auto-generates order ID
  - Validates stock availability
  - Records timestamp
- `get_order_status(order_id)` - Retrieve order details
- `cancel_order(order_id)` - Cancel order & restore stock
- `validate_order_items(items)` - Verify order can be fulfilled

**Order Workflow:**
1. User requests to place order
2. Intent detector recognizes `ORDER_PLACEMENT`
3. Entity extractor gets book title & quantity
4. Stock check performed
5. Order created with timestamp
6. User confirmed with order ID

---

#### **app/logger.py** - Activity Logging
Tracks all user interactions and system metrics.

**Key Functions:**
- `log_message(role, content, intent)` - Log chat message
- `log_interaction(intent, entity_data)` - Log user action
- `get_statistics()` - Retrieve session/overall stats
- `increment_counter(counter_name)` - Update metrics

**Tracked Metrics:**
- Total queries
- Book searches performed
- Orders placed
- FAQs accessed
- LLM fallbacks
- All messages (user & bot)

---

#### **app/utils.py** - Utility Functions
Helper functions for JSON operations.

**Key Functions:**
- `load_json(filepath)` - Safe JSON file loading with error handling
- `save_json(data, filepath)` - Atomic JSON writing
- `merge_json(existing, new)` - Merge JSON data structures
- `ensure_data_files()` - Initialize missing data files

---

## 💬 Usage Examples

### Example 1: FAQ Query
```
User: "What are your store hours?"
→ Intent: FAQ
→ Response: [FAQ match from faq.json]
```

### Example 2: Book Search
```
User: "Show me fiction books under $20"
→ Intent: BOOK_SEARCH
→ Entities: genre="Fiction", max_price=20.0
→ Response: [Filtered book list with descriptions]
```

### Example 3: Place Order
```
User: "I want to buy 2 copies of Atomic Habits"
→ Intent: ORDER_PLACEMENT
→ Entities: title="Atomic Habits", quantity=2, customer_name=[from sidebar]
→ Actions: Check stock → Create order → Return order ID
→ Response: "Order #10042 confirmed! 2x Atomic Habits for $27.98"
```

### Example 4: Check Order Status
```
User: "Check my order 10042"
→ Intent: ORDER_STATUS
→ Entities: order_id=10042
→ Response: [Order details: items, total, status, date]
```

### Example 5: Cancel Order
```
User: "Cancel order 10042"
→ Intent: CANCEL_ORDER
→ Entities: order_id=10042
→ Actions: Remove order → Restore stock
→ Response: "Order #10042 cancelled. Stock restored."
```

### Example 6: General Question
```
User: "What's your return policy?"
→ Intent: GENERAL (no FAQ match strong enough)
→ Context: [System prompt + conversation history]
→ Response: [LLM-generated helpful answer]
```

---

## 📊 Data File Schemas

### **data/faq.json**
```json
[
  {
    "id": 1,
    "question": "What are your store hours?",
    "answer": "We're open Monday-Friday 9AM-6PM, Saturday 10AM-4PM, closed Sundays.",
    "category": "Operations"
  },
  ...
]
```

### **data/books.json**
```json
[
  {
    "id": 1,
    "title": "Atomic Habits",
    "author": "James Clear",
    "genre": "Self-Help",
    "price": 14.99,
    "stock": 42,
    "description": "Tiny changes, remarkable results..."
  },
  ...
]
```

### **data/orders.json**
```json
[
  {
    "order_id": 10001,
    "customer_name": "John Doe",
    "items": [
      { "book_id": 1, "title": "Atomic Habits", "quantity": 2, "price_per_unit": 14.99 }
    ],
    "total": 29.98,
    "timestamp": "2024-01-15 14:30:00",
    "status": "Completed"
  },
  ...
]
```

### **data/chat_logs.json**
```json
{
  "sessions": [
    {
      "messages": [
        { "role": "user", "content": "Show me books", "intent": "book_search" },
        { "role": "assistant", "content": "[response]", "used_llm": false }
      ],
      "timestamp": "2024-01-15 14:30:00"
    }
  ],
  "statistics": {
    "total_queries": 156,
    "book_searches": 43,
    "orders_placed": 12,
    "faq_accessed": 35
  }
}
```

---

## 🔧 Dependencies

### Key Libraries
- **streamlit** (1.55.0) - Web UI framework
- **requests** (2.33.0) - HTTP client for Ollama API
- **pandas** (2.3.3) - Data manipulation
- **numpy** (2.4.4) - Numerical computing
- **pillow** (12.1.1) - Image processing
- **python-dateutil** (2.9.0) - Date utilities

See [requirements.txt](requirements.txt) for complete list.

---

## 🎯 Best Practices

### 1. **Deterministic Responses**
For consistent answers across sessions, use the deterministic model:
```bash
ollama create ansira-mistral-deterministic -f ollama/AnsiraMistralDeterministic/Modelfile
export OLLAMA_MODEL=ansira-mistral-deterministic
export OLLAMA_TEMPERATURE=0.0
```

### 2. **Conversation History**
The bot automatically maintains conversation context by passing message history to the LLM. This enables:
- Follow-up questions
- Context awareness
- Better entity resolution

### 3. **Error Handling**
All JSON operations are wrapped in try-except blocks. The app gracefully handles:
- Missing data files (auto-creates defaults)
- Malformed JSON (logs error, uses fallback)
- Ollama connection issues (displays friendly error)

### 4. **Performance Optimization**
- FAQ search uses early exit on high-confidence matches
- Book search uses efficient filtering
- LLM calls are cached when possible
- Session state minimizes re-computation

---

## 🐛 Troubleshooting

### Issue: "Connection refused" for Ollama
**Solution:** Ensure Ollama is running
```bash
# Windows/Mac: Check system tray or Services
# Linux: sudo systemctl status ollama
ollama serve
```

### Issue: Model not found
**Solution:** Pull the model first
```bash
ollama pull mistral
# Or use custom model
ollama pull neural-chat
export OLLAMA_MODEL=neural-chat
```

### Issue: Slow responses
**Solution:** Use deterministic model with lower temperature
```bash
export OLLAMA_TEMPERATURE=0.0
export OLLAMA_TOP_K=1
```

### Issue: Chat history not loading
**Solution:** Check data directory permissions
```bash
# Ensure data/ directory exists and is writable
mkdir -p data/
chmod 755 data/
```

---

## 📝 Logging & Debugging

### View Chat Logs
Check `data/chat_logs.json` for:
- All messages (user & bot)
- Intent detection results
- LLM usage statistics
- Order metrics

### Enable Verbose Output
```python
# In app/logger.py or any module
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Monitor Ollama
```bash
# Check Ollama API health
curl http://127.0.0.1:11434/api/tags
```

---

## 🚀 Future Enhancements

- [ ] Database backend (PostgreSQL/MongoDB) for scalability
- [ ] Advanced NLP with spaCy/BERT for better entity extraction
- [ ] Multi-language support
- [ ] Integration with payment gateways
- [ ] Real-time inventory sync
- [ ] Customer authentication & profiles
- [ ] Voice input/output support
- [ ] Analytics dashboard with charts

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

## 👥 Support

For issues, questions, or suggestions:
1. Check existing documentation in [README.md](README.md)
2. Review data files in `data/` directory
3. Check chat logs in `data/chat_logs.json` for error patterns

---

## 🙏 Acknowledgments

Built with:
- **Streamlit** - Fast web app framework
- **Ollama** - Local LLM inference
- **Mistral** - Powerful open-source language model

---

**Happy coding! 📚✨**
