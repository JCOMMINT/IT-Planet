"""Shared pytest fixtures and HTML stubs for all test layers."""
from __future__ import annotations

import os
import pytest

# ── Environment stub (must be set before any shared.config import) ────────────
os.environ.setdefault("PROXY_USER", "test-proxy-user")
os.environ.setdefault("PROXY_PASS", "test-proxy-pass")
os.environ.setdefault("GCS_BUCKET", "test-bucket")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
os.environ.setdefault("FIRESTORE_PROJECT", "test-project")
os.environ.setdefault("CLOUD_TASKS_QUEUE", "test-queue")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_USER", "test@test.com")
os.environ.setdefault("SMTP_PASS", "test-pass")
os.environ.setdefault("SMTP_FROM", "test@test.com")
os.environ.setdefault("NOTIFICATION_EMAIL", "notify@test.com")
os.environ.setdefault("JACOB_WORKER_URL", "http://jacob-worker/")
os.environ.setdefault("IT_RESELL_WORKER_URL", "http://it-resell-worker/")
os.environ.setdefault("IT_MARKET_WORKER_URL", "http://it-market-worker/")
os.environ.setdefault("TONITRUS_DISCOVERY_URL", "http://tonitrus-discovery/")
os.environ.setdefault("TONITRUS_WORKER_URL", "http://tonitrus-worker/")
os.environ.setdefault("TONITRUS_MERGE_URL", "http://tonitrus-merge/")


# ── HTML fixtures ─────────────────────────────────────────────────────────────

JACOB_PLP_HTML = """
<html><body>
  <a href="/produkte/laptop-abc-12345">Laptop ABC</a>
  <a href="/produkte/keyboard-xyz-99999">Keyboard XYZ</a>
  <a href="/other/link">Not a product</a>
</body></html>
"""

JACOB_PLP_EMPTY_HTML = """
<html><body><p>No results found.</p></body></html>
"""

JACOB_PDP_HTML = """
<html><body>
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "Laptop ABC",
  "sku": "SKU-001",
  "mpn": "MPN-ABC",
  "gtin13": "1234567890123",
  "description": "A great laptop",
  "brand": {"@type": "Brand", "name": "BrandX"},
  "offers": {
    "@type": "Offer",
    "price": "999.00",
    "priceCurrency": "EUR",
    "itemCondition": "https://schema.org/NewCondition",
    "availability": "https://schema.org/InStock"
  }
}
</script>
</body></html>
"""

JACOB_PDP_MULTI_OFFER_HTML = """
<html><body>
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "Server X",
  "sku": "SRV-001",
  "brand": {"name": "HPE"},
  "offers": [
    {"price": "500.00", "priceCurrency": "EUR", "itemCondition": "NewCondition"},
    {"price": "350.00", "priceCurrency": "EUR", "itemCondition": "RefurbishedCondition"}
  ]
}
</script>
</body></html>
"""

IT_RESELL_PLP_HTML = """
<html><body>
  <div class="product_item">
    <a class="product-name" href="/en/products/thinkpad-t490">ThinkPad T490</a>
    <span class="money main_price">€ 450.00</span>
    <span class="money main_price">€ 520.00</span>
    <input name="id" value="var-001" />
    <div class="single_product__sku">ABC123</div>
  </div>
  <div class="product_item">
    <a class="product-name" href="/en/products/dell-xps-15">Dell XPS 15</a>
    <span class="money main_price">€ 1200.00</span>
    <input name="id" value="var-002" />
  </div>
</body></html>
"""

IT_RESELL_PAGINATION_HTML = """
<html><body>
  <ul>
    <li class="pagination_el"><a href="?page=1">1</a></li>
    <li class="pagination_el"><a href="?page=2">2</a></li>
    <li class="pagination_el"><a href="?page=740">740</a></li>
  </ul>
</body></html>
"""

IT_MARKET_PLP_HTML = """
<html><body>
  <div class="product-box">
    <a class="product-name" href="/en/category/laptop-123">Laptop 123</a>
    <input name="product-name" value="LAP-CODE-001" />
    <input name="product-id" value="prod-id-001" />
    <div class="product-description">Fast laptop with SSD</div>
    <div class="product-detail-configurator-option" data-product-id="var-A">
      <div class="maxia-variants-list-text">New condition text</div>
      <div class="product-variant-price">€ 799.00</div>
      <div class="product-variant-stock">5 items</div>
      <span class="product-variant-availability inStock"></span>
    </div>
    <div class="product-detail-configurator-option" data-product-id="var-B">
      <div class="maxia-variants-list-text">Refurbished grade A</div>
      <div class="product-variant-price">€ 499.00</div>
      <div class="product-variant-stock">12 items</div>
      <span class="product-variant-availability withDelivery"></span>
    </div>
  </div>
</body></html>
"""

IT_MARKET_PAGINATION_HTML = """
<html><body>
  <div class="pagination">
    <a href="?p=1" data-page="1">1</a>
    <a href="?p=2" data-page="2">2</a>
    <a href="?p=50" data-page="50">50</a>
  </div>
</body></html>
"""

TONITRUS_PLP_HTML = """
<html><body>
  <div class="productlist-item-info">Showing 1-50 of 127 products</div>
  <div class="product-thumbnail">
    <a href="/dell-poweredge-r750_del-r750-001">PowerEdge R750</a>
    <span class="product-name">Dell PowerEdge R750</span>
    <span class="price h1">€ 4,500.00</span>
    <span class="manufacturer-name">Dell</span>
  </div>
  <div class="product-thumbnail">
    <a href="/hpe-proliant-dl380-gen10_hpe-dl380-g10">HPE ProLiant DL380</a>
    <span class="product-name">HPE ProLiant DL380 Gen10</span>
    <span class="price h1">€ 3,200.00</span>
    <span class="manufacturer-name">HPE</span>
  </div>
</body></html>
"""


@pytest.fixture()
def jacob_plp_html() -> str:
    """Return sample Jacob PLP HTML."""
    return JACOB_PLP_HTML


@pytest.fixture()
def jacob_pdp_html() -> str:
    """Return sample Jacob PDP HTML with single offer."""
    return JACOB_PDP_HTML


@pytest.fixture()
def jacob_pdp_multi_html() -> str:
    """Return sample Jacob PDP HTML with multiple offers."""
    return JACOB_PDP_MULTI_OFFER_HTML


@pytest.fixture()
def it_resell_plp_html() -> str:
    """Return sample IT-Resell PLP HTML."""
    return IT_RESELL_PLP_HTML


@pytest.fixture()
def it_resell_pagination_html() -> str:
    """Return sample IT-Resell pagination HTML."""
    return IT_RESELL_PAGINATION_HTML


@pytest.fixture()
def it_market_plp_html() -> str:
    """Return sample IT Market PLP HTML."""
    return IT_MARKET_PLP_HTML


@pytest.fixture()
def it_market_pagination_html() -> str:
    """Return sample IT Market pagination HTML."""
    return IT_MARKET_PAGINATION_HTML


@pytest.fixture()
def tonitrus_plp_html() -> str:
    """Return sample Tonitrus PLP HTML."""
    return TONITRUS_PLP_HTML
