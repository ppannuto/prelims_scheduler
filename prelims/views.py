from pyramid.response import Response
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func

from .models import (
    DBSession,
    Faculty,
    Event,
    EventDay,
    TimeSlot,
    PrelimAssignment,
    )

import logging
log = logging.getLogger(__name__)

import datetime
import nptime
import time

def render_date_range_to_weeks(start_date, end_date, start_time, end_time,
        interval_in_minutes, show_weekends=False, event=None,
        hide_blackouts=False, uniqname=None):
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

        if hide_blackouts:
            def day_query(date):
                try:
                    return DBSession.query(EventDay).filter_by(event_id=event.id, date=date).one()
                except NoResultFound:
                    return None
            wmd = day_query(wm)
            wtd = day_query(wt)
            wwd = day_query(ww)
            wrd = day_query(wr)
            wfd = day_query(wf)

        t = start_time
        entries = ''
        while (t < end_time):
            m_cls = 'time_slot'
            t_cls = 'time_slot'
            w_cls = 'time_slot'
            r_cls = 'time_slot'
            f_cls = 'time_slot'

            if hide_blackouts:
                def blackout_query(day):
                    if day == None:
                        return True
                    try:
                        DBSession.query(TimeSlot).filter_by(
                                event_day_id=day.id, uniqname=None, time_slot=t).one()
                        return True
                    except NoResultFound:
                        return False

                m_cls = 'disable_time_slot' if blackout_query(wmd) else m_cls
                t_cls = 'disable_time_slot' if blackout_query(wtd) else t_cls
                w_cls = 'disable_time_slot' if blackout_query(wwd) else w_cls
                r_cls = 'disable_time_slot' if blackout_query(wrd) else r_cls
                f_cls = 'disable_time_slot' if blackout_query(wfd) else f_cls

                if uniqname != None:
                    def busy_query(day):
                        if blackout_query(day):
                            return False
                        try:
                            DBSession.query(TimeSlot).filter_by(
                                    event_day_id=day.id, uniqname=uniqname, time_slot=t).one()
                            return True
                        except NoResultFound:
                            return False

                    m_cls += ' busy_time_slot' if busy_query(wmd) else ''
                    t_cls += ' busy_time_slot' if busy_query(wtd) else ''
                    w_cls += ' busy_time_slot' if busy_query(wwd) else ''
                    r_cls += ' busy_time_slot' if busy_query(wrd) else ''
                    f_cls += ' busy_time_slot' if busy_query(wfd) else ''

                    def lock_query(day):
                        if blackout_query(day):
                            return False
                        try:
                            DBSession.query(TimeSlot).filter_by(
                                    event_day_id=day.id, uniqname=uniqname, time_slot=t).\
                                            filter(TimeSlot.prelim_id != None).one()
                            return True
                        except NoResultFound:
                            return False

                    m_cls += ' lock_time_slot' if lock_query(wmd) else ''
                    t_cls += ' lock_time_slot' if lock_query(wtd) else ''
                    w_cls += ' lock_time_slot' if lock_query(wwd) else ''
                    r_cls += ' lock_time_slot' if lock_query(wrd) else ''
                    f_cls += ' lock_time_slot' if lock_query(wfd) else ''

            if event is not None:
                pass
                ts_id_m = 'ts_{0}_{1}'.format(event.id, wm.strftime('%Y-%m-%d'))
                ts_id_t = 'ts_{0}_{1}'.format(event.id, wt.strftime('%Y-%m-%d'))
                ts_id_w = 'ts_{0}_{1}'.format(event.id, ww.strftime('%Y-%m-%d'))
                ts_id_r = 'ts_{0}_{1}'.format(event.id, wr.strftime('%Y-%m-%d'))
                ts_id_f = 'ts_{0}_{1}'.format(event.id, wf.strftime('%Y-%m-%d'))
            else:
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
                'm_cls': 'disable_time_slot' if (start > wm) or (end < wm) else m_cls,
                't_cls': 'disable_time_slot' if (start > wt) or (end < wt) else t_cls,
                'w_cls': 'disable_time_slot' if (start > ww) or (end < ww) else w_cls,
                'r_cls': 'disable_time_slot' if (start > wr) or (end < wr) else r_cls,
                'f_cls': 'disable_time_slot' if (start > wf) or (end < wf) else f_cls,
                })#, request=request)
            t += datetime.timedelta(minutes=interval_in_minutes)

        week_html += render('templates/week.pt', {
            'week_str': 'Week of {0} to {1}'.format(
                w.strftime('%b %e'),
                (w + datetime.timedelta(days=5)).strftime('%b %e')),
            'entries': entries,
            'w': week_idx,
            })#, request = request)

        w += datetime.timedelta(days=7)
        week_idx += 1

    #log.debug('Full week html: >>>{0}<<<'.format(week_html))
    return week_html

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
    print("Invaliding session")
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
        query = DBSession.query(
                func.min(EventDay.date).label("start"),
                func.max(EventDay.date).label("end"),
                ).filter_by(event_id=event.id)
        res = query.one()
        cal = render_date_range_to_weeks(
                res.start.strftime('%Y-%m-%d'),
                res.end.strftime('%Y-%m-%d'),
                "0800",
                "1700",
                event.time_slot_size,
                event=event,
                hide_blackouts=True,
                )

        busy_js = ''
        can_schedule = []
        no_results = []
        for faculty in DBSession.query(Faculty).order_by(Faculty.uniqname):
            try:
                busy = DBSession.query(TimeSlot).join(EventDay).join(Event).\
                        filter(Event.id==event.id).\
                        filter(TimeSlot.uniqname==faculty.uniqname).all()
                if len(busy) == 0:
                    raise NoResultFound
                for t in busy:
                    busy_js += '$("#ts_{0}_{1}_{2}").addClass("fac_busy_{3}");\n'.format(
                            event.id,
                            t.event_day.date.strftime('%Y-%m-%d'),
                            t.time_slot.strftime('%H-%M'),
                            faculty.uniqname,
                            )
                    #busy_js += 'console.log("#ts_{0}_{1}_{2} addClass(busy_{3})");\n'.format(
                    #        event.id,
                    #        t.event_day.date.strftime('%Y-%m-%d'),
                    #        t.time_slot.strftime('%H-%M'),
                    #        faculty.uniqname,
                    #        )
                can_schedule.append(faculty.uniqname)
            except NoResultFound:
                no_results.append(faculty.uniqname)

        q = DBSession.query(PrelimAssignment).order_by(PrelimAssignment.student_uniqname)
        prelims_html = render_prelims(DBSession, event, q)

        events_html += render('templates/conf_event.pt', {
            'event': event,
            'start': res.start,
            'end': res.end,
            'event_cal': cal,
            'prelims': prelims_html,
            'can_schedule': can_schedule,
            'no_results': no_results,
            }, request = request)
        extra_js += busy_js

    return {'events':events_html, 'extra_js':extra_js}

