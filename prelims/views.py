from pyramid.response import Response
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from sqlalchemy.exc import (
    DBAPIError,
    IntegrityError,
    )
from sqlalchemy.orm.exc import (
    NoResultFound,
    )
from sqlalchemy.sql import func

from .models import (
    DBSession,
    Faculty,
    Event,
    TimeSlot,
    PrelimAssignment,
    )

import logging
log = logging.getLogger(__name__)

import datetime
import nptime
import time

def render_date_range_to_weeks(start_date, end_date, start_time, end_time,
        interval_in_minutes, show_weekends=False):
    """Helper function that converts a date range to a series of HTML tables"""
    start = datetime.date(*map(int, start_date.split('-')))
    end   = datetime.date(*map(int,   end_date.split('-')))

    if show_weekends:
        raise NotImplementedError("Weekend support")
    else:
        if start.weekday() not in range(0,5):
            raise ValueError("Start date must be a weekday")
        if end.weekday() not in range(0,5):
            raise ValueError("End date must be a weekday")

    start_mon = start - datetime.timedelta(days=start.weekday())
    end_fri   = end   + datetime.timedelta(days=4-end.weekday())
    log.debug('start     {0} end     {1}'.format(start, end))
    log.debug('start_mon {0} end_fri {1}'.format(start_mon, end_fri))

    start_time = nptime.nptime(*map(int, (start_time[:2], start_time[2:])))
    end_time   = nptime.nptime(*map(int, (  end_time[:2],   end_time[2:])))

    week_idx = 0
    week_html = ''
    w = start_mon

    while (end_fri - w).days > 0:
        log.debug('rendering week {0}'.format(week_idx))

        wm = w
        wt = w + datetime.timedelta(days=1)
        ww = w + datetime.timedelta(days=2)
        wr = w + datetime.timedelta(days=3)
        wf = w + datetime.timedelta(days=4)

        t = start_time
        entries = ''
        while (t < end_time):
            m_cls = 'time_slot'
            t_cls = 'time_slot'
            w_cls = 'time_slot'
            r_cls = 'time_slot'
            f_cls = 'time_slot'

            ts_id_m = 'ts_{0}'.format(wm.strftime('%Y-%m-%d'))
            ts_id_t = 'ts_{0}'.format(wt.strftime('%Y-%m-%d'))
            ts_id_w = 'ts_{0}'.format(ww.strftime('%Y-%m-%d'))
            ts_id_r = 'ts_{0}'.format(wr.strftime('%Y-%m-%d'))
            ts_id_f = 'ts_{0}'.format(wf.strftime('%Y-%m-%d'))

            entries += render('templates/week_entry.pt', {
                'ts_id_m': ts_id_m,
                'ts_id_t': ts_id_t,
                'ts_id_w': ts_id_w,
                'ts_id_r': ts_id_r,
                'ts_id_f': ts_id_f,
                'time': t.strftime('%H-%M'),
                'disp_time': t.strftime('%l:%M %p'),
                'm_cls': 'disable_time_slot' if (start > wm) or (end < wm) else 'time_slot',
                't_cls': 'disable_time_slot' if (start > wt) or (end < wt) else 'time_slot',
                'w_cls': 'disable_time_slot' if (start > ww) or (end < ww) else 'time_slot',
                'r_cls': 'disable_time_slot' if (start > wr) or (end < wr) else 'time_slot',
                'f_cls': 'disable_time_slot' if (start > wf) or (end < wf) else 'time_slot',
                })
            t += datetime.timedelta(minutes=interval_in_minutes)

        week_html += render('templates/week.pt', {
            'week_str': 'Week of {0} to {1}'.format(
                w.strftime('%b %e'),
                (w + datetime.timedelta(days=5)).strftime('%b %e')),
            'entries': entries,
            'w': week_idx,
            })

        w += datetime.timedelta(days=7)
        week_idx += 1

    #log.debug('Full week html: >>>{0}<<<'.format(week_html))
    return week_html

