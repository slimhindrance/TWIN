# 🔧 Environment Configuration Template

**Copy the content below to a `.env` file in the `backend/` directory**

```bash
# Total Life AI - Multi-Provider Configuration Template
# Copy this file to .env and configure your AI providers

# =============================================================================  
# 💰 COST-OPTIMIZED AI CONFIGURATION (90% SAVINGS!)
# =============================================================================

# Primary provider for most queries (together = 90% cost savings!)
AI_PRIMARY_PROVIDER=together

# Fallback provider for complex queries or when primary fails  
AI_FALLBACK_PROVIDER=openai

# =============================================================================
# TOGETHER AI (RECOMMENDED - 90% Cost Savings!)
# =============================================================================
# Get your API key: https://api.together.xyz/settings/api-keys
# Cost: ~$0.20 per 1M tokens (vs $2.00 for GPT-4)

TOGETHER_API_KEY=your_together_api_key_here

# Available models (Llama 3.1 8B is best cost/performance):
# - meta-llama/Llama-3.1-8B-Instruct-Turbo (recommended)
# - meta-llama/Llama-3.1-70B-Instruct-Turbo (more capable, higher cost)
TOGETHER_MODEL=meta-llama/Llama-3.1-8B-Instruct-Turbo
TOGETHER_EMBEDDING_MODEL=togethercomputer/m2-bert-80M-8k-retrieval

# =============================================================================
# AWS BEDROCK (FALLBACK - Good Quality & Cost)
# =============================================================================
# Configure AWS credentials: https://docs.aws.amazon.com/bedrock/
# Cost: ~$0.30 per 1M tokens (Haiku) to $15 per 1M tokens (Opus)

AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here

# Available models:
# - anthropic.claude-3-haiku-20240307-v1:0 (fastest, cheapest)
# - anthropic.claude-3-sonnet-20240229-v1:0 (balanced)
# - anthropic.claude-3-opus-20240229-v1:0 (most capable, expensive)
BEDROCK_MODEL=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v1

# =============================================================================
# OPENAI (BACKUP - Most Expensive)
# =============================================================================
# Only needed as ultimate fallback - not recommended for regular use
# Cost: $30 per 1M tokens (GPT-4) vs $0.20 for Together AI

# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_MODEL=gpt-4-1106-preview
# OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# =============================================================================
# SMART ROUTING CONFIGURATION
# =============================================================================

# Simple queries (<=15 words) go to primary provider
SIMPLE_QUERY_MAX_WORDS=15

# Patterns that trigger simple routing (comma-separated)
SIMPLE_QUERY_PATTERNS=what,when,where,who,how many,hello,hi,thanks

# Complex query detection threshold (characters)
COMPLEX_QUERY_THRESHOLD=50

# =============================================================================
# APPLICATION SETTINGS  
# =============================================================================

# Security
SECRET_KEY=change-this-in-production-to-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS (add your frontend URL)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Database & Storage
CHROMA_PERSIST_DIRECTORY=./chroma_db
COLLECTION_NAME=digital_twin_knowledge

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Environment
ENVIRONMENT=development
DEBUG=true
```

## 💰 Cost Comparison

| Provider | Cost per 1M tokens | Cost per 1000 chats* |
|----------|-------------------|---------------------|
| **Together AI** | $0.20 | **$0.20** ✅ |
| AWS Bedrock (Haiku) | $0.25 | $0.25 |
| AWS Bedrock (Sonnet) | $3.00 | $3.00 |
| OpenAI GPT-4 | $30.00 | $30.00 ❌ |

*Estimated based on average chat length

## 🚀 Quick Setup

1. **Copy to .env file:**
   ```bash
   cd backend
   copy ENV_TEMPLATE.md .env
   # Edit .env and add your API keys
   ```

2. **Get Together AI API Key:** 
   - Visit: https://api.together.xyz/settings/api-keys
   - Sign up and get your key
   - Add to `TOGETHER_API_KEY=` in .env

3. **Optional - AWS Bedrock:**
   - Set up AWS credentials
   - Add to AWS_* fields in .env

4. **Start the server:**
   ```bash
   ../start_backend.ps1
   ```

## 🎯 Smart Routing Logic

- **Simple queries** → Together AI (90% cheaper)
- **Complex reasoning** → AWS Bedrock Claude (better quality)  
- **Auto-fallback** if primary provider fails
- **Query complexity detection** based on patterns and length

## 🔧 Configuration Tips

- Start with just Together AI for 90% cost savings
- Add Bedrock as fallback for production reliability
- OpenAI only needed if others fail
- Monitor usage and adjust providers as needed
