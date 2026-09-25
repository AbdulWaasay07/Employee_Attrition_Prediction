from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Employee Intelligence & Attrition Platform"
    
    # Since you are running MySQL locally, these are default local credentials.
    # We recommend changing the password to match your local setup, or using a .env file.
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "12345678" # Update this to your local MySQL password
    MYSQL_SERVER: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "attrition_database"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    class Config:
        env_file = ".env"

settings = Settings()
