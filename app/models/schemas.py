from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = 'ok'


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float | None = None
    stock_quantity: int | None = None
    stock_status: str | None = None


class ProductListResponse(BaseModel):
    items: list[ProductOut]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=3)


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    used_products: list[int] = Field(default_factory=list)


class AddToCartRequest(BaseModel):
    session_id: str
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float | None = None
    line_total: float | None = None


class CartOut(BaseModel):
    session_id: str
    items: list[CartItemOut]
    total: float


class CheckoutResponse(BaseModel):
    session_id: str
    payment_url: str
