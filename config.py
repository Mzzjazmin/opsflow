class Config:
    SECRET_KEY = "opsflow-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///opsflow.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False