def render_event(event, uniqname=None, blackout_as_busy=False):
    """Helper function that builds an HTML table for an event"""

    start_time = nptime.nptime.from_time(event.start_time)
    end_time = nptime.nptime.from_time(event.end_time)

    weeks_html = ''
    monday = event.start_date - datetime.timedelta(days=event.start_date.weekday())
    while monday < event.end_date:
        friday = monday + datetime.timedelta(days=5)
        week_str = 'Week of {0} to {1}'.format(
                monday.strftime('%b %e'), friday.strftime('%b %e'))

        week_html = ''
        day_time = start_time
        while day_time < end_time:
            row_html = ''
            for day in xrange(5):
                cls = 'time_slot'
                t = datetime.datetime.combine(monday+datetime.timedelta(days=day), day_time)

                if t.date() < event.start_date or t.date() > event.end_date:
                    cls += ' disable_time_slot'
                else:
                    if uniqname != None:
                        exists = DBSession.query(TimeSlot).\
                                filter_by(event_id=event.id).\
                                filter_by(uniqname=uniqname).\
                                filter_by(prelim_id=None).\
                                filter_by(time_slot=t)
                        try:
                            exists.one()
                            cls += ' busy_time_slot'
                        except NoResultFound:
                            pass

                    exists = DBSession.query(TimeSlot).\
                            filter_by(event_id=event.id).\
                            filter_by(uniqname=None).\
                            filter_by(prelim_id=None).\
                            filter_by(time_slot=t)
                    try:
                        exists.one()
                    except NoResultFound:
                        if blackout_as_busy:
                            cls += ' busy_time_slot'
                        else:
                            cls += ' disable_time_slot'

                row_html += render('templates/day_entry.pt', {
                    'ts_id' : 'ts_{0}_{1}'.format(event.id, (monday+datetime.timedelta(days=day)).strftime('%Y-%m-%d')),
                    'time': day_time.strftime('%H-%M'),
                    'disp_time': day_time.strftime('%l:%M %p'),
                    'cls': cls,
                    })

            week_html += render('templates/week_entry2.pt', {'week': row_html})
            day_time += datetime.timedelta(minutes=event.time_slot_size)

        weeks_html += render('templates/week.pt', {
            'week_str': week_str,
            'entries': week_html,
            'w': monday.isocalendar()[1],
            })
        monday += datetime.timedelta(days=7)

    return weeks_html

@view_config(route_name='login', renderer='templates/login.pt')
def login_view(request):
    try:
        uniqname = request.GET['uniqname']
        if uniqname == 'dawnf':
            return HTTPFound(location='/conf.html')
        DBSession.query(Faculty).filter_by(uniqname=uniqname).one()
        request.session['uniqname'] = uniqname
        return HTTPFound(location='/calendar.html')
    except KeyError:
        return {'why_failed': 'uniqname is required'}
    except NoResultFound:
        return {'why_failed': 'That uniqname is not a faculty uniqname'}
    return {'why_failed': ''}

@view_config(route_name='logout', request_method='POST')
def logout_view(request):
    request.session.invalidate()
    return HTTPFound(location='/')

def render_prelims(DBSession, event, query):
    prelims_html = ''
    for prelim in query.all():
        faculty = DBSession.query(TimeSlot.uniqname).filter_by(prelim_id=prelim.id).distinct()
        times = DBSession.query(TimeSlot.time_slot).filter_by(prelim_id=prelim.id).distinct()
        start = min(times)
        finish = nptime.nptime().from_time(max(times)) + datetime.timedelta(minutes=event.time_slot_size)

        prelims_html += render('templates/prelim_event.pt', {
            'event': event,
            'prelim': prelim,
            'student': student,
            'faculty': faculty,
            'start': start,
            'finish': finish,
            }, request = request)
    return prelims_html


