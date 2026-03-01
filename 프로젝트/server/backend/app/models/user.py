from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(50), nullable=False)
    login_id = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    profile_image_url = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # [핵심] 이 두 함수가 꼭 있어야 합니다!
    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "login_id": self.login_id,
            "profile_image_url": self.profile_image_url,
            "phone_number": self.phone_number
        }