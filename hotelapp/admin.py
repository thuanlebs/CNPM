from datetime import datetime
from flask import redirect, request
from flask_admin import Admin, expose, AdminIndexView, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from __init__ import app, db
from models import UserRole, RoomType, Room, AmenityType, Amenity, Policy, Service
import dao


class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


class MyRoomTypeView(AuthenticatedView):
    column_list = ['id', 'name', 'room_size', 'description', 'adults', 'children', 'price', 'rooms']
    column_searchable_list = ['id', 'name']
    column_filters = ['id', 'name', 'price']
    column_editable_list = ['name', 'price', 'room_size', 'description', 'adults', 'children']
    can_export = True


class MyRoomView(AuthenticatedView):
    column_list = ['id', 'name', 'room_type']
    column_searchable_list = ['id', 'name']
    column_filters = ['id', 'name', 'room_type']
    column_editable_list = ['name']


class MyAmenityTypeView(AuthenticatedView):
    column_list = ['id', 'name', 'amenities']
    column_searchable_list = ['id', 'name']
    column_filters = ['name']
    column_editable_list = ['name']


class MyAmenityView(AuthenticatedView):
    column_list = ['id', 'name', 'description', 'amenity_type']
    column_searchable_list = ['id', 'name']
    column_filters = ['name', 'amenity_type']
    column_editable_list = ['name', 'description']


class MyPolicyView(AuthenticatedView):
    column_list = ['id', 'name', 'details', 'creator']
    column_searchable_list = ['id', 'name']
    column_filters = ['name']
    column_editable_list = ['name', 'details']


class MyServiceView(AuthenticatedView):
    column_list = ['id', 'name', 'details', 'price', 'unit']
    column_searchable_list = ['id', 'name']
    column_filters = ['name', 'price', 'unit']
    column_editable_list = ['name', 'details', 'price', 'unit']


class MyAdminStatsView(BaseView):
    @expose('/')
    def index(self):
        stats_revenue = dao.revenue_by_month(month=request.args.get('month'),
                                             year=request.args.get('year'))
        room_utilization_stats = dao.room_utilization(month=request.args.get('month'),
                                             year=request.args.get('year'))

        return self.render('admin/stats.html', stats_revenue=stats_revenue,
                           room_utilization_stats=room_utilization_stats)

    def is_accessible(self):
        return current_user.is_authenticated


admin = Admin(app, name='Hotel Admin Center', template_mode='bootstrap4')

admin.add_view(MyRoomTypeView(RoomType, db.session))
admin.add_view(MyRoomView(Room, db.session))
admin.add_view(MyAmenityTypeView(AmenityType, db.session))
admin.add_view(MyAmenityView(Amenity, db.session))
admin.add_view(MyPolicyView(Policy, db.session))
admin.add_view(MyServiceView(Service, db.session))
admin.add_view(MyAdminStatsView(name='Stats'))

admin.add_view(LogoutView(name='Logout'))