@view_config(route_name='conf', renderer='templates/conf.pt')
def conf_view(request):
    events_html = ''
    extra_js = ''
    for event in DBSession.query(Event).order_by(Event.id):
        #Saved for syntax reference, query isn't needed
        #query = DBSession.query(
        #        func.min(TimeSlot.time_slot).label("start"),
        #        func.max(TimeSlot.time_slot).label("end"),
        #        ).filter_by(event_id=event.id)
        #res = query.one()
        cal = render_event(event)

        busy_js = ''
        can_schedule = []
        no_results = []
        for faculty in DBSession.query(Faculty).order_by(Faculty.uniqname):
            try:
                busy = DBSession.query(TimeSlot).join(Event).\
                        filter(Event.id==event.id).\
                        filter(TimeSlot.uniqname==faculty.uniqname).all()
                if len(busy) == 0:
                    raise NoResultFound
                for t in busy:
                    busy_js += '$("#ts_{0}_{1}_{2}").addClass("fac_busy_{3}");\n'.format(
                            event.id,
                            t.time_slot.strftime('%Y-%m-%d'),
                            t.time_slot.strftime('%H-%M'),
                            faculty.uniqname,
                            )
                can_schedule.append(faculty.uniqname)
            except NoResultFound:
                no_results.append(faculty.uniqname)

        q = DBSession.query(PrelimAssignment).\
                filter(PrelimAssignment.times!=None).\
                order_by(PrelimAssignment.student_uniqname)
        prelims_html = render_prelims(DBSession, event, q)

        unscheduled = DBSession.query(PrelimAssignment).\
                filter(PrelimAssignment.times==None).\
                order_by(PrelimAssignment.student_uniqname)
        unscheduled_html = ''
        for prelim in unscheduled.all():
            f = []
            f.append(DBSession.query(Faculty).filter_by(id=prelim.faculty1).one().uniqname)
            f.append(DBSession.query(Faculty).filter_by(id=prelim.faculty2).one().uniqname)
            f.append(DBSession.query(Faculty).filter_by(id=prelim.faculty3).one().uniqname)
            f.sort()
            unscheduled_html += render('templates/unscheduled_prelim.pt', {
            'event': event,
            'prelim': prelim,
            'deleteable': True,
            'student': prelim.student_uniqname,
            'fac': f,
            }, request = request)


        events_html += render('templates/conf_event.pt', {
            'event': event,
            'start': event.start_date,
            'end': event.end_date,
            'event_cal': cal,
            'prelims': prelims_html,
            'unscheduled': unscheduled_html,
            'can_schedule': can_schedule,
            'no_results': no_results,
            }, request = request)
        extra_js += busy_js

    return {'events':events_html, 'extra_js':extra_js}

@view_config(route_name='add_prelim', request_method='POST', renderer='json')
def add_prelim(request):
    try:
        log.debug(request.POST.mixed())
        event = DBSession.query(Event).filter_by(id=request.POST['event_id']).one()

        f1 = DBSession.query(Faculty).filter_by(uniqname=request.POST['faculty1']).one()
        f2 = DBSession.query(Faculty).filter_by(uniqname=request.POST['faculty2']).one()
        f3 = DBSession.query(Faculty).filter_by(uniqname=request.POST['faculty3']).one()
        log.debug('queried all faculty successfully')

        prelim = PrelimAssignment(
                event_id=event.id,
                student_uniqname=request.POST['student'],
                faculty1=f1.id,
                faculty2=f2.id,
                faculty3=f3.id,
                )
        DBSession.add(prelim)
        log.debug('added prelim successfully')

        # Must flush so that the prelim has an id
        DBSession.flush()

        prelim_html = render('templates/unscheduled_prelim.pt', {
            'event': event,
            'prelim': prelim,
            'deleteable': True,
            'student': prelim.student_uniqname,
            'fac': (f1.uniqname, f2.uniqname, f3.uniqname),
            }, request = request)
        log.debug('rendered new prelim html')

        return {'success': True, 'event_id': event.id,
                'student': prelim.student_uniqname, 'html': prelim_html}

    except KeyError:
        DBSession.rollback()
        return {'success': False, 'event_id': event.id,
                'msg': 'Missing a key. (Must input a student name and all three faculty)'}

    except IntegrityError as e:
        DBSession.rollback()
        return {'success': False, 'event_id': event.id,
                'msg': "Something's duplicated. You can only schedule one prelim"
                " per student and must have three distinct faculty for each"
                " student."}

    except:
        DBSession.rollback()
        return {'success': False, 'event_id': event.id,
                'msg': 'Could not add this prelim. Unknown error?'}

