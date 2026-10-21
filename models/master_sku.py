from database import db


class MasterSKU(db.Model):
    __tablename__ = "master_sku"

    item_id = db.Column(db.String(50), primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    cpp = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "description": self.description,
            "cpp": self.cpp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
