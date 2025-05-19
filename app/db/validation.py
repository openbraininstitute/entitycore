from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY  # Using PostgreSQL's array type for sets

Base = declarative_base()

class Validation(Base):
    __tablename__ = "validations"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False, index=True)
    
    # Using PostgreSQL ARRAY type to store sets of strings
    # Note: This doesn't guarantee uniqueness like Python sets do - application logic would need to enforce that
    must_pass_to_upload = Column(ARRAY(String), nullable=True)
    must_run_upon_upload = Column(ARRAY(String), nullable=True)
    must_pass_to_simulate = Column(ARRAY(String), nullable=True)
    
    def __repr__(self):
        return f"<Validation(entity_type='{self.entity_type}')>"
    
    # Helper methods to work with the array fields as sets
    def get_must_pass_to_upload(self):
        return set(self.must_pass_to_upload) if self.must_pass_to_upload else set()
    
    def set_must_pass_to_upload(self, value_set):
        self.must_pass_to_upload = list(value_set) if value_set else None
    
    def get_must_run_upon_upload(self):
        return set(self.must_run_upon_upload) if self.must_run_upon_upload else set()
    
    def set_must_run_upon_upload(self, value_set):
        self.must_run_upon_upload = list(value_set) if value_set else None
    
    def get_must_pass_to_simulate(self):
        return set(self.must_pass_to_simulate) if self.must_pass_to_simulate else set()
    
    def set_must_pass_to_simulate(self, value_set):
        self.must_pass_to_simulate = list(value_set) if value_set else None
