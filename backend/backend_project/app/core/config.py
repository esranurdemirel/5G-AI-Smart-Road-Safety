from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Teknofest 2026 OGW Backend"

    OGW_BASE_URL: str
    OGW_CLIENT_ID: str
    OGW_CLIENT_SECRET: str
    OGW_REDIRECT_URI: str

    INPUT_VIDEO_PATH: str = "/app/data/input/video.mp4"
    OUTPUT_JSON_PATH: str = "/app/data/output/results.json"

    # Open Gateway Yetkilendirme Scope'ları[cite: 4]
    OGW_SCOPES: str = (
        "openid "
        "dpv:FraudPreventionAndDetection#number-verification:verify "
        "dpv:RequestedServiceProvision#quality-on-demand:sessions:create"
    )

    class Config:
        env_file = ".env"

settings = Settings()
