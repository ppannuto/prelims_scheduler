from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    unsec_session_factory = UnencryptedCookieSessionFactoryConfig('prelims_cookie')
    config = Configurator(settings=settings, session_factory = unsec_session_factory)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login.html')
    config.add_route('logout', '/logout')
    config.add_route('conf', '/conf.html')
    config.add_route('add_prelim', '/add_prelim')
    config.add_route('delete_unscheduled_prelim', '/delete_unscheduled_prelim')
    config.add_route('new_event', '/new_event')
    config.add_route('save_new_event', '/save_new_event')
    config.add_route('delete_event', '/delete_event')
    config.add_route('calendar', '/calendar.html')
    config.add_route('update_times', '/update_times')
    config.add_route('cancel_prelim', '/cancel_prelim')
    config.add_route('schedule_prelim', '/schedule_prelim')
    config.add_route('select_prelim', '/select_prelim')
    config.scan()
    return config.make_wsgi_app()
