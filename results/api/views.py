from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
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
from results.models import Session, Semester, Course, CourseResult, SemesterDocument, SemesterEnroll
from account.models import StudentAccount
from . import utils
from results.utils import get_ordinal_number
from results.tabulation_generator import get_tabulation_files
from io import BytesIO
import openpyxl
    
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_new_entry_to_course(request, pk):
    # checking posted data
    try:
        reg_no = request.data['registration']
        semester_id = request.data['semester_id']
    except KeyError:
        return Response(data={"details":"Data is missing"}, status=status.HTTP_400_BAD_REQUEST)
    # course
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response(data={"details":"Course not found"}, status=status.HTTP_404_NOT_FOUND)
    # finding student
    try:
        student = StudentAccount.objects.get(registration=reg_no)
    except StudentAccount.DoesNotExist:
        return Response(data={"details":"Invalid Registration Number"}, status=status.HTTP_400_BAD_REQUEST)
    # finding enrollment of the specified semester
    try:
        enroll = SemesterEnroll.objects.get(semester__id=semester_id, semester__is_running=True, student=student)
    except SemesterEnroll.DoesNotExist:
        return Response(data={"details":"Student didn't enrolled for this semester, or the semester is not running"}, status=status.HTTP_400_BAD_REQUEST)
    # checking if this course is already in the enrollment
    if course in enroll.courses.all():
        return Response(data={"details":"Student already registered for this course"}, status=status.HTTP_400_BAD_REQUEST)
    # checking wheather this semester has included this course in the drop courses, then add it if not included
    if course not in enroll.semester.drop_courses.all():
        enroll.semester.drop_courses.add(course)
    # adding course to enrollment
    enroll.courses.add(course)
    # creating course result
    CourseResult.objects.create(
        student = student,
        course = course,
        is_drop_course = True
    )
    return Response(data={'status': 'Course Result for the student has been created'})

@csrf_exempt
def process_course_excel(request, pk):
    header_to_course_property_config = {
        'code_a': 'part_A_code',
        'marks_a': 'part_A_score',
        'code_b': 'part_B_code',
        'marks_b': 'part_B_score',
        'marks_tt': 'incourse_score',
        'total': 'total_score',
    }
    if request.method == "POST" and request.FILES.get('excel'):
        excel_file = request.FILES.get('excel')
        try:
            buffer = BytesIO(excel_file.read())
            wb = openpyxl.load_workbook(buffer)
            sheet = wb[wb.sheetnames[0]]
            rows = list(sheet.rows)
            header = [cell.value.lower().strip() for cell in rows[0]]
            data_rows = rows[1:]
        except Exception as e:
            return JsonResponse({'details': e}, status=400)
        
        if 'reg' not in header:
            return JsonResponse({'details': "Registration no. column 'reg' not found"}, status=400)
        
        
        
        
        
        
        
        
        
        
        
        
        return JsonResponse({'status':'Complete'})
    else:
        return JsonResponse({'details': 'Not allowed!'}, status=400)
