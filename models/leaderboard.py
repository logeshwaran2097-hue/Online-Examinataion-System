from datetime import datetime
from database import db

class Leaderboard(db.Model):
    """
    Model representing the global scoring leaderboard for students.
    """
    __tablename__ = 'leaderboard'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    total_score = db.Column(db.Integer, default=0)
    rank_position = db.Column(db.Integer, nullable=True, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('total_score >= 0', name='chk_total_score'),
        db.CheckConstraint('rank_position > 0', name='chk_rank_position'),
    )

    # Relationships
    student = db.relationship('User', back_populates='leaderboard_entry')

    def __repr__(self):
        return f"<Leaderboard student={self.student_id} rank={self.rank_position}>"
