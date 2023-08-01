from django.urls import path
from results import views

app_name = "results"

urlpatterns = [
    path('', views.DashboardView.as_view(), name="dashboard"),
    path('departments/', views.departments_all, name="all_departments"),
    path('departments/<str:dept_name>', views.DepartmentView.as_view(), name="view_department"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>', views.SessionView.as_view(), name="view_session"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/semester/<str:year>-<int:semester>', views.SemesterView.as_view(), name="view_semester"),
    path('staffs', views.pending_view, name="stuffs_view"),
    path('activities', views.pending_view, name="activities_view"),
    path('bin', views.pending_view, name="recycle_bin_view"),
]

