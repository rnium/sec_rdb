import openpyxl
from io import BytesIO
from typing import Any, Dict
from datetime import timedelta
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.views.generic import DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.generics import CreateAPIView
from . import utils
from results.api.utils import is_confirmed_user
from .models import StudentAccount, InviteToken, AdminAccount
from .serializer import StudentAccountSerializer
from results.utils import render_error
from results.models import Department, Session

    
def login_page(request):
    if request.user.is_authenticated:
            return redirect("results:dashboard")
    else:
        return render(request=request, template_name='account/login_page.html')
    
class LogoutView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return redirect("account:user_login_get")
    

class StudentProfileView(LoginRequiredMixin, DetailView):
    template_name = "account/view_student_profile.html"
    
    def get_object(self):
        student = get_object_or_404(
            StudentAccount, 
            registration = self.kwargs.get("registration", "")
        )
        return student
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['student'] = context['studentaccount'] # Alias
        context['enrollments'] = context['student'].semesterenroll_set.all().order_by('semester__semester_no')
        context['gradesheet_years'] = context['student'].gradesheet_years
        context['request'] = self.request
        return context


def signup_admin(request):
    # checking if user logged in or not
    if not isinstance(request.user, AnonymousUser):
        return render_error(request, "Logged In User Cannot Perform Signup")
    # token id
    tokenId = request.GET.get('token')
    if tokenId == None:
        return render_error(request, "Signup Requires an Invitation Token")
    try:
        token = InviteToken.objects.get(id=tokenId)
    except InviteToken.DoesNotExist:
        return render_error(request, "Invalid Token")
    # checking expiration
    timenow = timezone.now()
    if token.expiration <= timenow:
        return render_error(request, "This Invitation Has Expired", "You can request for a new one to existing admins")
    # context dict
    context = {
        "token": token
    }
    # to user dept (if specified in the invitation)
    if token.to_user_dept_id:
        try:
            print(token.to_user_dept_id)
            dept = Department.objects.get(id=token.to_user_dept_id)
        except Department.DoesNotExist:
            return render_error(request, "This Invitation Is Corrupted", "Request for a new invitation to existing admins")
        context['dept'] = dept
    return render(request, "account/staff_signup.html", context=context)


@login_required
def view_admin_profile_edit(request):
    if hasattr(request.user, 'adminaccount'):
        return render(request, 'account/admin_profile_edit.html', context={'admin':request.user.adminaccount})
    else:
        return render_error(request, "Go Back. You're not supposed to see this!")

