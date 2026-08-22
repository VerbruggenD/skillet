from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(320), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, server_default='user')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=True)
    user = relationship('User')


class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prep_time = Column(Integer, nullable=True)
    cook_time = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    source_url = Column(String(2048), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    search_vector = Column(TSVECTOR)
    owner = relationship('User')
    ingredients = relationship('Ingredient', back_populates='recipe')
    steps = relationship('Step', back_populates='recipe')
    images = relationship('Image', back_populates='recipe')


class Ingredient(Base):
    __tablename__ = 'ingredients'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=True)
    unit = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    recipe = relationship('Recipe', back_populates='ingredients')


class Step(Base):
    __tablename__ = 'steps'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    order = Column(Integer, nullable=False)
    instruction = Column(Text, nullable=False)
    recipe = relationship('Recipe', back_populates='steps')


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)


class RecipeTag(Base):
    __tablename__ = 'recipe_tags'
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)


class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    filename = Column(String(1024), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    recipe = relationship('Recipe', back_populates='images')
