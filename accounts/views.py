import os
import random
import requests
from dotenv import load_dotenv
from django.core.cache import cache
from django.shortcuts import redirect
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView

from allauth.socialaccount.models import SocialApp
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter

load_dotenv()
User = get_user_model()


# Sign-in with Facebook
class RedirectToFacebookAPiView(APIView):
    def get(self, request):
        facebook_redirect_url = os.getenv('FACEBOOK_REDIRECT_URL')
        facebook_app_id = os.getenv('FACEBOOK_APP_ID')
        try:
            url = f'https://www.facebook.com/v9.0/dialog/oauth?client_id={facebook_app_id}&redirect_uri={facebook_redirect_uri}&scope=email,public_profile'
        except SocialApp.DoesNotExist:
            return Response({'success': False}, status=status.HTTP_400_BAD_REQUEST)
        return redirect(url)


class FacebookLoginApiView(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    callback_uri = 'http://127.0.0.1:8000/accounts/facebook/callback-facebook'
    client_class = OAuth2Client


@api_view(['GET'])
def callback_facebook(request):
    code = request.query_params.get('code')
    if not code:
        return Response({'error': 'Code query parameter missing'}, status=400)
    try:
        response = requests.get("https://graph.facebook.com/v9.0/oauth/access_token", params={
            'client_id': os.getenv('FACEBOOK_APP_ID'),
            'redirect_uri': os.getenv('FACEBOOK_REDIRECT_URI'),
            'client_secret': os.getenv('FACEBOOK_APP_SECRET'),
            'code': code,
        })
        response.raise_for_status()
        data = response.json()
        access_token = data.get('access_token')

        if access_token:
            user_info_response = requests.get("https://graph.facebook.com/me", params={
                'fields': 'id,name,email',
                'access_token': access_token,
            })
            user_info_response.raise_for_status()
            user_info = user_info_response.json()

            return Response({'access_token': access_token, 'user_info': user_info}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Access token not found.'}, status=status.HTTP_400_BAD_REQUEST)
    except requests.exceptions.RequestException as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Google sign-in
class RedirectToGoogleAPIView(APIView):

    def get(self, request):
        google_redirect_uri = os.getenv('GOOGLE_REDIRECT_URL')
        try:
            google_client_id = SocialApp.objects.get(provider='google').client_id
        except SocialApp.DoesNotExist:
            return Response({'success': False, 'message': 'SocialApp does not exist'}, status=404)
        url = f'https://accounts.google.com/o/oauth2/v2/auth?redirect_uri={google_redirect_uri}&prompt=consent&response_type=code&client_id={google_client_id}&scope=openid email profile&access_type=offline'
        return redirect(url)


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://127.0.0.1:8000/accounts/google/callback'
    client_class = OAuth2Client


@api_view(["GET"])
def callback_google(request):
    code = request.GET.get("code")
    res = requests.post("http://127.0.0.1:8000/accounts/google", data={"code": code}, timeout=30)
    return Response(res.json())

