from sqlalchemy import (
    Column,
    Boolean,
    Index,
    Integer,
    String,
    DateTime,
    Date,
    Time,
    ForeignKey,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
    )

from zope.sqlalchemy import ZopeTransactionExtension

import logging
log = logging.getLogger(__name__)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    time_slot_size = Column(Integer)
    active = Column(Boolean)

    days = relationship("EventDay", backref='event',
            cascade='all, delete, delete-orphan')
    prelims = relationship("PrelimAssignment", backref='event',
            cascade='all, delete, delete-orphan')
    #meetings = relationship("Meeting", backref='event',
    #        cascade='all, delete, delete-orphan')

    def __repr__(self):
        try:
            return "<Event(id='%d', name='%s', time_slot_size='%d', active='%d')>" % (
                    self.id, self.name, self.time_slot_size, self.active)
        except TypeError:
            if self.id == None:
                log.debug("id field is None. Did you forget to flush?")
            raise

class EventDay(Base):
    __tablename__ = 'event_days'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    date = Column(Date)

    slots = relationship("TimeSlot", backref='event_day',
            cascade='all, delete, delete-orphan')

    def __repr__(self):
        try:
            return "<EventDay(id='%d', event_id='%d', date='%s')>" % (
                    self.id, self.event_id, self.date)
        except TypeError:
            if self.id == None:
                log.debug("id field is None. Did you forget to flush?")
            raise

class TimeSlot(Base):
    __tablename__ = 'time_slots'
    id = Column(Integer, primary_key=True)
    event_day_id = Column(Integer, ForeignKey("event_days.id"), nullable=False)

    time_slot = Column(Time, nullable=False)

    # uniqname is populated if this is the result from a submitted user, it is
    # blank if this is a blackout slot for the event
    uniqname = Column(String(8))

    # The prelim_id maps back to a scheduled prelim. Note that the username
    # (must) also be populated for a scheduled prelim -- the effect is the add
    # to the set of times that are marked as busy for that user
    prelim_id = Column(Integer, ForeignKey("prelim_assignments.id"));

    def __repr__(self):
        try:
            return "<TimeSlot(id='%d', event_day_id='%d', uniqname='%s', time_slot='%s')>" % (
                    self.id, self.event_day_id, self.uniqname, self.time_slot)
        except TypeError:
            if self.id == None:
                log.debug("id field is None. Did you forget to flush?")
            raise

class Faculty(Base):
    __tablename__ = 'faculty'
    id = Column(Integer, primary_key=True)
    uniqname = Column(String(8), unique=True)
    name = Column(String(50))
    office = Column(String(50))

    def __repr__(self):
        return "<Faculty(id='{0}', uniqname='{1}', name='{2}', office='{3}')>".format(
                self.id, self.uniqname, self.name, self.office)

class PrelimAssignment(Base):
    __tablename__ = 'prelim_assignments'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    student_uniqname = Column(String(8))

    times = relationship("TimeSlot", backref='prelim',
            cascade='all, delete, delete-orphan')

#class Meeting(Base):
#    __tablename__ = 'meetings'
#    id = Column(Integer, primary_key=True)
#    discriminator = Column('type', String(50))
#    __mapper_args__ = {'polymorphic_on': discriminator}
#
#    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
#
#    times = relationship("MeetingTimeSlot", backref='meeting',
#            cascade='all, delete, delete-orphan')
#
#class PrelimAssignment(Meeting):
#    __tablename__ = 'prelim_assignments'
#    __mapper_args__ = {'polymorphic_identity': 'prelim_assignment'}
#    id = Column(Integer, ForeignKey("meetings.id"), primary_key=True)
#
#    faculty_uniqname_1 = Column(String(8), ForeignKey("faculty.uniqname"))
#    faculty_uniqname_2 = Column(String(8), ForeignKey("faculty.uniqname"))
#    faculty_uniqname_3 = Column(String(8), ForeignKey("faculty.uniqname"))
#    student_uniqname = Column(String(8))
#
#class MeetingTimeSlot(Base):
#    __tablename__ = 'meeting_time_slots'
#    id = Column(Integer, primary_key=True)
#    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
#    datetime_slot = Column(DateTime, nullable=False)
#
#    def __repr__(self):
#        try:
#            return "<TimeSlot(id='%d', event_day_id='%d', uniqname='%s', time_slot='%s')>" % (
#                    self.id, self.event_day_id, self.uniqname, self.time_slot)
#        except TypeError:
#            if self.id == None:
#                log.debug("id field is None. Did you forget to flush?")
#            raise