@csrf_exempt
def set_admin_avatar(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse(data={'details': 'Unauthorized'}, status=403)
        # check if user has permission
        if not hasattr(request.user, 'adminaccount'):
            return JsonResponse(data={'details': 'Forbidden'}, status=403)
        else:
            account = request.user.adminaccount
        # Saving file
        if len(request.FILES) > 0:
            try:
                image_file = request.FILES.get('dp')
                compressed_image = utils.compress_image(image_file)
            except ValidationError as e:
                return JsonResponse(data={'details': e.message}, status=400)
            if account.profile_picture is not None:
                account.profile_picture.delete(save=True)
            try:
                account.profile_picture = compressed_image
                account.save()
            except Exception as e:
                return JsonResponse(data={'details': 'Cannot save image'}, status=400)

            return JsonResponse({'status':'profile picture set'})
        else:
            return JsonResponse(data={'details': 'No image uploaded'}, status=400)
    else:
        return JsonResponse(data={'details': 'Method not allowed'}, status=400)
 
 
@csrf_exempt
def set_student_avatar(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse(data={'details': 'Unauthorized'}, status=403)
        # get student account
        try:
            registration = request.POST.get('registration')
            account = StudentAccount.objects.get(registration=registration)
        except StudentAccount.DoesNotExist:
            return JsonResponse(data={'details': "Account not found"}, status=400)
        # check if user has permission
        if not hasattr(request.user, 'adminaccount'):
            if not (hasattr(request.user, 'studentaccount') and (request.user.studentaccount == account)):
                return JsonResponse(data={'details': 'Unauthorized'}, status=403)
        # Saving file
        if len(request.FILES) > 0:
            try:
                image_file = request.FILES.get('dp')
                compressed_image = utils.compress_image(image_file)
            except ValidationError as e:
                return JsonResponse(data={'details': e.message}, status=400)
            if account.profile_picture is not None:
                account.profile_picture.delete(save=True)
            try:
                account.profile_picture = compressed_image
                account.save()
            except Exception as e:
                return JsonResponse(data={'details': 'Cannot save image'}, status=400)

            return JsonResponse({'status':'profile picture set'})
        else:
            return JsonResponse(data={'details': 'No image uploaded'}, status=400)
    else:
        return JsonResponse(data={'details': 'Method not allowed'}, status=400)


@csrf_exempt
def create_student_via_excel(request, pk):
    try:
        session = Session.objects.get(pk=pk)
    except Session.DoesNotExist:
        return JsonResponse({'details': "Course not found"}, status=404)
    
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
            return JsonResponse({'details': 'Can\'t open excel file'}, status=400)
            
        try:
            reg_col_idx = header.index('reg')
            first_name_col_idx = header.index('first_name')
        except ValueError:
            return JsonResponse({'details': "Some required columns not found"}, status=400)
        logs = {
            'success': 0,
            'errors': {
                'parse_errors': [],
                'save_errors': []
            }
        }
        # data saving
        try:
            last_name_col_idx = header.index('last_name')
        except ValueError:
            last_name_col_idx = None
        for r in range(len(data_rows)):
            try:
                registration = int(data_rows[r][reg_col_idx].value)
            except Exception as e:
                logs['errors']['parse_errors'].append(f'row: {r+2}. Errors: [cannot parse registration no.]')
                continue
            first_name = data_rows[r][first_name_col_idx].value
            if first_name is None:
                logs['errors']['parse_errors'].append(f'registration: {registration}. Errors: [first name cannot be empty]')
                continue
            account_kwargs = {
                'registration': registration,
                'session': session,
                'first_name': first_name.strip()
            }
            if last_name_col_idx is not None:
                last_name = data_rows[r][last_name_col_idx].value
                if last_name is not None and len(last_name) > 0:
                    account_kwargs['last_name'] = last_name.strip()
            try:
                StudentAccount.objects.create(**account_kwargs)
            except Exception as e:
                logs['errors']['save_errors'].append(f'Registration: {registration}. Errors: {e}')
                continue
            logs['success'] += 1
        
        logs['has_parse_errors'] = bool(len(logs['errors']['parse_errors']))    
        logs['has_save_errors'] = bool(len(logs['errors']['save_errors']))
        
        summary = render_to_string('results/components/excel_summary_list.html', context={'logs': logs})
        return JsonResponse({'status':'Complete', 'summary':summary})
    else:
        return JsonResponse({'details': 'Not allowed!'}, status=400)

    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_student(request, registration):
    try:
        student = StudentAccount.objects.get(registration=registration)
    except StudentAccount.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != student.session.dept):
            return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    # url to be redirected after deletion
    session_url = reverse('results:view_session', kwargs={
        'dept_name': student.session.dept.name,
        'from_year': student.session.from_year,
        'to_year': student.session.to_year
    })
    # delete
    if student.user:
        student.user.delete()
    else:   
        student.delete()
    return Response(data={"session_url": session_url})       
 

# Account recovery
def forgot_password_get(request):
    return render(request, 'account/forgot.html')

def reset_password_get(request,  uidb64, token):
    try :
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except Exception as e:
        user = None
    
    if user and default_token_generator.check_token(user, token):
        uid = uidb64
        emaildb64 = urlsafe_base64_encode(force_bytes(user.email))
        reset_password_api_url = reverse("account:reset_password_api", args=(uid, emaildb64))
        return render(request, 'account/setup_new_pass.html', context={'reset_password_api_url':reset_password_api_url})
    else:
        return render_error(request, 'Invalid or expired recovery link')
 
# REST API SECTION BELOW

class UnauthorizedException(APIException):
    status_code = 403
    default_detail = 'Unauthorized'
    
class BadrequestException(APIException):
    status_code = 400
    default_detail = 'Bad Request'
    
@api_view(['POST'])
def api_login(request):
    user = authenticate(username=request.data['email'], password=request.data['password'])
    if user:
        login(request, user)
        success_url = reverse("results:dashboard")
        return Response({'status':'logged in', 'succes_url': success_url}, status=HTTP_200_OK)
    else:
        return Response({'status':'Invalid Credentials'}, status=HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def create_admin_account(request, tokenId):
    try:
        token = InviteToken.objects.get(id=tokenId)
    except InviteToken.DoesNotExist:
        return Response(data={"details": "Invalid Token"}, status=HTTP_400_BAD_REQUEST)
    # checking expiration
    timenow = timezone.now()
    if token.expiration <= timenow:
        return Response(data={"details": "Token Expired"}, status=HTTP_400_BAD_REQUEST)
    # to user dept (if specified in the invitation)
    admin_account_data = {
        'invited_by': token.from_user
    }
    if token.to_user_dept_id:
        try:
            print(token.to_user_dept_id)
            dept = Department.objects.get(id=token.to_user_dept_id)
        except Department.DoesNotExist:
            return Response(data={"details": "Corrupted token"}, status=HTTP_400_BAD_REQUEST)
        admin_account_data['dept'] = dept
        admin_account_data['is_super_admin'] = False
    else:
        admin_account_data['is_super_admin'] = True
    # user cration
    user_data = {
        "username": token.user_email,
        "email": token.user_email
    }
    try:
        user_data['first_name'] = request.data['first_name']
        password = request.data['password']
        if last_name:= request.data.get('last_name', False):
            user_data['last_name'] = last_name
    except KeyError:
        return Response(data={"details": "Data Missing"}, status=HTTP_400_BAD_REQUEST)
    user = User(**user_data)
    user.set_password(password)
    user.save()
    admin_account_data['user'] = user
    # creating adminaccount
    admin = AdminAccount(**admin_account_data)
    admin.save()
    login(request, user)
    # deleting token
    token.delete()
    return Response(data={'status': "Account Created"})

class StudentAccountCreate(CreateAPIView):
    # To be used by admin user
    serializer_class = StudentAccountSerializer
    permission_classes = [IsAuthenticated]
    queryset = StudentAccount.objects.all()
    
    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'adminaccount'):
            raise UnauthorizedException("User not authorized")
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))
   

