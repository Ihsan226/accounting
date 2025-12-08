from .models import UserProfile

def user_profile_context(request):
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            user_profile = None
        return {'user_profile': user_profile}
    return {}
