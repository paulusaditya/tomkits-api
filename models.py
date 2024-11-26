from extensions import db
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from google.cloud import storage

credentials_path = "./service-account.json"

storage_client = storage.Client.from_service_account_json(credentials_path)

buckets = list(storage_client.list_buckets())

class History(db.Model):  # Use db.Model instead of Base
    __tablename__ = "history"
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid4()))
    percentage = db.Column(db.DECIMAL(5, 2), nullable=False)
    user_id = db.Column(db.String(255), db.ForeignKey("users.id", ondelete="CASCADE"))
    disease_id = db.Column(db.Integer, db.ForeignKey("disease.id", ondelete="CASCADE"))
    images = db.Column(db.String(255))
    created_at = db.Column(TIMESTAMP, default=lambda: datetime.now(tz=timezone.utc))

    user = relationship("User", back_populates="histories")
    disease = relationship("Disease", back_populates="histories")

    @classmethod
    def save_image(cls, file) -> str:
        BUCKET_NAME = 'tomkits'

        storage_client = storage.Client()

        try:
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(file.filename)

            # Reset file stream before uploading
            file.stream.seek(0)

            blob.upload_from_file(file, content_type=file.content_type)
            blob.make_public()

            return blob.public_url
        except Exception as e:
            print(f"Failed to upload image: {e}")
            return ""


class User(db.Model):  # Use db.Model instead of Base
    __tablename__ = "users"
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(TIMESTAMP, default=lambda: datetime.now(tz=timezone.utc))

    histories = relationship("History", back_populates="user")

    def __init__(self, username: str, email: str) -> None:
        self.username = username
        self.email = email

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @classmethod
    def get_user_by_email(cls, email: str):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def get_user_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Disease(db.Model):  # Use db.Model instead of Base
    __tablename__ = "disease"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disease_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    solution = db.Column(db.Text)
    created_at = db.Column(TIMESTAMP, default=lambda: datetime.now(tz=timezone.utc))

    products = relationship("Product", back_populates="disease")
    histories = relationship("History", back_populates="disease")


class Product(db.Model):  # Use db.Model instead of Base
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(255), nullable=False)
    active_ingredient = db.Column(db.String(255))
    usage_frequency = db.Column(db.String(255))
    application_method = db.Column(db.String(255))
    product_link = db.Column(db.String(255))
    product_image = db.Column(db.String(255))
    disease_id = db.Column(db.Integer, db.ForeignKey("disease.id", ondelete="SET NULL"))

    disease = relationship("Disease", back_populates="products")


class TokenBlocklist(db.Model):  # Use db.Model instead of Base
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    jti = db.Column(db.String(), nullable=True)
    create_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"Token {self.jti}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