@view_config(route_name='delete_unscheduled_prelim', request_method='POST', renderer='json')
def delete_unscheduled_prelim(request):
    log.debug(request.POST.mixed())
    prelim = DBSession.query(PrelimAssignment).filter_by(id=request.POST['prelim_id']).one()
    resp = {'event_id': prelim.event_id, 'student': prelim.student_uniqname}
    DBSession.delete(prelim)
    return resp

@view_config(route_name='new_event', renderer='templates/new_event.pt')
def new_event(request):
    try:
        log.debug(request.POST.mixed())
        hidden_inputs = ''
        for n in (
                'new_event_name',
                'new_time_slot_size',
                'new_start_date',
                'new_end_date',
                'new_start_time',
                'new_end_time',
                'new_weekends'
                ):
            log.debug('\t{0}: {1}'.format(n, request.POST[n]))
            hidden_inputs += '<input type="hidden" name="{0}" value="{1}">'.format(
                    n, request.POST[n])
        weeks = render_date_range_to_weeks(
                request.POST['new_start_date'],
                request.POST['new_end_date'],
                request.POST['new_start_time'],
                request.POST['new_end_time'],
                int(request.POST['new_time_slot_size']),
                )
        return {
                'mode': 'save',
                'name': request.POST['new_event_name'],
                'weeks': weeks,
                'hidden_inputs': hidden_inputs,
                }
    except:
        # Something went wrong with form parameters, return to conf page
        # TODO: Send the user some kind of message?
        raise
        return HTTPFound(location='/conf.html')

@view_config(route_name='save_event', request_method='POST')
def save_event(request):
    try:
        log.debug(request.POST.mixed())

        syear, smonth, sday = map(int, request.POST['new_start_date'].split('-'))
        eyear, emonth, eday = map(int, request.POST['new_end_date'  ].split('-'))
        shour = int(request.POST['new_start_time'][:2])
        smin  = int(request.POST['new_start_time'][2:])
        ehour = int(request.POST['new_end_time'][:2])
        emin  = int(request.POST['new_end_time'][2:])

        event = Event(
                name=request.POST['new_event_name'],
                time_slot_size=int(request.POST['new_time_slot_size']),
                active=True,
                start_date=datetime.date(syear, smonth, sday),
                end_date=datetime.date(eyear, emonth, eday),
                start_time=datetime.time(shour, smin),
                end_time=datetime.time(ehour, emin),
                )
        DBSession.add(event)
        DBSession.flush()
        log.debug("Created event: {0}".format(event))

        blackouts = set()
        for blackout in request.POST['blackouts'].split():
            ts, date, time = blackout.split('_')
            y, m, d = map(int, date.split('-'))
            h, M = map(int, time.split('-'))
            blackouts.add(datetime.datetime(y, m, d, h, M))

        # Add timeslots for this event
        stime = datetime.datetime(syear, smonth, sday, shour, smin)
        etime = datetime.datetime(eyear, emonth, eday, ehour, emin)
        while stime < etime:
            if stime not in blackouts:
                time_slot = TimeSlot(event_id=event.id, time_slot=stime)
                DBSession.add(time_slot)

            # n.b. if custom time ranges are allowed, this should be modified to
            # avoid wraparound end -> start over long time_slot_size's
            stime += datetime.timedelta(minutes=event.time_slot_size)
            if stime.time() >= datetime.time(ehour, emin):
                stime += nptime.nptime(ehour, emin) - nptime.nptime(shour, smin)
    except:
        DBSession.rollback()
        log.debug("Rolled back DB")
        raise

    return HTTPFound(location='/conf.html')

@view_config(route_name='edit_event', renderer='templates/new_event.pt', request_method='POST')
def edit_event(request):
    log.debug(request.POST.mixed())
    event = DBSession.query(Event).filter_by(id=request.POST['event_id']).one()

    cal = render_event(event, blackout_as_busy=True)

    return {
            'mode': 'update',
            'name': event.name,
            'weeks': cal,
            'hidden_inputs': '<input type="hidden" name="event_id" value="{0}">'.format(event.id)
            }

