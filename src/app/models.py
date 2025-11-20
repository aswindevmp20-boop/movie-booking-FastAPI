from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="customer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(500))
    duration = Column(Integer, nullable=False)
    release_date = Column(DateTime(timezone=True))
    rating = Column(String(10))

    shows = relationship("Show", back_populates="movie")


class Theatre(Base):
    __tablename__ = "theatres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)

    shows = relationship("Show", back_populates="theatre")
    seats = relationship("Seat", back_populates="theatre", cascade="all, delete")  


class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    theatre_id = Column(Integer, ForeignKey("theatres.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    movie = relationship("Movie", back_populates="shows")
    theatre = relationship("Theatre", back_populates="shows")


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    theatre_id = Column(Integer, ForeignKey("theatres.id", ondelete="CASCADE"))
    row = Column(String(5), nullable=False)
    number = Column(Integer, nullable=False)
    status = Column(String(20), default="available")  # not per show yet

    theatre = relationship("Theatre", back_populates="seats")
