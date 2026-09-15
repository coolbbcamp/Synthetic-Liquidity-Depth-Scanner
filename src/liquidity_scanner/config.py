from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://scanner:scanner@localhost:5432/liquidity_scanner",
        alias="DATABASE_URL",
    )
    jup_api_key: str = Field(default="", alias="JUP_API_KEY")
    jup_base_url: str = "https://api.jup.ag"
    jup_lite_base_url: str = "https://api.jup.ag"
    jup_api_base_override: str = Field(default="", alias="JUP_API_BASE")
    jup_quote_version: str = Field(default="v1", alias="JUP_QUOTE_VERSION")
    stonkfun_base_url: str = "https://www.stonkfun.xyz/api/public/v1"
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    enable_scheduler: bool = Field(default=True, alias="ENABLE_SCHEDULER")
    jup_rps: float = Field(default=10.0, alias="JUP_RPS")
    monthly_credit_budget: int = Field(default=25_000_000, alias="MONTHLY_CREDIT_BUDGET")
    user_agent: str = "LiquidityDepthScanner/0.1"
    baseline_notional_usd: float = 200.0
    ladder_notionals_usd: list[float] = Field(
        default_factory=lambda: [1_000, 10_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
    )
    usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    cliff_efficiency_delta: float = 0.15
    rfq_venues: list[str] = Field(
        default_factory=lambda: [
            "Riptide",
            "Byreal",
            "AlphaQ",
            "Quantum",
            "HumidiFi",
            "GoonFi V2",
            "Flux",
            "TesseraV",
            "BisonFi",
        ]
    )

    @property
    def jup_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        if self.jup_api_key:
            headers["x-api-key"] = self.jup_api_key
        return headers

    @property
    def jup_api_base(self) -> str:
        if self.jup_api_base_override:
            return self.jup_api_base_override.rstrip("/")
        return self.jup_base_url if self.jup_api_key else self.jup_lite_base_url

    @property
    def jup_quote_path(self) -> str:
        version = self.jup_quote_version.lstrip("/")
        if not version.startswith("swap/"):
            version = f"swap/{version}"
        if not version.endswith("/quote"):
            version = f"{version}/quote"
        return version


@lru_cache
def get_settings() -> Settings:
    return Settings()