@view_config(route_name='update_event', request_method='POST')
def update_event(request):
    log.debug(request.POST.mixed())
    event = DBSession.query(Event).filter_by(id=request.POST['event_id']).one()

    blackouts = set()
    for blackout in request.POST['blackouts'].split():
        ts, ev_id, date, time = blackout.split('_')
        y, m, d = map(int, date.split('-'))
        h, M = map(int, time.split('-'))
        blackouts.add(datetime.datetime(y, m, d, h, M))

    stime = datetime.datetime.combine(event.start_date, event.start_time)
    etime = datetime.datetime.combine(event.end_date, event.end_time)
    while stime < etime:
        if stime not in blackouts:
            try:
                DBSession.query(TimeSlot).\
                        filter_by(event_id=event.id).\
                        filter_by(time_slot=stime).\
                        filter_by(uniqname=None).\
                        filter_by(prelim_id=None).one()
            except NoResultFound:
                time_slot = TimeSlot(event_id=event.id, time_slot=stime)
                DBSession.add(time_slot)
        else:
            try:
                DBSession.query(TimeSlot).\
                        filter_by(event_id=event.id).\
                        filter_by(time_slot=stime).\
                        filter(TimeSlot.uniqname!=None).\
                        filter_by(prelim_id=None).delete()
                prelims = DBSession.query(TimeSlot).\
                        filter_by(event_id=event.id).\
                        filter_by(time_slot=stime).\
                        filter_by(uniqname=None).\
                        filter(TimeSlot.prelim_id!=None).all()
                for prelim in prelims:
                    DBSession.query(TimeSlot).\
                            filter_by(event_id=event.id).\
                            filter_by(time_slot=stime).\
                            filter_by(prelim_id=prelim.id).delete()
                DBSession.query(TimeSlot).\
                        filter_by(event_id=event.id).\
                        filter_by(time_slot=stime).\
                        filter_by(uniqname=None).\
                        filter_by(prelim_id=None).delete()
            except NoResultFound:
                pass

        # n.b. if custom time ranges are allowed, this should be modified to
        # avoid wraparound end -> start over long time_slot_size's
        stime += datetime.timedelta(minutes=event.time_slot_size)
        if stime.time() >= event.end_time:
            stime += nptime.nptime().from_time(event.end_time) - nptime.nptime().from_time(event.start_time)

    return HTTPFound(location='/conf.html')


@view_config(route_name='delete_event', request_method='POST')
def delete_event(request):
    try:
        log.debug(request.POST.mixed())

        event = DBSession.query(Event).filter_by(id=request.POST['event_id']).one()
        # The cascading delete relationship should remove everything
        DBSession.delete(event)

    except:
        DBSession.rollback()
        raise

    return HTTPFound(location='/conf.html')

@view_config(route_name='calendar', renderer='templates/calendar.pt')
def calendar_view(request):
    try:
        uniqname = request.session['uniqname']
    except KeyError:
        return HTTPFound(location='/login.html')
    events_html = ''
    for event in DBSession.query(Event).order_by(Event.id).filter_by(active=True):
        cal = render_event(event, uniqname=uniqname)

        q = DBSession.query(PrelimAssignment).join(TimeSlot).\
                filter(TimeSlot.uniqname==uniqname)
        prelims_html = render_prelims(DBSession, event, q)

        events_html += render('templates/cal_event.pt', {
            'event': event,
            'event_cal': cal,
            'prelims': prelims_html,
            }, request = request)
    return {'events': events_html}

@view_config(route_name="update_times", request_method='POST')
def update_times(request):
    try:
        log.debug(request.POST.mixed())

        # Add entries for blacked out times
        day_ids = {}

        for new_busy in request.POST['busy_times'].split():
            ts, event_id, date, time = new_busy.split('_')
            date = datetime.date(*map(int, date.split('-')))
            time = datetime.time(*map(int, time.split('-')))
            ts = datetime.datetime.combine(date, time)

            time_slot = TimeSlot(
                    event_id=event_id,
                    uniqname=request.session['uniqname'],
                    time_slot=ts,
                    )
            DBSession.add(time_slot)

        for new_free in request.POST['free_times'].split():
            ts, event_id, date, time = new_free.split('_')
            date = datetime.date(*map(int, date.split('-')))
            time = datetime.time(*map(int, time.split('-')))
            ts = datetime.datetime.combine(date, time)

            ts = DBSession.query(TimeSlot).join(Event).\
                    filter(Event.id==event_id).\
                    filter(TimeSlot.uniqname==request.session['uniqname']).\
                    filter(TimeSlot.time_slot==ts).\
                    one()

            if ts.prelim_id != None:
                # Someone got cute and circumvented to JS to try to delete a
                # scheduled meeting, reject that
                raise ValueError("Attempt to delete scheduled meeting")
            DBSession.delete(ts)
    except:
        DBSession.rollback()
        log.debug("Rolled back DB")
        raise

    return HTTPFound(location='/calendar.html')

