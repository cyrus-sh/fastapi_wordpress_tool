# AI Sales Agent for WordPress (FastAPI + LangChain)

A FastAPI-based AI agent for e-commerce businesses with:
- Customer support chat with AI intelligence
- Product Q&A (availability, stock count, description)
- Sales flow (add to cart and checkout redirection)
- RAG pipeline from WordPress/WooCommerce MySQL data
- Pluggable LLM support (Gemini, OpenAI, DeepSeek, etc.)

## Architecture

- `app/main.py`: API entrypoint
- `app/core/config.py`: environment-based configuration
- `app/core/database.py`: SQLAlchemy async engine/session
- `app/services/wordpress/repository.py`: product and stock access from WP DB
- `app/services/rag/retriever.py`: RAG context builder from WP product data
- `app/services/llm/providers.py`: pluggable LLM provider factory
- `app/services/agent/customer_agent.py`: LangChain agent orchestration
- `app/services/wordpress/cart_service.py`: cart and checkout logic
- `app/routers/*.py`: REST endpoints

## Prerequisites

- Python 3.10+
- MySQL Server (or use Docker Compose)
- API Key for one of the supported LLM providers:
  - Google Gemini (free tier available)
  - OpenAI
  - DeepSeek
  - Any OpenAI-compatible provider

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/fastapi-wordpress-agent.git
cd fastapi-wordpress-agent
```

### 2. Copy environment template and configure:

```bash
cp .env.example .env
```

Edit `.env` and set the following variables:

```env
# MySQL / WordPress Database
MYSQL_HOST=your_mysql_host
MYSQL_PORT=3306
MYSQL_USER=your_wordpress_database_user
MYSQL_PASSWORD=your_secure_password
MYSQL_DB=wordpress

# LLM Configuration
LLM_PROVIDER=gemini  # Options: gemini, openai, deepseek, openai_compatible
GEMINI_API_KEY=your_google_api_key_here
# OR for OpenAI:
# OPENAI_API_KEY=your_openai_api_key_here
# OR for DeepSeek:
# DEEPSEEK_API_KEY=your_deepseek_api_key_here

# WordPress Checkout URL
WP_CHECKOUT_BASE_URL=https://your-domain.com/checkout
```

### 3. Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Run the API:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### 5. View interactive API documentation:

Open your browser and go to:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Using Docker Compose

```bash
# Build and run all services
docker-compose up --build

# The API will be available at http://localhost:8000
```

**Note:** Update the environment variables in `docker-compose.yml` before running.

## API Endpoints

### Health Check
```
GET /api/v1/health
```
Returns service health status.

### Products
```
GET /api/v1/products
```
Get all products from WordPress.

```
GET /api/v1/products/{product_id}
```
Get details for a specific product.

### Chat (AI Agent)
```
POST /api/v1/chat
Content-Type: application/json

{
  "message": "What products do you have?",
  "session_id": "user-session-123"
}
```
Send a message to the AI agent. The agent will use RAG to answer questions about your products.

### Cart Management
```
POST /api/v1/cart
Content-Type: application/json

{
  "session_id": "user-session-123",
  "product_id": 42,
  "quantity": 2
}
```
Add a product to the shopping cart.

```
GET /api/v1/cart/{session_id}
```
Retrieve the current shopping cart.

```
POST /api/v1/checkout
Content-Type: application/json

{
  "session_id": "user-session-123"
}
```
Initiate checkout and get a redirect URL to WordPress payment page.

## Supported LLM Providers

### Google Gemini (Recommended)
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Add to `.env`: `GEMINI_API_KEY=your_key`
4. Set `LLM_PROVIDER=gemini`

### OpenAI
1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add to `.env`: `OPENAI_API_KEY=your_key`
3. Set `LLM_PROVIDER=openai`

### DeepSeek
1. Get API key from [DeepSeek Platform](https://platform.deepseek.com)
2. Add to `.env`: `DEEPSEEK_API_KEY=your_key`
3. Set `LLM_PROVIDER=deepseek`

### OpenAI-Compatible Services
For any service compatible with OpenAI's API format (LiteLLM, Ollama, etc.):
```env
LLM_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_BASE_URL=https://your-provider.com/v1
OPENAI_COMPATIBLE_API_KEY=your_key
```

## WordPress / WooCommerce Notes

- This service reads from standard WooCommerce tables (`wp_posts`, `wp_postmeta`)
- For production checkout, keep final order placement in WordPress itself
- This service provides a headless cart flow and returns a `payment_url` parameter
- The cart session is stateless; you can store it in your frontend application
- RAG context is built from product titles, descriptions, and custom post meta

## Troubleshooting

### MySQL Connection Error
```
Error: Unable to connect to MySQL
```
- Ensure MySQL is running
- Check credentials in `.env`
- If using Docker, verify MySQL container is running: `docker-compose ps`

### LLM API Key Invalid
```
Error: Invalid API key or authentication failed
```
- Verify the API key in `.env` is correct and active
- Ensure you're using the right provider (check `LLM_PROVIDER` setting)
- Some APIs require IP whitelisting

### CORS Issues
If your frontend is on a different domain, enable CORS in `app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Table Not Found
- Ensure your WordPress tables have the correct prefix (set `WP_TABLE_PREFIX` in `.env`)
- Verify the database user has SELECT permissions on WordPress tables

## Performance Tips

1. **Embeddings**: Use `embedding_provider=google` for better accuracy with Gemini
2. **LLM Temperature**: Lower values (0.0-0.3) for factual product information
3. **Database**: Add indexes on `wp_posts` and `wp_postmeta` for large product catalogs
4. **Caching**: Consider adding Redis for session management in production

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Google AI Studio Embeddings (Free Tier)

Use your Google AI Studio API key in `GEMINI_API_KEY`, then set:

```env
EMBEDDING_PROVIDER=google
GOOGLE_EMBEDDING_MODEL=models/text-embedding-004
```

RAG retriever will run semantic ranking with Google embeddings and automatically fallback to keyword retrieval if embedding is unavailable.

## Gemini As LLM Provider (Google AI Studio)

Set your AI Studio key in `GEMINI_API_KEY`, then use:

```env
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash
```

Notes:
- `GEMINI_MODEL` is now the primary model field for `provider=gemini`.
- If `GEMINI_MODEL` starts with `models/`, it is normalized automatically.
- `LLM_MODEL` is still used by non-Gemini providers.
- For AI Studio naming, `LLM_PROVIDER` also accepts: `google`, `aistudio`, `google_aistudio`.

## Main Endpoints

- `POST /api/v1/chat/query`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `POST /api/v1/cart/add-item`
- `GET /api/v1/cart/{session_id}`
- `POST /api/v1/cart/{session_id}/checkout`

## Development

- Uses async SQLAlchemy with `aiomysql`
- Designed with separable services for easier scaling (can split Agent, RAG, Cart into microservices later)

#cyrusai