@api_view(['POST'])
def send_signup_token(request):
    if not hasattr(request.user, 'adminaccount'):
        print("no admin")
        return Response(data={'details': "Unauthorized"}, status=HTTP_401_UNAUTHORIZED)
    try:
        to_user_email = request.data['to_email']
    except KeyError:
        return Response(data={'details': "No email provided"}, status=HTTP_400_BAD_REQUEST)
    # checking if user exists with this email
    users = User.objects.filter(email=to_user_email)
    if users.count():
        return Response(data={'details': "User with this email already exists!"}, status=HTTP_400_BAD_REQUEST)
    to_user_dept = None
    if request.user.adminaccount.is_super_admin:
        if not request.data.get('is_to_user_superadmin', True):
            try:
                to_user_dept = request.data['to_user_dept']
            except KeyError:
                return Response(data={'details': "No department provided"}, status=HTTP_400_BAD_REQUEST)
    else:
        to_user_dept = request.user.adminaccount.dept.id
    expiration = timezone.now() + timedelta(days=7)
    invite_token = InviteToken(
        from_user = request.user,
        user_email = to_user_email,
        to_user_dept_id = to_user_dept,
        expiration = expiration
    )
    invite_token.save()
    try:
        utils.send_signup_email(request, invite_token)
    except Exception as e:
        return Response(data={'details': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response(data={"status": "Invitation email sent"}, status=HTTP_200_OK)
    
# Account Recovery API's
@api_view(["POST"])
def send_recovery_email_api(request):
    email_subject = "Password Recovery"
    try:
        email = request.data['email']
    except Exception as e:
        return Response(data={"error":"no email provided"}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.filter(email=email).first()
    if user is None:
        return Response(data={'info':'no user found with this email'}, status=status.HTTP_404_NOT_FOUND)
    # # checking if user has account
    # if not hasattr(user, 'account'):
    #     return Response(data={"info":"user has no account"}, status=status.HTTP_409_CONFLICT)

    uid = urlsafe_base64_encode(force_bytes(user.id))
    token = default_token_generator.make_token(user)
    recovery_url = request.build_absolute_uri(reverse("account:reset_password_get", args=(uid, token)))
    email_body = render_to_string('account/recovery_mail.html', context={
        "user": user,
        "recovery_url": recovery_url
    })
    try:
        utils.send_html_email(user.email, email_subject, email_body)
    except Exception as e:
        return Response(data={'info':'cannot send email'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(data={"info":"email sent"}, status=status.HTTP_200_OK)
    
    
@api_view(["POST"])
def reset_password_api(request, uidb64, emailb64):
    try :
        user_id = force_str(urlsafe_base64_decode(uidb64))
        email = force_str(urlsafe_base64_decode(emailb64))
        user = User.objects.get(pk=user_id, email=email)
    except Exception as e:
        user = None
    try:
        new_pass = request.data['new_password']
    except KeyError:
        return Response(data={"info":"required data not provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    if user is not None:
        user.set_password(new_pass)
        user.save()
        logout(request)
        return Response(data={"info":"password reset successful"},status=status.HTTP_200_OK)
    else:
        return Response(data={"info":"User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_admin_account(request):
    if not hasattr(request.user, 'adminaccount'):
        return Response(data={'details': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    try:
        first_name = request.data['first_name']
        last_name = request.data['last_name']
    except KeyError:
        return Response(data={'details': 'Necessary data not provided'}, status=status.HTTP_400_BAD_REQUEST)
    user = request.user
    user.first_name = first_name
    user.last_name = last_name
    try:
        user.save()
    except Exception as e:
        return Response(data={'details': 'Cannot update'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(data={'status': 'Changes Saved'})