@view_config(route_name='cancel_prelim', request_method='POST')
def cancel_prelim(request):
    try:
        log.debug(request.POST.mixed())
        event = DBSession.query(Event).filter_by(id=request.POST['event_id']).one()
        prelim = DBSession.query(PrelimAssignment).filter_by(id=request.POST['prelim_id']).one()
        DBSession.delete(prelim)

    except:
        DBSession.rollback()
        log.debug("Rolled back DB")
        raise

    return HTTPFound(location='/conf.html')

@view_config(route_name='schedule_unscheduled', request_method='POST')
def schedule_prelim(request):
    try:
        log.debug(request.POST.mixed())
        event = DBSession.query(Event).filter_by(id=request.POST['event_id']).one()
        # 'event':       A reference to this event (prelims) in the database

        unscheduled = DBSession.query(PrelimAssignment).\
                filter(PrelimAssignment.times==None).\
                order_by(PrelimAssignment.student_uniqname).all()
        # 'unscheduled': An array of prelims that need to be scheduled.

        # 'prelim':      Each element of unscheduled is an instance of Prelim
        #                as defined by models.py

        # To convert a faculty_id to a uniqname:
        FACULTY_ID = unscheduled[0].faculty1
        FACULTY_UNIQNAME = DBSession.query(Faculty.uniqname).\
                filter_by(id=FACULTY_ID).\
                scalar()

        # To query for all busy times for a given faculty member:
        busy_times = DBSession.query(TimeSlot).\
                filter_by(event_id=event.id).\
                filter_by(uniqname=FACULTY_UNIQNAME)

        # busy_times is an array of TimeSlot objects as defined in models.py
        #
        #  if busy_times[N].prelim_id == None:
        #    The faculty member listed this time as busy
        #  else:
        #    The faculty member is scheduled for a prelim at this time already


        # Dawn is allowed to "black out" some times as invalid for any prelims
        # To query for all valid times to schedule
        valid_times = DBSession.query(TimeSlot).\
                filter_by(event_id=event.id).\
                filter_by(uniqname=None).\
                filter_by(prelim_id=None).\
                all()

        def add_scheduled_prelim_to_db(times, prelim_id):
            # 'times':     An array of datetime.datetime objects that represent the
            #              time slots taken by this event (e.g. this will be a two-
            #              element array for a 1-hour meeting and 30-minute timesteps)
            # 'prelim_id': The prelim being scheduled

            prelim = PrelimAssignment(event_id=event.id, student_uniqname=student)
            DBSession.add(prelim)

            for fac in faculty:
                for t in times:
                    ts = TimeSlot(
                            event_id=event.id,
                            time_slot=t,
                            uniqname=fac,
                            prelim_id=prelim.id,
                            )
                    DBSession.add(ts)

        # TODO: Integrate scheduling here

    except:
        DBSession.rollback()
        log.debug("Rolled back DB")
        raise
    return HTTPFound(location='/conf.html')

@view_config(route_name='home')
def index_to_login(request):
    return HTTPFound(location='/login.html')

#@view_config(route_name='home', renderer='templates/mytemplate.pt')
#def my_view(request):
#    try:
#        one = DBSession.query(MyModel).filter(MyModel.name == 'one').first()
#    except DBAPIError:
#        return Response(conn_err_msg, content_type='text/plain', status_int=500)
#    return {'one': one, 'project': 'prelims'}

conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_prelims_db" script
    to initialize your database tables.  Check your virtual 
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