@view_config(route_name='new_event', renderer='templates/new_event.pt')
def new_event(request):
    try:
        log.debug(request.POST.mixed())
        hidden_inputs = ''
        for n in ('new_event_name', 'new_time_slot_size', 'new_start', 'new_end', 'new_weekends'):
            log.debug('\t{0}: {1}'.format(n, request.POST[n]))
            hidden_inputs += '<input type="hidden" name="{0}" value="{1}">'.format(
                    n, request.POST[n])
        weeks = render_date_range_to_weeks(
                request.POST['new_start'],
                request.POST['new_end'],
                "0800",
                "1700",
                int(request.POST['new_time_slot_size']),
                )
        return {
                'name': request.POST['new_event_name'],
                'weeks': weeks,
                'hidden_inputs': hidden_inputs,
                }
    except:
        # Something went wrong with form parameters, return to conf page
        # TODO: Send the user some kind of message?
        raise
        return HTTPFound(location='/conf.html')

@view_config(route_name='save_new_event', request_method='POST')
def save_event(request):
    try:
        log.debug(request.POST.mixed())
        event = Event(
                name=request.POST['new_event_name'],
                time_slot_size=int(request.POST['new_time_slot_size']),
                active=True,
                )
        DBSession.add(event)
        DBSession.flush()
        log.debug("Created event: {0}".format(event))

        start = datetime.date(*map(int, request.POST['new_start'].split('-')))
        end   = datetime.date(*map(int, request.POST['new_end'  ].split('-')))
        day_ids = {}

        while start <= end:
            event_day = EventDay(event_id=event.id, date=start)
            DBSession.add(event_day)
            DBSession.flush()
            day_ids[start] = event_day.id
            log.debug("Created event day: {0}".format(event_day))
            start += datetime.timedelta(days=1)

        # Add entries for blacked out times
        for blackout in request.POST['blackouts'].split():
            ts, date, time = blackout.split('_')
            date = datetime.date(*map(int, date.split('-')))
            time = datetime.time(*map(int, time.split('-')))
            time_slot = TimeSlot(event_day_id=day_ids[date], time_slot=time)
            DBSession.add(time_slot)
            DBSession.flush()
            log.debug("Created blackout time slot: {0}".format(time_slot))
    except:
        DBSession.rollback()
        log.debug("Rolled back DB")
        raise

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
        query = DBSession.query(
                func.min(EventDay.date).label("start"),
                func.max(EventDay.date).label("end"),
                ).filter_by(event_id=event.id)
        res = query.one()
        cal = render_date_range_to_weeks(
                res.start.strftime('%Y-%m-%d'),
                res.end.strftime('%Y-%m-%d'),
                "0800",
                "1700",
                event.time_slot_size,
                event=event,
                hide_blackouts=True,
                uniqname=uniqname,
                )

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

            try:
                event_day_id = day_ids[date]
            except KeyError:
                day_ids[date] = DBSession.query(EventDay).\
                        filter_by(event_id=event_id).\
                        filter_by(date=date).one().id

            time_slot = TimeSlot(
                    event_day_id=day_ids[date],
                    uniqname=request.session['uniqname'],
                    time_slot=time,
                    )
            DBSession.add(time_slot)
            DBSession.flush()
            log.debug("Created busy time slot: {0}".format(time_slot))

        for new_free in request.POST['free_times'].split():
            ts, event_id, date, time = new_free.split('_')
            date = datetime.date(*map(int, date.split('-')))
            time = datetime.time(*map(int, time.split('-')))

            log.debug('ts {0} event_id {1} date {2} time {3}'.format(
                ts, event_id, date, time))

            ts = DBSession.query(TimeSlot).join(EventDay).join(Event).\
                    filter(Event.id==event_id).\
                    filter(EventDay.date==date).\
                    filter(TimeSlot.time_slot==time).\
                    filter(TimeSlot.uniqname==request.session['uniqname']).one()
            log.debug("ts: {0}".format(ts))

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

