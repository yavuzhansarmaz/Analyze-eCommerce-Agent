# 🤖 Data Analysis LangGraph Agent

A sophisticated AI-powered tool for analyzing e-commerce data from Google BigQuery and generating business insights using Google Gemini and LangGraph framework.

## 🚀 Features

- **Natural Language Queries**: Ask questions in plain English
- **Multiple Analysis Types**:
  - Customer segmentation (RFM analysis)
  - Product performance analysis
  - Sales trends analysis
  - Geographic sales patterns
- **AI-Powered Insights**: Uses Google Gemini for enhanced explanations
- **Interactive CLI**: Simple command-line interface

## 📋 Requirements

- Python 3.8+
- Google Gemini API key (from [Google AI Studio](https://makersuite.google.com/app/apikey))
- Google Cloud BigQuery access (free tier available)

## 🛠️ Installation

1. **Set up environment variables**:
```bash
cp env_example.txt .env
```

2. **Launch the application**:
```bash
python main.py
```

## 💡 Usage

```bash
# Customer Analysis
analyze customer segments
customer behavior analysis

# Product Analysis
product performance analysis
which products sell best

# Sales Analysis
sales trends analysis
how are sales trending

# Geographic Analysis
geographic sales patterns
sales by state
```

## 🏗️ Architecture

**LangGraph-powered modular design** with:

- **Google BigQuery** for data processing
- **Google Gemini** for AI insights
- **LangGraph** for workflow orchestration and state management
- **Pandas** for data analysis
- **Simple CLI** for interaction

### Project Structure
```
├── main.py              # CLI interface
├── config.py           # Configuration management
├── agent/              # LangGraph workflow & state management
│   ├── __init__.py     # LangGraph-based agent with workflow nodes
│   ├── state.py        # State management with LangGraph integration
│   └── prompts.py      # LLM prompts
├── tools/              # Analysis tools
│   ├── query_builder.py    # SQL generation
│   └── analyzers/      # Business logic analyzers
└── bq_client.py        # BigQuery client
```

### LangGraph Workflow
The agent uses a **graph-based workflow** with these nodes:
1. **classify_query** - Determines analysis type from natural language
2. **build_query** - Constructs appropriate SQL query
3. **execute_query** - Runs query against BigQuery
4. **analyze_data** - Applies business logic using specialized analyzers
5. **enhance_insights** - Improves insights with AI

## 📊 Analysis Capabilities

- **Customer Segmentation**: RFM analysis and customer grouping
- **Product Performance**: Revenue and margin analysis
- **Sales Intelligence**: Trend analysis and patterns
- **Geographic Insights**: Regional sales analysis

## 🔧 Configuration

```env
GOOGLE_API_KEY=your-gemini-api-key-here
GOOGLE_CLOUD_PROJECT=your-project-id
```

## 📈 Cost & Performance

- **BigQuery**: 1TB/month free tier
- **Gemini API**: Pay-per-use with free quota
- **High Performance**: Async AI enhancement for 2.45x faster processing (93s → 38s for 3 insights)
- **Efficient**: Optimized queries and parallel processing

## 📚 Documentation

See the code comments and examples in the files for usage details.

---

**Built with ❤️ using Gemini and BigQuery**