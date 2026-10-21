from database import db


class InboundHistory(db.Model):
    __tablename__ = "inbound_history"

    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_name = db.Column(db.String(255), nullable=False)
    total_container = db.Column(db.Integer, nullable=False, default=0)
    total_qty_cs = db.Column(db.Integer, nullable=False, default=0)
    total_required_pallets = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False)  # 'Success' | 'Failed'
    upload_time = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    details = db.relationship(
        "InboundDetail",
        back_populates="history",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class InboundDetail(db.Model):
    __tablename__ = "inbound_detail"

    detail_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    history_id = db.Column(
        db.Integer,
        db.ForeignKey("inbound_history.history_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    container_number = db.Column(db.String(50), nullable=False)
    batch_number = db.Column(db.String(50), nullable=False)
    item_id = db.Column(
        db.String(50), db.ForeignKey("master_sku.item_id"), nullable=False, index=True
    )
    qty_carton = db.Column(db.Integer, nullable=False)
    qty_pallet = db.Column(db.Integer, nullable=False)

    history = db.relationship("InboundHistory", back_populates="details")
    sku = db.relationship("MasterSKU")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)