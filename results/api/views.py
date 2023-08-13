from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status
from .serializer import (SessionSerializer, SemesterSerializer,
                         CourseSerializer, CourseResultSerializer)
from .permission import IsCampusAdmin
from results.models import Session, Semester, Course, CourseResult, SemesterDocument
from . import utils
from results.utils import get_ordinal_number
from results.tabulation_generator import get_tabulation_files
 
    
class BadrequestException(APIException):
    status_code = 403
    default_detail = 'Bad Request'
    

class SessionCreate(CreateAPIView):
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    queryset = Session.objects.all()
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))


class SemesterCreate(CreateAPIView):
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        sessions = Session.objects.filter(id=pk)
        return sessions
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
            # create enrollments. this sould be removed in future version
            pk = serializer.data.get('id')
            semester = Semester.objects.get(pk=pk)
            utils.create_course_enrollments(semester)
        except Exception as e:
            raise BadrequestException(str(e))



class CourseCreate(CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    queryset = Course.objects.all()
    
    def create(self, request, *args, **kwargs):
        data = request.data
        data['added_by'] = request.user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            course_id = serializer.data.get('id')
            course = Course.objects.get(id=course_id)
            utils.add_course_to_enrollments(course=course)
            utils.create_course_results(course=course)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
    
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))


@api_view(["POST"])
def updateDropCourses(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Semester not found"}, status=status.HTTP_404_NOT_FOUND)
    if request.user.adminaccount.is_super_admin or request.user.adminaccount.dept == semester.session.dept:
        try:
            add_courses = request.data['add_courses']
            remove_courses = request.data['remove_courses']
        except Exception as e:
            return Response(data={"details": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST)
        for course_id in add_courses:
            course = get_object_or_404(Course, pk=course_id)
            if course not in semester.drop_courses.all():
                semester.drop_courses.add(course)
        for course_id in remove_courses:
            course = get_object_or_404(Course, pk=course_id)
            if course in semester.drop_courses.all():
                semester.drop_courses.remove(course)
        return Response(data={"details": "complete"})
    

class CourseResultList(ListAPIView):
    serializer_class = CourseResultSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    def get_object(self):
        # get the course object first before getting queryset
        pk = self.kwargs.get('pk')
        course = get_object_or_404(Course, pk=pk)
        self.check_object_permissions(self.request, course.semester.session)
        return course
    
    def get_queryset(self):
        course = self.get_object()
        course_results = CourseResult.objects.filter(course=course)
        return course_results


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_course_results(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != course.semester.session.dept):
            return Response(status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)
    for registration in request.data:
        course_result = get_object_or_404(CourseResult, course=course, student__registration=registration)
        for attr, value in request.data[registration].items():
            setattr(course_result, attr, value)
        try:
            course_result.save()
        except Exception as e:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    # updating stats data: credits, points and gpa for each enrolls
    course.semester.update_enrollments()
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def render_tabulation(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Semester not found"}, status=status.HTTP_404_NOT_FOUND)
    render_config = request.data['render_config']
    footer_data_raw = request.data['footer_data_raw']
    try:
        files = get_tabulation_files(semester, render_config, footer_data_raw)
    except Exception as e:
        return Response(data={'details': e}, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(semester, 'semesterdocument'):
        semesterdoc = semester.semesterdocument
    else:
        semesterdoc = SemesterDocument.objects.create(semester=semester)
    filename = f"{get_ordinal_number(semester.semester_no)} semester ({semester.session.dept.name.upper()} {semester.session.session_code})"
    # erasing before saving
    semesterdoc.tabulation_sheet.delete(save=True)
    semesterdoc.tabulation_thumbnail.delete(save=True)
    semesterdoc.tabulation_sheet.save(filename+'.pdf', ContentFile(files["pdf_file"]))
    semesterdoc.tabulation_thumbnail.save('thumbnail.png', ContentFile(files["thumbnail_file"]))
    semesterdoc.tabulation_sheet_render_by = request.user
    semesterdoc.tabulation_sheet_render_time = timezone.now()
    semesterdoc.tabulatiobn_sheet_render_config = utils.format_render_config(request)
    semesterdoc.save()
    doc_data = {
        'thumbnail': semesterdoc.tabulation_thumbnail.url,
        'tabulation_name': semesterdoc.tabulation_filename,
        'download_url': reverse('results:download_semester_tabulation', kwargs={'pk':semester.id}),
        'render_time': semesterdoc.tabulation_sheet_render_time,
        'renderer_user': semesterdoc.tabulation_sheet_render_by.adminaccount.user_full_name,
    }
    return Response(data=doc_data)
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_semester_is_running(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != semester.session.dept):
            return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    semester.is_running = not semester.is_running
    semester.save()
    return Response(data={"status": "ok"})    
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_semester(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != semester.session.dept):
            return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    # checking if it has courses
    if semester.has_courses:
        return Response(data={"details": "This semester cannot be deleted while it has courses"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    # url to be redirected after deletion
    session_url = reverse('results:view_session', kwargs={
        'dept_name': semester.session.dept.name,
        'from_year': semester.session.from_year,
        'to_year': semester.session.to_year
    })
    # delete
    semester.delete()
    return Response(data={"session_url": session_url})    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_course(request, pk):
    try:
        course = Course.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != course.semester.session.dept):
            return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    # checking if it has non empty records
    if bool(num := course.num_nonempty_records):
        return Response(
            data={"details": f"This course cannot be deleted while it has {num} non empty records"}, 
            status=status.HTTP_406_NOT_ACCEPTABLE
        )
    # url to be redirected after deletion
    semester_url = reverse('results:view_semester', kwargs={
        'dept_name': course.semester.session.dept.name,
        'from_year': course.semester.session.from_year,
        'to_year': course.semester.session.to_year,
        'year': course.semester.year,
        'semester': course.semester.year_semester,
    })
    # delete
    course.delete()
    return Response(data={"semester_url": semester_url})