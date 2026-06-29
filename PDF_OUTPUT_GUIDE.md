# Multi-Agent Research Assistant - PDF Output System

## 📋 Project Overview

Your multi-agent research assistant now generates **three output formats**:
1. **Markdown** (`.md`) - Raw structured markdown
2. **Formatted Text** (`.txt`) - Beautifully formatted plain text with ASCII boxes
3. **Professional PDF** (`.pdf`) - Publication-ready PDF report

## 🤖 The 5 Agents & Their Tasks

### 1. **Researcher Agent**
- **Task:** Search the web and find 3 important, accurate points about the topic with credible sources
- **Output:** Key findings with source references

### 2. **Teacher Agent**
- **Task:** Explain the topic step-by-step with clear real-world examples
- **Output:** Structured explanation (What it is → How it works → Real-world example)

### 3. **Simplifier Agent**
- **Task:** Rewrite complex explanations in the simplest possible language
- **Output:** Plain language summary without jargon

### 4. **Student Agent**
- **Task:** Write concise, well-organized revision notes
- **Output:** Bullet-point study notes for quick review

### 5. **Examiner Agent**
- **Task:** Create 3 questions to test genuine understanding
- **Output:** Self-test questions (recall → explanation → application)

## 📄 Output Files Generated

When you run the project, three files are saved to `outputs/`:

```
outputs/
├── report_20260629_132617.md              # Markdown format
├── report_20260629_132617_structured.txt  # Formatted text with ASCII boxes
└── report_20260629_132617.pdf             # Professional PDF report
```

### PDF Report Features

The PDF includes:
- ✅ Title page with topic and generation timestamp
- ✅ Table of Contents
- ✅ 5 sections - one for each agent
- ✅ Each section shows:
  - Agent name
  - Task description
  - Complete output/answer
- ✅ Professional formatting with:
  - Blue headers
  - Proper spacing and pagination
  - Justified text
  - Footer with generation info

### Example PDF Structure

```
┌─────────────────────────────────────────┐
│  Multi-Agent Research Report            │
│  Topic: What is Artificial Intelligence?│
│  Generated: June 29, 2026                │
└─────────────────────────────────────────┘

Table of Contents
1. Research Findings
2. Detailed Explanation
3. Simplified Summary
4. Study Notes
5. Self-Test Questions

─────────────────────────────────────────

1. RESEARCH FINDINGS
   Agent: Researcher
   Task: Search the web and find 3 important points...
   
   [Full researcher output here]

─────────────────────────────────────────

2. DETAILED EXPLANATION
   Agent: Teacher
   Task: Explain topic step-by-step...
   
   [Full teacher output here]

[... continues for all 5 agents ...]
```

## 🚀 Usage

### Run with Default Topic
```bash
python main.py
```

### Run with Custom Topic
```bash
python main.py --topic "What is Machine Learning?"
```

### Run in Async Mode (Faster)
```bash
python main.py --topic "What is Quantum Computing?" --async
```

## 📦 Files Changed/Created

### Created:
- **`pdf_formatter.py`** - PDF generation module with professional formatting
- **`.env.example`** - Environment variables template

### Updated:
- **`requirements.txt`** - Added `reportlab` for PDF generation
- **`pyproject.toml`** - Added `reportlab` to dependencies
- **`main.py`** - Now generates 3 output formats (markdown, text, PDF)
- **`output_formatter.py`** - Structured text output formatter
- **`agents/reporter_agent.py`** - New Reporter agent for aggregation
- **`tasks/report_task.py`** - New Report task for final aggregation
- **`crew.py`** - Updated with Reporter agent

## 🔧 Configuration

### OpenRouter Setup
1. Get API key from [openrouter.ai](https://openrouter.ai)
2. Create `.env` file:
   ```
   OPENROUTER_API_KEY=your_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   SERPER_API_KEY=your_serper_key_here
   ```

### Change LLM Model
Edit `config.py` line 60:
```python
DEFAULT_LLM = "anthropic/claude-3-5-sonnet"  # 200k tokens
# Or try:
# DEFAULT_LLM = "openai/gpt-4-turbo-preview"  # 128k tokens
```

## 📊 Output Flow

```
CLI Input (Topic)
        ↓
Researcher → Teacher → Simplifier → Student → Examiner → Reporter
        ↓
save_output()
        ├→ report_*.md (Markdown)
        ├→ report_*_structured.txt (ASCII formatted)
        └→ report_*.pdf (Professional PDF)
```

## 🎨 PDF Formatting Details

- **Font:** Helvetica (standard PDF font)
- **Colors:**
  - Title: Dark blue (#1a237e)
  - Headers: White text on blue (#1565c0)
  - Body: Dark gray (#212121)
  - Metadata: Light gray (#9e9e9e)
- **Layout:** Letter size (8.5" × 11") with 0.5" margins
- **Sections:** Each agent output on a new page

## ✨ Next Steps

1. **Test the PDF output:**
   ```bash
   python main.py --topic "Your Topic Here"
   ```
2. **Check the outputs folder** for the generated PDF
3. **Open the PDF** in any PDF reader to view the professional report

## 📝 Dependencies

- `crewai` - Multi-agent orchestration
- `crewai-tools` - Built-in tools
- `openai` - LLM API client
- `python-dotenv` - Environment management
- `reportlab` - PDF generation ✨ **New**

All dependencies are listed in `requirements.txt` and `pyproject.toml`.