@view_config(route_name='schedule_prelim', renderer='templates/schedule_prelim.pt')
def schedule_prelim(request):
    try:
        log.debug(request.POST.mixed())
        event = DBSession.query(Event).filter_by(id=request.POST['event_id']).one()
        faculty = request.POST['fac_cb']

        # Have:
        #  'event':   A reference to this event (prelims) in the database
        #  'faculty': An array of faculty uniqnames to come up with candidate
        #             schedules for

        raise NotImplementedError("Scheduler Integration")

    except:
        DBSession.rollback()
        log.debug("Rolled back DB")
        raise

    return {'event': event}

@view_config(route_name='select_prelim', request_method='POST')
def select_prelim(request):
    try:
        log.debug(request.POST.mixed())
        # Need:
        #  'date':    A datetime.date object with the day chosen
        #  'times':   An array of datetime.time (or nptime.nptime) objects that
        #             represent the time slots taken by this event (e.g. this will
        #             be a two-element array for a 1-hour meeting and 30-minute
        #             timesteps).
        #  'faculty': An array of uniqnames for each faculty being assigned
        #  'student': The uniqname of the student being scheduled

        event_day = DBSession.query(EventDay).filter_by(event_id=event.id, date=date)

        prelim = PrelimAssignment(event_id=event.id, student_uniqname=student)
        DBSession.add(prelim)

        for fac in faculty:
            for t in times:
                ts = TimeSlot(
                        event_day_id=event_day.id,
                        time_slot=t,
                        uniqname=fac,
                        prelim_id=prelim.id,
                        )
                DBSession.add(ts)
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

